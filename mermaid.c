#include <stdio.h>

#include "mermaid.h"


/*
 * Imprime una cadena escapando caracteres
 * especiales para Mermaid.
 */
static void print_escaped(
    FILE *output,
    const char *text
)
{
    if (text == NULL) {
        return;
    }

    const char *current = text;

    while (*current != '\0') {

        if (*current == '"') {

            fprintf(
                output,
                "\\\""
            );

        } else if (*current == '\\') {

            fprintf(
                output,
                "\\\\"
            );

        } else if (*current == '\n') {

            fprintf(
                output,
                " "
            );

        } else {

            fputc(
                *current,
                output
            );
        }

        current++;
    }
}


/*
 * Genera una entidad.
 */
static void generate_entity(
    FILE *output,
    const AstNode *node
)
{
    fprintf(
        output,
        "    %s[\"",
        node->id
    );

    print_escaped(
        output,
        node->label
    );

    fprintf(
        output,
        "\"]\n"
    );
}


/*
 * Genera un proceso.
 *
 * Por ahora utilizamos una representacion
 * provisoria.
 *
 * La notacion grafica definitiva puede
 * modificarse posteriormente solamente
 * en este backend.
 */
static void generate_process(
    FILE *output,
    const AstNode *node
)
{
    fprintf(
        output,
        "    %s((\"",
        node->id
    );

    print_escaped(
        output,
        node->label
    );

    fprintf(
        output,
        "\"))\n"
    );
}


/*
 * Genera un almacen.
 *
 * La representacion grafica definitiva
 * queda encapsulada aqui.
 */
static void generate_store(
    FILE *output,
    const AstNode *node
)
{
    fprintf(
        output,
        "    %s@{ shape: datastore, label: \"",
        node->id
    );

    print_escaped(
        output,
        node->label
    );

    fprintf(
        output,
        "\" }\n"
    );
}


/*
 * Genera un flujo.
 */
static void generate_flow(
    FILE *output,
    const AstNode *node
)
{
    fprintf(
        output,
        "    %s -->|\"",
        node->source
    );

    print_escaped(
        output,
        node->label
    );

    fprintf(
        output,
        "\"| %s\n",
        node->target
    );
}


int mermaid_generate(
    const AstNode *root,
    const char *output_path
)
{
    if (
        root == NULL ||
        output_path == NULL
    ) {
        return 0;
    }


    FILE *output = fopen(
        output_path,
        "w"
    );


    if (output == NULL) {

        fprintf(
            stderr,
            "Error: no se pudo crear el archivo Mermaid '%s'.\n",
            output_path
        );

        return 0;
    }


    /*
     * Encabezado Mermaid.
     */
    fprintf(
        output,
        "flowchart LR\n"
    );


    fprintf(
        output,
        "    %%%% Generado automaticamente por dfdc\n"
    );


    fprintf(
        output,
        "    %%%% DFD: "
    );


    print_escaped(
        output,
        root->label
    );


    fprintf(
        output,
        "\n\n"
    );


    /*
     * Primero generamos todos los elementos.
     */
    const AstNode *current = root->children;


    while (current != NULL) {

        switch (current->type) {

            case AST_ENTITY:

                generate_entity(
                    output,
                    current
                );

                break;


            case AST_PROCESS:

                generate_process(
                    output,
                    current
                );

                break;


            case AST_STORE:

                generate_store(
                    output,
                    current
                );

                break;


            default:

                break;
        }

        current = current->next;
    }


    fprintf(
        output,
        "\n"
    );


    /*
     * Luego generamos los flujos.
     */
    current = root->children;


    while (current != NULL) {

        if (current->type == AST_FLOW) {

            generate_flow(
                output,
                current
            );
        }

        current = current->next;
    }


    fclose(output);


    return 1;
}
