"""
Семантический анализатор для проверки правильности программы.

Проверяет:
- Дублирование имен (поля в struct, члены в enum, переменные)
- Использование несуществующих идентификаторов (переменные, функции, поля)
"""
from __future__ import annotations
from typing import Dict, Set, Optional
from parser.ast import (
    Program, Stmt, Decl, Assign, If, For, FuncDef, Block,
    EnumDecl, StructDecl, FieldDecl,
    Expr, Ident, FieldAccessExpr, CallExpr, IndexExpr,
    NamedStructType
)
from semantic.errors import SemanticError
from semantic.scope import Scope, Symbol


class SemanticAnalyzer:
    """Семантический анализатор, который проходит по AST и проверяет правила языка."""
    
    def __init__(self):
        # Глобальная область видимости для переменных, функций, типов
        self.global_scope = Scope()
        # Таблица структур: имя struct -> множество имен полей
        self.struct_fields: Dict[str, Set[str]] = {}
        # Текущая область видимости (для вложенных блоков)
        self.current_scope: Scope = self.global_scope
    
    def analyze(self, program: Program) -> None:
        """
        Главный метод анализа - запускает проверку всей программы.
        
        Args:
            program: AST программы для анализа
            
        Raises:
            SemanticError: если найдена семантическая ошибка
        """
        # Сначала собираем все объявления (struct, enum, func) в глобальной области
        for stmt in program.stmts:
            if isinstance(stmt, StructDecl):
                self._check_struct_decl(stmt)
            elif isinstance(stmt, EnumDecl):
                self._check_enum_decl(stmt)
            elif isinstance(stmt, FuncDef):
                self._declare_func(stmt)
        
        # Теперь проверяем все statements (включая использование переменных)
        for stmt in program.stmts:
            self._check_stmt(stmt)
    
    def _check_struct_decl(self, struct: StructDecl) -> None:
        """
        Проверяет объявление struct на дублирование полей.
        
        Args:
            struct: объявление структуры
            
        Raises:
            SemanticError: если найдено дублирование поля
        """
        seen_fields: Set[str] = set()
        
        for field in struct.fields:
            # Проверяем, не было ли уже поля с таким именем
            if field.name in seen_fields:
                # Формируем сообщение об ошибке с позицией
                pos = self._get_position(field)
                raise SemanticError(
                    f"Duplicate field '{field.name}' in struct '{struct.name}'",
                    field
                )
            
            seen_fields.add(field.name)
        
        # Сохраняем информацию о полях структуры для дальнейшей проверки
        self.struct_fields[struct.name] = seen_fields
    
    def _check_enum_decl(self, enum: EnumDecl) -> None:
        """
        Проверяет объявление enum на дублирование членов.
        
        Args:
            enum: объявление перечисления
            
        Raises:
            SemanticError: если найден дублирующийся член
        """
        seen_members: Set[str] = set()
        
        for member in enum.members:
            # Проверяем, не было ли уже члена с таким именем
            if member in seen_members:
                # Для enum members у нас нет прямого доступа к узлу,
                # но можем использовать span самого enum
                pos = self._get_position(enum)
                raise SemanticError(
                    f"Duplicate member '{member}' in enum '{enum.name}'",
                    enum
                )
            
            seen_members.add(member)
    
    def _declare_func(self, func: FuncDef) -> None:
        """
        Объявляет функцию в глобальной области видимости.
        
        Args:
            func: определение функции
        """
        try:
            symbol = Symbol(name=func.name, kind="func", data=func)
            self.global_scope.define(symbol)
        except KeyError:
            # Функция уже объявлена - это ошибка
            pos = self._get_position(func)
            raise SemanticError(
                f"Function '{func.name}' already declared",
                func
            )
    
    def _check_stmt(self, stmt: Stmt) -> None:
        """
        Проверяет statement на семантические ошибки.
        
        Args:
            stmt: statement для проверки
        """
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
            # Функции уже обработаны в _declare_func, но нужно проверить тело
            self._check_func_body(stmt)
        # EnumDecl и StructDecl уже проверены отдельно
        elif isinstance(stmt, (EnumDecl, StructDecl)):
            pass  # Уже проверено
    
    def _check_decl(self, decl: Decl) -> None:
        """
        Проверяет объявление переменной.
        
        Args:
            decl: объявление переменной
        """
        # Проверяем, не объявлена ли уже переменная в текущей области
        existing = self.current_scope.lookup(decl.name)
        if existing and existing.kind == "var":
            pos = self._get_position(decl)
            raise SemanticError(
                f"Variable '{decl.name}' already declared in this scope",
                decl
            )
        
        # Объявляем переменную
        try:
            symbol = Symbol(name=decl.name, kind="var", data=decl)
            self.current_scope.define(symbol)
        except KeyError:
            # Это не должно произойти, т.к. мы уже проверили выше
            pass
        
        # Проверяем инициализатор (если есть)
        if decl.init is not None:
            self._check_expr(decl.init)
    
    def _check_assign(self, assign: Assign) -> None:
        """
        Проверяет присваивание.
        
        Args:
            assign: присваивание
        """
        # Проверяем левую часть (lvalue)
        self._check_lvalue(assign.lvalue)
        # Проверяем правую часть (выражение)
        self._check_expr(assign.expr)
    
    def _check_lvalue(self, expr: Expr) -> None:
        """
        Проверяет левую часть присваивания (lvalue).
        
        Args:
            expr: выражение, которое должно быть lvalue
        """
        if isinstance(expr, Ident):
            # Проверяем, что переменная объявлена
            self._check_ident(expr)
        elif isinstance(expr, IndexExpr):
            # Проверяем базовое выражение и индекс
            self._check_lvalue(expr.base)
            self._check_expr(expr.index)
        elif isinstance(expr, FieldAccessExpr):
            # Проверяем доступ к полю
            self._check_field_access(expr)
        else:
            # Это не должно произойти при правильном парсинге
            pos = self._get_position(expr)
            raise SemanticError(
                f"Invalid lvalue in assignment",
                expr
            )
    
    def _check_expr(self, expr: Expr) -> None:
        """
        Проверяет выражение на семантические ошибки.
        
        Args:
            expr: выражение для проверки
        """
        if isinstance(expr, Ident):
            self._check_ident(expr)
        elif isinstance(expr, FieldAccessExpr):
            self._check_field_access(expr)
        elif isinstance(expr, CallExpr):
            self._check_call(expr)
        elif isinstance(expr, IndexExpr):
            # Проверяем базовое выражение и индекс
            self._check_expr(expr.base)
            self._check_expr(expr.index)
        # Для остальных типов выражений (BinOp, UnOp, Literal) рекурсивно проверяем подвыражения
        elif hasattr(expr, 'left') and hasattr(expr, 'right'):
            # BinOp
            self._check_expr(expr.left)
            self._check_expr(expr.right)
        elif hasattr(expr, 'expr'):
            # UnOp
            self._check_expr(expr.expr)
        # Literal не требует проверки
    
    def _check_ident(self, ident: Ident) -> None:
        """
        Проверяет использование идентификатора (переменной).
        
        Args:
            ident: идентификатор
            
        Raises:
            SemanticError: если переменная не объявлена
        """
        symbol = self.current_scope.lookup(ident.name)
        if symbol is None:
            pos = self._get_position(ident)
            raise SemanticError(
                f"Undeclared variable '{ident.name}'",
                ident
            )
    
    def _check_field_access(self, field_expr: FieldAccessExpr) -> None:
        """
        Проверяет доступ к полю структуры.
        
        Args:
            field_expr: выражение доступа к полю
            
        Raises:
            SemanticError: если поле не существует
        """
        # Сначала проверяем базовое выражение
        self._check_expr(field_expr.base)
        
        # Определяем тип базового выражения
        # Для упрощения, проверяем только случаи, когда base - это Ident с типом struct
        if isinstance(field_expr.base, Ident):
            # Нужно найти тип переменной
            symbol = self.current_scope.lookup(field_expr.base.name)
            if symbol and symbol.kind == "var":
                decl: Decl = symbol.data
                if isinstance(decl.type_spec, NamedStructType):
                    struct_name = decl.type_spec.name
                    # Проверяем, существует ли поле в этой структуре
                    if struct_name in self.struct_fields:
                        if field_expr.field not in self.struct_fields[struct_name]:
                            pos = self._get_position(field_expr)
                            raise SemanticError(
                                f"Field '{field_expr.field}' does not exist in struct '{struct_name}'",
                                field_expr
                            )
                    else:
                        # Структура не найдена (не была объявлена)
                        pos = self._get_position(field_expr)
                        raise SemanticError(
                            f"Struct '{struct_name}' not found",
                            field_expr
                        )
        # Для более сложных случаев (например, arr[i].field) пока пропускаем
    
    def _check_call(self, call: CallExpr) -> None:
        """
        Проверяет вызов функции.
        
        Args:
            call: вызов функции
            
        Raises:
            SemanticError: если функция не объявлена
        """
        symbol = self.global_scope.lookup(call.callee)
        if symbol is None or symbol.kind != "func":
            pos = self._get_position(call)
            raise SemanticError(
                f"Undeclared function '{call.callee}'",
                call
            )
        
        # Проверяем аргументы
        for arg in call.args:
            self._check_expr(arg)
    
    def _check_if(self, if_stmt: If) -> None:
        """Проверяет if statement."""
        self._check_expr(if_stmt.cond)
        self._check_stmt(if_stmt.then_branch)
        if if_stmt.else_branch is not None:
            self._check_stmt(if_stmt.else_branch)
    
    def _check_for(self, for_stmt: For) -> None:
        """Проверяет for loop."""
        # Создаем новую область видимости для for loop
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        
        try:
            self._check_stmt(for_stmt.init)
            if for_stmt.cond is not None:
                self._check_expr(for_stmt.cond)
            if for_stmt.step is not None:
                self._check_assign(for_stmt.step)
            self._check_stmt(for_stmt.body)
        finally:
            # Восстанавливаем предыдущую область видимости
            self.current_scope = old_scope
    
    def _check_block(self, block: Block) -> None:
        """Проверяет блок (создает новую область видимости)."""
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        
        try:
            for stmt in block.stmts:
                self._check_stmt(stmt)
        finally:
            self.current_scope = old_scope
    
    def _check_func_body(self, func: FuncDef) -> None:
        """Проверяет тело функции (создает новую область видимости для параметров)."""
        old_scope = self.current_scope
        self.current_scope = Scope(parent=self.global_scope)
        
        try:
            # Объявляем параметры функции
            for param in func.params:
                try:
                    symbol = Symbol(name=param.name, kind="var", data=param)
                    self.current_scope.define(symbol)
                except KeyError:
                    pos = self._get_position(param)
                    raise SemanticError(
                        f"Duplicate parameter '{param.name}' in function '{func.name}'",
                        param
                    )
            
            # Проверяем тело функции
            self._check_block(func.body)
        finally:
            self.current_scope = old_scope
    
    def _get_position(self, node) -> str:
        """
        Получает строковое представление позиции узла из его span.
        
        Args:
            node: узел AST
            
        Returns:
            Строка в формате "line:col" или пустая строка, если span нет
        """
        if hasattr(node, 'span') and node.span is not None:
            return f"{node.span.start.line}:{node.span.start.col}"
        return ""


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

