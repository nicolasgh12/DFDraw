#ifndef MERMAID_H
#define MERMAID_H

#include "ast.h"


/*
 * Genera un archivo Mermaid a partir del AST.
 *
 * Retorna:
 *
 * 1 -> correcto
 * 0 -> error
 */
int mermaid_generate(
    const AstNode *root,
    const char *output_path
);


#endif
