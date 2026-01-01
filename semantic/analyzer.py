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
    """
    Семантический анализатор, который проходит по AST и проверяет правила языка.
    
    Как работает:
    1. Два прохода по AST:
       - Первый проход: собираем все объявления (struct, enum, функции)
       - Второй проход: проверяем использование (переменные, функции, поля)
    
    2. Использует области видимости (scopes) для отслеживания переменных:
       - global_scope: глобальная область (функции, глобальные переменные)
       - current_scope: текущая область (может быть вложенной для блоков, функций)
    
    3. Хранит информацию о структурах:
       - struct_fields: словарь "имя структуры" -> "множество имен полей"
    """
    
    def __init__(self):
        # Глобальная область видимости - здесь хранятся функции и глобальные переменные
        # Функции всегда ищутся в глобальной области
        self.global_scope = Scope()
        
        # Таблица структур: имя struct -> множество имен полей
        # Пример: {"Point": {"x", "y"}} означает, что struct Point имеет поля x и y
        # Используется для проверки существования полей при доступе (например, p.x)
        self.struct_fields: Dict[str, Set[str]] = {}
        
        # Текущая область видимости - может меняться при входе в блоки/функции
        # Изначально равна глобальной области
        self.current_scope: Scope = self.global_scope
    
    def analyze(self, program: Program) -> None:
        """
        Главный метод анализа - запускает проверку всей программы.
        
        Алгоритм работы (ВАЖНО - два прохода!):
        
        ПРОХОД 1: Сбор объявлений
        - Проходим по всем statements и собираем информацию о:
          * Структурах (struct) - проверяем дублирование полей, сохраняем поля
          * Перечислениях (enum) - проверяем дублирование членов
          * Функциях (func/proc) - добавляем в таблицу символов
        
        Зачем нужен первый проход?
        - Чтобы знать, какие функции/структуры существуют, когда будем проверять их использование
        - Пример: func int add() {...} объявлена позже, но используется раньше
        
        ПРОХОД 2: Проверка использования
        - Проходим по всем statements и проверяем:
          * Объявления переменных (нет ли дублирования)
          * Использование переменных (объявлены ли они)
          * Доступ к полям структур (существуют ли поля)
          * Вызовы функций (объявлены ли функции)
        
        Args:
            program: AST программы для анализа
            
        Raises:
            SemanticError: если найдена семантическая ошибка
        """
        # ========== ПРОХОД 1: Сбор объявлений ==========
        # Собираем все объявления (struct, enum, func) в глобальной области
        for stmt in program.stmts:
            if isinstance(stmt, StructDecl):
                # Проверяем дублирование полей и сохраняем информацию о полях
                self._check_struct_decl(stmt)
            elif isinstance(stmt, EnumDecl):
                # Проверяем дублирование членов enum
                self._check_enum_decl(stmt)
            elif isinstance(stmt, FuncDef):
                # Добавляем функцию в глобальную таблицу символов
                self._declare_func(stmt)
        
        # ========== ПРОХОД 2: Проверка использования ==========
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
                # Позиция ошибки будет извлечена из field.span в format_error()
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
                # Позиция ошибки будет извлечена из enum.span в format_error()
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
            # Позиция ошибки будет извлечена из func.span в format_error()
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
            # Позиция ошибки будет извлечена из decl.span в format_error()
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
            # Позиция ошибки будет извлечена из expr.span в format_error()
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
        
        Как работает:
        1. Ищем переменную в текущей области видимости (current_scope)
        2. Если не найдена - ищем в родительской области (scope.lookup делает это автоматически)
        3. Если не найдена нигде - ошибка
        
        Пример:
        ```minilang
        int x = 10;        // ← объявлена в глобальной области
        {
            int y = 20;    // ← объявлена в локальной области
            int z = x;     // ← x найдена в родительской области ✓
        }
        int w = y;         // ← y не найдена (она в дочерней области) ✗
        ```
        
        Args:
            ident: идентификатор
            
        Raises:
            SemanticError: если переменная не объявлена
        """
        # Ищем переменную в текущей области видимости (и во всех родительских)
        # scope.lookup автоматически ищет по цепочке: current -> parent -> parent.parent -> ...
        symbol = self.current_scope.lookup(ident.name)
        
        if symbol is None:
            # Переменная не найдена ни в одной области видимости - это ошибка
            # Позиция ошибки будет извлечена из ident.span в format_error()
            raise SemanticError(
                f"Undeclared variable '{ident.name}'",
                ident
            )
    
    def _check_field_access(self, field_expr: FieldAccessExpr) -> None:
        """
        Проверяет доступ к полю структуры.
        
        Как работает:
        1. Проверяем базовое выражение (например, переменную p в p.x)
        2. Находим тип базового выражения (должен быть struct)
        3. Ищем структуру в self.struct_fields
        4. Проверяем, есть ли поле в этой структуре
        
        Пример:
        ```minilang
        struct Point { int x; int y; }
        struct Point p;
        p.x = 10;  // ← проверяем: есть ли поле x в struct Point? ✓
        p.z = 20;  // ← проверяем: есть ли поле z в struct Point? ✗ ОШИБКА
        ```
        
        Args:
            field_expr: выражение доступа к полю (например, p.x)
            
        Raises:
            SemanticError: если поле не существует
        """
        # Сначала проверяем базовое выражение (например, переменную p)
        self._check_expr(field_expr.base)
        
        # Определяем тип базового выражения
        # Для упрощения, проверяем только случаи, когда base - это Ident с типом struct
        # (например, p.x, но не arr[i].x)
        if isinstance(field_expr.base, Ident):
            # Ищем переменную в области видимости
            symbol = self.current_scope.lookup(field_expr.base.name)
            
            if symbol and symbol.kind == "var":
                # Получаем объявление переменной
                decl: Decl = symbol.data
                
                # Проверяем, что тип переменной - это struct
                if isinstance(decl.type_spec, NamedStructType):
                    struct_name = decl.type_spec.name  # Например, "Point"
                    
                    # Проверяем, существует ли структура в нашей таблице
                    if struct_name in self.struct_fields:
                        # Проверяем, есть ли поле в этой структуре
                        if field_expr.field not in self.struct_fields[struct_name]:
                            # Поле не найдено - ошибка
                            # Позиция ошибки будет извлечена из field_expr.span в format_error()
                            raise SemanticError(
                                f"Field '{field_expr.field}' does not exist in struct '{struct_name}'",
                                field_expr
                            )
                    else:
                        # Структура не найдена (не была объявлена)
                        # Позиция ошибки будет извлечена из field_expr.span в format_error()
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
            # Позиция ошибки будет извлечена из call.span в format_error()
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
        """
        Проверяет блок (создает новую область видимости).
        
        Как работает:
        1. Сохраняем текущую область видимости
        2. Создаем новую область с родителем = текущая область
        3. Проверяем все statements в блоке (они видят переменные из родительской области)
        4. Восстанавливаем предыдущую область видимости
        
        Пример:
        ```minilang
        int x = 10;        // ← в глобальной области
        {
            int y = 20;    // ← в локальной области (внутри блока)
            x = 5;         // ← x видна (ищем в родительской области) ✓
        }
        y = 30;            // ← y не видна (она была в дочерней области) ✗
        ```
        """
        # Сохраняем текущую область видимости
        old_scope = self.current_scope
        
        # Создаем новую область видимости с родителем = текущая область
        # Это позволяет видеть переменные из внешней области
        self.current_scope = Scope(parent=old_scope)
        
        try:
            # Проверяем все statements в блоке
            for stmt in block.stmts:
                self._check_stmt(stmt)
        finally:
            # ВАЖНО: всегда восстанавливаем предыдущую область видимости
            # даже если произошла ошибка (благодаря try-finally)
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
                    # Позиция ошибки будет извлечена из param.span в format_error()
                    raise SemanticError(
                        f"Duplicate parameter '{param.name}' in function '{func.name}'",
                        param
                    )
            
            # Проверяем тело функции
            self._check_block(func.body)
        finally:
            self.current_scope = old_scope
    
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

