#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ast.h"


/*
 * Duplica una cadena.
 */
static char *duplicate_string(const char *text)
{
    if (text == NULL) {
        return NULL;
    }

    size_t length = strlen(text);

    char *copy = malloc(length + 1);

    if (copy == NULL) {
        fprintf(
            stderr,
            "Error: no se pudo reservar memoria para el AST.\n"
        );

        exit(EXIT_FAILURE);
    }

    memcpy(
        copy,
        text,
        length + 1
    );

    return copy;
}


/*
 * Reserva memoria para un nodo.
 */
static AstNode *ast_create_node(AstType type)
{
    AstNode *node = malloc(sizeof(AstNode));

    if (node == NULL) {
        fprintf(
            stderr,
            "Error: no se pudo reservar memoria para un nodo AST.\n"
        );

        exit(EXIT_FAILURE);
    }

    node->type = type;

    node->id = NULL;

    node->label = NULL;

    node->source = NULL;

    node->target = NULL;

    node->line = 0;

    node->children = NULL;

    node->next = NULL;

    return node;
}


AstNode *ast_create_dfd(
    const char *title,
    AstNode *declarations
)
{
    AstNode *node = ast_create_node(AST_DFD);

    node->label = duplicate_string(title);

    node->children = declarations;

    return node;
}


AstNode *ast_create_named(
    AstType type,
    const char *id,
    const char *label,
    int line
)
{
    AstNode *node = ast_create_node(type);

    node->id = duplicate_string(id);

    node->label = duplicate_string(label);

    node->line = line;

    return node;
}


AstNode *ast_create_flow(
    const char *source,
    const char *target,
    const char *label,
    int line
)
{
    AstNode *node = ast_create_node(AST_FLOW);

    node->source = duplicate_string(source);

    node->target = duplicate_string(target);

    node->label = duplicate_string(label);

    node->line = line;

    return node;
}


AstNode *ast_append(
    AstNode *list,
    AstNode *node
)
{
    if (node == NULL) {
        return list;
    }

    if (list == NULL) {
        return node;
    }

    AstNode *current = list;

    while (current->next != NULL) {
        current = current->next;
    }

    current->next = node;

    return list;
}


const char *ast_type_name(AstType type)
{
    switch (type) {

        case AST_DFD:
            return "DFD";

        case AST_ENTITY:
            return "ENTIDAD";

        case AST_PROCESS:
            return "PROCESO";

        case AST_STORE:
            return "ALMACEN";

        case AST_FLOW:
            return "FLUJO";

        default:
            return "DESCONOCIDO";
    }
}


void ast_free(AstNode *node)
{
    if (node == NULL) {
        return;
    }


    /*
     * Liberar hijos.
     */
    AstNode *child = node->children;

    while (child != NULL) {

        AstNode *next_child = child->next;

        /*
         * Evitamos que ast_free() intente recorrer
         * el hermano como parte del nodo.
         */
        child->next = NULL;

        ast_free(child);

        child = next_child;
    }


    free(node->id);

    free(node->label);

    free(node->source);

    free(node->target);

    free(node);
}