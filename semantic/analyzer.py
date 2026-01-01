"""
Semantic analyzer: checks program correctness with full type checking.
"""
from __future__ import annotations
from typing import Dict, Set, Optional
from parser.ast import (
    Program, Stmt, Decl, Assign, If, For, FuncDef, Block,
    EnumDecl, StructDecl, FieldDecl,
    Expr, Ident, FieldAccessExpr, CallExpr, IndexExpr,
    BinOp, UnOp, Literal, Return, ExprStmt, PrintStmt, ReadStmt,
    NamedStructType, BaseType, ArrayType as ASTArrayType, TypeSpec,
    OpKind, Node
)
from semantic.errors import SemanticError
from semantic.scope import Scope, Symbol
from semantic.types import Type, INT, REAL, BOOL, VOID, ArrayType, StructType, TypeTag


class SemanticAnalyzer:
    """Semantic analyzer: two-pass analysis with full type checking."""
    
    def __init__(self):
        self.global_scope = Scope()
        # struct_fields: struct_name -> {field_name -> field_type}
        self.struct_fields: Dict[str, Dict[str, Type]] = {}
        self.current_scope: Scope = self.global_scope
        # Type table: maps node.id -> Type
        self.types_by_node_id: Dict[int, Type] = {}
        # Current function context (for return checking)
        self.current_func: Optional[FuncDef] = None
    
    def analyze(self, program: Program) -> None:
        """
        Main analysis method: two-pass analysis with type checking.
        
        PASS 1: Declaration gathering
        - Collect struct, enum, func declarations
        - Check for duplicates
        
        PASS 2: Usage checking and type inference
        - Check variable declarations and usage
        - Infer types for all expressions
        - Check type compatibility
        
        Args:
            program: AST program to analyze
            
        Raises:
            SemanticError: if semantic error found
        """
        # ========== PASS 1: Declaration gathering ==========
        for stmt in program.stmts:
            if isinstance(stmt, StructDecl):
                self._check_struct_decl(stmt)
            elif isinstance(stmt, EnumDecl):
                self._check_enum_decl(stmt)
            elif isinstance(stmt, FuncDef):
                self._declare_func(stmt)
        
        # Check for exactly one main function
        main_funcs = [s for s in program.stmts if isinstance(s, FuncDef) and s.name == "main"]
        if len(main_funcs) == 0:
            raise SemanticError("TYPE_ERROR: No 'main' function found", program)
        elif len(main_funcs) > 1:
            raise SemanticError("TYPE_ERROR: Multiple 'main' functions found", main_funcs[1])
        
        # ========== PASS 2: Usage checking and type inference ==========
        for stmt in program.stmts:
            self._check_stmt(stmt)
    
    # ========== Type conversion and inference ==========
    
    def _type_spec_to_type(self, type_spec: TypeSpec) -> Type:
        """Convert AST TypeSpec to semantic Type."""
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
        raise SemanticError(f"TYPE_ERROR: Unknown type specification", type_spec)
    
    def _get_node_type(self, node: Node) -> Optional[Type]:
        """Get inferred type for a node."""
        return self.types_by_node_id.get(node.id)
    
    def _set_node_type(self, node: Node, typ: Type) -> None:
        """Set inferred type for a node."""
        self.types_by_node_id[node.id] = typ
    
    def _check_type_compat(self, expected: Type, actual: Type, node: Node, context: str = "") -> None:
        """Check type compatibility (no implicit casts)."""
        if expected.tag != actual.tag:
            raise SemanticError(
                f"TYPE_ERROR: Type mismatch{context}: expected {self._type_to_str(expected)}, got {self._type_to_str(actual)}",
                node
            )
        if expected.tag == TypeTag.ARRAY:
            if not isinstance(expected, ArrayType) or not isinstance(actual, ArrayType):
                raise SemanticError(f"TYPE_ERROR: Array type mismatch{context}", node)
            if expected.dims != actual.dims:
                raise SemanticError(
                    f"TYPE_ERROR: Array dimension mismatch{context}: expected {expected.dims}, got {actual.dims}",
                    node
                )
            self._check_type_compat(expected.elem, actual.elem, node, context)
        elif expected.tag == TypeTag.STRUCT:
            if not isinstance(expected, StructType) or not isinstance(actual, StructType):
                raise SemanticError(f"TYPE_ERROR: Struct type mismatch{context}", node)
            if expected.name != actual.name:
                raise SemanticError(
                    f"TYPE_ERROR: Struct name mismatch{context}: expected '{expected.name}', got '{actual.name}'",
                    node
                )
    
    def _type_to_str(self, typ: Type) -> str:
        """Convert Type to string representation."""
        if typ.tag == TypeTag.INT:
            return "int"
        elif typ.tag == TypeTag.REAL:
            return "real"
        elif typ.tag == TypeTag.BOOL:
            return "bool"
        elif typ.tag == TypeTag.VOID:
            return "void"
        elif typ.tag == TypeTag.ARRAY:
            if isinstance(typ, ArrayType):
                base_str = self._type_to_str(typ.elem)
                return f"{base_str}[{typ.dims}]"
        elif typ.tag == TypeTag.STRUCT:
            if isinstance(typ, StructType):
                return f"struct {typ.name}"
        return "unknown"
    
    def _infer_type(self, expr: Expr) -> Type:
        """Infer type of expression and store it."""
        if expr.id in self.types_by_node_id:
            return self.types_by_node_id[expr.id]
        
        typ: Optional[Type] = None
        
        if isinstance(expr, Literal):
            if isinstance(expr.value, bool):
                typ = BOOL
            elif isinstance(expr.value, int):
                typ = INT
            elif isinstance(expr.value, float):
                typ = REAL
            elif isinstance(expr.value, str):
                # String literals not in spec, but handle gracefully
                raise SemanticError("TYPE_ERROR: String literals not supported", expr)
            else:
                raise SemanticError(f"TYPE_ERROR: Unknown literal type: {type(expr.value)}", expr)
        
        elif isinstance(expr, Ident):
            symbol = self.current_scope.lookup(expr.name)
            if symbol is None:
                raise SemanticError(f"TYPE_ERROR: Undeclared variable '{expr.name}'", expr)
            if symbol.kind != "var":
                raise SemanticError(f"TYPE_ERROR: '{expr.name}' is not a variable", expr)
            decl: Decl = symbol.data
            typ = self._type_spec_to_type(decl.type_spec)
        
        elif isinstance(expr, BinOp):
            left_type = self._infer_type(expr.left)
            right_type = self._infer_type(expr.right)
            
            if expr.op in (OpKind.ADD, OpKind.SUB, OpKind.MUL, OpKind.DIV):
                # Arithmetic: both operands must be numbers, same type
                if left_type.tag not in (TypeTag.INT, TypeTag.REAL):
                    raise SemanticError(
                        f"TYPE_ERROR: Arithmetic operand must be number, got {self._type_to_str(left_type)}",
                        expr.left
                    )
                if right_type.tag not in (TypeTag.INT, TypeTag.REAL):
                    raise SemanticError(
                        f"TYPE_ERROR: Arithmetic operand must be number, got {self._type_to_str(right_type)}",
                        expr.right
                    )
                if left_type.tag != right_type.tag:
                    raise SemanticError(
                        f"TYPE_ERROR: Arithmetic operands must have same type: {self._type_to_str(left_type)} and {self._type_to_str(right_type)}",
                        expr
                    )
                typ = left_type  # Result type is same as operands
            
            elif expr.op in (OpKind.LT, OpKind.LE, OpKind.GT, OpKind.GE, OpKind.EQ, OpKind.NEQ):
                # Comparison: both operands must be numbers, result is bool
                if left_type.tag not in (TypeTag.INT, TypeTag.REAL):
                    raise SemanticError(
                        f"TYPE_ERROR: Comparison operand must be number, got {self._type_to_str(left_type)}",
                        expr.left
                    )
                if right_type.tag not in (TypeTag.INT, TypeTag.REAL):
                    raise SemanticError(
                        f"TYPE_ERROR: Comparison operand must be number, got {self._type_to_str(right_type)}",
                        expr.right
                    )
                if left_type.tag != right_type.tag:
                    raise SemanticError(
                        f"TYPE_ERROR: Comparison operands must have same type: {self._type_to_str(left_type)} and {self._type_to_str(right_type)}",
                        expr
                    )
                typ = BOOL
            
            elif expr.op in (OpKind.AND, OpKind.OR):
                # Logic: both operands must be bool, result is bool
                if left_type.tag != TypeTag.BOOL:
                    raise SemanticError(
                        f"TYPE_ERROR: Logical operand must be bool, got {self._type_to_str(left_type)}",
                        expr.left
                    )
                if right_type.tag != TypeTag.BOOL:
                    raise SemanticError(
                        f"TYPE_ERROR: Logical operand must be bool, got {self._type_to_str(right_type)}",
                        expr.right
                    )
                typ = BOOL
        
        elif isinstance(expr, UnOp):
            expr_type = self._infer_type(expr.expr)
            
            if expr.op == OpKind.NEG:
                # Negation: operand must be number
                if expr_type.tag not in (TypeTag.INT, TypeTag.REAL):
                    raise SemanticError(
                        f"TYPE_ERROR: Negation operand must be number, got {self._type_to_str(expr_type)}",
                        expr.expr
                    )
                typ = expr_type
            
            elif expr.op == OpKind.NOT:
                # Not: operand must be bool
                if expr_type.tag != TypeTag.BOOL:
                    raise SemanticError(
                        f"TYPE_ERROR: Not operand must be bool, got {self._type_to_str(expr_type)}",
                        expr.expr
                    )
                typ = BOOL
        
        elif isinstance(expr, IndexExpr):
            base_type = self._infer_type(expr.base)
            index_type = self._infer_type(expr.index)
            
            # Index must be int
            if index_type.tag != TypeTag.INT:
                raise SemanticError(
                    f"TYPE_ERROR: Array index must be int, got {self._type_to_str(index_type)}",
                    expr.index
                )
            
            # Base must be array
            if base_type.tag != TypeTag.ARRAY:
                raise SemanticError(
                    f"TYPE_ERROR: Indexing non-array type {self._type_to_str(base_type)}",
                    expr.base
                )
            
            if not isinstance(base_type, ArrayType):
                raise SemanticError("TYPE_ERROR: Invalid array type", expr.base)
            
            # Result is element type, with one less dimension
            if base_type.dims == 1:
                typ = base_type.elem
            else:
                typ = ArrayType(elem=base_type.elem, dims=base_type.dims - 1)
        
        elif isinstance(expr, FieldAccessExpr):
            base_type = self._infer_type(expr.base)
            
            # Base must be struct
            if base_type.tag != TypeTag.STRUCT:
                raise SemanticError(
                    f"TYPE_ERROR: Field access on non-struct type {self._type_to_str(base_type)}",
                    expr.base
                )
            
            if not isinstance(base_type, StructType):
                raise SemanticError("TYPE_ERROR: Invalid struct type", expr.base)
            
            struct_name = base_type.name
            
            # Look up field type
            if struct_name not in self.struct_fields:
                raise SemanticError(
                    f"TYPE_ERROR: Struct '{struct_name}' not found",
                    expr
                )
            
            if expr.field not in self.struct_fields[struct_name]:
                raise SemanticError(
                    f"TYPE_ERROR: Field '{expr.field}' does not exist in struct '{struct_name}'",
                    expr
                )
            
            typ = self.struct_fields[struct_name][expr.field]
        
        elif isinstance(expr, CallExpr):
            symbol = self.global_scope.lookup(expr.callee)
            if symbol is None or symbol.kind != "func":
                raise SemanticError(f"TYPE_ERROR: Undeclared function '{expr.callee}'", expr)
            
            func: FuncDef = symbol.data
            
            # Check argument count
            if len(expr.args) != len(func.params):
                raise SemanticError(
                    f"TYPE_ERROR: Function '{expr.callee}' expects {len(func.params)} arguments, got {len(expr.args)}",
                    expr
                )
            
            # Check argument types
            for i, (arg_expr, param) in enumerate(zip(expr.args, func.params)):
                arg_type = self._infer_type(arg_expr)
                param_type = self._type_spec_to_type(param.type_spec)
                self._check_type_compat(param_type, arg_type, arg_expr, f" in argument {i+1} of '{expr.callee}'")
            
            # Check if proc is used in expression
            if func.is_proc:
                raise SemanticError(
                    f"TYPE_ERROR: Procedure '{expr.callee}' cannot be used in expression",
                    expr
                )
            
            # Return type
            if func.ret_type is None:
                raise SemanticError(f"TYPE_ERROR: Function '{expr.callee}' has no return type", func)
            typ = self._type_spec_to_type(func.ret_type)
        
        else:
            raise SemanticError(f"TYPE_ERROR: Cannot infer type for expression", expr)
        
        if typ is None:
            raise SemanticError(f"TYPE_ERROR: Failed to infer type", expr)
        
        self._set_node_type(expr, typ)
        return typ
    
    def _check_struct_decl(self, struct: StructDecl) -> None:
        """Check struct declaration: no duplicate fields, store field types."""
        field_types: Dict[str, Type] = {}
        
        for field in struct.fields:
            if field.name in field_types:
                raise SemanticError(
                    f"TYPE_ERROR: Duplicate field '{field.name}' in struct '{struct.name}'",
                    field
                )
            # Convert field type_spec to Type
            field_type = self._type_spec_to_type(field.type_spec)
            field_types[field.name] = field_type
        
        self.struct_fields[struct.name] = field_types
    
    def _check_enum_decl(self, enum: EnumDecl) -> None:
        """Check enum declaration: no duplicate members."""
        seen_members: Set[str] = set()
        
        for member in enum.members:
            if member in seen_members:
                raise SemanticError(
                    f"TYPE_ERROR: Duplicate member '{member}' in enum '{enum.name}'",
                    enum
                )
            seen_members.add(member)
    
    def _declare_func(self, func: FuncDef) -> None:
        """Declare function in global scope."""
        try:
            symbol = Symbol(name=func.name, kind="func", data=func)
            self.global_scope.define(symbol)
        except KeyError:
            raise SemanticError(
                f"TYPE_ERROR: Function '{func.name}' already declared",
                func
            )
    
    def _check_stmt(self, stmt: Stmt) -> None:
        """Check statement for semantic errors."""
        if isinstance(stmt, Decl):
            self._check_decl(stmt)
        elif isinstance(stmt, Assign):
            self._check_assign(stmt)
        elif isinstance(stmt, If):
            self._check_if(stmt)
        elif isinstance(stmt, For):
            self._check_for(stmt)
        elif isinstance(stmt, Block):
            self._check_block(stmt)
        elif isinstance(stmt, FuncDef):
            self._check_func_body(stmt)
        elif isinstance(stmt, Return):
            self._check_return(stmt)
        elif isinstance(stmt, ExprStmt):
            # Expression statement: infer type but don't require specific type
            if stmt.expr is not None:
                self._infer_type(stmt.expr)
        elif isinstance(stmt, PrintStmt):
            # Print: can print any type
            if stmt.expr is not None:
                self._infer_type(stmt.expr)
        elif isinstance(stmt, ReadStmt):
            # Read: variable must exist
            symbol = self.current_scope.lookup(stmt.name)
            if symbol is None:
                raise SemanticError(
                    f"TYPE_ERROR: Undeclared variable '{stmt.name}' in read statement",
                    stmt
                )
        elif isinstance(stmt, (EnumDecl, StructDecl)):
            pass  # Already checked
    
    def _check_decl(self, decl: Decl) -> None:
        """Check variable declaration."""
        # Check for redeclaration
        existing = self.current_scope.lookup(decl.name)
        if existing and existing.kind == "var":
            raise SemanticError(
                f"TYPE_ERROR: Variable '{decl.name}' already declared in this scope",
                decl
            )
        
        # Declare variable
        try:
            symbol = Symbol(name=decl.name, kind="var", data=decl)
            self.current_scope.define(symbol)
        except KeyError:
            pass
        
        # Check initializer type (if present)
        if decl.init is not None:
            init_type = self._infer_type(decl.init)
            decl_type = self._type_spec_to_type(decl.type_spec)
            self._check_type_compat(decl_type, init_type, decl.init, f" in initialization of '{decl.name}'")
    
    def _check_assign(self, assign: Assign) -> None:
        """Check assignment with type checking."""
        # Check lvalue and get its type
        lvalue_type = self._check_lvalue(assign.lvalue)
        # Check rhs expression and get its type
        rhs_type = self._infer_type(assign.expr)
        # Check type compatibility
        self._check_type_compat(lvalue_type, rhs_type, assign.expr, " in assignment")
    
    def _check_lvalue(self, expr: Expr) -> Type:
        """Check lvalue and return its type."""
        if isinstance(expr, Ident):
            self._check_ident(expr)
            return self._infer_type(expr)
        elif isinstance(expr, IndexExpr):
            # Check base is array, index is int
            base_type = self._infer_type(expr.base)
            index_type = self._infer_type(expr.index)
            
            if index_type.tag != TypeTag.INT:
                raise SemanticError(
                    f"TYPE_ERROR: Array index must be int, got {self._type_to_str(index_type)}",
                    expr.index
                )
            if base_type.tag != TypeTag.ARRAY:
                raise SemanticError(
                    f"TYPE_ERROR: Indexing non-array type {self._type_to_str(base_type)}",
                    expr.base
                )
            
            if not isinstance(base_type, ArrayType):
                raise SemanticError("TYPE_ERROR: Invalid array type", expr.base)
            
            # Return element type
            if base_type.dims == 1:
                return base_type.elem
            else:
                return ArrayType(elem=base_type.elem, dims=base_type.dims - 1)
        elif isinstance(expr, FieldAccessExpr):
            self._check_field_access(expr)
            # Field access type is inferred in _infer_type
            return self._infer_type(expr)
        else:
            raise SemanticError(
                f"TYPE_ERROR: Invalid lvalue in assignment",
                expr
            )
    
    def _check_expr(self, expr: Expr) -> None:
        """Check expression and infer its type."""
        # Infer type (this will check all subexpressions and types)
        self._infer_type(expr)
    
    def _check_ident(self, ident: Ident) -> None:
        """Check identifier usage."""
        symbol = self.current_scope.lookup(ident.name)
        if symbol is None:
            raise SemanticError(
                f"TYPE_ERROR: Undeclared variable '{ident.name}'",
                ident
            )
        if symbol.kind != "var":
            raise SemanticError(
                f"TYPE_ERROR: '{ident.name}' is not a variable",
                ident
            )
    
    def _check_field_access(self, field_expr: FieldAccessExpr) -> None:
        """Check field access: base must be struct, field must exist."""
        # Type checking is done in _infer_type for FieldAccessExpr
        self._infer_type(field_expr)
    
    def _check_call(self, call: CallExpr) -> None:
        """Check function call (type checking done in _infer_type)."""
        # Type checking is done in _infer_type for CallExpr
        self._infer_type(call)
    
    def _check_if(self, if_stmt: If) -> None:
        """Check if statement: condition must be bool."""
        cond_type = self._infer_type(if_stmt.cond)
        if cond_type.tag != TypeTag.BOOL:
            raise SemanticError(
                f"TYPE_ERROR: If condition must be bool, got {self._type_to_str(cond_type)}",
                if_stmt.cond
            )
        self._check_stmt(if_stmt.then_branch)
        if if_stmt.else_branch is not None:
            self._check_stmt(if_stmt.else_branch)
    
    def _check_for(self, for_stmt: For) -> None:
        """Check for loop: condition must be bool."""
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        
        try:
            self._check_stmt(for_stmt.init)
            if for_stmt.cond is not None:
                cond_type = self._infer_type(for_stmt.cond)
                if cond_type.tag != TypeTag.BOOL:
                    raise SemanticError(
                        f"TYPE_ERROR: For condition must be bool, got {self._type_to_str(cond_type)}",
                        for_stmt.cond
                    )
            if for_stmt.step is not None:
                self._check_assign(for_stmt.step)
            self._check_stmt(for_stmt.body)
        finally:
            self.current_scope = old_scope
    
    def _check_block(self, block: Block) -> None:
        """Check block (creates new scope)."""
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        
        try:
            for stmt in block.stmts:
                self._check_stmt(stmt)
        finally:
            self.current_scope = old_scope
    
    def _check_return(self, ret: Return) -> None:
        """Check return statement: must match function return type."""
        if self.current_func is None:
            raise SemanticError("TYPE_ERROR: Return statement outside function", ret)
        
        if self.current_func.is_proc:
            # Procedure: return must not have expression
            if ret.expr is not None:
                raise SemanticError(
                    f"TYPE_ERROR: Procedure '{self.current_func.name}' cannot return a value",
                    ret
                )
        else:
            # Function: return must have expression matching return type
            if ret.expr is None:
                raise SemanticError(
                    f"TYPE_ERROR: Function '{self.current_func.name}' must return a value",
                    ret
                )
            
            if self.current_func.ret_type is None:
                raise SemanticError(
                    f"TYPE_ERROR: Function '{self.current_func.name}' has no return type",
                    self.current_func
                )
            
            ret_expr_type = self._infer_type(ret.expr)
            expected_type = self._type_spec_to_type(self.current_func.ret_type)
            self._check_type_compat(expected_type, ret_expr_type, ret.expr, f" in return statement of '{self.current_func.name}'")
    
    def _check_func_body(self, func: FuncDef) -> None:
        """Check function body: return type checking."""
        old_scope = self.current_scope
        old_func = self.current_func
        self.current_scope = Scope(parent=self.global_scope)
        self.current_func = func
        
        try:
            # Declare parameters
            for param in func.params:
                try:
                    symbol = Symbol(name=param.name, kind="var", data=param)
                    self.current_scope.define(symbol)
                except KeyError:
                    raise SemanticError(
                        f"TYPE_ERROR: Duplicate parameter '{param.name}' in function '{func.name}'",
                        param
                    )
            
            # Check function body
            self._check_block(func.body)
            
            # Check return statements (done in _check_return)
        finally:
            self.current_scope = old_scope
            self.current_func = old_func
    
def analyze(program: Program) -> None:
    """
    Главная функция для запуска семантического анализа.
    
    Args:
        program: AST программы для анализа
        
    Raises:
        SemanticError: если найдена семантическая ошибка
    """
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)

