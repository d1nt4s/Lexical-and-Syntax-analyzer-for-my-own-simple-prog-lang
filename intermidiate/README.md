# Генерация промежуточного кода (IR)

Пакет `intermidiate` содержит генератор промежуточного кода для стек-машины.

## Структура

- `ir.py` - определения команд IR (Push, Op, Label, Jmp, JmpIfFalse)
- `generator.py` - генератор IR из AST
- `__init__.py` - экспорты пакета

## Команды IR

### Push
```
push <value>
```
Кладет значение на стек. Значение может быть:
- Число: `push 10`, `push 3.14`
- Булево: `push true`, `push false`
- Имя переменной: `push x` (для загрузки переменной)

### Операции
```
add    # сложение: a + b
sub    # вычитание: a - b
mul    # умножение: a * b
div    # деление: a / b
lt     # меньше: a < b
le     # меньше или равно: a <= b
gt     # больше: a > b
ge     # больше или равно: a >= b
eq     # равно: a == b
neq    # не равно: a != b
and    # логическое И: a && b
or     # логическое ИЛИ: a || b
not    # логическое НЕ: !a
```

Все операции работают со стеком:
1. Берет два верхних значения со стека (для бинарных операций)
2. Выполняет операцию
3. Кладет результат обратно на стек

### Метки и переходы
```
label <name>        # метка для переходов
jmp <label>         # безусловный переход к метке
jmp_if_false <label> # условный переход: если на стеке false, перейти
```

## Использование

### Генерация IR в stdout
```bash
python3 -m main.main examples/span_test_simple.txt --ir
```

### Генерация IR в файл
```bash
python3 -m main.main examples/span_test_simple.txt --ir --ir-output output.ir
```

## Примеры

### Простое выражение
**Исходный код:**
```minilang
int a = 1;
int b = 2;
int c = a + b;
```

**IR:**
```
push 1
push 2
push a
push b
add
push c
```

### If statement
**Исходный код:**
```minilang
if (x > 5) {
    print(x);
} else {
    print(0);
}
```

**IR:**
```
push x
push 5
gt
jmp_if_false L0
push x
jmp L1
label L0
push 0
label L1
```

### For loop
**Исходный код:**
```minilang
for (int i = 0; i < 10; i = i + 1) {
    print(i);
}
```

**IR:**
```
push 0
label L0
push i
push 10
lt
jmp_if_false L1
push i
push i
push 1
add
jmp L0
label L1
```

## Архитектура

Генерация IR происходит после семантического анализа:

```
Исходный код
  ↓
Лексер (токены)
  ↓
Парсер (AST)
  ↓
Семантический анализатор
  ↓
Генератор IR (IR код)
  ↓
Вывод IR (stdout или файл)
```

## API

### `generate_ir(program: Program) -> IRProgram`
Генерирует IR из AST программы.

### `ir_to_string(program: IRProgram) -> str`
Преобразует список инструкций IR в строку для вывода.

