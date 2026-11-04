%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ast.h"
#include "diccionario.h" /* NUEVO: Cabecera del generador de diccionario */

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

/* NUEVO: Tokens para el diccionario de datos */
%token T_ESTRUCTURA
%token T_ELEMENTO
%token T_IGUAL
%token T_MAS
%token T_LLAVE_A
%token T_LLAVE_C
%token T_CORCHETE_A
%token T_CORCHETE_C
%token T_PARENTESIS_A
%token T_PARENTESIS_C
%token T_PIPE
%token T_GUION

%token <str> T_ID
%token <str> T_STRING
%token <str> T_NUMERO /* NUEVO: Captura el valor numérico (ej: repeticiones) */

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

/* NUEVO: Tipos para las reglas del diccionario */
%type <node> estructura
%type <node> elemento
%type <node> definicion_dicc
%type <str> expresion_dicc
%type <str> termino_dicc
%type <str> lista_opciones

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
    T_DFD T_STRING T_LLAVE_A declaraciones T_LLAVE_C opt_semicolon
    {
        ast_root = ast_create_dfd($2, $4);
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
    | declaraciones declaracion
    {
        /* ast_append maneja la union de los nodos del AST.
           Si le pasamos NULL (como en los nodos del diccionario),
           simplemente los ignora y mantiene limpio el arbol. */
        $$ = ast_append($1, $2);
    }
;

declaracion:
    entidad { $$ = $1; }
    | proceso { $$ = $1; }
    | almacen { $$ = $1; }
    | flujo { $$ = $1; }
    /* NUEVO: Se agregan las declaraciones del diccionario */
    | estructura { $$ = $1; }
    | elemento { $$ = $1; }
    | definicion_dicc { $$ = $1; }
;

/* =========================
   Entidad externa
   ========================= */

entidad:
    T_ENTIDAD T_ID T_STRING ';'
    {
        $$ = ast_create_named(AST_ENTITY, $2, $3, yylineno);
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
        $$ = ast_create_named(AST_PROCESS, $2, $3, yylineno);
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
        registrar_diccionario($2, "ALMACEN"); /* NUEVO: Registro en diccionario */
        $$ = ast_create_named(AST_STORE, $2, $3, yylineno);
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
        registrar_diccionario($5, "FLUJO"); /* NUEVO: Registro de flujo por su nombre literal */
        $$ = ast_create_flow($2, $4, $5, yylineno);
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
    | ';'
;

/* =======================================================
   REGLAS DEL DICCIONARIO DE DATOS (NUEVAS)
   ======================================================= */

estructura:
    T_ESTRUCTURA T_ID T_STRING ';'
    {
        registrar_diccionario($2, "ESTRUCTURA");
        $$ = NULL; /* No interfiere con el AST grafico */
        free($2);
        free($3);
    }
;

elemento:
    T_ELEMENTO T_ID T_STRING ';'
    {
        registrar_diccionario($2, "ELEMENTO");
        $$ = NULL; /* No interfiere con el AST grafico */
        free($2);
        free($3);
    }
;

definicion_dicc:
    T_ID T_IGUAL expresion_dicc ';'
    {
        asignar_definicion($1, $3, yylineno);
        $$ = NULL;
        free($1);
        free($3);
    }
    | T_STRING T_IGUAL expresion_dicc ';'
    {
        asignar_definicion($1, $3, yylineno);
        $$ = NULL;
        free($1);
        free($3);
    }
;

expresion_dicc:
    termino_dicc { $$ = $1; }
    | expresion_dicc T_MAS termino_dicc
    {
        $$ = malloc(strlen($1) + strlen($3) + 4);
        sprintf($$, "%s + %s", $1, $3);
        free($1);
        free($3);
    }
;

termino_dicc:
    T_ID { $$ = strdup($1); }
    | T_STRING { $$ = strdup($1); }
    | T_NUMERO { $$ = strdup($1); }
    | T_LLAVE_A expresion_dicc T_LLAVE_C
    {
        $$ = malloc(strlen($2) + 5);
        sprintf($$, "{ %s }", $2);
        free($2);
    }
    | T_NUMERO T_LLAVE_A expresion_dicc T_LLAVE_C T_NUMERO
    {
        $$ = malloc(strlen($1) + strlen($3) + strlen($5) + 6);
        sprintf($$, "%s{%s}%s", $1, $3, $5);
        free($1);
        free($3);
        free($5);
    }
    | T_PARENTESIS_A expresion_dicc T_PARENTESIS_C
    {
        $$ = malloc(strlen($2) + 5);
        sprintf($$, "( %s )", $2);
        free($2);
    }
    | T_CORCHETE_A lista_opciones T_CORCHETE_C
    {
        $$ = malloc(strlen($2) + 5);
        sprintf($$, "[ %s ]", $2);
        free($2);
    }
    | termino_dicc T_GUION termino_dicc
    {
        $$ = malloc(strlen($1) + strlen($3) + 4);
        sprintf($$, "%s-%s", $1, $3);
        free($1);
        free($3);
    }
;

lista_opciones:
    expresion_dicc { $$ = $1; }
    | lista_opciones T_PIPE expresion_dicc
    {
        $$ = malloc(strlen($1) + strlen($3) + 4);
        sprintf($$, "%s | %s", $1, $3);
        free($1);
        free($3);
    }
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