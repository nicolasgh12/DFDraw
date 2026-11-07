#ifndef DICCIONARIO_H
#define DICCIONARIO_H

void registrar_diccionario(const char *nombre, const char *tipo);
int asignar_definicion(const char *nombre, const char *definicion, int linea);
int generar_csv_diccionario(const char *filename);
void liberar_diccionario(void);

#endif
