#include <stdio.h>
#include <string.h>

#include "semantic.h"


/*
 * Determina si un nodo representa una declaracion
 * que posee identificador.
 */
static int is_named_declaration(const AstNode *node)
{
    if (node == NULL) {
        return 0;
    }

    return (
        node->type == AST_ENTITY ||
        node->type == AST_PROCESS ||
        node->type == AST_STORE
    );
}


/*
 * Busca una declaracion por identificador.
 */
static const AstNode *find_declaration(
    const AstNode *root,
    const char *id
)
{
    if (
        root == NULL ||
        id == NULL
    ) {
        return NULL;
    }

    const AstNode *current = root->children;

    while (current != NULL) {

        if (
            is_named_declaration(current) &&
            current->id != NULL &&
            strcmp(current->id, id) == 0
        ) {
            return current;
        }

        current = current->next;
    }

    return NULL;
}


/*
 * Informa un identificador duplicado.
 */
static void validate_duplicates(
    const AstNode *root,
    SemanticReport *report
)
{
    const AstNode *first = root->children;

    while (first != NULL) {

        if (!is_named_declaration(first)) {
            first = first->next;
            continue;
        }


        const AstNode *second = first->next;

        while (second != NULL) {

            if (
                is_named_declaration(second) &&
                first->id != NULL &&
                second->id != NULL &&
                strcmp(first->id, second->id) == 0
            ) {

                fprintf(
                    stderr,
                    "Error semantico [linea %d]: "
                    "identificador duplicado '%s'. "
                    "Ya fue declarado anteriormente como %s.\n",
                    second->line,
                    second->id,
                    ast_type_name(first->type)
                );

                report->errors++;
            }

            second = second->next;
        }

        first = first->next;
    }
}


/*
 * Valida un flujo individual.
 */
static void validate_flow(
    const AstNode *root,
    const AstNode *flow,
    SemanticReport *report
)
{
    const AstNode *source;

    const AstNode *target;


    /*
     * Validacion del nombre del flujo.
     */
    if (
        flow->label == NULL ||
        flow->label[0] == '\0'
    ) {

        fprintf(
            stderr,
            "Error semantico [linea %d]: "
            "el flujo debe poseer un nombre.\n",
            flow->line
        );

        report->errors++;
    }


    /*
     * Buscar origen.
     */
    source = find_declaration(
        root,
        flow->source
    );


    if (source == NULL) {

        fprintf(
            stderr,
            "Error semantico [linea %d]: "
            "el origen '%s' del flujo no fue declarado.\n",
            flow->line,
            flow->source
        );

        report->errors++;
    }


    /*
     * Buscar destino.
     */
    target = find_declaration(
        root,
        flow->target
    );


    if (target == NULL) {

        fprintf(
            stderr,
            "Error semantico [linea %d]: "
            "el destino '%s' del flujo no fue declarado.\n",
            flow->line,
            flow->target
        );

        report->errors++;
    }


    /*
     * Si alguno no existe no continuamos con
     * validaciones que dependen de su tipo.
     */
    if (
        source == NULL ||
        target == NULL
    ) {
        return;
    }


    /*
     * Un elemento no puede enviarse datos
     * a si mismo.
     */
    if (
        strcmp(
            flow->source,
            flow->target
        ) == 0
    ) {

        fprintf(
            stderr,
            "Error semantico [linea %d]: "
            "el origen y destino del flujo no pueden ser "
            "el mismo elemento ('%s').\n",
            flow->line,
            flow->source
        );

        report->errors++;
    }


    /*
     * Regla inicial del dominio:
     *
     * todo flujo debe involucrar al menos
     * un proceso.
     *
     * Esto impide, por ejemplo:
     *
     * ENTIDAD -> ENTIDAD
     * ENTIDAD -> ALMACEN
     * ALMACEN -> ENTIDAD
     * ALMACEN -> ALMACEN
     */
    if (
        source->type != AST_PROCESS &&
        target->type != AST_PROCESS
    ) {

        fprintf(
            stderr,
            "Error semantico [linea %d]: "
            "flujo invalido '%s -> %s'. "
            "Todo flujo de datos debe involucrar "
            "al menos un PROCESO.\n",
            flow->line,
            flow->source,
            flow->target
        );

        report->errors++;
    }
}


int semantic_validate(
    const AstNode *root,
    SemanticReport *report
)
{
    if (report == NULL) {
        return 0;
    }


    report->errors = 0;


    if (
        root == NULL ||
        root->type != AST_DFD
    ) {

        fprintf(
            stderr,
            "Error semantico: no existe un DFD valido.\n"
        );

        report->errors++;

        return 0;
    }


    /*
     * Primera pasada:
     * identificadores duplicados.
     */
    validate_duplicates(
        root,
        report
    );


    /*
     * Segunda pasada:
     * validar flujos.
     */
    const AstNode *current = root->children;

    while (current != NULL) {

        if (current->type == AST_FLOW) {

            validate_flow(
                root,
                current,
                report
            );
        }

        current = current->next;
    }


    return report->errors == 0;
}
