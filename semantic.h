#ifndef SEMANTIC_H
#define SEMANTIC_H

#include "ast.h"


typedef struct {

    int errors;

} SemanticReport;


/*
 * Ejecuta las validaciones semanticas.
 *
 * Retorna:
 *
 * 1 -> valido
 * 0 -> existen errores
 */
int semantic_validate(
    const AstNode *root,
    SemanticReport *report
);


#endif
