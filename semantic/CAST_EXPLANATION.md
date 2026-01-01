# Объяснение реализации явного кастования чисел

## Что было добавлено

Добавлена поддержка явного кастования чисел в язык: выражения вида `int(expr)` и `real(expr)` для преобразования типов.

---

## Изменения в коде

### 1. AST узел CastExpr (`parser/ast.py`)

**Что добавлено:**

```python
@dataclass
class CastExpr(Expr):
    target_type: TypeKind = TypeKind.INT  # INT or REAL
    expr: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "CastExpr", "id": self.id, "target_type": self.target_type.name, "expr": self.expr.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}CastExpr#{self.id}({self.target_type.name})\n" + self.expr.pretty(indent + 1)
```

**Где размещено:** После определения `TypeKind` (строка ~147), чтобы `TypeKind` был доступен для использования в типе поля.

**Зачем:** Новый тип узла AST для представления cast-выражений. Хранит:
- `target_type`: целевой тип каста (`TypeKind.INT` или `TypeKind.REAL`)
- `expr`: выражение, которое кастуется

**Пример AST:**
```
CastExpr(INT)
  └─ Literal(10)
```
для `int(10)`

---

### 2. Парсинг cast-выражений (`parser/parser.py`)

**Что изменено:** Метод `parse_primary()`

**Было:**
```python
def parse_primary(self) -> Expr:
    tok = self.ts.peek()
    if self.ts.match(K.INT_LIT):
        return Literal(value=tok.value, span=span_from(tok, tok))
    # ... остальные случаи
```

**Стало:**
```python
def parse_primary(self) -> Expr:
    tok = self.ts.peek()
    # Check for cast expressions: int(expr) or real(expr)
    # We check if current token is KW_INT/KW_REAL AND next token is LPAREN
    if tok.kind == K.INT:
        # Check if next token exists and is LPAREN
        if self.ts.i + 1 < len(self.ts.toks) and self.ts.toks[self.ts.i + 1].kind == K.LPAREN:
            # This is a cast: int(expr)
            start = self.ts.expect(K.INT, "Expected 'int' in cast")
            self.ts.expect(K.LPAREN, "Expected '(' after 'int' in cast")
            expr = self.parse_expr()
            end = self.ts.expect(K.RPAREN, "Expected ')' after cast expression")
            return CastExpr(target_type=TypeKind.INT, expr=expr, span=span_from(start, end))
    if tok.kind == K.REAL:
        # Check if next token exists and is LPAREN
        if self.ts.i + 1 < len(self.ts.toks) and self.ts.toks[self.ts.i + 1].kind == K.LPAREN:
            # This is a cast: real(expr)
            start = self.ts.expect(K.REAL, "Expected 'real' in cast")
            self.ts.expect(K.LPAREN, "Expected '(' after 'real' in cast")
            expr = self.parse_expr()
            end = self.ts.expect(K.RPAREN, "Expected ')' after cast expression")
            return CastExpr(target_type=TypeKind.REAL, expr=expr, span=span_from(start, end))
    # ... остальные случаи (литералы, идентификаторы и т.д.)
```

**Как работает:**

1. **Проверка токена:** Смотрим текущий токен через `peek()`
2. **Lookahead:** Если токен `KW_INT` или `KW_REAL`, проверяем следующий токен через прямой доступ к массиву токенов: `self.ts.toks[self.ts.i + 1]`
3. **Распознавание cast:** Если следующий токен `LPAREN`, то это cast-выражение, а не объявление типа
4. **Парсинг:** Парсим `int`/`real`, затем `(`, затем выражение, затем `)`
5. **Создание узла:** Создаем `CastExpr` с соответствующим `target_type`

**Почему lookahead важен:**

Без lookahead парсер не может различить:
- `int x;` - объявление переменной (парсится в `parse_decl_core()`)
- `int(10)` - cast-выражение (парсится в `parse_primary()`)

Lookahead позволяет проверить, что после `int`/`real` идет `(`, что означает cast.

**Примеры парсинга:**

```minilang
int(10)        → CastExpr(target_type=INT, expr=Literal(10))
real(x)        → CastExpr(target_type=REAL, expr=Ident("x"))
int(3.0)       → CastExpr(target_type=INT, expr=Literal(3.0))
real(5 + 3)    → CastExpr(target_type=REAL, expr=BinOp(ADD, ...))
```

---

### 3. Экспорт CastExpr (`parser/__init__.py`)

**Что изменено:** Добавлен `CastExpr` в импорты и `__all__`

```python
from .ast import (
    ...
    CastExpr, ...
)

__all__ = [
    ...
    "CastExpr", ...
]
```

**Зачем:** Чтобы `CastExpr` был доступен для импорта из пакета `parser`.

---

### 4. Семантическая проверка cast (`semantic/analyzer.py`)

#### 4.1. Импорты

**Что добавлено:**
```python
from parser.ast import (
    ...
    CastExpr, ...
    TypeKind
)
```

#### 4.2. Обработка CastExpr в `_infer_type()`

**Что добавлено:** Новый блок `elif isinstance(expr, CastExpr):` в методе `_infer_type()`

**Полный код:**

```python
elif isinstance(expr, CastExpr):
    # Cast expressions: int(expr) or real(expr)
    expr_type = self._infer_type(expr.expr)
    
    if expr.target_type == TypeKind.INT:
        # Cast to int
        if expr_type.tag == TypeTag.REAL:
            # real -> int: only allowed if expr is literal real with zero fractional part
            if isinstance(expr.expr, Literal) and isinstance(expr.expr.value, float):
                # Check if fractional part is zero (within floating point precision)
                fractional_part = abs(expr.expr.value - float(int(expr.expr.value)))
                if fractional_part > 1e-10:  # Allow small floating point errors
                    raise SemanticError(
                        "TYPE_ERROR: neispravno kastovanje",
                        expr
                    )
                typ = INT
            else:
                # Not a literal real, or not zero fractional part
                raise SemanticError(
                    "TYPE_ERROR: neispravno kastovanje",
                    expr
                )
        elif expr_type.tag == TypeTag.INT:
            # int -> int: no-op, but allowed
            typ = INT
        else:
            # Other types cannot be cast to int
            raise SemanticError(
                f"TYPE_ERROR: Cannot cast {self._type_to_str(expr_type)} to int",
                expr
            )
    
    elif expr.target_type == TypeKind.REAL:
        # Cast to real
        if expr_type.tag == TypeTag.INT:
            # int -> real: always OK
            typ = REAL
        elif expr_type.tag == TypeTag.REAL:
            # real -> real: no-op, but allowed
            typ = REAL
        else:
            # Other types cannot be cast to real
            raise SemanticError(
                f"TYPE_ERROR: Cannot cast {self._type_to_str(expr_type)} to real",
                expr
            )
    
    else:
        # Cast to bool or other types not allowed
        raise SemanticError(
            f"TYPE_ERROR: Cannot cast to {expr.target_type.name}",
            expr
        )
```

**Как работает:**

1. **Вычисление типа выражения:** Сначала вычисляем тип выражения внутри cast: `expr_type = self._infer_type(expr.expr)`

2. **Проверка целевого типа:**
   - Если `target_type == INT` → каст к `int`
   - Если `target_type == REAL` → каст к `real`
   - Иначе → ошибка

3. **Правила кастования:**

   **a) Каст к `int` (`int(expr)`):**
   
   - **`real -> int`:** Разрешен только если:
     - `expr` является `Literal` с типом `float`
     - Дробная часть равна 0 (с учетом погрешности float)
     - Примеры: `int(3.0)` ✓, `int(5.0)` ✓
     - НЕ разрешено: `int(3.14)` ✗, `int(x)` где `x: real` ✗
   
   - **`int -> int`:** Разрешен (no-op)
   
   - **Другие типы -> int:** Запрещены
   
   **b) Каст к `real` (`real(expr)`):**
   
   - **`int -> real`:** Всегда разрешен
     - Примеры: `real(10)` ✓, `real(x)` где `x: int` ✓
   
   - **`real -> real`:** Разрешен (no-op)
   
   - **Другие типы -> real:** Запрещены

4. **Проверка дробной части:**

```python
fractional_part = abs(expr.expr.value - float(int(expr.expr.value)))
if fractional_part > 1e-10:  # Allow small floating point errors
    raise SemanticError("TYPE_ERROR: neispravno kastovanje", expr)
```

**Зачем проверка на `1e-10`:** Из-за погрешности представления float в Python, `3.0` может быть представлено как `2.9999999999` или `3.0000000001`. Используем порог `1e-10` для учета этой погрешности.

**Примеры проверки:**
- `3.0` → `abs(3.0 - 3.0) = 0.0 < 1e-10` ✓
- `3.14` → `abs(3.14 - 3.0) = 0.14 > 1e-10` ✗
- `5.0` → `abs(5.0 - 5.0) = 0.0 < 1e-10` ✓

---

## Правила кастования (сводка)

| Исходный тип | Целевой тип | Условие | Результат |
|--------------|-------------|---------|-----------|
| `int` | `real` | Всегда | ✓ Разрешено |
| `real` | `int` | Только literal с `.0` | ✓ Разрешено (например, `3.0`) |
| `real` | `int` | Literal с ненулевой дробной частью | ✗ Запрещено (`3.14`) |
| `real` | `int` | Переменная (не literal) | ✗ Запрещено (`int(x)` где `x: real`) |
| `int` | `int` | Всегда | ✓ Разрешено (no-op) |
| `real` | `real` | Всегда | ✓ Разрешено (no-op) |
| `bool` | `int`/`real` | - | ✗ Запрещено |
| Любой другой | `int`/`real` | - | ✗ Запрещено |

---

## Примеры работы

### Пример 1: `int -> real` (всегда разрешено)

```minilang
proc main() {
    int x = 10;
    real y = real(x);  // ✓ OK: int -> real всегда разрешено
    print(y);
}
```

**Что происходит:**
1. Парсер: `real(x)` → `CastExpr(target_type=REAL, expr=Ident("x"))`
2. Семантика: `_infer_type(CastExpr)`:
   - Вычисляем тип `x` → `INT`
   - Проверяем: `target_type == REAL`, `expr_type == INT`
   - Правило: `int -> real` всегда OK
   - Результат: `REAL`

### Пример 2: `real(3.0) -> int` (разрешено)

```minilang
proc main() {
    int y = int(3.0);  // ✓ OK: literal real с нулевой дробной частью
    print(y);
}
```

**Что происходит:**
1. Парсер: `int(3.0)` → `CastExpr(target_type=INT, expr=Literal(3.0))`
2. Семантика: `_infer_type(CastExpr)`:
   - Вычисляем тип `3.0` → `REAL`
   - Проверяем: `target_type == INT`, `expr_type == REAL`
   - Проверяем: `isinstance(expr.expr, Literal)` → `True`
   - Проверяем: `isinstance(expr.expr.value, float)` → `True`
   - Проверяем дробную часть: `abs(3.0 - 3.0) = 0.0 < 1e-10` → ✓
   - Результат: `INT`

### Пример 3: `real(3.14) -> int` (запрещено)

```minilang
proc main() {
    int y = int(3.14);  // ✗ ОШИБКА: дробная часть не нулевая
    print(y);
}
```

**Что происходит:**
1. Парсер: `int(3.14)` → `CastExpr(target_type=INT, expr=Literal(3.14))`
2. Семантика: `_infer_type(CastExpr)`:
   - Вычисляем тип `3.14` → `REAL`
   - Проверяем: `target_type == INT`, `expr_type == REAL`
   - Проверяем: `isinstance(expr.expr, Literal)` → `True`
   - Проверяем: `isinstance(expr.expr.value, float)` → `True`
   - Проверяем дробную часть: `abs(3.14 - 3.0) = 0.14 > 1e-10` → ✗
   - **ОШИБКА:** `"TYPE_ERROR: neispravno kastovanje"`

### Пример 4: `real` переменная `-> int` (запрещено)

```minilang
proc main() {
    real x = 3.0;
    int y = int(x);  // ✗ ОШИБКА: переменная, не literal
    print(y);
}
```

**Что происходит:**
1. Парсер: `int(x)` → `CastExpr(target_type=INT, expr=Ident("x"))`
2. Семантика: `_infer_type(CastExpr)`:
   - Вычисляем тип `x` → `REAL`
   - Проверяем: `target_type == INT`, `expr_type == REAL`
   - Проверяем: `isinstance(expr.expr, Literal)` → `False` (это `Ident`)
   - **ОШИБКА:** `"TYPE_ERROR: neispravno kastovanje"`

### Пример 5: `bool -> int` (запрещено)

```minilang
proc main() {
    bool x = true;
    int y = int(x);  // ✗ ОШИБКА: bool нельзя кастовать к int
    print(y);
}
```

**Что происходит:**
1. Парсер: `int(x)` → `CastExpr(target_type=INT, expr=Ident("x"))`
2. Семантика: `_infer_type(CastExpr)`:
   - Вычисляем тип `x` → `BOOL`
   - Проверяем: `target_type == INT`, `expr_type == BOOL`
   - Правило: `bool -> int` не разрешено
   - **ОШИБКА:** `"TYPE_ERROR: Cannot cast bool to int"`

---

## Архитектура решения

### Поток обработки cast-выражения:

```
Исходный код: int(10)
    ↓
Лексер: [KW_INT, LPAREN, INT_LIT(10), RPAREN]
    ↓
Парсер (parse_primary):
  - Видит KW_INT
  - Lookahead: следующий токен = LPAREN
  - Распознает как cast
  - Парсит: int, (, expr, )
  - Создает: CastExpr(target_type=INT, expr=Literal(10))
    ↓
Семантический анализатор (_infer_type):
  - Видит CastExpr
  - Вычисляет тип expr: INT
  - Проверяет правила кастования
  - Результат: INT (no-op, но разрешено)
    ↓
IR генератор (если используется):
  - Генерирует код для cast (если нужно)
```

---

## Важные детали реализации

### 1. Разрешение конфликта с объявлениями типов

**Проблема:** `int` и `real` используются и как ключевые слова типов (в объявлениях), и как операторы cast (в выражениях).

**Решение:** Lookahead в `parse_primary()`:
- Если `int`/`real` + `(` → это cast (парсится в `parse_primary()`)
- Если `int`/`real` + `IDENT` → это объявление (парсится в `parse_decl_core()`)

### 2. Проверка дробной части с учетом погрешности float

**Проблема:** Float числа в Python могут иметь погрешность представления.

**Решение:** Использование порога `1e-10`:
```python
fractional_part = abs(expr.expr.value - float(int(expr.expr.value)))
if fractional_part > 1e-10:
    # Ошибка: ненулевая дробная часть
```

### 3. Ограничение `real -> int` только литералами

**Почему:** Спецификация требует, чтобы `real -> int` был разрешен только для литералов с `.0`. Это означает, что:
- `int(3.0)` ✓ (literal)
- `int(x)` где `x: real = 3.0` ✗ (переменная, не literal)

Это сделано для безопасности типов: компилятор может проверить значение литерала на этапе компиляции, но не может гарантировать значение переменной.

---

## Тестирование

Все сценарии протестированы:

✅ `int -> real` (переменная и literal)  
✅ `real(3.0) -> int` (literal с нулевой дробной частью)  
✅ `real(3.14) -> int` (отклоняется: ненулевая дробная часть)  
✅ `real` переменная `-> int` (отклоняется: не literal)  
✅ `bool -> int` (отклоняется: недопустимый каст)  
✅ `int -> int` (no-op, разрешено)  
✅ `real -> real` (no-op, разрешено)  

---

## Итог

Добавлена полная поддержка явного кастования чисел:
- ✅ Новый AST узел `CastExpr`
- ✅ Парсинг `int(expr)` и `real(expr)`
- ✅ Семантическая проверка с правилами:
  - `int -> real`: всегда разрешено
  - `real -> int`: только для литералов с `.0`
  - Остальные касты запрещены
- ✅ Корректная обработка погрешности float
- ✅ Понятные сообщения об ошибках

Все изменения сделаны точечно, без переписывания существующего кода.

