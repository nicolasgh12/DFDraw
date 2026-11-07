"""Ejecuta las cinco situaciones, valida las salidas y conserva evidencia por caso."""

import argparse
import csv
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "pruebas/casos.json"
NS = {"s": "http://www.w3.org/2000/svg"}
HEADERS = [
    ["ALMACENES DE DATOS", "", "ELEMENTOS"],
    ["FLUJO", "", "COMPONENTES"],
    ["ESTRUCTURA DE DATOS", "", "COMPONENTES"],
    ["ELEMENTO", "", "COMPONENTES"],
]


def execute(command, cwd, timeout):
    try:
        process = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
        return {
            "argv": command, "cwd": str(cwd), "codigo": process.returncode,
            "stdout": process.stdout.decode("utf-8", "replace"),
            "stderr": process.stderr.decode("utf-8", "replace"),
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        stdout = getattr(error, "stdout", None) or b""
        stderr = getattr(error, "stderr", None) or b""
        return {
            "argv": command, "cwd": str(cwd), "codigo": None,
            "stdout": stdout.decode("utf-8", "replace"),
            "stderr": stderr.decode("utf-8", "replace"), "incidencia": str(error),
        }


def validate_svg(path, expected):
    root = ET.parse(path).getroot()
    nodes = [
        group for group in root.findall(".//s:g", NS)
        if "node" in group.get("class", "").split()
    ]
    edge_labels = [
        group for group in root.findall(".//s:g", NS)
        if "edgeLabel" in group.get("class", "").split()
    ]
    expected_shapes = {"entity": "rect", "process": "circle", "store": "rect"}
    errors = []
    if len(nodes) != len(expected["nodes"]):
        errors.append(f"SVG contiene {len(nodes)} nodos, se esperaban {len(expected['nodes'])}.")
    for node_id, kind in expected["nodes"]:
        matches = [node for node in nodes if re.fullmatch(
            rf"(?:my-svg-)?flowchart-(?:n_)?{re.escape(node_id)}-\d+", node.get("id", "")
        )]
        shape = expected_shapes[kind]
        if not matches or matches[0].find(f"./s:{shape}", NS) is None:
            errors.append(f"El nodo SVG {node_id} no tiene la figura {shape}.")
        elif kind == "store":
            rect = matches[0].find("./s:rect", NS)
            horizontal_vertical = f"{rect.get('width')} {rect.get('height')}"
            if rect.get("stroke-dasharray") != horizontal_vertical:
                errors.append(f"El almacén {node_id} carece de dos bordes horizontales visibles.")
        elif kind == "entity" and matches[0].find("./s:rect", NS).get("stroke-dasharray"):
            errors.append(f"La entidad {node_id} debe tener un contorno completo.")

    labels = [" ".join("".join(text.itertext()).split())
              for text in [*root.findall(".//s:text", NS), *root.findall(".//s:foreignObject", NS)]]
    for label in expected["labels"]:
        if label not in labels:
            errors.append(f"Etiqueta SVG ausente o alterada: {label!r}.")
    expected_edges = expected.get("edgeCount", len(expected.get("edges", [])))
    if len(edge_labels) != expected_edges:
        errors.append(f"SVG contiene {len(edge_labels)} etiquetas de flujo, se esperaban {expected_edges}.")
    return errors


def validate_outputs(cwd, output, expected):
    problems = []
    mermaid_path = cwd / output
    csv_path = cwd / "diccionario.csv"
    if mermaid_path.is_file():
        lines = mermaid_path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0] != "flowchart LR":
            problems.append("Cabecera Mermaid incorrecta.")
        statements = [line.strip() for line in lines[1:] if line.strip() and "%%" not in line]
        shapes = {"entity": r'\["', "process": r'\(\("', "store": r'@\{ shape: datastore,'}
        for node, shape in expected["nodes"]:
            if not any(re.match(rf"(?:n_)?{re.escape(node)}{shapes[shape]}", line)
                       for line in statements):
                problems.append(f"Falta el nodo Mermaid {node} con tipo {shape}.")
        for origin, label, target in expected.get("edges", []):
            if not any(re.fullmatch(
                rf'(?:n_)?{re.escape(origin)} -->\|"{re.escape(label)}"\| (?:n_)?{re.escape(target)}',
                line,
            ) for line in statements):
                problems.append(f"Falta el flujo {origin} -> {target} con etiqueta {label!r}.")
        if len(statements) != len(expected["nodes"]) + expected.get(
            "edgeCount", len(expected.get("edges", []))
        ):
            problems.append("Cantidad incorrecta de declaraciones Mermaid.")

    if csv_path.is_file():
        try:
            with csv_path.open(encoding="utf-8", newline="") as csv_file:
                rows = list(csv.reader(csv_file, delimiter=";", strict=True))
            if any(len(row) != 3 for row in rows if row):
                problems.append("El CSV contiene una fila con una cantidad incorrecta de campos.")
            if [row for row in rows if row in HEADERS] != HEADERS:
                problems.append("Cabeceras del CSV incorrectas.")
            for expected_row in expected.get("rows", []):
                if expected_row not in rows:
                    name = expected_row[0]
                    problems.append(f"Fila CSV ausente o alterada: {name[:60]!r}.")
        except (csv.Error, UnicodeError) as error:
            problems.append(f"CSV no legible: {error}")
    return problems


def run_case(case, binary, renderer, evidence):
    expected = case["expected"]
    phase = expected.get("phase", "valido")
    output = expected.get("output", "salida.mmd")
    input_path = ROOT / f"pruebas/situacion_{case['group']}/{case['id']}.dfd"
    input_bytes = input_path.read_bytes()
    folder = evidence / case["id"]
    folder.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory(prefix=f"dfdc-{case['id']}-") as temp_dir:
        cwd = Path(temp_dir)
        shutil.copyfile(input_path, cwd / "entrada.dfd")
        if expected.get("setup") == "csv_dir":
            (cwd / "diccionario.csv").mkdir()
        result = execute([str(binary), "entrada.dfd", output], cwd, timeout=15)
        errors = []
        if result["codigo"] != (0 if phase == "valido" else 1):
            errors.append(f"Código inesperado: {result['codigo']}.")
        for text in expected.get("diagnostics", []):
            if text not in result["stderr"]:
                errors.append(f"Diagnóstico ausente en stderr: {text!r}.")
        if phase == "lexico" and "Error sintactico" in result["stderr"]:
            errors.append("Diagnóstico sintáctico secundario tras el error léxico.")
        if phase == "valido" and result["stderr"].strip():
            errors.append("Una ejecución válida produjo stderr.")
        if phase == "valido" and "Compilacion finalizada correctamente." not in result["stdout"]:
            errors.append("Falta la confirmación de éxito en stdout.")
        if phase != "valido" and "Compilacion finalizada correctamente." in result["stdout"]:
            errors.append("Un caso inválido informó éxito en stdout.")
        source = cwd / "entrada.dfd"
        if not source.is_file() or source.read_bytes() != input_bytes:
            errors.append("La entrada fue modificada.")
            if source.is_file():
                shutil.copyfile(source, folder / "entrada-sobrescrita.dfd")

        files = sorted(path.relative_to(cwd).as_posix() for path in cwd.rglob("*")
                       if path.is_file() and path.name != "entrada.dfd")
        wanted = expected.get("files", ["diccionario.csv", "salida.mmd"] if phase == "valido" else [])
        if files != sorted(wanted):
            errors.append(f"Archivos esperados: {wanted}; observados: {files}.")
        for name in files:
            destination = folder / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cwd / name, destination)

        rendering = None
        blocked = result["codigo"] is None and "timed out" not in result.get("incidencia", "")
        if phase == "valido":
            try:
                errors.extend(validate_outputs(cwd, output, expected))
            except (OSError, UnicodeError) as error:
                errors.append(f"Salida del compilador ilegible: {error}")
            if not (cwd / output).is_file():
                errors.append("Falta la entrada para Mermaid CLI.")
            elif renderer is None:
                blocked = True
            else:
                config = "mermaid_html.json" if expected.get("htmlLabels") else "mermaid.json"
                command = [*renderer, "-c", str(ROOT / "diagramas" / config),
                           "-i", output, "-o", "salida.svg"]
                rendering = execute(command, cwd, timeout=60)
                svg_path = cwd / "salida.svg"
                if rendering["codigo"] != 0 or not svg_path.is_file():
                    errors.append("Mermaid CLI no produjo un SVG válido.")
                    if rendering["codigo"] is None and "timed out" not in rendering.get("incidencia", ""):
                        blocked = True
                else:
                    shutil.copyfile(svg_path, folder / svg_path.name)
                    try:
                        errors.extend(validate_svg(svg_path, expected))
                    except (ET.ParseError, OSError) as error:
                        errors.append(f"SVG ilegible: {error}")

    result.update({
        "id": case["id"], "archivos_compilador": files,
        "render": rendering, "verificaciones_fallidas": errors,
        "estado": "BLOQUEADA" if blocked else "FALLIDA" if errors else "APROBADA",
    })
    (folder / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binario", type=Path, required=True)
    parser.add_argument("--evidencia", type=Path, required=True,
                        help="Directorio nuevo para evitar sobrescribir evidencia.")
    parser.add_argument("--mmdc-js", type=Path, help="Ruta al punto de entrada JS de Mermaid CLI.")
    parser.add_argument("--chrome", type=Path, help="Ejecutable Chromium para Mermaid CLI.")
    args = parser.parse_args()
    binary = args.binario.resolve(strict=True)
    evidence = args.evidencia.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="dfdc-mermaid-") as temp_dir:
        options = ["-t", "neutral"]
        if args.chrome:
            puppeteer = Path(temp_dir) / "chrome.json"
            puppeteer.write_text(json.dumps({"executablePath": str(args.chrome.resolve(strict=True))}),
                                 encoding="utf-8")
            options += ["-p", str(puppeteer)]
        mmdc = shutil.which("mmdc")
        renderer = (["node", str(args.mmdc_js.resolve(strict=True)), *options] if args.mmdc_js
                    else [mmdc, *options] if mmdc else None)
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda case: run_case(case, binary, renderer, evidence),
                                    manifest["cases"]))

    states = {state: sum(result["estado"] == state for result in results)
              for state in ("APROBADA", "FALLIDA", "BLOQUEADA")}
    for result in results:
        print(result["id"], result["estado"], "exit=", result["codigo"])
        for issue in result["verificaciones_fallidas"]:
            print(" ", issue)
    print(states)
    (evidence / "resumen.json").write_text(json.dumps(states, indent=2) + "\n", encoding="utf-8")
    return int(states["FALLIDA"] + states["BLOQUEADA"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
