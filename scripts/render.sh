#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Uso: bash scripts/render.sh entrada.mmd salida.svg" >&2
    exit 1
fi

if ! command -v mmdc >/dev/null 2>&1; then
    echo "Error: Mermaid CLI (mmdc) no esta instalado." >&2
    exit 1
fi

exec mmdc -i "$1" -o "$2"
