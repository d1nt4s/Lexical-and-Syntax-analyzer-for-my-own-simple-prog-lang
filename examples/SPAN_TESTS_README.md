# Инструкция по запуску примеров для проверки spans

## Созданные примеры

### Валидные примеры (синтаксически и семантически правильные):

1. **`span_test_simple.txt`** - самый простой пример
   - Базовые объявления и операции
   - Идеален для быстрой проверки

2. **`span_test_valid.txt`** - полный валидный пример
   - Все типы statements: Decl, StructDecl, EnumDecl, FuncDef, If, For, Return, Read, Print
   - Проверяет spans для всех конструкций

3. **`span_test_struct_fields.txt`** - пример с struct и полями
   - Проверяет spans для FieldDecl
   - Доступ к полям через точку

4. **`span_test_functions.txt`** - пример с функциями и процедурами
   - Проверяет spans для FuncDef
   - Вызовы функций

### Примеры с семантическими ошибками:

5. **`span_test_semantic_errors.txt`** - примеры с семантическими ошибками
   - Дублирование полей в struct
   - Дублирование членов в enum
   - Использование несуществующих переменных
   - Использование несуществующих полей
   - Вызов несуществующих функций
   
   ⚠️ **Важно**: Эти примеры синтаксически правильные и будут успешно парситься.
   Семантические ошибки будут обнаружены только при реализации семантического анализатора.

## Как запустить примеры

### 1. Красивый вывод AST (pretty print):

```bash
# Простой пример
python3 -m main.main examples/span_test_simple.txt

# Полный валидный пример
python3 -m main.main examples/span_test_valid.txt

# Пример с struct
python3 -m main.main examples/span_test_struct_fields.txt

# Пример с функциями
python3 -m main.main examples/span_test_functions.txt

# Пример с семантическими ошибками (парсится успешно)
python3 -m main.main examples/span_test_semantic_errors.txt
```

### 2. JSON вывод AST (для проверки spans в JSON):

```bash
# Простой пример в JSON
python3 -m main.main examples/span_test_simple.txt --json

# Полный пример в JSON
python3 -m main.main examples/span_test_valid.txt --json

# Пример с struct в JSON
python3 -m main.main examples/span_test_struct_fields.txt --json

# Пример с функциями в JSON
python3 -m main.main examples/span_test_functions.txt --json

# Пример с семантическими ошибками в JSON
python3 -m main.main examples/span_test_semantic_errors.txt --json
```

### 3. Запуск всех примеров одной командой:

```bash
# Все span_test примеры
for f in examples/span_test_*.txt; do
  echo "=========================================="
  echo ">>> $f"
  echo "=========================================="
  python3 -m main.main "$f" || echo "(ошибка парсинга)"
  echo
done
```

### 4. Сравнение pretty и JSON вывода:

```bash
# Pretty print
python3 -m main.main examples/span_test_simple.txt

# JSON (можно сохранить в файл)
python3 -m main.main examples/span_test_simple.txt --json > output.json
```

## Что проверять в выводе

### В pretty print:
- Узлы AST должны отображаться с правильной структурой
- Все statements должны иметь spans (проверяется в тестах)

### В JSON выводе:
- Каждый узел должен иметь поле `span` (если он его поддерживает)
- `span` должен содержать `start` и `end` с полями `line` и `col`
- Пример:
  ```json
  {
    "type": "Decl",
    "id": 3,
    "span": {
      "start": {"line": 1, "col": 1},
      "end": {"line": 1, "col": 10}
    },
    ...
  }
  ```

## Проверка spans для семантических ошибок

Когда будет реализован семантический анализатор, примеры из `span_test_semantic_errors.txt` должны:
1. Успешно парситься (синтаксически правильные)
2. Выдавать семантические ошибки с правильными позициями благодаря spans

Например, при дублировании поля в struct, ошибка должна указывать на правильную позицию второго объявления поля благодаря span в FieldDecl.

## Быстрый старт

Самый простой способ начать:

```bash
# 1. Простой пример
python3 -m main.main examples/span_test_simple.txt

# 2. Посмотреть JSON
python3 -m main.main examples/span_test_simple.txt --json

# 3. Полный пример
python3 -m main.main examples/span_test_valid.txt --json | head -50
```

