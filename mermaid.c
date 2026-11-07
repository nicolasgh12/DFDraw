#include <stdio.h>
#include <string.h>

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

        if (*current == '\n' || *current == '\r') {
            if (*current != '\r' || current[1] != '\n') {
                fputc(' ', output);
            }
        } else if (strchr("\"\\|#<>&`", *current) != NULL) {
            fprintf(output, "#%u;", (unsigned char)*current);
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
        "    n_%s[\"",
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
 * El circulo representa una transformacion del DFD.
 */
static void generate_process(
    FILE *output,
    const AstNode *node
)
{
    fprintf(
        output,
        "    n_%s((\"",
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
 * datastore dibuja las dos lineas paralelas.
 */
static void generate_store(
    FILE *output,
    const AstNode *node
)
{
    fprintf(
        output,
        "    n_%s@{ shape: datastore, label: \"",
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
        "    n_%s -->|\"",
        node->source
    );

    print_escaped(
        output,
        node->label
    );

    fprintf(
        output,
        "\"| n_%s\n",
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


    int error = ferror(output);
    if (fclose(output) != 0 || error) {
        fprintf(stderr, "Error: no se pudo escribir el archivo Mermaid '%s'.\n", output_path);
        return 0;
    }
    return 1;
}
