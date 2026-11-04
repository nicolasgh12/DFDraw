#ifndef DICCIONARIO_H
#define DICCIONARIO_H

void registrar_diccionario(const char* nombre, const char* tipo);
void asignar_definicion(const char* nombre, const char* definicion, int linea);
void generar_csv_diccionario(const char* filename);

#endif
