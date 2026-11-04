#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "diccionario.h"

typedef struct {
    char nombre[150];
    char tipo[50];
    char definicion[500];
} EntradaDicc;

EntradaDicc diccionario[1000];
int total_entradas = 0;

void registrar_diccionario(const char* nombre, const char* tipo) {
    for(int i = 0; i < total_entradas; i++) {
        if(strcmp(diccionario[i].nombre, nombre) == 0 && strcmp(diccionario[i].tipo, tipo) == 0) return;
    }
    strcpy(diccionario[total_entradas].nombre, nombre);
    strcpy(diccionario[total_entradas].tipo, tipo);
    strcpy(diccionario[total_entradas].definicion, "");
    total_entradas++;
}

void asignar_definicion(const char* nombre, const char* definicion, int linea) {
    int encontrado = 0;
    for(int i = 0; i < total_entradas; i++) {
        if(strcmp(diccionario[i].nombre, nombre) == 0) {
            strcpy(diccionario[i].definicion, definicion);
            encontrado = 1;
            break;
        }
    }
    if(!encontrado) {
        printf("Error Semantico (Analisis Semantico) en linea %d: El elemento '%s' no esta declarado como almacen, flujo, estructura o elemento.\n", linea, nombre);
    }
}

void imprimir_tabla(FILE* f, const char* tipo, const char* col1, const char* col3) {
    /* Dejamos la columna central vacía en el encabezado (;;), empujando col3 a la derecha */
    fprintf(f, "%s;;%s\n", col1, col3);
    for(int i = 0; i < total_entradas; i++) {
        if(strcmp(diccionario[i].tipo, tipo) == 0) {
            /* Imprimimos el nombre, luego una columna para el =, y luego la definición */
            fprintf(f, "%s;=;%s\n", diccionario[i].nombre, diccionario[i].definicion);
        }
    }
    fprintf(f, "\n");
}

void generar_csv_diccionario(const char* filename) {
    FILE* f = fopen(filename, "w");
    if(!f) return;
    imprimir_tabla(f, "ALMACEN", "ALMACENES DE DATOS", "ELEMENTOS");
    imprimir_tabla(f, "FLUJO", "FLUJO", "COMPONENTES");
    imprimir_tabla(f, "ESTRUCTURA", "ESTRUCTURA DE DATOS", "COMPONENTES");
    imprimir_tabla(f, "ELEMENTO", "ELEMENTO", "COMPONENTES");
    fclose(f);
}
