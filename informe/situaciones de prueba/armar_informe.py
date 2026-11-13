"""Genera el DOCX académico a partir del texto, las pruebas y los Mermaid del informe."""

import argparse
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.shared import Inches, Pt, RGBColor
from lxml import etree
from PIL import Image


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidencias/ejecuciones"
AUTHORS = ("Nicolas Gonzalez Heinrich", "Bewig Alejo", "Decunha Lucas", "Enriquez Emiliano")
TITLE = "Compilador para la Generación Automática de Diagramas de Flujo de Datos"
FIGURES = {
    "arquitectura": ("Arquitectura del compilador y rutas de generación", 4.15),
    "flujo_compilacion": ("Dependencias de compilación del ejecutable", 2.9),
    "S01A": ("DFD mínimo con un proceso aislado", 1.25),
    "S02A": ("DFD de atención con las tres formas y cinco flujos", 1.9),
    "S03B": ("DFD con caracteres especiales en etiquetas", 2.05),
    "S04A": ("Proyección gráfica de una entrada con diccionario", 1.45),
    "S05A": ("Componentes gráficos de la prueba de capacidad", 1.35),
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_figures(args, workspace):
    command = ["node", str(args.mmdc_js.resolve(strict=True))] if args.mmdc_js else [shutil.which("mmdc")]
    if not command[0]:
        raise SystemExit("Instalá Mermaid CLI o indicá --mmdc-js.")
    if args.chrome:
        browser = workspace / "puppeteer.json"
        browser.write_text(json.dumps({"executablePath": str(args.chrome.resolve(strict=True))}),
                           encoding="utf-8")
        command += ["-p", str(browser)]

    def render(name):
        config = "mermaid_html.json" if name == "S03B" else "mermaid.json"
        source = ROOT / "diagramas" / f"{name}.mmd"
        if name.startswith("S"):
            assert source.read_bytes() == (EVIDENCE / "final" / name / "salida.mmd").read_bytes()
        options = [*command, "-c", str(ROOT / "diagramas" / config), "-t", "neutral",
                   "-i", str(source)]
        svg, png = (workspace / f"{name}.{extension}" for extension in ("svg", "png"))
        for path in (svg, png):
            if name == "S03B" and path == svg:
                continue
            size = ["-s", "3"] if path == png else []
            result = subprocess.run([*options, "-o", str(path), *size],
                                    capture_output=True, timeout=90)
            if result.returncode:
                raise RuntimeError(f"{name}: {result.stderr.decode('utf-8', 'replace')}")
        with Image.open(png) as raster:
            monochrome = raster.convert("L")
        monochrome.save(png)
        if svg.exists():
            tree = etree.parse(str(svg))
            root = tree.getroot()
            _, _, width, height = root.get("viewBox").split()
            root.set("width", width)
            root.set("height", height)
            tree.write(str(svg), encoding="utf-8")
        return name, (svg, png)

    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(pool.map(render, FIGURES))


def element(name, **attributes):
    node = OxmlElement(name)
    for key, value in attributes.items():
        node.set(qn(f"w:{key}"), str(value))
    return node


class Report:
    def __init__(self, figures):
        self.doc = Document()
        self.figures = figures
        self.setup()

    def setup(self):
        doc = self.doc
        doc.core_properties.title = TITLE
        doc.core_properties.subject = "Auditoría técnica y validación funcional de DFDraw"
        doc.core_properties.author = ", ".join(AUTHORS)
        section = doc.sections[0]
        section.page_width, section.page_height = Inches(8.27), Inches(11.69)
        section.top_margin, section.bottom_margin = Inches(0.78), Inches(0.76)
        section.left_margin = section.right_margin = Inches(0.85)
        section.footer_distance = Inches(0.34)
        section.different_first_page_header_footer = True

        styles = doc.styles
        for name, size in [("Normal", 10.5), ("Title", 27), ("Subtitle", 13),
                           ("Heading 1", 18), ("Heading 2", 13), ("Heading 3", 11),
                           ("Caption", 9), ("Footer", 8)]:
            style = styles[name]
            style.font.name = "Arial"
            style.font.size = Pt(size)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.element.get_or_add_rPr().append(element("w:lang", val="es-AR"))
        normal = styles["Normal"].paragraph_format
        normal.space_after = Pt(7)
        normal.line_spacing = 1.12
        for name in ("Heading 1", "Heading 2", "Heading 3"):
            style = styles[name]
            style.font.bold = True
            style.font.italic = False
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(5)
        styles["Title"].font.bold = True
        styles["Title"].paragraph_format.space_after = Pt(14)
        styles["Subtitle"].font.italic = False
        styles["Caption"].font.italic = False
        styles["Caption"].paragraph_format.space_before = Pt(2)
        styles["Caption"].paragraph_format.space_after = Pt(8)
        styles["Caption"].paragraph_format.keep_with_next = False
        for name in ("Title", "Subtitle"):
            props = styles[name].element.get_or_add_pPr()
            border = props.find(qn("w:pBdr"))
            if border is not None:
                props.remove(border)

        code = styles.add_style("Listado", WD_STYLE_TYPE.PARAGRAPH)
        code.font.name, code.font.size = "Consolas", Pt(8.4)
        code.paragraph_format.line_spacing = Pt(10.3)
        code.paragraph_format.space_after = Pt(5)
        code.paragraph_format.left_indent = Inches(0.16)
        code.paragraph_format.right_indent = Inches(0.06)
        code.paragraph_format.keep_together = True

        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer.add_run("DFDRAW  ·  COMPILADORES      ")
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        footer._p.append(field)

    def paragraph(self, text, style=None):
        return self.doc.add_paragraph(text, style)

    def heading(self, title, level=1, new_page=False):
        heading = self.doc.add_heading(title, level)
        heading.paragraph_format.page_break_before = new_page
        return heading

    def code(self, text):
        return self.paragraph(text.rstrip("\r\n") if text else "∅", "Listado")

    def field(self, label, text, compact=True):
        paragraph = self.paragraph("")
        paragraph.add_run(f"{label}. ").bold = True
        paragraph.add_run(text)
        if compact:
            paragraph.paragraph_format.space_after = Pt(2.5)
        return paragraph

    def table(self, headers, rows, widths):
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.autofit = False
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for col, width in zip(table.columns, widths):
            col.width = Inches(width)

        borders = element("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borders.append(element(f"w:{side}", val="single", sz=5, color="D9D9D9"))
        table._tbl.tblPr.append(borders)
        table.rows[0]._tr.get_or_add_trPr().append(element("w:tblHeader"))
        for index, values in enumerate([headers, *rows]):
            row = table.rows[0] if index == 0 else table.add_row()
            row._tr.get_or_add_trPr().append(element("w:cantSplit"))
            for cell, value, width in zip(row.cells, values, widths):
                cell.width = Inches(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if index == 0:
                    cell._tc.get_or_add_tcPr().append(element("w:shd", fill="EEEEEE"))
                paragraph = cell.paragraphs[0]
                paragraph.paragraph_format.space_before = Pt(4)
                paragraph.paragraph_format.space_after = Pt(4)
                run = paragraph.add_run(str(value))
                run.bold = index == 0
                run.font.size = Pt(9)
        self.paragraph("").paragraph_format.space_after = Pt(0)

    def figure(self, name):
        description, max_height = FIGURES[name]
        svg, png = self.figures[name]
        with Image.open(png) as image:
            pixel_width, pixel_height = image.size
        ratio = pixel_width / pixel_height
        width = min(6.45, max_height * ratio, pixel_width / 180)
        paragraph = self.paragraph("")
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.keep_with_next = True
        paragraph.paragraph_format.space_after = Pt(0)
        shape = paragraph.add_run().add_picture(str(png), width=Inches(width))
        shape._inline.docPr.set("descr", description)
        if svg.exists():
            part = Part(PackURI(f"/word/media/{name}.svg"), "image/svg+xml",
                        svg.read_bytes(), self.doc.part.package)
            relationship = self.doc.part.relate_to(
                part, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
            blip = shape._inline.xpath(".//a:blip")[0]
            extensions = etree.SubElement(blip, qn("a:extLst"))
            extension = etree.SubElement(extensions, qn("a:ext"))
            extension.set("uri", "{96DAC541-7B7A-43D3-8B79-37D633B846F1}")
            svg_blip = etree.SubElement(extension,
                "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip")
            svg_blip.set(qn("r:embed"), relationship)
        caption = self.paragraph(
            f"Figura {list(FIGURES).index(name) + 1}. {description}", "Caption")
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def cover(self):
        center = WD_ALIGN_PARAGRAPH.CENTER
        top = self.paragraph("Universidad Gastón Dachary")
        top.alignment = center
        top.paragraph_format.space_before = Pt(69)
        top.runs[0].bold = True
        self.paragraph("Posadas, Misiones, Argentina").alignment = center
        self.paragraph("Asignatura Compiladores · 2026").alignment = center
        title = self.paragraph(TITLE, "Title")
        title.alignment = center
        title.paragraph_format.space_before = Pt(74)
        self.paragraph("Auditoría técnica y validación funcional de DFDraw", "Subtitle").alignment = center
        authors = self.paragraph("\n".join(AUTHORS))
        authors.alignment = center
        authors.paragraph_format.space_before = Pt(52)
        authors.paragraph_format.line_spacing = 1.55
        date = self.paragraph("7 de noviembre de 2026")
        date.alignment = center
        date.paragraph_format.space_before = Pt(42)


def write_body(r):
    r.heading("Resumen", new_page=True)
    r.paragraph(
        "Se auditó un compilador de diagramas de flujo de datos basado en Flex, Bison y C. "
        "La versión corregida genera un DFD en Mermaid y un diccionario CSV. La compilación "
        "desde cero y cinco situaciones reproducibles permiten comparar la versión original "
        "con la corregida, incluidos los rechazos del lenguaje y los errores de salida.")
    r.field("Palabras clave", "Compiladores, DSL, análisis léxico, análisis sintáctico, DFD, Mermaid.")
    r.heading("1 Introducción")
    r.paragraph(
        "DFDraw es un compilador para un lenguaje específico de dominio que describe "
        "Diagramas de Flujo de Datos (DFD). Una especificación textual expresa entidades "
        "externas, procesos, almacenes y flujos. El compilador reconoce la entrada, verifica "
        "las reglas del modelo y genera Mermaid y un diccionario de datos en CSV.")
    r.paragraph(
        "El trabajo conserva la motivación del informe inicial. Separar el modelado del "
        "dibujo permite versionar el DFD como texto y detectar relaciones inválidas antes de "
        "generar el gráfico. La separación entre análisis y síntesis también permite observar "
        "el papel del escáner, el parser, el AST y los generadores de salida [1–4].")
    r.heading("2 Estado del proyecto")
    final = read_json(EVIDENCE / "final/resumen.json")
    base = read_json(EVIDENCE / "base/resumen.json")
    r.paragraph(
        "El prototipo implementa análisis léxico con Flex, análisis sintáctico con Bison, "
        "un AST gráfico, reglas de dominio y dos salidas de texto. Mermaid CLI renderiza el "
        "diagrama después de la compilación. El diccionario normaliza expresiones y valida "
        "la clave de cada asignación.")
    r.table(("Verificación", "Resultado registrado"), [
        ("Compilación limpia", "Flex, Bison y GCC ejecutados con las fuentes del repositorio. "
         "GCC con advertencias como errores. Bison sin conflictos reportados."),
        ("Suite histórica", "7 aprobadas. También se ejecutaron los cinco ejemplos válidos y prueba.dfd."),
        ("Suite de auditoría", f"{final['APROBADA']} aprobadas, {final['FALLIDA']} fallidas y "
         f"{final['BLOQUEADA']} bloqueadas en la versión corregida."),
        ("Línea de base", f"{base['FALLIDA']} fallas funcionales tras añadir únicamente el objeto "
         "omitido en el enlazado de una copia aislada."),
    ], (1.72, 4.78))
    r.paragraph(
        "El alcance actual termina en la traducción del DFD y la generación del diccionario. "
        "Quedan pendientes los niveles de descomposición, su balance y la resolución de "
        "identificadores o evaluación de rangos dentro de las expresiones del diccionario.")

    r.heading("3 Arquitectura y estructura del repositorio", new_page=True)
    r.figure("arquitectura")
    r.paragraph("El parser construye el AST gráfico y registra las entradas del diccionario durante "
                "las reducciones. El controlador autoriza ambas salidas tras comprobar los diagnósticos.")
    r.code(
        "DFDraw/\n"
        "  lexer.l, parser.y            Especificaciones de Flex y Bison\n"
        "  main.c, ast.*, semantic.*    Controlador, nodos y validaciones\n"
        "  mermaid.*, diccionario.*     Generadores de Mermaid y CSV\n"
        "  Makefile, build/             Reglas y archivos derivados locales\n"
        "  examples/{valid,invalid}/    Entradas de ejemplo\n"
        "  prueba.dfd                   Ejemplo de diccionario completo\n"
        "  tests/run_tests.sh           Suite histórica\n"
        "  scripts/render.sh            Adaptador de Mermaid CLI\n"
        "  docs/GRAMATICA.md, README.md  Lenguaje e instrucciones\n"
        "  Paper_Compilador_*.pdf        Informe académico de referencia\n"
        "  informe/                     Informe, entradas, fuentes y evidencias")
    r.paragraph("El directorio build contiene el código generado, las dependencias y los objetos. "
                "El ejecutable conserva su ubicación en la raíz. Los SVG de evidencia y los .mmd "
                "de figuras son entregables reproducibles de la auditoría.")

    r.heading("4 Diseño del lenguaje", new_page=True)
    r.heading("4.1 Tokens y prioridad", 2)
    r.table(("Familia", "Tokens y formas"), [
        ("Reservadas", "T_DFD, T_ENTIDAD, T_PROCESO, T_ALMACEN, T_FLUJO, "
         "T_ESTRUCTURA y T_ELEMENTO. Coincidencias exactas en mayúscula."),
        ("Atributos de texto", "T_ID con [a-zA-Z_][a-zA-Z0-9_]*, T_NUMERO con [0-9]+ "
         "y T_STRING para literales entre comillas dobles."),
        ("Operadores", "T_ARROW (->), T_IGUAL (=), T_MAS (+), T_GUION (-) y T_PIPE (|)."),
        ("Delimitadores", "Llaves, corchetes, paréntesis y el token literal ';'."),
    ], (1.42, 5.08))
    r.paragraph(
        "Flex selecciona el lexema más largo. Ante un empate, aplica la primera regla. "
        "Así, DFD es una reservada y DFD_2 es un identificador. Los espacios, las "
        "tabulaciones, CR, LF y comentarios de línea // o # se omiten fuera de las cadenas. "
        "Las cadenas admiten saltos de línea y se decodifican las comillas y la barra invertida "
        "escapadas. Las demás secuencias con barra invertida permanecen literales.")
    r.heading("4.2 Producciones", 2)
    r.code(
        'programa ::= "DFD" STRING "{" declaraciones "}" cierre\n'
        'cierre ::= ε | ";"\n'
        'declaraciones ::= ε | declaraciones declaracion\n'
        'declaracion ::= entidad | proceso | almacen | flujo\n'
        '              | estructura | elemento | definicion\n'
        'entidad ::= "ENTIDAD" ID STRING ";"\n'
        'proceso ::= "PROCESO" ID STRING ";"\n'
        'almacen ::= "ALMACEN" ID STRING ";"\n'
        'flujo ::= "FLUJO" ID "->" ID STRING ";"\n'
        'estructura ::= "ESTRUCTURA" ID STRING ";"\n'
        'elemento ::= "ELEMENTO" ID STRING ";"\n'
        'definicion ::= ID "=" expresion ";" | STRING "=" expresion ";"\n'
        'expresion ::= termino | expresion "+" termino\n'
        'termino ::= ID | STRING | NUMERO | "{" expresion "}"\n'
        '          | NUMERO "{" expresion "}" NUMERO | "(" expresion ")"\n'
        '          | "[" opciones "]" | termino "-" termino\n'
        'opciones ::= expresion | opciones "|" expresion')
    r.paragraph("El guion pertenece al término y tiene precedencia sobre la concatenación. "
                "La declaración %right T_GUION conserva la agrupación a la derecha que Bison "
                "elegía al desplazar. La concatenación y la lista de opciones se construyen "
                "mediante recursión izquierda. S04A y S04B ejemplifican ambas familias.")

    r.heading("5 Implementación y gestión de errores", new_page=True)
    r.heading("5.1 Interacción de Flex y Bison", 2)
    r.paragraph(
        "main.c abre la entrada, inicializa yyin y llama a yyparse. El parser solicita "
        "tokens a yylex. Los valores de ID, STRING y NUMERO llegan por yylval.str y los "
        "tipos se comparten en parser.tab.h. La regla residual devuelve T_INVALID, incrementa "
        "lexical_errors e informa el carácter y la línea. Si el parser recibe ese token, "
        "yyerror evita un diagnóstico sintáctico secundario.")
    r.paragraph(
        "Las producciones construyen nodos con ast_create_named y ast_create_flow. "
        "ast_create_dfd agrupa la lista bajo la raíz. Ante un descarte sintáctico, los "
        "destructores de Bison liberan cadenas y listas parciales. El parser informa el "
        "primer error sintáctico con línea, token observado y tokens esperados cuando "
        "Bison puede determinarlos. La gramática carece de producciones de recuperación.")
    r.heading("5.2 Reglas del modelo y del diccionario", 2)
    r.paragraph(
        "semantic_validate verifica unicidad de ID entre los elementos gráficos. Para cada "
        "flujo exige etiqueta no vacía, extremos declarados y distintos y al menos un proceso. "
        "Busca los extremos en la lista del AST completa, lo que permite referencias "
        "adelantadas. Un bloque vacío, un elemento aislado y un proceso sin entrada o sin "
        "salida son construcciones admitidas.")
    r.paragraph(
        "registrar_diccionario mantiene una lista dinámica en orden de registro. Usa el ID "
        "en almacenes, estructuras y elementos, y la etiqueta en flujos. Una asignación exige "
        "un nombre registrado previamente. Las claves que se repiten dentro de la misma "
        "categoría se agrupan. Si coinciden entre categorías, la asignación toma la primera "
        "registrada. Las expresiones del lado derecho se serializan como texto. El registro "
        "es independiente del AST y sus búsquedas son lineales.")
    r.heading("5.3 Salidas y códigos de proceso", 2)
    r.paragraph(
        "mermaid_generate emite primero los nodos y después las aristas. El prefijo n_ evita "
        "colisiones con palabras como end de Mermaid. Las etiquetas se protegen mediante "
        "códigos de entidad y sus saltos de línea se convierten en espacios. Las entidades "
        "son rectángulos, los procesos son círculos y datastore presenta dos bordes "
        "horizontales. La forma requiere Mermaid 11.3 o superior [5].")
    r.paragraph(
        "generar_csv_diccionario escribe cuatro secciones y tres campos por fila, con "
        "separador punto y coma. Los campos con delimitador, comillas o saltos se citan, "
        "y las comillas internas se duplican. Ambas salidas comprueban apertura, escritura "
        "y cierre. El ejecutable usa código 0 cuando ambas se generan y 1 ante un error "
        "controlado. Los errores léxicos, sintácticos y semánticos detienen la generación. "
        "Ante un fallo de CSV puede quedar el Mermaid que ya se escribió.")

    r.heading("6 Auditoría del historial y de la estructura", new_page=True)
    r.paragraph(
        "Se inspeccionó main con referencia local origin/main en 3560506. El estado inicial "
        "mostraba el PDF académico sin seguimiento y no mostraba cambios en archivos "
        "versionados. El historial local contiene tres commits. Se compararon sus archivos "
        "y parches con git log, git show y git diff. No se actualizó la referencia remota.")
    r.heading("6.1 Revisión de los commits", 2)
    r.field("5782ac8 · Initial commit",
            "Alta de README.md con el nombre DFDraw. Establece la identidad del repositorio. "
            "En ese punto todavía no había fuentes, dependencias declaradas ni pruebas. "
            "El siguiente commit incorporó la implementación.")
    r.field("eb01b33 · Add files via upload",
            "Modifica README.md y agrega Makefile, ast.[ch], main.c, semantic.[ch], "
            "mermaid.[ch], lexer.l.c, parser.c, docs/GRAMATICA.md, scripts/render.sh, "
            "tests/run_tests.sh y siete entradas bajo examples. Introduce el AST, las "
            "validaciones del dominio y Mermaid. El Makefile pedía lexer.l y parser.y, "
            "ausentes en ese commit. Las fuentes añadidas correspondían a un front-end "
            "manual. El siguiente commit incorpora las especificaciones requeridas.")
    r.field("3560506 · Implementacion del diccionario de datos en CSV y actualizacion del compilador",
            "Agrega diccionario.[ch], diccionario.csv, lexer.l, parser.y, lex.yy.c, "
            "parser.tab.[ch], prueba.dfd, salida.mmd y los ejemplos atencion_chat, prisma "
            "y simulacion_trafico. Elimina lexer.l.c y parser.c. Modifica main.c y Makefile. "
            "Los cambios en scripts/render.sh y tests/run_tests.sh corresponden a fines de "
            "línea. El nuevo front-end conserva las reglas gráficas y agrega el diccionario, "
            "pero el enlace omite diccionario.o. También quedan un conflicto de guion, "
            "límites de almacenamiento inseguros y errores de salida sin propagar.")
    r.heading("6.2 Correcciones estructurales y compatibilidad", 2)
    r.paragraph(
        "El Makefile declara el diccionario, genera en build/ y usa una regla agrupada para "
        "los dos archivos de Bison. Se retiraron tres copias de C y cabecera generados y "
        "las dos salidas de ejemplo de la raíz, reproducibles desde prueba.dfd y el historial. "
        ".gitignore excluye derivados locales y .gitattributes fija LF para Bash. El informe "
        "de referencia se conservó. Se actualizaron README y la gramática para reflejar el "
        "nuevo diccionario, el uso de datastore y los comandos vigentes.")
    r.paragraph(
        "La suite histórica ahora aísla sus salidas y exige código 1 sin archivos nuevos "
        "para los casos negativos. El adaptador render.sh devuelve el resultado de mmdc. "
        "La evidencia del historial y del defecto de prefijo observado durante la corrección "
        "se conserva en evidencias/auditoria/.")

    r.heading("7 Compilación y ejecución", new_page=True)
    r.figure("flujo_compilacion")
    r.paragraph(
        "La ejecución se realizó en Windows con MSYS2, GNU Make 4.4.1, GCC 15.3.0, Flex 2.6.4 "
        "y Bison 3.8.2. La regla agrupada requiere GNU Make 4.3 o superior. El render se "
        "ejecutó con Mermaid CLI 11.12.0, Mermaid 11.17.2, Node.js 24.19.0 y Chrome 156.0.8078.81.")
    r.code(
        'make clean\n'
        'make -j4 CFLAGS="-Wall -Wextra -Werror -std=c11 -g"\n'
        'make test\n'
        './dfdc examples/valid/turnos.dfd salida.mmd\n'
        'bash scripts/render.sh salida.mmd salida.svg')
    r.paragraph(
        "La compilación original terminó con código 2 de make y referencias indefinidas "
        "al diccionario. Bison reportó un conflicto shift/reduce y GCC dos advertencias "
        "del escáner. La compilación corregida terminó con código 0 y sin advertencias. "
        "Los registros completos están en evidencias/compilacion/.")
    r.heading("8 Metodología de pruebas")
    r.paragraph(
        "Los oráculos se derivaron de parser.y, semantic.c, los ejemplos y el contrato "
        "de salida. Cada alternativa se ejecutó con límite de tiempo en un directorio "
        "independiente. El ejecutor comprobó el código de proceso, stderr, archivos "
        "generados, filas CSV y, para los casos válidos, los nodos, etiquetas y formas "
        "del SVG. Una negativa aprobada corresponde a un rechazo previsto.")
    r.paragraph(
        "El mismo conjunto se ejecutó sobre una copia de 3560506 que solo incorporó "
        "diccionario.o durante el enlace, y sobre la compilación corregida. Los JSON "
        "conservan el argv real, el directorio, stdout, stderr y el resultado del render. "
        "Los diagnósticos de ejecución se registran sin deducir tiempos.")


GROUP_SCOPE = {
    "01": "Se verifica la frontera entre un programa mínimo, una lista vacía válida y una entrada sin tokens.",
    "02": "Se inspeccionan el grafo generado, las referencias adelantadas y las restricciones sobre los flujos.",
    "03": "Se comprueba la prioridad léxica, la conservación de etiquetas y la clasificación del diagnóstico.",
    "04": "Se cubren las expresiones del diccionario y las fronteras sintácticas entre sus operandos y delimitadores.",
    "05": "Se comprueban la capacidad del diccionario, la validez de su clave y los fallos de entrada y salida.",
}

ANALYSIS = {
    "S01A": "El AST contiene un nodo de proceso y el SVG lo dibuja como un círculo. El CSV contiene las cuatro cabeceras.",
    "S01B": "Bison deriva una lista vacía y consume el punto y coma final. Mermaid se renderiza sin nodos.",
    "S01C": "El escáner entrega fin de archivo y Bison espera T_DFD en el estado inicial.",
    "S02A": "Las cinco aristas preservan origen, destino y etiqueta. El SVG conserva dos entidades rectangulares, dos procesos circulares y el almacén con dos bordes horizontales. El CSV contiene los registros correspondientes.",
    "S02B": "La búsqueda de extremos en el AST completo encuentra el proceso y el almacén aunque el flujo aparezca primero.",
    "S02C": "Los dos extremos existen. El error surge de la regla que exige un proceso en cada flujo.",
    "S02D": "La pasada de duplicados y la validación de flujos reportan cuatro errores independientes.",
    "S03A": "La coincidencia más larga conserva DFD_2 y _Origen9 como identificadores. Los dos tipos de comentario quedan fuera del flujo de tokens.",
    "S03B": "El prefijo n_ protege el ID end. Los códigos de entidad preservan los caracteres en el render con etiquetas HTML y la cita CSV mantiene nombre y definición en tres columnas.",
    "S03C": "La regla residual reconoce @ como carácter inválido. Bison aborta y deja al lexer como responsable del diagnóstico.",
    "S03D": "La comilla inicial carece de pareja y queda fuera del patrón de cadena. La regla residual informa el error en la línea.",
    "S04A": "El parser construye las expresiones y las normaliza como texto. ESTRUCTURA y ELEMENTO aparecen en CSV y quedan fuera del grafo.",
    "S04B": "El guion encadenado conserva la serialización 1-2-3. La palabra referencia queda como texto sin resolución del lado derecho.",
    "S04C": "T_PROCESO es un token válido. En esa posición la producción entidad todavía requiere un punto y coma.",
    "S04D": "El token T_CORCHETE_C aparece donde la producción de opciones necesita otra expresión.",
    "S05A": "Se verifican el nombre de más de 149 bytes, la definición de más de 499 bytes y la fila siguiente. El AST gráfico conserva dos nodos.",
    "S05B": "La clave ausente falla durante la asignación. El contador del diccionario se incorpora al estado semántico y evita las dos salidas.",
    "S05C": "La apertura del CSV falla por el directorio preexistente. Se informa el error y queda el Mermaid generado en el paso anterior.",
    "S05D": "La comprobación del nombre y del directorio resuelve que ./diccionario.csv corresponde a la ruta fija y evita escrituras.",
    "S05E": "El generador Mermaid no puede abrir el archivo de destino y el controlador interrumpe el proceso antes de escribir CSV.",
    "S05F": "La comparación de rutas detecta que el destino es la entrada. El ejecutor confirma que sus bytes se conservan.",
}

CORRECTIONS = {
    "S02A": "Durante la corrección se detectó un prefijo faltante en los procesos. Se aplicó a los nodos y a los dos extremos de cada arista.",
    "S04B": "Se declaró %right T_GUION y se verificó que Bison genera sin conflictos.",
    "S03B": "Se aislaron los IDs del DSL de los de Mermaid, se codificaron caracteres especiales y se agregó escape CSV.",
    "S03C": "Se suprimió el diagnóstico del parser cuando el lexer ya clasificó el error.",
    "S03D": "Se suprimió el diagnóstico del parser cuando el lexer ya clasificó el error.",
    "S05A": "Se reemplazaron el arreglo fijo y strcpy por una lista de entradas con memoria ajustada al texto.",
    "S05B": "Se cambió el diagnóstico a stderr y se contabilizó como error semántico.",
    "S05C": "El backend del diccionario devuelve el estado de apertura, escritura y cierre.",
    "S05D": "Se valida la identidad de las rutas antes de escribir.",
    "S05F": "Se valida la identidad de las rutas antes de escribir.",
}

BEFORE_FAILURES = {
    "S03B": "El CSV incluyó una fila con campos de más y Mermaid CLI devolvió un error de análisis en el ID end.",
    "S03C": "El programa devolvió 1 y stderr mostró un diagnóstico sintáctico secundario tras el léxico.",
    "S03D": "El programa devolvió 1 y stderr mostró un diagnóstico sintáctico secundario tras el léxico.",
    "S05A": "El CSV alteró el nombre largo y perdió la fila guardia. El programa informó éxito.",
    "S05B": "El diagnóstico de la clave ausente salió por stdout, seguido de una confirmación de éxito. Se escribieron ambos archivos.",
    "S05C": "El programa informó que había generado el CSV aunque la ruta correspondía a un directorio.",
    "S05D": "El CSV sobrescribió el Mermaid porque ambos apuntaron al mismo archivo.",
    "S05F": "El programa reemplazó los bytes de entrada con Mermaid y generó un CSV.",
}


def describe_expected(expected):
    phase = expected.get("phase", "valido")
    if phase == "valido":
        nodes = len(expected["nodes"])
        edges = expected.get("edgeCount", len(expected.get("edges", [])))
        node_word = "nodo" if nodes == 1 else "nodos"
        edge_word = "flujo" if edges == 1 else "flujos"
        return (f"Código 0, stderr vacío, Mermaid y CSV válidos. "
                f"El SVG debe contener {nodes} {node_word} y {edges} {edge_word}.")
    message = {
        "lexico": "Código 1 y diagnóstico léxico en stderr.",
        "sintactico": "Código 1 y diagnóstico sintáctico en stderr.",
        "semantico": "Código 1 y diagnóstico semántico en stderr.",
        "io": "Código 1 y diagnóstico de E/S en stderr.",
    }[phase]
    if expected.get("files"):
        return message + " Se espera solo salida.mmd."
    return message + " Se espera que la ejecución no genere archivos."


def write_tests(r):
    manifest = read_json(ROOT / "pruebas/casos.json")
    page_starts = {"S01B", "S02B", "S02D", "S03B", "S03C",
                   "S04B", "S04C", "S05C", "S05E"}
    for number, (group, name) in enumerate(manifest["groups"].items(), 1):
        title = f"9.{number} Situación {number} {name}"
        if number == 1:
            r.heading("9 Situaciones de prueba", new_page=True)
        r.heading(title, 2, new_page=number > 1)
        r.paragraph(GROUP_SCOPE[group])
        for case in (case for case in manifest["cases"] if case["group"] == group):
            identifier = case["id"]
            expected = case["expected"]
            original = read_json(EVIDENCE / "base" / identifier / "resultado.json")
            final = read_json(EVIDENCE / "final" / identifier / "resultado.json")
            source = ROOT / "pruebas" / f"situacion_{group}" / f"{identifier}.dfd"

            r.heading(f"{identifier} {case['title']}", 3, new_page=identifier in page_starts)
            r.field("Objetivo y justificación", case["reason"])
            field = r.field("Entrada completa", f"{source.relative_to(ROOT).as_posix()}.")
            field.paragraph_format.keep_with_next = True
            r.code(source.read_text(encoding="utf-8"))
            output = expected.get("output", "salida.mmd")
            setup = "El directorio temporal contiene una carpeta diccionario.csv. " if expected.get("setup") else ""
            r.field("Comando", f"{setup}dfdc entrada.dfd {output}")
            r.field("Resultado esperado", describe_expected(expected))

            if original["estado"] == "FALLIDA":
                r.field("Resultado original",
                        f"FALLIDA, código {original['codigo']}. {BEFORE_FAILURES[identifier]}")
            else:
                r.field("Resultado original", f"{original['estado']}, código {original['codigo']}.")
            if identifier in CORRECTIONS:
                r.field("Corrección", CORRECTIONS[identifier])
            result = f"{final['estado']}, código {final['codigo']}."
            files = final["archivos_compilador"]
            result += " Archivos del compilador: " + ", ".join(files) + "." if files else " Archivos nuevos: ninguno."
            if final["render"] and final["render"]["codigo"] == 0:
                result += " Mermaid CLI devolvió 0 y produjo salida.svg."
            r.field("Nueva ejecución", result)
            for label, key in (("Salida estándar", "stdout"), ("Salida de errores", "stderr")):
                if final[key]:
                    field = r.field(label, "")
                    field.paragraph_format.keep_with_next = True
                    r.code(final[key])
                else:
                    r.field(label, "Vacía.")
            r.field("Análisis técnico", ANALYSIS[identifier])
            r.field("Evidencia por versión", f"evidencias/ejecuciones/{{base,final}}/{identifier}/resultado.json.")
            if identifier in FIGURES:
                r.figure(identifier)


def write_results(r):
    r.heading("10 Resultados consolidados", new_page=True)
    manifest = read_json(ROOT / "pruebas/casos.json")
    states = ("APROBADA", "FALLIDA", "BLOQUEADA")

    def counts(version, identifiers):
        observed = [read_json(EVIDENCE / version / identifier / "resultado.json")["estado"]
                    for identifier in identifiers]
        return " / ".join(str(observed.count(state)) for state in states)

    rows = []
    for group, title in manifest["groups"].items():
        ids = [c["id"] for c in manifest["cases"] if c["group"] == group]
        rows.append((f"{group} {title}", ", ".join(ids), counts("base", ids), counts("final", ids)))
    ids = [c["id"] for c in manifest["cases"]]
    rows.append(("Total", len(ids), counts("base", ids), counts("final", ids)))
    r.paragraph("Las últimas dos columnas expresan aprobadas, fallidas y bloqueadas, en ese orden.")
    r.table(("Situación", "Alternativas", "Original", "Corregida"), rows, (2.22, 2.18, 1.04, 1.06))
    r.heading("10.1 Problemas corregidos", 2)
    r.table(("Hallazgo", "Corrección y comprobación"), [
        ("Enlace incompleto y conflicto de guion", "Regla de diccionario, generación limpia, "
         "dependencias y asociatividad explícita. Registros de make y S04B."),
        ("CSV alterado y clave sin propagar", "Cadenas dinámicas, escape de campos y código "
         "semántico. S03B, S05A y S05B."),
        ("Salida Mermaid inválida para etiquetas y algunos ID", "Prefijo uniforme y códigos "
         "de entidad. Nodos, etiquetas y direcciones inspeccionados en S02A y S03B."),
        ("Diagnóstico duplicado y fugas por descarte", "Supresión del mensaje secundario "
         "y destructores de Bison. Rechazo comprobado en S03C, S03D y S04C."),
        ("Fallas de salida y sobrescritura", "Verificación de escritura y cierre, "
         "comprobación de identidad y resultado de Mermaid CLI. S05C–S05F."),
    ], (2.33, 4.17))
    r.heading("10.2 Límites observados", 2)
    r.paragraph(
        "El diccionario conserva definiciones textuales y aplica el primer registro ante "
        "colisiones entre categorías. El CSV usa un nombre fijo y conviene aislar las "
        "ejecuciones concurrentes. Las dos escrituras son secuenciales. Una falla de CSV "
        "puede dejar el .mmd previo. La suite comprueba funcionalidad y casos de borde. "
        "El costo de las búsquedas lineales y de las pasadas de duplicados queda fuera de "
        "la medición de rendimiento.")
    r.paragraph(
        "Para etiquetas especiales, el motor ensayado conserva los caracteres en modo "
        "HTML. Su modo SVG de texto puede mostrar las entidades como literales. La figura "
        "S03B usa una imagen Mermaid de alta resolución para preservar las etiquetas "
        "al exportar en Word. Las demás figuras incluyen SVG en el DOCX y una imagen de "
        "respaldo. La exportación de Word incorpora las siete figuras como imágenes en el PDF.")

    r.heading("11 Conclusiones", new_page=True)
    r.paragraph(
        "DFDraw implementa el objetivo académico de traducir una especificación textual "
        "validada a una representación gráfica reproducible. Las cinco situaciones "
        "comprueban la aceptación del DSL, la clasificación de rechazos y la correspondencia "
        "entre la entrada, Mermaid y el diccionario. Las ocho fallas de la línea de base "
        "dejaron evidencia y quedaron resueltas en la repetición.")
    r.paragraph(
        "El proyecto ofrece una base para incorporar reglas de diccionario y de "
        "descomposición de DFD. Ese trabajo requiere definir el significado de referencias, "
        "rangos y niveles, además de establecer pruebas para esas reglas.")
    r.heading("12 Anexos y evidencias")
    r.table(("Ubicación", "Contenido"), [
        ("docs/GRAMATICA.md", "Léxico, producciones y reglas de dominio."),
        ("informe/pruebas/", "Cinco carpetas de entradas y casos.json con el oráculo."),
        ("evidencias/auditoria/", "Historial y cambios del diccionario."),
        ("evidencias/compilacion/", "Enlace original, conflicto Bison, compilación corregida y ejemplos."),
        ("evidencias/ejecuciones/", "Base y final con un resultado.json por alternativa y archivos reales."),
        ("diagramas/", "Siete fuentes Mermaid y configuración neutral de render."),
        ("informe/README.md", "Reproducción de pruebas y generación de Word y PDF."),
    ], (2.25, 4.25))
    r.paragraph(
        "El ejecutor automatizado reside en ejecutar_pruebas.py. En cada JSON se "
        "registran el comando original, los canales completos de salida y, cuando "
        "corresponde, el comando y resultado de Mermaid CLI. La copia de la entrada "
        "sobrescrita en la línea de base de S05F se preserva como evidencia de la falla.")
    r.heading("Referencias", 2)
    for reference in (
        "[1] Aho, A. V., Lam, M. S., Sethi, R. y Ullman, J. D. Compiladores. Principios, técnicas y herramientas. 2.ª ed. Pearson Educación, 2008.",
        "[2] Universidad Gastón Dachary. Compiladores. Análisis Léxico y generación automática de analizadores con Lex/Flex. Material de cátedra.",
        "[3] Universidad Gastón Dachary. Compiladores. Generación automática de analizadores sintácticos con Yacc/Bison. Material de cátedra.",
        "[4] Universidad Gastón Dachary. Construcción y manipulación de árboles de sintaxis abstracta para compiladores en C. Versión 1, 2016.",
        "[5] Mermaid Contributors. Flowchart Syntax. https://mermaid.js.org/syntax/flowchart.html",
        "[6] Mermaid Contributors. Mermaid CLI. https://github.com/mermaid-js/mermaid-cli",
        "[7] Gonzalez Heinrich, N., Bewig, A., Decunha, L. y Enriquez, E. Compilador para la Generación Automática de Diagramas de Flujo de Datos. Informe académico original conservado en la raíz.",
    ):
        r.paragraph(reference)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mmdc-js", type=Path)
    parser.add_argument("--chrome", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="dfdraw-informe-") as folder:
        report = Report(build_figures(args, Path(folder)))
        report.cover()
        write_body(report)
        write_tests(report)
        write_results(report)
        report.doc.save(ROOT / "Informe_Compiladores.docx")


if __name__ == "__main__":
    main()
