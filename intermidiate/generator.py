"""
IR generator: converts AST to stack machine instructions.
"""
from __future__ import annotations
from typing import List
from parser.ast import (
    Program, Stmt, Decl, Assign, If, For, FuncDef, Block,
    PrintStmt, ReadStmt, Return, ExprStmt,
    Expr, BinOp, UnOp, Literal, Ident, IndexExpr, FieldAccessExpr, CallExpr, CastExpr, OpKind
)
from intermidiate.ir import (
    IRProgram, IRInstruction, Push, Op, IROp, Label, Jmp, JmpIfFalse,
    Pop, StoreIndex, LoadIndex, StoreField, LoadField, Call, Ret, Retv
)


class IRGenerator:
    """Generates IR code from AST."""
    
    def __init__(self):
        self.label_counter = 0
        self.instructions: List[IRInstruction] = []
    
    def generate(self, program: Program) -> IRProgram:
        """Generate IR from AST program."""
        self.instructions = []
        self.label_counter = 0
        
        for stmt in program.stmts:
            self._gen_stmt(stmt)
        
        return self.instructions
    
    def _gen_stmt(self, stmt: Stmt) -> None:
        """Generate IR for statement. Stack contract: leaves stack empty."""
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
    
    def _gen_decl(self, decl: Decl) -> None:
        """Generate IR for variable declaration. Stack contract: leaves stack empty."""
        if decl.init is not None:
            self._gen_expr(decl.init)
            # Use pop <name> for variable writes (spec requirement)
            self.instructions.append(Pop(decl.name))
    
    def _gen_assign(self, assign: Assign) -> None:
        """Generate IR for assignment. Stack contract: leaves stack empty."""
        self._gen_expr(assign.expr)
        self._gen_lvalue_store(assign.lvalue)
    
    def _gen_if(self, if_stmt: If) -> None:
        """Generate IR for if statement. Stack contract: leaves stack empty."""
        self._gen_expr(if_stmt.cond)
        
        else_label = self._new_label()
        end_label = self._new_label()
        
        if if_stmt.else_branch is not None:
            self.instructions.append(JmpIfFalse(else_label))
        else:
            self.instructions.append(JmpIfFalse(end_label))
        
        self._gen_stmt(if_stmt.then_branch)
        
        if if_stmt.else_branch is not None:
            self.instructions.append(Jmp(end_label))
            self.instructions.append(Label(else_label))
            self._gen_stmt(if_stmt.else_branch)
        
        self.instructions.append(Label(end_label))
    
    def _gen_for(self, for_stmt: For) -> None:
        """Generate IR for for loop. Stack contract: leaves stack empty."""
        loop_label = self._new_label()
        end_label = self._new_label()
        
        self._gen_stmt(for_stmt.init)
        self.instructions.append(Label(loop_label))
        
        if for_stmt.cond is not None:
            self._gen_expr(for_stmt.cond)
            self.instructions.append(JmpIfFalse(end_label))
        
        self._gen_stmt(for_stmt.body)
        
        if for_stmt.step is not None:
            self._gen_assign(for_stmt.step)
        
        self.instructions.append(Jmp(loop_label))
        self.instructions.append(Label(end_label))
    
    def _gen_block(self, block: Block) -> None:
        """Generate IR for block."""
        for stmt in block.stmts:
            self._gen_stmt(stmt)
    
    def _gen_print(self, print_stmt: PrintStmt) -> None:
        """Generate IR for print statement. Stack contract: leaves stack empty."""
        self._gen_expr(print_stmt.expr)
        self.instructions.append(Pop())  # Discard after printing
    
    def _gen_read(self, read_stmt: ReadStmt) -> None:
        """Generate IR for read statement. Stack contract: leaves stack empty."""
        self.instructions.append(Push(0))  # Placeholder value
        self.instructions.append(Pop(read_stmt.name))  # Use pop <name> for variable write
    
    def _gen_return(self, return_stmt: Return) -> None:
        """Generate IR for return statement."""
        if return_stmt.expr is not None:
            self._gen_expr(return_stmt.expr)
            self.instructions.append(Retv())
        else:
            self.instructions.append(Ret())
    
    def _gen_expr_stmt(self, expr_stmt: ExprStmt) -> None:
        """Generate IR for expression statement. Stack contract: leaves stack empty."""
        self._gen_expr(expr_stmt.expr)
        self.instructions.append(Pop())  # Discard expression result
    
    def _gen_expr(self, expr: Expr) -> None:
        """Generate IR for expression. Stack contract: leaves exactly 1 value on stack."""
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
        elif isinstance(expr, CastExpr):
            self._gen_cast_expr(expr)
        else:
            raise ValueError(f"Unsupported expression type: {type(expr)}")
    
    def _gen_literal(self, literal: Literal) -> None:
        """Generate IR for literal."""
        self.instructions.append(Push(literal.value))
    
    def _gen_ident(self, ident: Ident) -> None:
        """Generate IR for identifier. Stack contract: leaves 1 value on stack."""
        # Use push <name> for variable reads (spec requirement)
        self.instructions.append(Push(ident.name))
    
    def _gen_binop(self, binop: BinOp) -> None:
        """Generate IR for binary operation."""
        self._gen_expr(binop.left)
        self._gen_expr(binop.right)
        
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
        
        if binop.op in op_map:
            self.instructions.append(Op(op_map[binop.op]))
        else:
            raise ValueError(f"Unsupported binary operation: {binop.op}")
    
    def _gen_unop(self, unop: UnOp) -> None:
        """Generate IR for unary operation."""
        self._gen_expr(unop.expr)
        
        if unop.op == OpKind.NOT:
            self.instructions.append(Op(IROp.NOT))
        elif unop.op == OpKind.NEG:
            self.instructions.append(Push(0))
            self.instructions.append(Op(IROp.SUB))
        else:
            raise ValueError(f"Unsupported unary operation: {unop.op}")
    
    def _gen_index_expr(self, index_expr: IndexExpr) -> None:
        """Generate IR for array index access. Stack contract: leaves 1 value on stack."""
        self._gen_expr(index_expr.base)
        self._gen_expr(index_expr.index)
        self.instructions.append(LoadIndex())
    
    def _gen_field_access_expr(self, field_expr: FieldAccessExpr) -> None:
        """Generate IR for struct field access. Stack contract: leaves 1 value on stack."""
        self._gen_expr(field_expr.base)
        self.instructions.append(LoadField(field_expr.field))
    
    def _gen_call_expr(self, call_expr: CallExpr) -> None:
        """Generate IR for function call. Stack contract: leaves 1 value for func, empty for proc."""
        for arg in call_expr.args:
            self._gen_expr(arg)
        
        func_name = f"func_{call_expr.callee}"
        self.instructions.append(Call(func_name))
    
    def _gen_cast_expr(self, cast_expr: CastExpr) -> None:
        """Generate IR for cast expression. Stack contract: leaves 1 value on stack."""
        # Generate the expression being cast
        self._gen_expr(cast_expr.expr)
        # Cast operations are handled at runtime - for now, just leave the value on stack
        # The cast itself doesn't need special IR instructions (type conversion happens at runtime)
        # If needed, we could add cast instructions, but for now we just pass through
    
    def _gen_lvalue_store(self, lvalue: Expr) -> None:
        """
        Generate IR for storing value to lvalue (left side of assignment).
        
        Stack contract: consumes value from stack, leaves stack empty.
        Assumes value is already on stack (after _gen_expr).
        """
        if isinstance(lvalue, Ident):
            # Store to variable: use pop <name> (spec requirement)
            # Stack: [value]
            self.instructions.append(Pop(lvalue.name))
            # Stack: []
        elif isinstance(lvalue, IndexExpr):
            # Store to array element
            # Stack: [value]
            # Need: [base, index, value] for store_index
            # Generate base and index
            self._gen_expr(lvalue.base)  # now: [value, base]
            self._gen_expr(lvalue.index)  # now: [value, base, index]
            # For spec compliance, we need to use only push/pop/operations
            # store_index is a pseudo-instruction, keep it for now
            self.instructions.append(StoreIndex())
            # Stack: []
        elif isinstance(lvalue, FieldAccessExpr):
            # Store to struct field
            # Stack: [value]
            # Generate base
            self._gen_expr(lvalue.base)  # now: [value, base]
            # store_field is a pseudo-instruction, keep it for now
            self.instructions.append(StoreField(lvalue.field))
            # Stack: []
        else:
            raise ValueError(f"Invalid lvalue type: {type(lvalue)}")
    
    def _gen_func(self, func: FuncDef) -> None:
        """Generate IR for function/procedure."""
        func_label = f"func_{func.name}"
        self.instructions.append(Label(func_label))
        self._gen_block(func.body)
        
        if not func.is_proc:
            has_return = self._has_return_in_block(func.body)
            if not has_return:
                self.instructions.append(Push(0))
                self.instructions.append(Retv())
        else:
            has_return = self._has_return_in_block(func.body)
            if not has_return:
                self.instructions.append(Ret())
    
    def _has_return_in_block(self, block: Block) -> bool:
        """Check if block contains return statement (simple check without CFG)."""
        for stmt in block.stmts:
            if isinstance(stmt, Return):
                return True
            elif isinstance(stmt, Block):
                if self._has_return_in_block(stmt):
                    return True
            elif isinstance(stmt, If):
                if isinstance(stmt.then_branch, Block) and self._has_return_in_block(stmt.then_branch):
                    if stmt.else_branch is None:
                        return False
                    if isinstance(stmt.else_branch, Block) and self._has_return_in_block(stmt.else_branch):
                        return True
        return False
    
    def _gen_return(self, return_stmt: Return) -> None:
        """
        Generate IR for return statement.
        
        Stack contract: for func - leaves value on stack, then retv.
        For proc - just ret (no value).
        """
        if return_stmt.expr is not None:
            # Function returns a value
            self._gen_expr(return_stmt.expr)  # leaves value on stack
            self.instructions.append(Retv())
        else:
            # Procedure returns without value
            self.instructions.append(Ret())
    
    def _new_label(self) -> str:
        """Generate unique label name."""
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label


def generate_ir(program: Program) -> IRProgram:
    """
    Main function for generating IR from AST.
    
    Args:
        program: AST program
        
    Returns:
        List of IR instructions
    """
    generator = IRGenerator()
    return generator.generate(program)

