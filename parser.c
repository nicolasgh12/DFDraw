%{
#include <stdio.h>
#include <stdlib.h>

#include "ast.h"

/*
 * Funcion generada por Flex.
 */
int yylex(void);

/*
 * Funcion utilizada por Bison para informar errores.
 */
void yyerror(const char *message);

/*
 * Numero de linea mantenido por Flex.
 */
extern int yylineno;


/*
 * Raiz del AST generado.
 */
AstNode *ast_root = NULL;


/*
 * Cantidad de errores sintacticos.
 */
int syntax_errors = 0;

%}


/*
 * ast.h debe estar disponible tambien en parser.tab.h
 * porque YYSTYPE utiliza AstNode.
 */
%code requires {
    #include "ast.h"
}


/*
 * Bison muestra mensajes de error mas descriptivos.
 */
%define parse.error verbose


/* =========================
   Valores semanticos
   ========================= */

%union {
    char *str;
    AstNode *node;
}


/* =========================
   Tokens
   ========================= */

%token T_DFD
%token T_ENTIDAD
%token T_PROCESO
%token T_ALMACEN
%token T_FLUJO
%token T_ARROW
%token T_INVALID

%token <str> T_ID
%token <str> T_STRING


/* =========================
   Tipos de no terminales
   ========================= */

%type <node> programa
%type <node> declaraciones
%type <node> declaracion
%type <node> entidad
%type <node> proceso
%type <node> almacen
%type <node> flujo


/* =========================
   Simbolo inicial
   ========================= */

%start programa


/*
 * Si se produce un error sintactico y Bison descarta
 * un ID o STRING, se libera la memoria.
 */
%destructor { free($$); } <str>


%%


/* =========================
   Programa completo
   ========================= */

programa:
    T_DFD T_STRING '{' declaraciones '}' opt_semicolon
    {
        ast_root = ast_create_dfd(
            $2,
            $4
        );

        free($2);

        $$ = ast_root;
    }
;


/* =========================
   Declaraciones
   ========================= */

declaraciones:
    %empty
    {
        $$ = NULL;
    }

    |

    declaraciones declaracion
    {
        $$ = ast_append(
            $1,
            $2
        );
    }
;


declaracion:
    entidad
    {
        $$ = $1;
    }

    |

    proceso
    {
        $$ = $1;
    }

    |

    almacen
    {
        $$ = $1;
    }

    |

    flujo
    {
        $$ = $1;
    }
;


/* =========================
   Entidad externa
   ========================= */

entidad:
    T_ENTIDAD T_ID T_STRING ';'
    {
        $$ = ast_create_named(
            AST_ENTITY,
            $2,
            $3,
            yylineno
        );

        free($2);
        free($3);
    }
;


/* =========================
   Proceso
   ========================= */

proceso:
    T_PROCESO T_ID T_STRING ';'
    {
        $$ = ast_create_named(
            AST_PROCESS,
            $2,
            $3,
            yylineno
        );

        free($2);
        free($3);
    }
;


/* =========================
   Almacen
   ========================= */

almacen:
    T_ALMACEN T_ID T_STRING ';'
    {
        $$ = ast_create_named(
            AST_STORE,
            $2,
            $3,
            yylineno
        );

        free($2);
        free($3);
    }
;


/* =========================
   Flujo
   ========================= */

flujo:
    T_FLUJO T_ID T_ARROW T_ID T_STRING ';'
    {
        $$ = ast_create_flow(
            $2,
            $4,
            $5,
            yylineno
        );

        free($2);
        free($4);
        free($5);
    }
;


/* =========================
   Punto y coma opcional
   despues del bloque DFD
   ========================= */

opt_semicolon:
    %empty
    |
    ';'
;


%%


void yyerror(const char *message)
{
    fprintf(
        stderr,
        "Error sintactico [linea %d]: %s.\n",
        yylineno,
        message
    );

    syntax_errors++;
}
