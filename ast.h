#ifndef AST_H
#define AST_H


/*
 * Tipos de nodos que pueden existir
 * dentro del AST.
 */
typedef enum {

    AST_DFD,

    AST_ENTITY,

    AST_PROCESS,

    AST_STORE,

    AST_FLOW

} AstType;


/*
 * Nodo generico del AST.
 */
typedef struct AstNode {

    /*
     * Tipo de nodo.
     */
    AstType type;


    /*
     * Identificador interno.
     *
     * Ejemplo:
     *
     * paciente
     * p1
     * turnos
     */
    char *id;


    /*
     * Etiqueta visible.
     *
     * Ejemplo:
     *
     * "Paciente"
     * "Registrar turno"
     */
    char *label;


    /*
     * Utilizados en nodos AST_FLOW.
     */
    char *source;

    char *target;


    /*
     * Linea donde fue declarado.
     */
    int line;


    /*
     * Hijos.
     *
     * Principalmente utilizado
     * por el nodo AST_DFD.
     */
    struct AstNode *children;


    /*
     * Siguiente nodo dentro de una lista.
     */
    struct AstNode *next;

} AstNode;


/*
 * Crea la raiz del DFD.
 */
AstNode *ast_create_dfd(
    const char *title,
    AstNode *declarations
);


/*
 * Crea una entidad, proceso o almacen.
 */
AstNode *ast_create_named(
    AstType type,
    const char *id,
    const char *label,
    int line
);


/*
 * Crea un flujo.
 */
AstNode *ast_create_flow(
    const char *source,
    const char *target,
    const char *label,
    int line
);


/*
 * Agrega un nodo al final de una lista.
 */
AstNode *ast_append(
    AstNode *list,
    AstNode *node
);


/*
 * Devuelve el nombre textual de un tipo.
 */
const char *ast_type_name(
    AstType type
);


/*
 * Libera el AST completo.
 */
void ast_free(
    AstNode *node
);


#endif