# Intermediate Representation (IR) Generation

The `intermidiate` package contains the IR generator for a stack machine.

## Structure

- `ir.py` - IR instruction definitions (Push, Op, Label, Jmp, JmpIfFalse, etc.)
- `generator.py` - IR generator from AST
- `__init__.py` - package exports

## IR Instruction Set

### Base Stack Operations

#### `push <value>`
Pushes a value onto the stack. Value can be:
- Number: `push 10`, `push 3.14`
- Boolean: `push true`, `push false`
- Variable name: `push x` (reads variable x and pushes its value)

**Stack contract:** `[] -> [value]`

**Note:** For variables, `push <name>` is used instead of `load <name>` (spec requirement).

#### `pop [<name>]`
Removes top value from stack. With operand: `pop <name>` stores value to variable before popping.

**Stack contract:**
- `pop`: `[value] -> []`
- `pop <name>`: `[value] -> []` (stores value to variable `name`)

**Note:** `pop <name>` is used for variable writes instead of `store <name>` (spec requirement).

### Операции

#### `add`, `sub`, `mul`, `div`
Арифметические операции. Берет два верхних значения со стека, выполняет операцию, кладет результат обратно.

**Контракт стека:** `[a, b] -> [result]`

#### `lt`, `le`, `gt`, `ge`, `eq`, `neq`
Операции сравнения. Берет два верхних значения, сравнивает, кладет результат (true/false).

**Контракт стека:** `[a, b] -> [bool]`

#### `and`, `or`, `not`
Логические операции. `and` и `or` берут два значения, `not` - одно.

**Контракт стека:**
- `and`, `or`: `[a, b] -> [bool]`
- `not`: `[a] -> [bool]`

### Array Operations (Pseudo-instructions)

#### `load_index`
Loads array element onto stack. Takes base (array) and index from stack.

**Stack contract:** `[base, index] -> [value]`

**Note:** This is a pseudo-instruction. It can be expanded to base instructions using pointer arithmetic and memory access operations.

**Example:**
```
push a      # load array a (using push <name>)
push 5      # index
load_index  # load a[5]
```

#### `store_index`
Stores value to array element. Takes value, base and index from stack.

**Stack contract:** `[value, base, index] -> []`

**Note:** This is a pseudo-instruction, expandable to base instructions.

**Example:**
```
push 10     # value
push a      # array (using push <name>)
push 5      # index
store_index # store a[5] = 10
```

### Struct Field Operations (Pseudo-instructions)

#### `load_field <field>`
Loads struct field onto stack. Takes base (struct) from stack.

**Stack contract:** `[base] -> [value]`

**Note:** This is a pseudo-instruction, expandable to base instructions using field offset calculations.

**Example:**
```
push p      # load struct p (using push <name>)
load_field x # load p.x
```

#### `store_field <field>`
Stores value to struct field. Takes value and base from stack.

**Stack contract:** `[value, base] -> []`

**Note:** This is a pseudo-instruction, expandable to base instructions.

**Example:**
```
push 10     # value
push p      # struct (using push <name>)
store_field x # store p.x = 10
```

### Labels and Jumps

#### `label <name>`
Label for jumps (pseudo-string, optional for readability).

#### `jmp <label>`
Unconditional jump to label.

#### `jmp_if_false <label>`
Conditional jump: if false on stack, jumps to label. **Consumes bool from stack.**

**Stack contract:** `[bool] -> []`

**Note:** This is a macro instruction. It expands to: pop bool, push false, eq, jmp_if_false (or equivalent sequence). For simplicity, it's kept as a single instruction but documented as expandable.

**Example:**
```
push x
push 5
gt          # [true] or [false]
jmp_if_false L0  # if false, jump to L0, bool consumed from stack
# code here if true
label L0
# code here if false
```

### Function Calls and Returns (IR Extensions)

**Note:** The following instructions (`call`, `ret`, `retv`) are IR extensions beyond the base instruction set. They correspond to base instructions as follows:

#### `call <name>`
Calls a function. Arguments must be on stack left-to-right. After call, stack contains function result (for func) or is empty (for proc).

**Stack contract:**
- For `func`: `[arg1, arg2, ...] -> [result]`
- For `proc`: `[arg1, arg2, ...] -> []`

**Name format:** `func_<name>` (e.g., `func_add`)

**Correspondence to base instructions:** `call <name>` is equivalent to:
- Push return address onto return stack
- `jmp func_<name>`
- Label for return point
- (Function body executes)
- `jmp <return_address>` (handled by `ret`/`retv`)

**Example:**
```
push 5      # first argument
push 3      # second argument
call func_add # call add(5, 3), result on stack
```

#### `ret`
Return from procedure (proc). No return value.

**Stack contract:** `[] -> []` (stack must be empty)

**Correspondence to base instructions:** `ret` is equivalent to `jmp <return_address>` (jump back to caller).

#### `retv`
Return from function (func) with value. Consumes value from stack and returns it.

**Stack contract:** `[value] -> []`

**Correspondence to base instructions:** `retv` is equivalent to:
- Keep value on stack (or move to return register)
- `jmp <return_address>` (jump back to caller)

**Example:**
```
push 10
retv       # returns 10
```

## IR Extensions

This IR implementation uses some extensions beyond the base instruction set for convenience:

1. **`jmp_if_false`** - Macro instruction that expands to: pop bool, push false, eq, conditional jump logic
2. **`call`, `ret`, `retv`** - Function call/return instructions (correspond to jmp-based calling convention with return address stack)
3. **`load_index`, `store_index`** - Array access pseudo-instructions (expandable to base instructions)
4. **`load_field`, `store_field`** - Struct field access pseudo-instructions (expandable to base instructions)

These extensions are documented with their correspondence to base instructions (push/pop/jmp/operations).

## Stack Contract

### IR Generation Rules

1. **`gen_expr(expr)`** always leaves exactly 1 value on stack
2. **`gen_stmt(stmt)`** leaves no garbage on stack (stack is clean after execution)
3. **`jmp_if_false`** consumes bool from stack before jumping
4. **Expression statements** (ExprStmt) discard result with explicit `pop` instruction

### Stack Contract Examples

```minilang
int x = 10;  // gen_expr(10) -> [10], pop x -> []
int y = x;   // gen_expr(x) -> [10], pop y -> []
x + y;       // gen_expr(x+y) -> [20], pop -> []
```

## Usage

### Generate IR to stdout
```bash
python3 -m main.main examples/ok_01_basic.txt --ir
```

### Generate IR to file
```bash
python3 -m main.main examples/ok_01_basic.txt --ir --ir-output output.ir
```

## Examples

### Simple Assignment
**Source code:**
```minilang
int x = 10;
int y = 20;
int z = x + y;
```

**IR:**
```
push 10
pop x
push 20
pop y
push x
push y
add
pop z
```

**Step-by-step execution:**
```
push 10    → stack: [10]
pop x      → stack: [] (x = 10)
push 20    → stack: [20]
pop y      → stack: [] (y = 20)
push x     → stack: [10] (read x)
push y     → stack: [10, 20] (read y)
add        → stack: [30]
pop z      → stack: [] (z = 30)
```

### If Statement
**Source code:**
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
pop
jmp L1
label L0
push 0
pop
label L1
```

**Explanation:**
- `jmp_if_false L0` consumes bool from stack and jumps if false
- `pop` discards print result (used only for side effect)

### For Loop
**Source code:**
```minilang
for (int i = 0; i < 10; i = i + 1) {
    print(i);
}
```

**IR:**
```
push 0
pop i
label L0
push i
push 10
lt
jmp_if_false L1
push i
pop
push i
push 1
add
pop i
jmp L0
label L1
```

**Structure:** init → label start → cond → jmp_if_false end → body → step → jmp start → label end

### Array Access
**Source code:**
```minilang
int x = a[5];
a[5] = 10;
```

**IR:**
```
push a
push 5
load_index
pop x
push 10
push a
push 5
store_index
```

### Struct Field Access
**Source code:**
```minilang
struct Point { int x; int y; }
struct Point p;
int x = p.x;
p.y = 20;
```

**IR:**
```
push p
load_field x
pop x
push 20
push p
store_field y
```

### Function Call
**Source code:**
```minilang
func int add(int a, int b) {
    return a + b;
}
int result = add(5, 3);
```

**IR:**
```
label func_add
push a
push b
add
retv
push 5
push 3
call func_add
pop result
```

**Explanation:**
- Arguments pushed left-to-right: `push 5`, `push 3`
- `call func_add` calls function, result on stack
- `retv` returns value from function

### Procedure Call
**Source code:**
```minilang
proc printSum(int x, int y) {
    print(x + y);
}
printSum(10, 20);
```

**IR:**
```
label func_printSum
push x
push y
add
pop
ret
push 10
push 20
call func_printSum
pop
```

**Explanation:**
- `ret` returns from procedure without value
- After proc call, stack should be empty (pop removes garbage if any)

## Architecture

IR generation happens after semantic analysis:

```
Source code
  ↓
Lexer (tokens)
  ↓
Parser (AST)
  ↓
Semantic analyzer
  ↓
IR generator (IR code)
  ↓
IR output (stdout or file)
```

## API

### `generate_ir(program: Program) -> IRProgram`
Generates IR from AST program.

### `ir_to_string(program: IRProgram) -> str`
Converts IR instruction list to string for output.

## Fallback Return

If a function (func) doesn't have an explicit return in all execution paths, the generator adds a fallback return:
```
push 0
retv
```

This ensures the function always returns a value. In a real implementation, this should be checked by the semantic analyzer through control flow graph (CFG) analysis.
