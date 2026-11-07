#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)" || exit 1
BIN="$ROOT_DIR/dfdc"
TMP_DIR="$(mktemp -d)" || exit 1
trap 'rm -f -- "$TMP_DIR"/*.mmd "$TMP_DIR/diccionario.csv"; rmdir -- "$TMP_DIR"' EXIT
cd "$TMP_DIR" || exit 1

PASSED=0
FAILED=0

run_test() {
    local name="$1" expected="$2" input="$3" result
    echo "----------------------------------------"
    echo "Prueba: $name (codigo esperado: $expected)"
    "$BIN" "$ROOT_DIR/examples/$input" "$name.mmd"
    result=$?

    if [[ "$result" -eq "$expected" ]] &&
       { [[ "$expected" -eq 0 && -s "$name.mmd" && -s diccionario.csv ]] ||
         [[ "$expected" -eq 1 && ! -e "$name.mmd" && ! -e diccionario.csv ]]; }; then
        echo "[OK] $name"
        PASSED=$((PASSED + 1))
    else
        echo "[ERROR] $name (codigo real: $result; revisar las salidas)"
        FAILED=$((FAILED + 1))
    fi
    rm -f -- diccionario.csv
}

run_test minimo_valido 0 valid/minimo.dfd
run_test turnos_valido 0 valid/turnos.dfd
run_test error_lexico 1 invalid/lexico.dfd
run_test error_sintactico 1 invalid/sintactico.dfd
run_test semantico_no_declarado 1 invalid/semantico_no_declarado.dfd
run_test semantico_duplicado 1 invalid/semantico_duplicado.dfd
run_test semantico_flujo_invalido 1 invalid/semantico_flujo_invalido.dfd

echo "Pruebas correctas: $PASSED"
echo "Pruebas fallidas:  $FAILED"
[[ "$FAILED" -eq 0 ]]
