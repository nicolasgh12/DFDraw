# Compilador para la generación automática de diagramas de flujo de datos

DFDraw traduce un lenguaje específico de dominio a Mermaid y genera un diccionario de datos en CSV. Flex reconoce los tokens, Bison valida la estructura y construye el AST gráfico, y los módulos C validan las relaciones y generan las salidas.

## Compilación y uso

Requisitos del compilador en Windows con MSYS2: Bash, GNU Make 4.3 o superior, GCC con C11, Flex y GNU Bison 3.8 o compatible.

```bash
make clean
make -j4
make test
./dfdc examples/valid/turnos.dfd salida.mmd
./dfdc prueba.dfd comercio.mmd
```

La forma general es `./dfdc entrada.dfd [salida.mmd]`. El CSV se llama `diccionario.csv` y se escribe en el directorio de ejecución. Utilizá un directorio de salida por ejecución si querés conservar varios diccionarios. Los errores devuelven código distinto de cero. Ante una falla al escribir el CSV puede quedar el Mermaid que ya se escribió.

Instalá Mermaid CLI con un motor Mermaid que admita `datastore` (Mermaid 11.3 o superior) para renderizar. El backend utiliza rectángulos para entidades, círculos para procesos y dos bordes horizontales para almacenes.

```bash
bash scripts/render.sh salida.mmd salida.svg
```

## Lenguaje y estructura

```text
DFD "Sistema de turnos" {
  ENTIDAD paciente "Paciente";
  PROCESO registrar "Registrar";
  ALMACEN turnos "Turnos";
  FLUJO paciente -> registrar "Solicitud";
  FLUJO registrar -> turnos "Turno registrado";
  ESTRUCTURA registro "Datos del turno";
  ELEMENTO fecha "Fecha de atención";
  registro = fecha + ( "Observaciones" );
  turnos = { registro };
}
```

- `lexer.l`, `parser.y`, `ast.*` y `semantic.*` implementan el análisis. `main.c` coordina las etapas.
- `mermaid.*` y `diccionario.*` escriben las salidas. El Makefile genera C, cabeceras y objetos en `build/`.
- `examples/` reúne entradas válidas e inválidas. `prueba.dfd` demuestra el diccionario completo y `tests/run_tests.sh` ejecuta la suite histórica.
- [Gramática y validaciones](docs/GRAMATICA.md).
- [Informe académico, pruebas de auditoría y reproducción](informe/README.md).

Los niveles de DFD, el balance entre niveles y la resolución de referencias dentro de expresiones del diccionario quedan fuera del alcance implementado.

## Autores

- Nicolas Gonzalez Heinrich
- Bewig Alejo
- Decunha Lucas
- Enriquez Emiliano

Universidad Gastón Dachary

Compiladores 2026
