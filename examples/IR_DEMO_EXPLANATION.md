# Демонстрация работы системы IR

## Полный пример работы

### 1. Исходный код

```minilang
int x = 10;
int y = 20;
int z = x + y;

if (z > 25) {
    print(z);
} else {
    print(0);
}
```

### 2. Этапы обработки

#### Этап 1: Лексер (Lexer)
Разбивает код на токены:
```
INT, IDENT("x"), ASSIGN, INT_LIT(10), SEMI,
INT, IDENT("y"), ASSIGN, INT_LIT(20), SEMI,
INT, IDENT("z"), ASSIGN, IDENT("x"), PLUS, IDENT("y"), SEMI,
IF, LPAREN, IDENT("z"), GT, INT_LIT(25), RPAREN, LBRACE,
PRINT, LPAREN, IDENT("z"), RPAREN, SEMI, RBRACE,
ELSE, LBRACE,
PRINT, LPAREN, INT_LIT(0), RPAREN, SEMI, RBRACE
```

#### Этап 2: Парсер (Parser)
Строит AST (абстрактное синтаксическое дерево):
```
Program
  ├─ Decl(x, init=Literal(10))
  ├─ Decl(y, init=Literal(20))
  ├─ Decl(z, init=BinOp(+, Ident(x), Ident(y)))
  └─ If
      ├─ cond: BinOp(>, Ident(z), Literal(25))
      ├─ then_branch: Block
      │   └─ PrintStmt(Ident(z))
      └─ else_branch: Block
          └─ PrintStmt(Literal(0))
```

#### Этап 3: Семантический анализ
Проверяет правильность:
- Все переменные объявлены ✓
- Типы совместимы ✓
- Нет дублирования ✓

#### Этап 4: Генерация IR
Преобразует AST в команды стек-машины

### 3. Как работает генератор IR

#### Шаг 1: Обработка объявлений

**Код:**
```minilang
int x = 10;
```

**Что происходит:**
```python
_gen_decl(Decl(x, init=Literal(10)))
  └─ _gen_expr(Literal(10))
      └─ _gen_literal(Literal(10))
          └─ instructions.append(Push(10))
```

**IR:**
```
push 10
```

#### Шаг 2: Обработка присваивания с выражением

**Код:**
```minilang
int z = x + y;
```

**Что происходит:**
```python
_gen_decl(Decl(z, init=BinOp(+, Ident(x), Ident(y))))
  └─ _gen_expr(BinOp(+, Ident(x), Ident(y)))
      ├─ _gen_binop(BinOp(+, ...))
      │   ├─ _gen_expr(Ident(x))
      │   │   └─ _gen_ident(Ident(x))
      │   │       └─ instructions.append(Push("x"))
      │   ├─ _gen_expr(Ident(y))
      │   │   └─ _gen_ident(Ident(y))
      │   │       └─ instructions.append(Push("y"))
      │   └─ instructions.append(Op(IROp.ADD))
```

**IR:**
```
push x
push y
add
```

**Как работает стек:**
```
Изначально: []
После push x: [x]
После push y: [x, y]
После add:   [x+y]  (берет два верхних, складывает, кладет результат)
```

#### Шаг 3: Обработка if statement

**Код:**
```minilang
if (z > 25) {
    print(z);
} else {
    print(0);
}
```

**Что происходит:**
```python
_gen_if(If(...))
  ├─ Генерируем метки: L0 (else), L1 (end)
  ├─ _gen_expr(BinOp(>, Ident(z), Literal(25)))
  │   ├─ push z
  │   ├─ push 25
  │   └─ gt
  ├─ jmp_if_false L0  (если false, переходим к else)
  ├─ _gen_stmt(PrintStmt(Ident(z)))  (then ветка)
  │   └─ push z
  ├─ jmp L1  (переходим к концу, пропуская else)
  ├─ label L0  (начало else ветки)
  ├─ _gen_stmt(PrintStmt(Literal(0)))  (else ветка)
  │   └─ push 0
  └─ label L1  (конец if)
```

**IR:**
```
push z
push 25
gt
jmp_if_false L0
push z
jmp L1
label L0
push 0
label L1
```

**Как работает стек и переходы:**
```
1. push z        → стек: [z]
2. push 25       → стек: [z, 25]
3. gt            → стек: [z > 25]  (true или false)
4. jmp_if_false L0
   - Если на стеке false → переходим к L0 (else)
   - Если на стеке true → продолжаем дальше
5. push z        → выполняется только если true
6. jmp L1        → переходим к концу, пропуская else
7. label L0      → метка для else ветки
8. push 0        → выполняется только если false
9. label L1      → конец if
```

### 4. Полный IR код для примера

```
push 10
push 20
push x
push y
add
push z
push 25
gt
jmp_if_false L0
push z
jmp L1
label L0
push 0
label L1
```

### 5. Пошаговое выполнение IR

**Исходное состояние:** стек = []

```
1. push 10          → стек: [10]
2. push 20          → стек: [10, 20]
3. push x           → стек: [10, 20, x]  (x = 10)
4. push y           → стек: [10, 20, x, y]  (y = 20)
5. add              → стек: [10, 20, 30]  (x + y = 30)
6. push z           → стек: [10, 20, 30, z]  (z = 30)
7. push 25          → стек: [10, 20, 30, z, 25]
8. gt               → стек: [10, 20, 30, true]  (z > 25 = true)
9. jmp_if_false L0  → на стеке true, продолжаем
10. push z          → стек: [10, 20, 30, true, z]  (z = 30)
11. jmp L1          → переходим к L1
12. label L0        → пропускаем (не выполняется)
13. push 0          → пропускаем (не выполняется)
14. label L1        → конец
```

### 6. Визуализация работы генератора

```
AST Node                    →  IR Instruction
─────────────────────────────────────────────────
Literal(10)                 →  push 10
Ident("x")                  →  push x
BinOp(+, left, right)       →  [код для left]
                              [код для right]
                              add
If(cond, then, else)        →  [код для cond]
                              jmp_if_false L0
                              [код для then]
                              jmp L1
                              label L0
                              [код для else]
                              label L1
```

### 7. Запуск генерации

```bash
# Генерация IR в stdout
python3 -m main.main examples/ir_demo_example.txt --ir

# Генерация IR в файл
python3 -m main.main examples/ir_demo_example.txt --ir --ir-output demo.ir
```

### 8. Код генератора (упрощенно)

```python
def _gen_binop(self, binop: BinOp) -> None:
    # Генерируем код для левого операнда
    self._gen_expr(binop.left)    # → push x
    # Генерируем код для правого операнда
    self._gen_expr(binop.right)   # → push y
    # Генерируем операцию
    self.instructions.append(Op(IROp.ADD))  # → add
    # Результат: push x, push y, add
```

### 9. Преимущества стек-машины

1. **Простота**: не нужно управлять регистрами
2. **Компактность**: команды короткие
3. **Универсальность**: одна команда для всех типов данных
4. **Легко интерпретировать**: можно написать простой интерпретатор

### 10. Пример интерпретации IR (концептуально)

```python
stack = []
pc = 0  # program counter

while pc < len(instructions):
    instr = instructions[pc]
    
    if isinstance(instr, Push):
        stack.append(instr.value)
    elif isinstance(instr, Op):
        if instr.op == IROp.ADD:
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
    elif isinstance(instr, JmpIfFalse):
        if stack.pop() == False:
            pc = find_label(instr.label)
            continue
    
    pc += 1
```

