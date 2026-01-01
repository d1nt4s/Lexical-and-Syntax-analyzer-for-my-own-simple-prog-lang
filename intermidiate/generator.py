"""
Генератор промежуточного кода (IR) из AST.

Преобразует AST в последовательность команд стек-машины.
"""
from __future__ import annotations
from typing import List
from parser.ast import (
    Program, Stmt, Decl, Assign, If, For, FuncDef, Block,
    PrintStmt, ReadStmt, Return, ExprStmt,
    Expr, BinOp, UnOp, Literal, Ident, OpKind
)
from intermidiate.ir import (
    IRProgram, IRInstruction, Push, Op, IROp, Label, Jmp, JmpIfFalse
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
        """Генерирует IR для объявления переменной."""
        # Если есть инициализатор, генерируем код для него
        if decl.init is not None:
            self._gen_expr(decl.init)
            # Результат выражения уже на стеке
            # В стек-машине переменные хранятся в памяти, но для простоты
            # мы просто оставляем значение на стеке
            # (в реальной реализации здесь был бы store)
        # Если инициализатора нет, переменная имеет значение по умолчанию
        # (для простоты не генерируем код)
    
    def _gen_assign(self, assign: Assign) -> None:
        """Генерирует IR для присваивания."""
        # Генерируем код для правой части (выражение)
        self._gen_expr(assign.expr)
        # Результат на стеке
        # В стек-машине здесь был бы store для сохранения в переменную
        # Для простоты оставляем значение на стеке
    
    def _gen_if(self, if_stmt: If) -> None:
        """Генерирует IR для if statement."""
        # Генерируем код для условия
        self._gen_expr(if_stmt.cond)
        
        # Генерируем уникальные метки
        else_label = self._new_label()
        end_label = self._new_label()
        
        # Если условие false, переходим к else или концу
        if if_stmt.else_branch is not None:
            self.instructions.append(JmpIfFalse(else_label))
        else:
            self.instructions.append(JmpIfFalse(end_label))
        
        # Генерируем код для then ветки
        self._gen_stmt(if_stmt.then_branch)
        
        # Если есть else, переходим к концу после then
        if if_stmt.else_branch is not None:
            self.instructions.append(Jmp(end_label))
            self.instructions.append(Label(else_label))
            # Генерируем код для else ветки
            self._gen_stmt(if_stmt.else_branch)
        
        # Метка конца if
        self.instructions.append(Label(end_label))
    
    def _gen_for(self, for_stmt: For) -> None:
        """Генерирует IR для for loop."""
        # Генерируем метки
        loop_label = self._new_label()
        end_label = self._new_label()
        
        # Генерируем код для init
        self._gen_stmt(for_stmt.init)
        
        # Метка начала цикла
        self.instructions.append(Label(loop_label))
        
        # Генерируем код для условия
        if for_stmt.cond is not None:
            self._gen_expr(for_stmt.cond)
            # Если условие false, выходим из цикла
            self.instructions.append(JmpIfFalse(end_label))
        
        # Генерируем код для тела цикла
        self._gen_stmt(for_stmt.body)
        
        # Генерируем код для step
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
        """Генерирует IR для print statement."""
        # Генерируем код для выражения
        self._gen_expr(print_stmt.expr)
        # Результат на стеке
        # В реальной реализации здесь был бы вызов функции print
    
    def _gen_read(self, read_stmt: ReadStmt) -> None:
        """Генерирует IR для read statement."""
        # В стек-машине здесь был бы вызов функции read
        # Для простоты генерируем push 0 (заглушка)
        self.instructions.append(Push(0))
    
    def _gen_return(self, return_stmt: Return) -> None:
        """Генерирует IR для return statement."""
        if return_stmt.expr is not None:
            # Генерируем код для выражения возврата
            self._gen_expr(return_stmt.expr)
            # Результат на стеке
        # В реальной реализации здесь был бы return
    
    def _gen_expr_stmt(self, expr_stmt: ExprStmt) -> None:
        """Генерирует IR для expression statement."""
        # Генерируем код для выражения
        self._gen_expr(expr_stmt.expr)
        # Результат на стеке (может быть проигнорирован)
    
    def _gen_func(self, func: FuncDef) -> None:
        """Генерирует IR для функции."""
        # Генерируем метку для функции
        func_label = self._new_label()
        self.instructions.append(Label(func_label))
        
        # Генерируем код для тела функции
        self._gen_block(func.body)
    
    def _gen_expr(self, expr: Expr) -> None:
        """Генерирует IR для выражения."""
        if isinstance(expr, Literal):
            self._gen_literal(expr)
        elif isinstance(expr, Ident):
            self._gen_ident(expr)
        elif isinstance(expr, BinOp):
            self._gen_binop(expr)
        elif isinstance(expr, UnOp):
            self._gen_unop(expr)
        # Для других типов выражений (IndexExpr, CallExpr, FieldAccessExpr)
        # пока не реализовано
    
    def _gen_literal(self, literal: Literal) -> None:
        """Генерирует IR для литерала."""
        self.instructions.append(Push(literal.value))
    
    def _gen_ident(self, ident: Ident) -> None:
        """Генерирует IR для идентификатора (переменной)."""
        # В стек-машине здесь был бы load для загрузки значения переменной
        # Для простоты генерируем push с именем переменной
        self.instructions.append(Push(ident.name))
    
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

