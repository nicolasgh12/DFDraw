# Gramática del lenguaje DFD

## Léxico

| Tokens | Lexemas |
|---|---|
| `T_DFD`, `T_ENTIDAD`, `T_PROCESO`, `T_ALMACEN`, `T_FLUJO` | `DFD`, `ENTIDAD`, `PROCESO`, `ALMACEN`, `FLUJO` |
| `T_ESTRUCTURA`, `T_ELEMENTO` | `ESTRUCTURA`, `ELEMENTO` |
| `T_ID` | `[a-zA-Z_][a-zA-Z0-9_]*` |
| `T_NUMERO` | `[0-9]+` |
| `T_STRING` | Literal entre comillas dobles |
| `T_ARROW`, `T_IGUAL`, `T_MAS`, `T_PIPE`, `T_GUION` | `->`, `=`, `+`, `\|`, `-` |
| `T_LLAVE_A/C`, `T_CORCHETE_A/C`, `T_PARENTESIS_A/C`, `';'` | `{ }`, `[ ]`, `( )`, `;` |

Las reservadas distinguen mayúsculas y minúsculas. Flex elige la coincidencia más larga y usa el orden de las reglas para desempatar. Ignora espacios, tabulaciones, CR, LF y comentarios de línea que empiezan con `//` o `#` fuera de las cadenas. En los literales se decodifican `\"` y `\\`. Las demás secuencias con barra invertida se conservan como texto. Las cadenas pueden contener saltos de línea.

## Producciones

```text
programa ::= "DFD" STRING "{" declaraciones "}" cierre
cierre ::= ε | ";"
declaraciones ::= ε | declaraciones declaracion
declaracion ::= entidad | proceso | almacen | flujo
              | estructura | elemento | definicion
entidad ::= "ENTIDAD" ID STRING ";"
proceso ::= "PROCESO" ID STRING ";"
almacen ::= "ALMACEN" ID STRING ";"
flujo ::= "FLUJO" ID "->" ID STRING ";"
estructura ::= "ESTRUCTURA" ID STRING ";"
elemento ::= "ELEMENTO" ID STRING ";"
definicion ::= ID "=" expresion ";" | STRING "=" expresion ";"
expresion ::= termino | expresion "+" termino
termino ::= ID | STRING | NUMERO
          | "{" expresion "}" | NUMERO "{" expresion "}" NUMERO
          | "(" expresion ")" | "[" opciones "]"
          | termino "-" termino
opciones ::= expresion | opciones "|" expresion
```

`-` agrupa hacia la derecha y pertenece a `termino`, de modo que se aplica antes de `+`. `+` y `|` se construyen por recursión izquierda en sus niveles gramaticales. Estas operaciones normalizan texto para el CSV.

## Validaciones y generación

Los identificadores gráficos deben ser únicos entre entidades, procesos y almacenes. Cada flujo debe tener una etiqueta no vacía y dos extremos declarados y distintos, con al menos un proceso. Se permiten referencias gráficas adelantadas, elementos aislados y bloques sin declaraciones.

Las claves del diccionario se registran por nombre y categoría. El almacén aporta su ID y el flujo su etiqueta literal. Las declaraciones `ESTRUCTURA` y `ELEMENTO` aportan su ID y quedan fuera del AST gráfico. El lado izquierdo de una asignación debe coincidir con una clave ya registrada. Si varias categorías comparten un nombre, la asignación conserva el comportamiento histórico y elige la primera registrada. Otra asignación a esa clave reemplaza la definición previa. El lado derecho se transcribe como texto normalizado, sin resolver sus identificadores ni evaluar rangos.

Un DFD válido genera Mermaid con identificadores internos prefijados por `n_` y mantiene las etiquetas visibles de la entrada. `datastore` usa los dos bordes horizontales definidos por Mermaid. El CSV tiene cuatro secciones de tres columnas, separador `;` y comillas duplicadas dentro de campos citados.
