%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parser.tab.h"

/*
 * Cantidad de errores lexicos detectados.
 * main.c utiliza esta variable para saber si debe
 * continuar con las siguientes fases.
 */
int lexical_errors = 0;


/*
 * Duplica una cadena de caracteres.
 */
static char *copy_string(const char *text)
{
    size_t length = strlen(text);

    char *copy = malloc(length + 1);

    if (copy == NULL) {
        fprintf(stderr, "Error: no se pudo reservar memoria.\n");
        exit(EXIT_FAILURE);
    }

    memcpy(copy, text, length + 1);

    return copy;
}


/*
 * Elimina las comillas externas de un STRING.
 *
 * Por ejemplo:
 *
 * "Paciente"
 *
 * se transforma en:
 *
 * Paciente
 */
static char *remove_quotes(const char *text)
{
    size_t length = strlen(text);

    if (length < 2) {
        return copy_string("");
    }

    char *result = malloc(length - 1);

    if (result == NULL) {
        fprintf(stderr, "Error: no se pudo reservar memoria.\n");
        exit(EXIT_FAILURE);
    }

    memcpy(result, text + 1, length - 2);

    result[length - 2] = '\0';

    return result;
}
%}


/*
 * Flex no necesita yywrap().
 */
%option noyywrap

/*
 * Flex mantiene automaticamente la variable yylineno.
 */
%option yylineno


/* =========================
   Definiciones regulares
   ========================= */

ID      [a-zA-Z_][a-zA-Z0-9_]*

STRING  \"([^\"\\]|\\.)*\"


%%


/* =========================
   Palabras reservadas
   ========================= */

"DFD"           { return T_DFD; }

"ENTIDAD"       { return T_ENTIDAD; }

"PROCESO"       { return T_PROCESO; }

"ALMACEN"       { return T_ALMACEN; }

"FLUJO"         { return T_FLUJO; }


/* =========================
   Operadores
   ========================= */

"->"            { return T_ARROW; }


/* =========================
   Cadenas
   ========================= */

{STRING}
{
    yylval.str = remove_quotes(yytext);

    return T_STRING;
}


/* =========================
   Identificadores
   ========================= */

{ID}
{
    yylval.str = copy_string(yytext);

    return T_ID;
}


/* =========================
   Delimitadores
   ========================= */

"{"             { return '{'; }

"}"             { return '}'; }

";"             { return ';'; }


/* =========================
   Comentarios
   ========================= */

"//".*          { /* Ignorar comentario */ }

"#".*           { /* Ignorar comentario */ }


/* =========================
   Espacios en blanco
   ========================= */

[ \t\r\n]+      { /* Ignorar */ }


/* =========================
   Error lexico
   ========================= */

.
{
    fprintf(
        stderr,
        "Error lexico [linea %d]: caracter no reconocido '%s'.\n",
        yylineno,
        yytext
    );

    lexical_errors++;

    return T_INVALID;
}


%%