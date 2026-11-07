# Informe académico y evidencia de auditoría

- [Informe_Compiladores.docx](Informe_Compiladores.docx) contiene texto, títulos y tablas editables.
- [Informe_Compiladores.pdf](Informe_Compiladores.pdf) se exporta desde el DOCX con Word.
- [diagramas/](diagramas/) contiene las siete fuentes Mermaid, incluidas las salidas representativas del compilador.
- [pruebas/](pruebas/) contiene las entradas completas de las cinco situaciones y los resultados esperados en `casos.json`.
- [evidencias/](evidencias/) conserva el historial, las compilaciones, los resultados y los artefactos generados por cada alternativa.

## Compilar y ejecutar las pruebas

En la raíz del repositorio, con Bash de MSYS2, GNU Make ≥ 4.3, GCC, Bison y Flex:

```bash
make clean
make -j4 CFLAGS="-Wall -Wextra -Werror -std=c11 -g"
make test
```

Las 21 alternativas de auditoría requieren Python 3.10+, Node.js, Mermaid CLI y Chromium. El entorno comprobado usó Mermaid CLI 11.12.0, Mermaid 11.17.2 y Chrome. Este ejemplo para PowerShell instala las dependencias de Mermaid en un directorio temporal y reutiliza Chrome:

```powershell
$env:Path = 'C:\msys64\usr\bin;' + $env:Path
$env:PUPPETEER_SKIP_DOWNLOAD = 'true'
$mermaidDeps = Join-Path $env:TEMP 'dfdraw-mermaid'
npm.cmd install --prefix $mermaidDeps @mermaid-js/mermaid-cli@11.12.0 mermaid@11.17.2
$cli = Join-Path $mermaidDeps 'node_modules/@mermaid-js/mermaid-cli/src/cli.js'
$chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
python informe/ejecutar_pruebas.py --binario ./dfdc.exe --evidencia "$env:TEMP/dfdraw-repeticion" --mmdc-js $cli --chrome $chrome
```

`--evidencia` requiere una ruta nueva. El ejecutor devuelve 0 cuando se aprueban todas las alternativas y 1 si alguna falla o queda bloqueada. Cada caso usa su propio directorio temporal y copia la entrada como `entrada.dfd`. Los resultados distinguen el código del compilador del de Mermaid CLI. El bloque `render` registra la salida adicional del renderizador y el comando con sus argumentos exactos.

Para reconstruir la línea de base, extraé `git archive 3560506` en un directorio separado. Dentro de esa copia ejecutá primero `make clean` y `make` para reproducir la falla de enlace. Luego agregá únicamente el objeto omitido al enlace:

```bash
gcc -Wall -Wextra -g -c diccionario.c
make OBJECTS="main.o ast.o semantic.o mermaid.o parser.tab.o lex.yy.o diccionario.o"
```

Repetí `ejecutar_pruebas.py` con ese binario y una ruta de evidencia nueva. Los ocho casos fallidos de la línea de base corresponden a fallas del producto. Las pruebas negativas aprobadas corresponden a rechazos previstos.

## Regenerar el informe

Instalá `python-docx` y `Pillow` en el entorno de Python para generar el Word. El generador toma el contenido de `armar_informe.py`, las entradas, la evidencia archivada y los Mermaid de `diagramas/`. Para actualizar una figura de caso, copiá su `salida.mmd` desde la evidencia que corresponde a esa ejecución.

```powershell
python informe/armar_informe.py --mmdc-js $cli --chrome $chrome
pwsh -NoProfile -File informe/exportar_pdf.ps1
```

El exportador requiere Microsoft Word para Windows y abre el DOCX para repaginar y exportar el PDF. Las figuras se generan con tema neutral y se incorporan con respaldo PNG. La figura S03B usa PNG de alta resolución para conservar las etiquetas HTML con caracteres especiales. El SVG correspondiente se guarda en su evidencia. Se puede renderizar el PDF con Poppler para revisar la paginación.
