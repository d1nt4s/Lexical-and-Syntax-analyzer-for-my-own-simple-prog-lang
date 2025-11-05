## 1. Lexical structure (tokens)

### 1.1 Whitespace and comments
- Whitespace characters (space, tab, CR, LF) are ignored except inside string literals (strings are **not** part of v1).
- Single-line comments start with `//` and continue until the end of the line.  
  The lexer must skip them and not produce tokens for comment contents.

### 1.2 Identifiers
- Regex: `[A-Za-z_][A-Za-z0-9_]*`
- Keywords listed below are reserved and cannot be used as identifiers.

### 1.3 Keywords
```
int real bool true false
if else for
func proc return
read print
```

### 1.4 Literals
- **Integer:** `0` | `[1-9][0-9]*` → type `int`
- **Real:** `<int>.<int>` (both parts required) → type `real`
- **Boolean:** `true` | `false` → type `bool`

### 1.5 Delimiters and operators
- **Delimiters:** `; , ( ) { } [ ]`
- **Operators:** `+ - * /`, `== != < <= > >=`, `&& || !`, assignment `=`
- Semicolon `;` terminates simple statements and declarations.  
  No trailing `;` after a closing `}` of a block.

### 1.6 Token positions and lexer errors
- Each token carries the start position `(line, column)` of its lexeme (1-based).
- Unknown or invalid characters must raise a lexical error with position and message.

### 1.7 Lexeme categories (regex summary)
- **IDENT:** `[A-Za-z_][A-Za-z0-9_]*`
- **INT_LIT:** `[0-9]+`
- **REAL_LIT:** `[0-9]+\.[0-9]+` (минимальная форма; допустимы улучшения)
- **BOOL_LIT:** `true|false` (как ключевые слова)
- **Punctuators:** `\[`, `\]`, `\(`, `\)`, `\{`, `\}`, `,`, `;`
- **Operators:** `\+`, `-`, `\*`, `/`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `&&`, `\|\|`, `!`, `=`

---

## 2. Types

### 2.1 Base types
```
int | real | bool
```

### 2.2 Array types
- Arrays are denoted by `[]` suffixes after a base type.
- Multidimensional arrays are formed by repeating `[]`.
- Array types: `T[]`, `T[][]`, ... for any base `T ∈ {int, real, bool}`

Examples:
```
int[] a;        // array of int
real[][] m;     // 2D array of real
bool[][][] b;   // 3D array of bool
```

- Indexing: `a[i]`, multidimensional indexing: `m[i][j]`
- Array sizes are not specified in v1 (semantic/runtime checking is out of scope).

---

## 3. Declarations and signatures

### 3.1 Variable declaration
```
<type> <ident> [= <expr>] ;
```

Examples:
```
int x;
real y = 1.5;
bool flag = false;
int[] data;
```

### 3.2 Functions and procedures
- **Function:** returns a value:  
  `func <type> name(params) { ... }`
- **Procedure:** returns no value:  
  `proc name(params) { ... }`
- Parameters are comma-separated and may be base or array types.

Examples:
```
func int add(int a, int b) {
  return a + b;
}

proc printTwice(int x) {
  print(x);
  print(x);
}
```

---

## 4. Statements

1. Declaration (see §3.1)  
2. Assignment: `<lvalue> = <expr> ;` where `<lvalue>` is an identifier or array index `a[i]` / `m[i][j]`.  
3. Call: `<ident>(arglist?) ;` (e.g. `print(x);`, `read(x);`)  
4. Block: `{ <stmt>* }`  
5. Conditional:
   ```
   if (<expr>) <stmt>
   else <stmt>        // `else` is optional
   ```
6. Loop (simplified C-like `for`):
   ```
   for ( <init>? ; <cond>? ; <step>? ) <stmt>
   ```
   - `<init>` — declaration or assignment  
   - `<cond>` — boolean expression  
   - `<step>` — assignment or call  
   Each part may be empty.
7. Return:
   ```
   return <expr>? ;
   ```
   - In functions: expression optional  
   - In procedures: only `return;` is allowed

### 4.1 Input/Output
Modeled as regular calls:
```
read(x);    // read into variable x
print(x);   // print the value of expression x
```

---

## 5. Expressions

### 5.1 Grammar (simplified)
```
type       ::= base_type ('[' ']')*
base_type  ::= 'int' | 'real' | 'bool'

primary    ::= INT | REAL | TRUE | FALSE | IDENT | IDENT '(' args? ')' | '(' expr ')'
postfix    ::= primary ('[' expr ']')*
unary      ::= ('!' | '+' | '-') unary | postfix
mul        ::= unary (('*' | '/') unary)*
add        ::= mul   (('+' | '-') mul)*
rel        ::= add   (('<' | '<=' | '>' | '>=') add)?
eq         ::= rel   (('==' | '!=') rel)?
land       ::= eq    ('&&' eq)*
lor        ::= land  ('||' land)*
assign     ::= lval '=' assign | lor
lval       ::= IDENT | postfix  // where postfix may be IndexExpr
expr       ::= assign
args       ::= expr (',' expr)*
```

### 5.2 Operator precedence and associativity

| Level | Operators             | Associativity |
|:------|:----------------------|:--------------|
| 9     | call `()` index `[]`  | left          |
| 8     | unary `! + -`         | right         |
| 7     | `* /`                 | left          |
| 6     | `+ -`                 | left          |
| 5     | `< <= > >=`           | left          |
| 4     | `== !=`               | left          |
| 3     | `&&`                  | left          |
| 2     | `||`                  | left          |
| 1     | `=` (assignment)      | **right**     |

Notes:
- Indexing `[]` and call `()` are postfix with the highest precedence.
- Assignment is right-associative: `a = b = 1;` parses as `a = (b = 1);`.

---

## 6. Statement grammar (EBNF-like)
```
program    ::= (decl | func | proc | stmt)*

decl       ::= type IDENT ('=' expr)? ';'

func       ::= 'func' type IDENT '(' params? ')' block
proc       ::= 'proc' IDENT '(' params? ')' block
params     ::= param (',' param)*
param      ::= type IDENT

stmt       ::= block
             | ifstmt
             | forstmt
             | assign ';'
             | call ';'
             | decl
             | return ';'

block      ::= '{' stmt* '}'
ifstmt     ::= 'if' '(' expr ')' stmt ('else' stmt)?
forstmt    ::= 'for' '(' init? ';' expr? ';' step? ')' stmt
init       ::= decl | assign
step       ::= assign | call
assign     ::= lval '=' expr
call       ::= IDENT '(' args? ')'
return     ::= 'return' expr?

// expressions — see section 5

lval       ::= IDENT | IDENT ('[' expr ']')+

type       ::= basetype array_suffix*
basetype   ::= 'int' | 'real' | 'bool'
array_suffix ::= '[]'
```

---

## 7. Errors and positions
- **Lexical errors:** unknown characters, malformed numbers, etc.  
  Must include `(line, column)` and a short, deterministic message.
- **Syntax errors:** “expected X, found Y” at the point of failure.  
  Position should be at or near the problematic token.

Error messages must be concise and predictable for testing.

---

## 8. Minimal examples

### 8.1 Declarations and assignments
```
int x;
real y = 1.5;
bool ok = true;
int[] a;
x = 2 + 3 * 4;
```

### 8.2 If/else and for
```
int i = 0;
for (i = 0; i < 10; i = i + 1) {
  if (i < 5) { print(i); } else { /* no-op */ }
}
```

### 8.3 Function and procedure
```
func int add(int a, int b) {
  return a + b;
}

proc show(int x) {
  print(x);
}

int z = add(2, 3);
show(z);
```

---

## 9. Implementation notes (pipeline)
1. **Lexer:** recognize keywords, identifiers, numbers, booleans, operators, and delimiters; attach positions; skip whitespace and comments.  
2. **Parser:** implement recursive descent (and Pratt for expressions) following precedence table; handle statements (`stmt`), blocks, `if`, `for`, declarations, `func/proc`.  
3. **AST:** each node has `id`, `kind`, `value` (for leaves), `children`; supports `pretty()` and `to_json()`.  
4. **Errors:** stop parsing on first failure; report `(line, column)`; keep messages minimal and deterministic.

---

**Version:** v1 (frozen for Stages 2–4).  
Any extensions (strings, `%`, `break/continue`, sized arrays) are postponed until the core implementation is stable.
