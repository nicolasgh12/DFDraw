#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#if defined(__MSYS__) || defined(__CYGWIN__)
#include <strings.h>
#endif

#include "ast.h"
#include "semantic.h"
#include "mermaid.h"
#include "diccionario.h"



/*
 * Variables generadas / mantenidas
 * por Flex y Bison.
 */
extern FILE *yyin;

extern int yyparse(void);
extern int yylex_destroy(void);

extern int yylineno;


/*
 * Errores generados por las fases anteriores.
 */
extern int lexical_errors;

extern int syntax_errors;
extern int dictionary_errors;


/*
 * AST construido por Bison.
 */
extern AstNode *ast_root;

static int same_file(const char *first, const char *second)
{
    struct stat a, b;
    return strcmp(first, second) == 0 ||
        (stat(first, &a) == 0 && stat(second, &b) == 0 &&
         a.st_ino != 0 && a.st_ino == b.st_ino && a.st_dev == b.st_dev);
}

static int uses_dictionary_path(const char *path, const char *dictionary)
{
    if (same_file(path, dictionary)) {
        return 1;
    }

    const char *separator = strrchr(path, '/');
#if defined(__MSYS__) || defined(__CYGWIN__)
    const char *backslash = strrchr(path, '\\');
    if (backslash != NULL && (separator == NULL || backslash > separator)) {
        separator = backslash;
    }
    if (strcasecmp(separator == NULL ? path : separator + 1, dictionary) != 0) {
#else
    if (strcmp(separator == NULL ? path : separator + 1, dictionary) != 0) {
#endif
        return 0;
    }
    if (separator == NULL) {
        return 1;
    }

    size_t size = (size_t)(separator - path) + 1;
    char *directory = malloc(size + 1);
    if (directory == NULL) {
        fprintf(stderr, "Error: no se pudo comprobar la ruta de salida.\n");
        exit(EXIT_FAILURE);
    }
    memcpy(directory, path, size);
    directory[size] = '\0';
    int matches = same_file(directory, ".");
    free(directory);
    return matches;
}

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
    const char *dictionary_path = "diccionario.csv";

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


    if (same_file(input_path, output_path) ||
        uses_dictionary_path(input_path, dictionary_path) ||
        uses_dictionary_path(output_path, dictionary_path)) {
        fprintf(stderr, "Error: el archivo fuente, la salida Mermaid y diccionario.csv "
                "deben ser archivos distintos.\n");
        fclose(input);
        return EXIT_FAILURE;
    }

    atexit(liberar_diccionario);
    yyin = input;

    yylineno = 1;


    /*
     * Ejecutar parser.
     *
     * El parser solicita tokens a Flex.
     */
    int parse_result = yyparse();


    fclose(input);
    yylex_destroy();


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


    semantic_validate(ast_root, &semantic_report);
    int semantic_errors = semantic_report.errors + dictionary_errors;
    if (semantic_errors > 0) {

        fprintf(
            stderr,
            "Analisis semantico: ERROR (%d error/es).\n",
            semantic_errors
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


    if (!generar_csv_diccionario(dictionary_path)) {
        fprintf(stderr, "Error durante la generacion del diccionario CSV.\n");
        ast_free(ast_root);
        return EXIT_FAILURE;
    }

    printf(
        "Diccionario CSV generado: diccionario.csv\n"
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
