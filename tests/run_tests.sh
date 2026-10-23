#!/usr/bin/env bash


ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

BIN="$ROOT_DIR/dfdc"

TMP_DIR="$ROOT_DIR/tests/tmp"


mkdir -p "$TMP_DIR"


PASSED=0

FAILED=0


success_test()
{
    NAME="$1"

    FILE="$2"

    OUTPUT="$TMP_DIR/$NAME.mmd"


    echo "----------------------------------------"
    echo "Prueba: $NAME"
    echo "Esperado: VALIDO"


    if "$BIN" "$FILE" "$OUTPUT"; then

        echo "[OK] $NAME"

        PASSED=$((PASSED + 1))

    else

        echo "[ERROR] $NAME deberia haber sido valido"

        FAILED=$((FAILED + 1))
    fi


    echo
}


failure_test()
{
    NAME="$1"

    FILE="$2"


    echo "----------------------------------------"
    echo "Prueba: $NAME"
    echo "Esperado: ERROR"


    if "$BIN" "$FILE" "$TMP_DIR/$NAME.mmd"; then

        echo "[ERROR] $NAME deberia haber sido rechazado"

        FAILED=$((FAILED + 1))

    else

        echo "[OK] $NAME: error detectado correctamente"

        PASSED=$((PASSED + 1))
    fi


    echo
}


success_test \
    "minimo_valido" \
    "$ROOT_DIR/examples/valid/minimo.dfd"


success_test \
    "turnos_valido" \
    "$ROOT_DIR/examples/valid/turnos.dfd"


failure_test \
    "error_lexico" \
    "$ROOT_DIR/examples/invalid/lexico.dfd"


failure_test \
    "error_sintactico" \
    "$ROOT_DIR/examples/invalid/sintactico.dfd"


failure_test \
    "semantico_no_declarado" \
    "$ROOT_DIR/examples/invalid/semantico_no_declarado.dfd"


failure_test \
    "semantico_duplicado" \
    "$ROOT_DIR/examples/invalid/semantico_duplicado.dfd"


failure_test \
    "semantico_flujo_invalido" \
    "$ROOT_DIR/examples/invalid/semantico_flujo_invalido.dfd"


echo "========================================"
echo "RESULTADO"
echo "========================================"

echo "Pruebas correctas: $PASSED"

echo "Pruebas fallidas:  $FAILED"


rm -rf "$TMP_DIR"


if [ "$FAILED" -ne 0 ]; then
    exit 1
fi


exit 0
