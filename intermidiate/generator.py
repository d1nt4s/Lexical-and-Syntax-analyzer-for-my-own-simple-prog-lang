"""
Генератор промежуточного кода (IR) из AST.

Преобразует AST в последовательность команд стек-машины.
"""
from __future__ import annotations
from typing import List
from parser.ast import (
    Program, Stmt, Decl, Assign, If, For, FuncDef, Block,
    PrintStmt, ReadStmt, Return, ExprStmt,
    Expr, BinOp, UnOp, Literal, Ident, IndexExpr, FieldAccessExpr, CallExpr, OpKind
)
from intermidiate.ir import (
    IRProgram, IRInstruction, Push, Op, IROp, Label, Jmp, JmpIfFalse,
    Pop, Store, Load, StoreIndex, LoadIndex, StoreField, LoadField,
    Call, Ret, Retv
)


class IRGenerator:
    """Генератор промежуточного кода из AST."""
    
    def __init__(self):
        # Счетчик для генерации уникальных меток
        self.label_counter = 0
        # Список инструкций IR
        self.instructions: List[IRInstruction] = []
    
    def generate(self, program: Program) -> IRProgram:
        """
        Генерирует IR из AST программы.
        
        Args:
            program: AST программы
            
        Returns:
            Список инструкций IR
        """
        self.instructions = []
        self.label_counter = 0
        
        # Генерируем код для всех statements
        for stmt in program.stmts:
            self._gen_stmt(stmt)
        
        return self.instructions
    
    def _gen_stmt(self, stmt: Stmt) -> None:
        """Генерирует IR для statement."""
        if isinstance(stmt, Decl):
            self._gen_decl(stmt)
        elif isinstance(stmt, Assign):
            self._gen_assign(stmt)
        elif isinstance(stmt, If):
            self._gen_if(stmt)
        elif isinstance(stmt, For):
            self._gen_for(stmt)
        elif isinstance(stmt, Block):
            self._gen_block(stmt)
        elif isinstance(stmt, PrintStmt):
            self._gen_print(stmt)
        elif isinstance(stmt, ReadStmt):
            self._gen_read(stmt)
        elif isinstance(stmt, Return):
            self._gen_return(stmt)
        elif isinstance(stmt, ExprStmt):
            self._gen_expr_stmt(stmt)
        elif isinstance(stmt, FuncDef):
            self._gen_func(stmt)
        # EnumDecl и StructDecl не генерируют код
    
    def _gen_decl(self, decl: Decl) -> None:
        """
        Генерирует IR для объявления переменной.
        
        Контракт стека: не оставляет значений на стеке.
        """
        # Если есть инициализатор, генерируем код для него
        if decl.init is not None:
            self._gen_expr(decl.init)  # оставляет 1 значение на стеке
            # Сохраняем значение в переменную
            self.instructions.append(Store(decl.name))
            # Стек чистый
        # Если инициализатора нет, переменная имеет значение по умолчанию
        # (не генерируем код, переменная будет неинициализированной)
    
    def _gen_assign(self, assign: Assign) -> None:
        """
        Генерирует IR для присваивания.
        
        Контракт стека: не оставляет значений на стеке.
        """
        # Генерируем код для правой части (выражение)
        self._gen_expr(assign.expr)  # оставляет 1 значение на стеке
        
        # Генерируем код для левой части (lvalue) и сохраняем значение
        self._gen_lvalue_store(assign.lvalue)
        # Стек чистый
    
    def _gen_if(self, if_stmt: If) -> None:
        """
        Генерирует IR для if statement.
        
        Контракт стека: не оставляет значений на стеке.
        Структура: cond → jmp_if_false else → then → jmp end → label else → else → label end
        """
        # Генерируем код для условия (оставляет bool на стеке)
        self._gen_expr(if_stmt.cond)
        
        # Генерируем уникальные метки
        else_label = self._new_label()
        end_label = self._new_label()
        
        # jmp_if_false снимает bool со стека и переходит, если false
        if if_stmt.else_branch is not None:
            self.instructions.append(JmpIfFalse(else_label))
        else:
            self.instructions.append(JmpIfFalse(end_label))
        
        # Генерируем код для then ветки (не оставляет значений на стеке)
        self._gen_stmt(if_stmt.then_branch)
        
        # Если есть else, переходим к концу после then
        if if_stmt.else_branch is not None:
            self.instructions.append(Jmp(end_label))
            self.instructions.append(Label(else_label))
            # Генерируем код для else ветки (не оставляет значений на стеке)
            self._gen_stmt(if_stmt.else_branch)
        
        # Метка конца if
        self.instructions.append(Label(end_label))
    
    def _gen_for(self, for_stmt: For) -> None:
        """
        Генерирует IR для for loop.
        
        Контракт стека: не оставляет значений на стеке.
        Структура: init → label start → cond → jmp_if_false end → body → step → jmp start → label end
        """
        # Генерируем метки
        loop_label = self._new_label()
        end_label = self._new_label()
        
        # Генерируем код для init (не оставляет значений на стеке)
        self._gen_stmt(for_stmt.init)
        
        # Метка начала цикла
        self.instructions.append(Label(loop_label))
        
        # Генерируем код для условия
        if for_stmt.cond is not None:
            self._gen_expr(for_stmt.cond)  # оставляет bool на стеке
            # jmp_if_false снимает bool со стека и выходит из цикла, если false
            self.instructions.append(JmpIfFalse(end_label))
        
        # Генерируем код для тела цикла (не оставляет значений на стеке)
        self._gen_stmt(for_stmt.body)
        
        # Генерируем код для step (не оставляет значений на стеке)
        if for_stmt.step is not None:
            self._gen_assign(for_stmt.step)
        
        # Переходим к началу цикла
        self.instructions.append(Jmp(loop_label))
        
        # Метка конца цикла
        self.instructions.append(Label(end_label))
    
    def _gen_block(self, block: Block) -> None:
        """Генерирует IR для блока."""
        for stmt in block.stmts:
            self._gen_stmt(stmt)
    
    def _gen_print(self, print_stmt: PrintStmt) -> None:
        """
        Генерирует IR для print statement.
        
        Контракт стека: не оставляет значений на стеке.
        Значение печатается и удаляется.
        """
        # Генерируем код для выражения (оставляет 1 значение на стеке)
        self._gen_expr(print_stmt.expr)
        # В реальной реализации здесь был бы вызов функции print, которая берет значение со стека
        # Для простоты удаляем значение (в реальности print забирает его)
        self.instructions.append(Pop())
    
    def _gen_read(self, read_stmt: ReadStmt) -> None:
        """
        Генерирует IR для read statement.
        
        Контракт стека: не оставляет значений на стеке.
        В реальной реализации read читает значение и сохраняет в переменную.
        """
        # В стек-машине здесь был бы вызов функции read, которая читает значение
        # и сохраняет его в переменную read_stmt.name
        # Для простоты генерируем push 0 и сохраняем (заглушка)
        self.instructions.append(Push(0))
        self.instructions.append(Store(read_stmt.name))
    
    def _gen_return(self, return_stmt: Return) -> None:
        """Генерирует IR для return statement."""
        if return_stmt.expr is not None:
            # Генерируем код для выражения возврата
            self._gen_expr(return_stmt.expr)
            # Результат на стеке
        # В реальной реализации здесь был бы return
    
    def _gen_expr_stmt(self, expr_stmt: ExprStmt) -> None:
        """
        Генерирует IR для expression statement.
        
        Контракт стека: не оставляет значений на стеке.
        Выражение вычисляется ради побочного эффекта, результат удаляется.
        """
        # Генерируем код для выражения (оставляет 1 значение на стеке)
        self._gen_expr(expr_stmt.expr)
        # Удаляем результат со стека (выражение использовано только ради эффекта)
        self.instructions.append(Pop())
    
    def _gen_func(self, func: FuncDef) -> None:
        """Генерирует IR для функции."""
        # Генерируем метку для функции
        func_label = self._new_label()
        self.instructions.append(Label(func_label))
        
        # Генерируем код для тела функции
        self._gen_block(func.body)
    
    def _gen_expr(self, expr: Expr) -> None:
        """
        Генерирует IR для выражения.
        
        Контракт стека: всегда оставляет ровно 1 значение на стеке.
        """
        if isinstance(expr, Literal):
            self._gen_literal(expr)
        elif isinstance(expr, Ident):
            self._gen_ident(expr)
        elif isinstance(expr, BinOp):
            self._gen_binop(expr)
        elif isinstance(expr, UnOp):
            self._gen_unop(expr)
        elif isinstance(expr, IndexExpr):
            self._gen_index_expr(expr)
        elif isinstance(expr, FieldAccessExpr):
            self._gen_field_access_expr(expr)
        elif isinstance(expr, CallExpr):
            self._gen_call_expr(expr)
        else:
            raise ValueError(f"Unsupported expression type: {type(expr)}")
    
    def _gen_literal(self, literal: Literal) -> None:
        """Генерирует IR для литерала."""
        self.instructions.append(Push(literal.value))
    
    def _gen_ident(self, ident: Ident) -> None:
        """
        Генерирует IR для идентификатора (переменной).
        
        Контракт стека: оставляет 1 значение на стеке (значение переменной).
        """
        # Загружаем значение переменной на стек
        self.instructions.append(Load(ident.name))
    
    def _gen_binop(self, binop: BinOp) -> None:
        """Генерирует IR для бинарной операции."""
        # Генерируем код для левого операнда
        self._gen_expr(binop.left)
        # Генерируем код для правого операнда
        self._gen_expr(binop.right)
        
        # Маппинг OpKind -> IROp
        op_map = {
            OpKind.ADD: IROp.ADD,
            OpKind.SUB: IROp.SUB,
            OpKind.MUL: IROp.MUL,
            OpKind.DIV: IROp.DIV,
            OpKind.LT: IROp.LT,
            OpKind.LE: IROp.LE,
            OpKind.GT: IROp.GT,
            OpKind.GE: IROp.GE,
            OpKind.EQ: IROp.EQ,
            OpKind.NEQ: IROp.NEQ,
            OpKind.AND: IROp.AND,
            OpKind.OR: IROp.OR,
        }
        
        # Генерируем операцию
        if binop.op in op_map:
            self.instructions.append(Op(op_map[binop.op]))
        else:
            raise ValueError(f"Unsupported binary operation: {binop.op}")
    
    def _gen_unop(self, unop: UnOp) -> None:
        """Генерирует IR для унарной операции."""
        # Генерируем код для операнда
        self._gen_expr(unop.expr)
        
        # Маппинг OpKind -> IROp
        if unop.op == OpKind.NOT:
            self.instructions.append(Op(IROp.NOT))
        elif unop.op == OpKind.NEG:
            # Отрицание: push 0, затем sub
            self.instructions.append(Push(0))
            self.instructions.append(Op(IROp.SUB))
        else:
            raise ValueError(f"Unsupported unary operation: {unop.op}")
    
    def _gen_index_expr(self, index_expr: IndexExpr) -> None:
        """
        Генерирует IR для доступа к элементу массива (выражение).
        
        Контракт стека: оставляет 1 значение на стеке (значение элемента).
        Порядок: base, index -> value
        """
        # Генерируем код для base (массив)
        self._gen_expr(index_expr.base)  # оставляет base на стеке
        # Генерируем код для index
        self._gen_expr(index_expr.index)  # оставляет [base, index] на стеке
        # Загружаем элемент массива
        self.instructions.append(LoadIndex())
        # Стек: [value]
    
    def _gen_field_access_expr(self, field_expr: FieldAccessExpr) -> None:
        """
        Генерирует IR для доступа к полю структуры (выражение).
        
        Контракт стека: оставляет 1 значение на стеке (значение поля).
        """
        # Генерируем код для base (структура)
        self._gen_expr(field_expr.base)  # оставляет base на стеке
        # Загружаем поле структуры
        self.instructions.append(LoadField(field_expr.field))
        # Стек: [value]
    
    def _gen_call_expr(self, call_expr: CallExpr) -> None:
        """
        Генерирует IR для вызова функции (выражение).
        
        Контракт стека: 
        - Для func: оставляет 1 значение на стеке (результат функции)
        - Для proc: не оставляет значений (но это должно проверяться семантикой)
        
        Аргументы кладутся на стек слева-направо.
        """
        # Генерируем код для аргументов слева-направо
        for arg in call_expr.args:
            self._gen_expr(arg)  # каждый аргумент оставляет значение на стеке
        
        # Вызываем функцию (формат: func_<name>)
        func_name = f"func_{call_expr.callee}"
        self.instructions.append(Call(func_name))
        # После вызова:
        # - Для func: на стеке результат функции (1 значение)
        # - Для proc: стек пустой (но это должно проверяться семантикой)
    
    def _gen_lvalue_store(self, lvalue: Expr) -> None:
        """
        Генерирует IR для сохранения значения в lvalue (левая часть присваивания).
        
        Контракт стека: берет значение со стека и сохраняет, стек становится пустым.
        Предполагается, что значение уже на стеке (после _gen_expr).
        """
        if isinstance(lvalue, Ident):
            # Сохраняем в переменную
            # На стеке: [value]
            self.instructions.append(Store(lvalue.name))
            # Стек: []
        elif isinstance(lvalue, IndexExpr):
            # Сохраняем в элемент массива
            # На стеке: [value]
            # Нужно: [base, index, value] для store_index
            # Генерируем base и index
            self._gen_expr(lvalue.base)  # теперь: [value, base]
            self._gen_expr(lvalue.index)  # теперь: [value, base, index]
            # Порядок для store_index: base, index, value (снизу вверх)
            # Но у нас value сверху, нужно переставить
            # В стек-машине обычно используется порядок: base, index, value
            # Используем соглашение: value, base, index -> store_index (value сверху, читается снизу)
            self.instructions.append(StoreIndex())
            # Стек: []
        elif isinstance(lvalue, FieldAccessExpr):
            # Сохраняем в поле структуры
            # На стеке: [value]
            # Генерируем base
            self._gen_expr(lvalue.base)  # теперь: [value, base]
            # Сохраняем в поле (порядок: value, base -> store_field)
            self.instructions.append(StoreField(lvalue.field))
            # Стек: []
        else:
            raise ValueError(f"Invalid lvalue type: {type(lvalue)}")
    
    def _gen_func(self, func: FuncDef) -> None:
        """
        Генерирует IR для функции.
        
        Контракт стека: функция должна оставить стек в чистом состоянии.
        Для func: должен быть return со значением.
        Для proc: return без значения или неявный ret в конце.
        """
        # Генерируем метку для функции (формат: func_<name>)
        func_label = f"func_{func.name}"
        self.instructions.append(Label(func_label))
        
        # Генерируем код для тела функции
        self._gen_block(func.body)
        
        # Если это функция (func), а не процедура (proc), и нет явного return,
        # добавляем fallback return (push 0; retv)
        # В реальной реализации это должно проверяться семантикой
        if not func.is_proc:
            # Проверяем, есть ли return в теле (простая проверка)
            has_return = self._has_return_in_block(func.body)
            if not has_return:
                # Добавляем fallback return
                self.instructions.append(Push(0))
                self.instructions.append(Retv())
        else:
            # Для процедуры, если нет return, добавляем неявный ret
            has_return = self._has_return_in_block(func.body)
            if not has_return:
                self.instructions.append(Ret())
    
    def _has_return_in_block(self, block: Block) -> bool:
        """Проверяет, есть ли return в блоке (простая проверка без CFG)."""
        for stmt in block.stmts:
            if isinstance(stmt, Return):
                return True
            elif isinstance(stmt, Block):
                if self._has_return_in_block(stmt):
                    return True
            elif isinstance(stmt, If):
                # Для if проверяем обе ветки (упрощенно)
                if isinstance(stmt.then_branch, Block) and self._has_return_in_block(stmt.then_branch):
                    if stmt.else_branch is None:
                        return False  # не все пути ведут к return
                    if isinstance(stmt.else_branch, Block) and self._has_return_in_block(stmt.else_branch):
                        return True
        return False
    
    def _gen_return(self, return_stmt: Return) -> None:
        """
        Генерирует IR для return statement.
        
        Контракт стека: для func - оставляет значение на стеке, затем retv.
        Для proc - просто ret (без значения).
        """
        if return_stmt.expr is not None:
            # Функция возвращает значение
            self._gen_expr(return_stmt.expr)  # оставляет значение на стеке
            self.instructions.append(Retv())
        else:
            # Процедура возвращается без значения
            self.instructions.append(Ret())
    
    def _new_label(self) -> str:
        """Генерирует уникальное имя метки."""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label


def generate_ir(program: Program) -> IRProgram:
    """
    Главная функция для генерации IR из AST.
    
    Args:
        program: AST программы
        
    Returns:
        Список инструкций IR
    """
    generator = IRGenerator()
    return generator.generate(program)

