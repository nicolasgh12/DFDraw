CC = gcc

CFLAGS = -Wall -Wextra -std=c11 -g

TARGET = dfdc


OBJECTS = \
	main.o \
	ast.o \
	semantic.o \
	mermaid.o \
	parser.tab.o \
	lex.yy.o


all: $(TARGET)


$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) $(OBJECTS) -o $(TARGET)


parser.tab.c parser.tab.h: parser.y
	bison -d -Wall parser.y


lex.yy.c: lexer.l parser.tab.h
	flex lexer.l


main.o: main.c ast.h semantic.h mermaid.h
	$(CC) $(CFLAGS) -c main.c


ast.o: ast.c ast.h
	$(CC) $(CFLAGS) -c ast.c


semantic.o: semantic.c semantic.h ast.h
	$(CC) $(CFLAGS) -c semantic.c


mermaid.o: mermaid.c mermaid.h ast.h
	$(CC) $(CFLAGS) -c mermaid.c


parser.tab.o: parser.tab.c ast.h
	$(CC) $(CFLAGS) -c parser.tab.c


lex.yy.o: lex.yy.c parser.tab.h
	$(CC) $(CFLAGS) -c lex.yy.c


test: all
	bash tests/run_tests.sh


clean:
	rm -f \
		$(TARGET) \
		$(TARGET).exe \
		*.o \
		lex.yy.c \
		parser.tab.c \
		parser.tab.h \
		parser.output \
		salida.mmd


.PHONY: all test clean
