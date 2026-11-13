# Alcance del historial y de la revisión

La auditoría partió de `main` en `3560506`, alineada con la referencia local `origin/main`. El único archivo local sin seguimiento era el informe original `Paper_Compilador_Generacion_Automatica_DFD.pdf`. Su SHA-256 registrado fue `BEED425833D85E4085001654F169548C10BB1F1A551B16C53A163A911ADE9A00`.

Se inspeccionaron los tres commits disponibles mediante `git log -10 --name-status`, `git show` y `git diff`. La comparación con `--ignore-space-at-eol` confirmó que los cambios de los scripts en `3560506` correspondían a los finales de línea. El alcance abarcó las fuentes y ejemplos versionados, además del PDF de referencia. La referencia remota se leyó desde el repositorio local.

Un primer intento de compilar la línea de base no ingresó al directorio temporal y regeneró derivados en la raíz. Se eliminó ese registro y se repitió la compilación a partir de `git archive HEAD` en un directorio separado, con un cambio de directorio que aborta si falla. El informe académico original se conservó. Los derivados antiguos se retiraron como parte de la separación de fuentes y salidas reproducibles.

Durante la corrección, una ejecución de S02A reveló que el prefijo del identificador Mermaid faltaba en la declaración de procesos. `intermedia-S02A.mmd` contiene la salida observada y `intermedia-S02A.json` registra la comprobación. El verificador inicial también clasificaba de manera incorrecta los identificadores de SVG y asumía que el almacén era un elemento `path`. Se ajustó contra el SVG real de Mermaid y se volvió a ejecutar con ambos binarios. El almacén usa un `rect` cuyo patrón de trazo dibuja los lados superior e inferior y omite los verticales.
