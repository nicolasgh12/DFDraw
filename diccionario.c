#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "diccionario.h"

typedef struct EntradaDicc {
    char *nombre;
    const char *tipo;
    char *definicion;
    struct EntradaDicc *siguiente;
} EntradaDicc;

static EntradaDicc *primera;
static EntradaDicc **siguiente = &primera;

static void *reservar(size_t size)
{
    void *memoria = malloc(size);
    if (memoria == NULL) {
        fprintf(stderr, "Error: no se pudo reservar memoria para el diccionario.\n");
        exit(EXIT_FAILURE);
    }
    return memoria;
}

static char *copiar(const char *texto)
{
    size_t size = strlen(texto) + 1;
    return memcpy(reservar(size), texto, size);
}

void registrar_diccionario(const char *nombre, const char *tipo)
{
    for (EntradaDicc *entrada = primera; entrada != NULL; entrada = entrada->siguiente) {
        if (strcmp(entrada->nombre, nombre) == 0 && strcmp(entrada->tipo, tipo) == 0) {
            return;
        }
    }

    EntradaDicc *entrada = reservar(sizeof *entrada);
    *entrada = (EntradaDicc){copiar(nombre), tipo, NULL, NULL};
    *siguiente = entrada;
    siguiente = &entrada->siguiente;
}

int asignar_definicion(const char *nombre, const char *definicion, int linea)
{
    for (EntradaDicc *entrada = primera; entrada != NULL; entrada = entrada->siguiente) {
        if (strcmp(entrada->nombre, nombre) == 0) {
            free(entrada->definicion);
            entrada->definicion = copiar(definicion);
            return 1;
        }
    }

    fprintf(stderr, "Error semantico [linea %d]: el elemento '%s' no esta declarado "
            "como almacen, flujo, estructura o elemento.\n", linea, nombre);
    return 0;
}

static void imprimir_campo(FILE *archivo, const char *texto)
{
    if (texto == NULL) {
        return;
    }
    if (strpbrk(texto, ";\"\r\n") == NULL) {
        fputs(texto, archivo);
        return;
    }

    fputc('"', archivo);
    for (; *texto != '\0'; texto++) {
        if (*texto == '"') {
            fputc('"', archivo);
        }
        fputc(*texto, archivo);
    }
    fputc('"', archivo);
}

static void imprimir_tabla(FILE *archivo, const char *tipo, const char *col1, const char *col3)
{
    fprintf(archivo, "%s;;%s\n", col1, col3);
    for (const EntradaDicc *entrada = primera; entrada != NULL; entrada = entrada->siguiente) {
        if (strcmp(entrada->tipo, tipo) == 0) {
            imprimir_campo(archivo, entrada->nombre);
            fputs(";=;", archivo);
            imprimir_campo(archivo, entrada->definicion);
            fputc('\n', archivo);
        }
    }
    fputc('\n', archivo);
}

int generar_csv_diccionario(const char *filename)
{
    FILE *archivo = fopen(filename, "w");
    if (archivo == NULL) {
        perror(filename);
        return 0;
    }

    imprimir_tabla(archivo, "ALMACEN", "ALMACENES DE DATOS", "ELEMENTOS");
    imprimir_tabla(archivo, "FLUJO", "FLUJO", "COMPONENTES");
    imprimir_tabla(archivo, "ESTRUCTURA", "ESTRUCTURA DE DATOS", "COMPONENTES");
    imprimir_tabla(archivo, "ELEMENTO", "ELEMENTO", "COMPONENTES");

    int error = ferror(archivo);
    if (fclose(archivo) != 0 || error) {
        fprintf(stderr, "Error: no se pudo escribir el diccionario '%s'.\n", filename);
        return 0;
    }
    return 1;
}

void liberar_diccionario(void)
{
    while (primera != NULL) {
        EntradaDicc *entrada = primera;
        primera = entrada->siguiente;
        free(entrada->nombre);
        free(entrada->definicion);
        free(entrada);
    }
    siguiente = &primera;
}
