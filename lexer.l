%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parser.tab.h"

int lexical_errors = 0;

static char *copy_string(const char *text) {
    size_t length = strlen(text);
    char *copy = malloc(length + 1);
    if (copy == NULL) {
        fprintf(stderr, "Error: no se pudo reservar memoria.\n");
        exit(EXIT_FAILURE);
    }
    memcpy(copy, text, length + 1);
    return copy;
}

static char *remove_quotes(const char *text) {
    size_t length = strlen(text);
    if (length < 2) {
        return copy_string("");
    }
    char *result = malloc(length - 1);
    if (result == NULL) {
        fprintf(stderr, "Error: no se pudo reservar memoria.\n");
        exit(EXIT_FAILURE);
    }
    size_t written = 0;
    for (size_t i = 1; i < length - 1; i++) {
        if (text[i] == '\\' && (text[i + 1] == '\\' || text[i + 1] == '"')) {
            i++;
        }
        result[written++] = text[i];
    }
    result[written] = '\0';
    return result;
}
%}

%option noyywrap noinput nounput never-interactive
%option yylineno

ID      [a-zA-Z_][a-zA-Z0-9_]*
STRING  \"([^\"\\]|\\.)*\"

%%

"DFD"           { return T_DFD; }
"ENTIDAD"       { return T_ENTIDAD; }
"PROCESO"       { return T_PROCESO; }
"ALMACEN"       { return T_ALMACEN; }
"FLUJO"         { return T_FLUJO; }

"ESTRUCTURA"    { return T_ESTRUCTURA; }
"ELEMENTO"      { return T_ELEMENTO; }

"->"            { return T_ARROW; }
"="             { return T_IGUAL; }
"+"             { return T_MAS; }
"|"             { return T_PIPE; }
"-"             { return T_GUION; }

"{"             { return T_LLAVE_A; }
"}"             { return T_LLAVE_C; }
"["             { return T_CORCHETE_A; }
"]"             { return T_CORCHETE_C; }
"("             { return T_PARENTESIS_A; }
")"             { return T_PARENTESIS_C; }
";"             { return ';'; }

[0-9]+          { yylval.str = copy_string(yytext); return T_NUMERO; }

{STRING}        { yylval.str = remove_quotes(yytext); return T_STRING; }
{ID}            { yylval.str = copy_string(yytext); return T_ID; }

"//".*          { /* Ignorar comentario */ }
"#".*           { /* Ignorar comentario */ }
[ \t\r\n]+      { /* Ignorar */ }

.               {
                    fprintf(stderr, "Error lexico [linea %d]: caracter no reconocido '%s'.\n", yylineno, yytext);
                    lexical_errors++;
                    return T_INVALID;
                }

%%
