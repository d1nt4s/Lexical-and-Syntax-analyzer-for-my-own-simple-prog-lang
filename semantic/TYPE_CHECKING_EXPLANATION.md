# Объяснение системы проверки типов в Semantic Analyzer

## Что было до этого и чего не хватало

### Старая версия (до добавления проверки типов)

Старый семантический анализатор проверял только:
- ✅ **Объявленность переменных** - есть ли переменная в scope
- ✅ **Дублирование имен** - нет ли повторных объявлений в том же scope
- ✅ **Существование полей структур** - есть ли поле в struct (но без проверки типов)
- ✅ **Существование функций** - объявлена ли функция (но без проверки аргументов и типов)

### Чего не хватало (требования спецификации)

Спецификация требует **статическую типизацию** и **type safety**, но старая версия этого не делала:

1. ❌ **Нет проверки типов в выражениях**
   - `int x = 10; bool y = true; int z = x + y;` - не ловилось (int + bool)
   - `if (10) { ... }` - не ловилось (int вместо bool)
   - `int x = true;` - не ловилось (int = bool)

2. ❌ **Нет проверки типов присваивания**
   - Можно было присвоить любой тип любому типу

3. ❌ **Нет проверки типов в операциях**
   - Арифметика: не проверялось, что операнды числа
   - Сравнения: не проверялось, что операнды числа
   - Логика: не проверялось, что операнды bool

4. ❌ **Нет проверки массивов**
   - Индекс может быть любым типом (должен быть int)
   - Можно индексировать не-массив
   - Не проверяется тип элемента при присваивании

5. ❌ **Нет проверки функций**
   - Не проверяется количество аргументов
   - Не проверяются типы аргументов
   - Не проверяется return type
   - Можно использовать `proc()` в выражениях

6. ❌ **Нет проверки return**
   - `func` может не возвращать значение
   - `proc` может возвращать значение

7. ❌ **Нет проверки main функции**
   - Не проверяется наличие ровно одной `main` функции

8. ❌ **Нет типизации узлов AST**
   - Каждому узлу выражения не назначался тип
   - Невозможно было проверить совместимость типов

---

## Что было добавлено

### 1. Система типизации узлов AST

**Проблема:** Нужно знать тип каждого выражения, чтобы проверять совместимость.

**Решение:** Добавлена таблица типов `types_by_node_id`, которая хранит тип каждого узла AST.

```python
# В __init__:
self.types_by_node_id: Dict[int, Type] = {}  # node.id -> Type

def _set_node_type(self, node: Node, typ: Type) -> None:
    """Сохранить тип узла в таблице."""
    self.types_by_node_id[node.id] = typ

def _get_node_type(self, node: Node) -> Optional[Type]:
    """Получить тип узла из таблицы."""
    return self.types_by_node_id.get(node.id)
```

**Зачем:** Каждый узел AST имеет уникальный `id`. Когда мы вычисляем тип выражения, мы сохраняем его в таблице. Потом можем быстро получить тип любого узла для проверки совместимости.

**Пример:**
```python
# int x = 10;
# 1. Вычисляем тип литерала 10 -> INT
# 2. Сохраняем: types_by_node_id[literal_node.id] = INT
# 3. Проверяем: тип x (INT) == тип 10 (INT) ✓
```

---

### 2. Конвертация TypeSpec → Type

**Проблема:** В AST типы хранятся как `TypeSpec` (из parser), но для проверки нужны семантические типы `Type` (из semantic/types.py).

**Решение:** Функция `_type_spec_to_type()` конвертирует AST типы в семантические.

```python
def _type_spec_to_type(self, type_spec: TypeSpec) -> Type:
    """Конвертировать AST TypeSpec в семантический Type."""
    if isinstance(type_spec, BaseType):
        if type_spec.kind.name == "INT":
            return INT
        elif type_spec.kind.name == "REAL":
            return REAL
        elif type_spec.kind.name == "BOOL":
            return BOOL
    elif isinstance(type_spec, ASTArrayType):
        elem_type = self._type_spec_to_type(type_spec.base)
        return ArrayType(elem=elem_type, dims=type_spec.dims)
    elif isinstance(type_spec, NamedStructType):
        return StructType(name=type_spec.name)
```

**Зачем:** 
- `BaseType(kind=INT)` из AST → `INT` из semantic/types.py
- `ArrayType(base=BaseType(INT), dims=1)` → `ArrayType(elem=INT, dims=1)`
- `NamedStructType(name="Point")` → `StructType(name="Point")`

**Пример:**
```python
# В AST: Decl(type_spec=BaseType(kind=INT), name="x")
# Конвертируем: _type_spec_to_type(BaseType(INT)) → INT
# Теперь можем сравнивать типы: INT == INT ✓
```

---

### 3. Вычисление типов выражений (_infer_type)

**Проблема:** Нужно вычислить тип любого выражения и проверить правильность операций.

**Решение:** Функция `_infer_type(expr)` рекурсивно вычисляет тип выражения и сохраняет его в таблице типов.

#### 3.1. Литералы

```python
if isinstance(expr, Literal):
    if isinstance(expr.value, bool):
        typ = BOOL
    elif isinstance(expr.value, int):
        typ = INT
    elif isinstance(expr.value, float):
        typ = REAL
```

**Зачем:** Литерал `10` имеет тип `int`, `true` имеет тип `bool`, `3.14` имеет тип `real`.

#### 3.2. Идентификаторы (переменные)

```python
elif isinstance(expr, Ident):
    symbol = self.current_scope.lookup(expr.name)
    if symbol is None:
        raise SemanticError(f"TYPE_ERROR: Undeclared variable '{expr.name}'", expr)
    decl: Decl = symbol.data
    typ = self._type_spec_to_type(decl.type_spec)
```

**Зачем:** 
1. Ищем переменную в scope
2. Если не найдена → ошибка
3. Если найдена → берем тип из объявления и конвертируем в семантический тип

**Пример:**
```python
# int x = 10;
# x (Ident) → ищем в scope → находим Decl(type_spec=BaseType(INT))
# → конвертируем → INT
```

#### 3.3. Арифметические операции (BinOp: +, -, *, /)

```python
elif isinstance(expr, BinOp):
    if expr.op in (OpKind.ADD, OpKind.SUB, OpKind.MUL, OpKind.DIV):
        left_type = self._infer_type(expr.left)
        right_type = self._infer_type(expr.right)
        
        # Оба операнда должны быть числами
        if left_type.tag not in (TypeTag.INT, TypeTag.REAL):
            raise SemanticError("Arithmetic operand must be number", expr.left)
        if right_type.tag not in (TypeTag.INT, TypeTag.REAL):
            raise SemanticError("Arithmetic operand must be number", expr.right)
        
        # Оба операнда должны иметь одинаковый тип
        if left_type.tag != right_type.tag:
            raise SemanticError("Arithmetic operands must have same type", expr)
        
        typ = left_type  # Результат имеет тот же тип, что и операнды
```

**Зачем:** 
- `int + int` → `int` ✓
- `real + real` → `real` ✓
- `int + real` → ошибка (нет неявных кастов) ✗
- `int + bool` → ошибка (bool не число) ✗

**Пример:**
```python
# int x = 10; bool y = true;
# x + y → вычисляем тип x (INT), тип y (BOOL)
# → проверяем: INT и BOOL не числа → ошибка!
```

#### 3.4. Сравнения (BinOp: <, <=, >, >=, ==, !=)

```python
elif expr.op in (OpKind.LT, OpKind.LE, OpKind.GT, OpKind.GE, OpKind.EQ, OpKind.NEQ):
    left_type = self._infer_type(expr.left)
    right_type = self._infer_type(expr.right)
    
    # Оба операнда должны быть числами
    if left_type.tag not in (TypeTag.INT, TypeTag.REAL):
        raise SemanticError("Comparison operand must be number", expr.left)
    if right_type.tag not in (TypeTag.INT, TypeTag.REAL):
        raise SemanticError("Comparison operand must be number", expr.right)
    
    # Оба операнда должны иметь одинаковый тип
    if left_type.tag != right_type.tag:
        raise SemanticError("Comparison operands must have same type", expr)
    
    typ = BOOL  # Результат сравнения всегда bool
```

**Зачем:** 
- `10 < 20` → `bool` ✓
- `10 < true` → ошибка (bool не число) ✗
- `10 < 3.14` → ошибка (int != real) ✗

#### 3.5. Логические операции (BinOp: &&, ||)

```python
elif expr.op in (OpKind.AND, OpKind.OR):
    left_type = self._infer_type(expr.left)
    right_type = self._infer_type(expr.right)
    
    # Оба операнда должны быть bool
    if left_type.tag != TypeTag.BOOL:
        raise SemanticError("Logical operand must be bool", expr.left)
    if right_type.tag != TypeTag.BOOL:
        raise SemanticError("Logical operand must be bool", expr.right)
    
    typ = BOOL  # Результат логической операции всегда bool
```

**Зачем:** 
- `true && false` → `bool` ✓
- `true && 10` → ошибка (int не bool) ✗

#### 3.6. Унарные операции

**Отрицание (-):**
```python
elif isinstance(expr, UnOp):
    if expr.op == OpKind.NEG:
        expr_type = self._infer_type(expr.expr)
        if expr_type.tag not in (TypeTag.INT, TypeTag.REAL):
            raise SemanticError("Negation operand must be number", expr.expr)
        typ = expr_type  # Результат имеет тот же тип
```

**Зачем:** `-10` → `int`, `-3.14` → `real`, `-true` → ошибка ✗

**Логическое НЕ (!):**
```python
elif expr.op == OpKind.NOT:
    expr_type = self._infer_type(expr.expr)
    if expr_type.tag != TypeTag.BOOL:
        raise SemanticError("Not operand must be bool", expr.expr)
    typ = BOOL
```

**Зачем:** `!true` → `bool`, `!10` → ошибка ✗

#### 3.7. Индексирование массивов (IndexExpr)

```python
elif isinstance(expr, IndexExpr):
    base_type = self._infer_type(expr.base)
    index_type = self._infer_type(expr.index)
    
    # Индекс должен быть int
    if index_type.tag != TypeTag.INT:
        raise SemanticError("Array index must be int", expr.index)
    
    # База должна быть массивом
    if base_type.tag != TypeTag.ARRAY:
        raise SemanticError("Indexing non-array type", expr.base)
    
    if not isinstance(base_type, ArrayType):
        raise SemanticError("Invalid array type", expr.base)
    
    # Результат - тип элемента, с уменьшенной размерностью
    if base_type.dims == 1:
        typ = base_type.elem  # int[10] → int
    else:
        typ = ArrayType(elem=base_type.elem, dims=base_type.dims - 1)  # int[10][5] → int[5]
```

**Зачем:** 
- `int[10] arr; arr[0]` → тип `int` ✓
- `int[10][5] arr; arr[0]` → тип `int[5]` ✓
- `int x; x[0]` → ошибка (x не массив) ✗
- `arr[true]` → ошибка (индекс не int) ✗

**Пример:**
```python
# int[10] arr;
# arr[0] → base_type = ArrayType(elem=INT, dims=1)
# → dims == 1 → typ = INT
```

#### 3.8. Доступ к полям структур (FieldAccessExpr)

```python
elif isinstance(expr, FieldAccessExpr):
    base_type = self._infer_type(expr.base)
    
    # База должна быть struct
    if base_type.tag != TypeTag.STRUCT:
        raise SemanticError("Field access on non-struct type", expr.base)
    
    if not isinstance(base_type, StructType):
        raise SemanticError("Invalid struct type", expr.base)
    
    struct_name = base_type.name
    
    # Ищем тип поля в struct_fields
    if struct_name not in self.struct_fields:
        raise SemanticError(f"Struct '{struct_name}' not found", expr)
    
    if expr.field not in self.struct_fields[struct_name]:
        raise SemanticError(f"Field '{expr.field}' does not exist", expr)
    
    # Получаем тип поля из struct_fields
    typ = self.struct_fields[struct_name][expr.field]
```

**Зачем:** 
- `struct Point { int x; real y; }`
- `struct Point p;`
- `p.x` → тип `int` ✓
- `p.y` → тип `real` ✓
- `p.z` → ошибка (поле не существует) ✗
- `int x; x.y` → ошибка (x не struct) ✗

**Важно:** Теперь `struct_fields` хранит не только имена полей, но и их типы:
```python
# Было: struct_fields["Point"] = {"x", "y"}  # только имена
# Стало: struct_fields["Point"] = {"x": INT, "y": REAL}  # имена и типы
```

#### 3.9. Вызов функций (CallExpr)

```python
elif isinstance(expr, CallExpr):
    symbol = self.global_scope.lookup(expr.callee)
    if symbol is None or symbol.kind != "func":
        raise SemanticError(f"Undeclared function '{expr.callee}'", expr)
    
    func: FuncDef = symbol.data
    
    # Проверка количества аргументов
    if len(expr.args) != len(func.params):
        raise SemanticError(f"Function expects {len(func.params)} arguments, got {len(expr.args)}", expr)
    
    # Проверка типов аргументов
    for i, (arg_expr, param) in enumerate(zip(expr.args, func.params)):
        arg_type = self._infer_type(arg_expr)
        param_type = self._type_spec_to_type(param.type_spec)
        self._check_type_compat(param_type, arg_type, arg_expr, f" in argument {i+1}")
    
    # Проверка: proc нельзя использовать в выражениях
    if func.is_proc:
        raise SemanticError(f"Procedure '{expr.callee}' cannot be used in expression", expr)
    
    # Тип вызова = return type функции
    if func.ret_type is None:
        raise SemanticError(f"Function '{expr.callee}' has no return type", func)
    typ = self._type_spec_to_type(func.ret_type)
```

**Зачем:** 
- `func int add(int a, int b) { return a + b; }`
- `add(5, 3)` → тип `int` ✓
- `add(5)` → ошибка (неправильное количество аргументов) ✗
- `add(5, true)` → ошибка (неправильный тип аргумента) ✗
- `proc print_hello() { ... }`
- `int x = print_hello();` → ошибка (proc в выражении) ✗

---

### 4. Проверка совместимости типов (_check_type_compat)

**Проблема:** Нужно проверить, что два типа совместимы (без неявных кастов).

**Решение:** Функция `_check_type_compat()` проверяет, что типы полностью совпадают.

```python
def _check_type_compat(self, expected: Type, actual: Type, node: Node, context: str = "") -> None:
    """Проверить совместимость типов (без неявных кастов)."""
    if expected.tag != actual.tag:
        raise SemanticError(
            f"TYPE_ERROR: Type mismatch{context}: expected {self._type_to_str(expected)}, got {self._type_to_str(actual)}",
            node
        )
    
    # Для массивов проверяем размерность и тип элемента
    if expected.tag == TypeTag.ARRAY:
        if not isinstance(expected, ArrayType) or not isinstance(actual, ArrayType):
            raise SemanticError(f"TYPE_ERROR: Array type mismatch{context}", node)
        if expected.dims != actual.dims:
            raise SemanticError(f"TYPE_ERROR: Array dimension mismatch{context}", node)
        self._check_type_compat(expected.elem, actual.elem, node, context)
    
    # Для структур проверяем имя
    elif expected.tag == TypeTag.STRUCT:
        if not isinstance(expected, StructType) or not isinstance(actual, StructType):
            raise SemanticError(f"TYPE_ERROR: Struct type mismatch{context}", node)
        if expected.name != actual.name:
            raise SemanticError(f"TYPE_ERROR: Struct name mismatch{context}", node)
```

**Зачем:** 
- `int x = 10;` → `INT == INT` ✓
- `int x = true;` → `INT != BOOL` → ошибка ✗
- `int x = 3.14;` → `INT != REAL` → ошибка ✗
- `int[10] arr1; int[10] arr2; arr1 = arr2;` → `ArrayType(INT, 1) == ArrayType(INT, 1)` ✓
- `int[10] arr1; int[5] arr2; arr1 = arr2;` → ошибка (разная размерность) ✗

**Пример использования:**
```python
# int x = 10;
decl_type = INT  # тип переменной x
init_type = self._infer_type(decl.init)  # тип литерала 10 → INT
self._check_type_compat(decl_type, init_type, decl.init, " in initialization")
# → INT == INT ✓
```

---

### 5. Проверка присваивания с типами

**Было:**
```python
def _check_assign(self, assign: Assign) -> None:
    self._check_lvalue(assign.lvalue)  # только проверка объявленности
    self._check_expr(assign.expr)      # только проверка объявленности
```

**Стало:**
```python
def _check_assign(self, assign: Assign) -> None:
    lvalue_type = self._check_lvalue(assign.lvalue)  # получаем тип lvalue
    rhs_type = self._infer_type(assign.expr)         # вычисляем тип rhs
    self._check_type_compat(lvalue_type, rhs_type, assign.expr, " in assignment")
```

**Зачем:** Теперь проверяем не только объявленность, но и совместимость типов.

**Пример:**
```python
# int x = 10;
# lvalue_type = INT (тип x)
# rhs_type = INT (тип 10)
# → INT == INT ✓

# int x = true;
# lvalue_type = INT
# rhs_type = BOOL
# → INT != BOOL → ошибка!
```

---

### 6. Проверка lvalue с типами

**Было:** `_check_lvalue()` только проверяла объявленность.

**Стало:** `_check_lvalue()` возвращает тип lvalue.

```python
def _check_lvalue(self, expr: Expr) -> Type:
    if isinstance(expr, Ident):
        self._check_ident(expr)
        return self._infer_type(expr)  # тип переменной
    
    elif isinstance(expr, IndexExpr):
        base_type = self._infer_type(expr.base)
        index_type = self._infer_type(expr.index)
        
        # Проверки...
        
        # Тип элемента массива
        if base_type.dims == 1:
            return base_type.elem  # int[10] → int
        else:
            return ArrayType(elem=base_type.elem, dims=base_type.dims - 1)
    
    elif isinstance(expr, FieldAccessExpr):
        return self._infer_type(expr)  # тип поля структуры
```

**Зачем:** Нужно знать тип lvalue, чтобы проверить совместимость с rhs.

**Пример:**
```python
# int[10] arr;
# arr[0] = 5;
# lvalue = arr[0] → тип INT (тип элемента массива)
# rhs = 5 → тип INT
# → INT == INT ✓
```

---

### 7. Проверка if/for с типами

**Было:**
```python
def _check_if(self, if_stmt: If) -> None:
    self._check_expr(if_stmt.cond)  # только проверка объявленности
```

**Стало:**
```python
def _check_if(self, if_stmt: If) -> None:
    cond_type = self._infer_type(if_stmt.cond)
    if cond_type.tag != TypeTag.BOOL:
        raise SemanticError(f"TYPE_ERROR: If condition must be bool, got {self._type_to_str(cond_type)}", if_stmt.cond)
```

**Зачем:** Условие if/for должно быть bool.

**Пример:**
```python
# if (10) { ... }  → ошибка (int вместо bool)
# if (true) { ... }  → OK
```

---

### 8. Проверка return с типами

**Новая функция:** `_check_return()`

```python
def _check_return(self, ret: Return) -> None:
    if self.current_func is None:
        raise SemanticError("TYPE_ERROR: Return statement outside function", ret)
    
    if self.current_func.is_proc:
        # Procedure: return должен быть без выражения
        if ret.expr is not None:
            raise SemanticError(f"TYPE_ERROR: Procedure cannot return a value", ret)
    else:
        # Function: return должен иметь выражение
        if ret.expr is None:
            raise SemanticError(f"TYPE_ERROR: Function must return a value", ret)
        
        # Тип выражения должен совпадать с return type функции
        ret_expr_type = self._infer_type(ret.expr)
        expected_type = self._type_spec_to_type(self.current_func.ret_type)
        self._check_type_compat(expected_type, ret_expr_type, ret.expr, " in return statement")
```

**Зачем:** 
- `func int get_value() { return 10; }` → OK (int == int)
- `func int get_value() { return true; }` → ошибка (int != bool)
- `proc print_hello() { return 10; }` → ошибка (proc не может возвращать значение)
- `func int get_value() { return; }` → ошибка (func должен возвращать значение)

**Важно:** Используется `self.current_func` для отслеживания текущей функции (устанавливается в `_check_func_body`).

---

### 9. Проверка main функции

**Добавлено в `analyze()`:**
```python
# Check for exactly one main function
main_funcs = [s for s in program.stmts if isinstance(s, FuncDef) and s.name == "main"]
if len(main_funcs) == 0:
    raise SemanticError("TYPE_ERROR: No 'main' function found", program)
elif len(main_funcs) > 1:
    raise SemanticError("TYPE_ERROR: Multiple 'main' functions found", main_funcs[1])
```

**Зачем:** Спецификация требует ровно одну `main` функцию.

---

### 10. Улучшенное хранение типов полей структур

**Было:**
```python
self.struct_fields: Dict[str, Set[str]] = {}  # struct_name -> {field_names}
```

**Стало:**
```python
self.struct_fields: Dict[str, Dict[str, Type]] = {}  # struct_name -> {field_name -> field_type}
```

**Зачем:** Теперь храним не только имена полей, но и их типы, чтобы правильно вычислять тип `FieldAccessExpr`.

**Обновлено в `_check_struct_decl()`:**
```python
def _check_struct_decl(self, struct: StructDecl) -> None:
    field_types: Dict[str, Type] = {}
    
    for field in struct.fields:
        if field.name in field_types:
            raise SemanticError(f"TYPE_ERROR: Duplicate field '{field.name}'", field)
        
        # Конвертируем тип поля и сохраняем
        field_type = self._type_spec_to_type(field.type_spec)
        field_types[field.name] = field_type
    
    self.struct_fields[struct.name] = field_types
```

**Пример:**
```python
# struct Point { int x; real y; }
# struct_fields["Point"] = {"x": INT, "y": REAL}
# p.x → тип INT
# p.y → тип REAL
```

---

## Итоговая архитектура

### Поток работы:

1. **ПРОХОД 1: Сбор объявлений**
   - Собираем struct, enum, func
   - Для struct сохраняем типы полей

2. **ПРОХОД 2: Проверка и типизация**
   - Для каждого statement:
     - Проверяем объявленность
     - Вычисляем типы выражений (`_infer_type`)
     - Проверяем совместимость типов (`_check_type_compat`)

### Ключевые функции:

| Функция | Что делает |
|---------|------------|
| `_type_spec_to_type()` | Конвертирует AST TypeSpec → семантический Type |
| `_infer_type()` | Вычисляет тип выражения и сохраняет в таблице |
| `_check_type_compat()` | Проверяет совместимость двух типов |
| `_check_lvalue()` | Проверяет lvalue и возвращает его тип |
| `_check_return()` | Проверяет return statement (func/proc) |
| `_set_node_type()` / `_get_node_type()` | Работа с таблицей типов |

### Таблицы данных:

| Таблица | Хранит |
|---------|--------|
| `types_by_node_id` | `node.id → Type` (тип каждого узла) |
| `struct_fields` | `struct_name → {field_name → field_type}` (типы полей) |
| `current_func` | Текущая функция (для проверки return) |

---

## Примеры работы

### Пример 1: Арифметика

```minilang
proc main() {
    int x = 10;
    bool y = true;
    int z = x + y;  // ОШИБКА
}
```

**Что происходит:**
1. `x` → тип `INT` (из объявления)
2. `y` → тип `BOOL` (из объявления)
3. `x + y` → `_infer_type(BinOp)`:
   - Вычисляем тип `x` → `INT`
   - Вычисляем тип `y` → `BOOL`
   - Проверяем: `BOOL.tag not in (INT, REAL)` → **ОШИБКА!**

### Пример 2: Присваивание

```minilang
proc main() {
    int x = 10;
    bool y = true;
    x = y;  // ОШИБКА
}
```

**Что происходит:**
1. `_check_assign()`:
   - `lvalue_type = _check_lvalue(x)` → `INT`
   - `rhs_type = _infer_type(y)` → `BOOL`
   - `_check_type_compat(INT, BOOL, ...)` → `INT.tag != BOOL.tag` → **ОШИБКА!**

### Пример 3: Функции

```minilang
func int add(int a, int b) {
    return a + b;
}

proc main() {
    int x = add(5, true);  // ОШИБКА
}
```

**Что происходит:**
1. `add(5, true)` → `_infer_type(CallExpr)`:
   - Находим функцию `add`
   - Проверяем количество аргументов: `2 == 2` ✓
   - Проверяем типы аргументов:
     - Аргумент 1: `5` → `INT`, параметр → `INT` ✓
     - Аргумент 2: `true` → `BOOL`, параметр → `INT` → **ОШИБКА!**

---

## Заключение

Теперь семантический анализатор полностью реализует **статическую типизацию** и **type safety**:

✅ Типизация всех узлов AST  
✅ Запрет неявных кастов  
✅ Проверка типов во всех операциях  
✅ Проверка массивов, структур, функций  
✅ Проверка return statements  
✅ Проверка main функции  

Все ошибки имеют префикс `TYPE_ERROR:` для ясности.

