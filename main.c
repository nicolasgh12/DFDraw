#include <stdio.h>
#include <stdlib.h>

#include "ast.h"
#include "semantic.h"
#include "mermaid.h"


/*
 * Variables generadas / mantenidas
 * por Flex y Bison.
 */
extern FILE *yyin;

extern int yyparse(void);

extern int yylineno;


/*
 * Errores generados por las fases anteriores.
 */
extern int lexical_errors;

extern int syntax_errors;


/*
 * AST construido por Bison.
 */
extern AstNode *ast_root;


int main(
    int argc,
    char *argv[]
)
{
    /*
     * Uso:
     *
     * ./dfdc entrada.dfd salida.mmd
     */
    if (
        argc < 2 ||
        argc > 3
    ) {

        fprintf(
            stderr,
            "Uso:\n"
            "  %s <archivo.dfd> [salida.mmd]\n",
            argv[0]
        );

        return EXIT_FAILURE;
    }


    const char *input_path = argv[1];

    const char *output_path;


    if (argc == 3) {

        output_path = argv[2];

    } else {

        output_path = "salida.mmd";
    }


    /*
     * Abrir archivo fuente.
     */
    FILE *input = fopen(
        input_path,
        "r"
    );


    if (input == NULL) {

        fprintf(
            stderr,
            "Error: no se pudo abrir '%s'.\n",
            input_path
        );

        return EXIT_FAILURE;
    }


    yyin = input;

    yylineno = 1;


    /*
     * Ejecutar parser.
     *
     * El parser solicita tokens a Flex.
     */
    int parse_result = yyparse();


    fclose(input);


    /*
     * Comprobar errores lexicos.
     */
    if (lexical_errors > 0) {

        fprintf(
            stderr,
            "\nAnalisis lexico: ERROR (%d error/es).\n",
            lexical_errors
        );

        if (ast_root != NULL) {
            ast_free(ast_root);
        }

        return EXIT_FAILURE;
    }


    printf(
        "Analisis lexico: OK\n"
    );


    /*
     * Comprobar parser.
     */
    if (
        parse_result != 0 ||
        syntax_errors > 0 ||
        ast_root == NULL
    ) {

        fprintf(
            stderr,
            "Analisis sintactico: ERROR.\n"
        );

        if (ast_root != NULL) {
            ast_free(ast_root);
        }

        return EXIT_FAILURE;
    }


    printf(
        "Analisis sintactico: OK\n"
    );


    /*
     * Analisis semantico.
     */
    SemanticReport semantic_report;


    if (
        !semantic_validate(
            ast_root,
            &semantic_report
        )
    ) {

        fprintf(
            stderr,
            "Analisis semantico: ERROR (%d error/es).\n",
            semantic_report.errors
        );

        ast_free(ast_root);

        return EXIT_FAILURE;
    }


    printf(
        "Analisis semantico: OK\n"
    );


    /*
     * Generar Mermaid.
     */
    if (
        !mermaid_generate(
            ast_root,
            output_path
        )
    ) {

        fprintf(
            stderr,
            "Error durante la generacion de Mermaid.\n"
        );

        ast_free(ast_root);

        return EXIT_FAILURE;
    }


    printf(
        "Mermaid generado: %s\n",
        output_path
    );


    printf(
        "Compilacion finalizada correctamente.\n"
    );


    /*
     * Liberar AST.
     */
    ast_free(ast_root);

    ast_root = NULL;


    return EXIT_SUCCESS;
}
