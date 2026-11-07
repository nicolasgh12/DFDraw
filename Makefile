CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -g
BISON = bison
FLEX = flex

TARGET = dfdc
BUILD = build
SOURCES = main ast semantic mermaid diccionario parser.tab lex.yy
OBJECTS = $(addprefix $(BUILD)/,$(addsuffix .o,$(SOURCES)))

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) $(LDLIBS) -o $@

$(BUILD):
	mkdir -p $@

$(BUILD)/parser.tab.c $(BUILD)/parser.tab.h &: parser.y | $(BUILD)
	$(BISON) -d -Wall -Werror=conflicts-sr -Werror=conflicts-rr -o $(BUILD)/parser.tab.c $<

$(BUILD)/lex.yy.c: lexer.l $(BUILD)/parser.tab.h
	$(FLEX) -o $@ $<

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

$(BUILD)/%.o: $(BUILD)/%.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -I. -MMD -MP -c $< -o $@

-include $(OBJECTS:.o=.d)

test: all
	bash tests/run_tests.sh

clean:
	rm -f $(TARGET) $(TARGET).exe $(BUILD)/*.o $(BUILD)/*.d \
		$(BUILD)/lex.yy.c $(BUILD)/parser.tab.c $(BUILD)/parser.tab.h

.PHONY: all test clean
