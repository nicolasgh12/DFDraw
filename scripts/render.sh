#!/usr/bin/env bash


if [ "$#" -ne 2 ]; then

    echo "Uso:"
    echo "  bash scripts/render.sh entrada.mmd salida.svg"

    exit 1
fi


INPUT="$1"

OUTPUT="$2"


if ! command -v mmdc >/dev/null 2>&1; then

    echo "Error: Mermaid CLI (mmdc) no esta instalado."

    echo
    echo "El archivo .mmd puede igualmente abrirse"
    echo "o probarse con Mermaid Live Editor."

    exit 1
fi


mmdc \
    -i "$INPUT" \
    -o "$OUTPUT"


echo "Diagrama generado: $OUTPUT"
