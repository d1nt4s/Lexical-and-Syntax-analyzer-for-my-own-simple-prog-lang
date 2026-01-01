"""
Промежуточное представление (IR) для стек-машины.

Команды IR:
- push <value> - положить значение на стек
- операции: add, sub, mul, div, lt, le, gt, ge, eq, neq, and, or, not
- label <name> - метка для переходов
- jmp <label> - безусловный переход
- jmp_if_false <label> - условный переход (если на стеке false, перейти)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Union, Any
from enum import Enum


class IROp(Enum):
    """Операции стек-машины."""
    # Арифметические операции
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    
    # Операции сравнения
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    EQ = "eq"
    NEQ = "neq"
    
    # Логические операции
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class IRInstruction:
    """Базовая инструкция IR."""
    pass


@dataclass
class Push(IRInstruction):
    """Команда push: положить значение на стек."""
    value: Union[int, float, bool, str]  # значение для push
    
    def __str__(self) -> str:
        # Для булевых значений выводим как true/false (с маленькой буквы)
        # т.к. в Python bool выводится как True/False
        if isinstance(self.value, bool):
            return f"push {'true' if self.value else 'false'}"
        # Для остальных типов (int, float, str) выводим как есть
        return f"push {self.value}"


@dataclass
class Op(IRInstruction):
    """Операция стек-машины (add, sub, mul, div, lt, le, gt, ge, eq, neq, and, or, not)."""
    op: IROp
    
    def __str__(self) -> str:
        return self.op.value


@dataclass
class Label(IRInstruction):
    """Метка для переходов."""
    name: str
    
    def __str__(self) -> str:
        return f"label {self.name}"


@dataclass
class Jmp(IRInstruction):
    """Безусловный переход к метке."""
    label: str
    
    def __str__(self) -> str:
        return f"jmp {self.label}"


@dataclass
class JmpIfFalse(IRInstruction):
    """Условный переход: если на стеке false, перейти к метке. Снимает bool со стека."""
    label: str
    
    def __str__(self) -> str:
        return f"jmp_if_false {self.label}"


@dataclass
class Pop(IRInstruction):
    """Удаляет верхнее значение со стека (для очистки стека от результатов выражений)."""
    
    def __str__(self) -> str:
        return "pop"


@dataclass
class Store(IRInstruction):
    """Сохраняет значение в переменную. Берет значение со стека и сохраняет в переменную."""
    name: str  # имя переменной
    
    def __str__(self) -> str:
        return f"store {self.name}"


@dataclass
class Load(IRInstruction):
    """Загружает значение переменной на стек."""
    name: str  # имя переменной
    
    def __str__(self) -> str:
        return f"load {self.name}"


@dataclass
class StoreIndex(IRInstruction):
    """Сохраняет значение в элемент массива. Стек: [value, base, index] -> []"""
    
    def __str__(self) -> str:
        return "store_index"


@dataclass
class LoadIndex(IRInstruction):
    """Загружает элемент массива на стек. Стек: [base, index] -> [value]"""
    
    def __str__(self) -> str:
        return "load_index"


@dataclass
class StoreField(IRInstruction):
    """Сохраняет значение в поле структуры. Стек: [value, base] -> []"""
    field: str  # имя поля
    
    def __str__(self) -> str:
        return f"store_field {self.field}"


@dataclass
class LoadField(IRInstruction):
    """Загружает поле структуры на стек. Стек: [base] -> [value]"""
    field: str  # имя поля
    
    def __str__(self) -> str:
        return f"load_field {self.field}"


@dataclass
class Call(IRInstruction):
    """Вызов функции. Аргументы должны быть на стеке слева-направо."""
    name: str  # имя функции (формат: func_<name>)
    
    def __str__(self) -> str:
        return f"call {self.name}"


@dataclass
class Ret(IRInstruction):
    """Возврат из процедуры (proc). Не возвращает значение."""
    
    def __str__(self) -> str:
        return "ret"


@dataclass
class Retv(IRInstruction):
    """Возврат из функции (func) со значением. Берет значение со стека."""
    
    def __str__(self) -> str:
        return "retv"


# Тип для списка инструкций IR
IRProgram = List[IRInstruction]


def ir_to_string(program: IRProgram) -> str:
    """
    Преобразует программу IR в строку для вывода.
    
    Args:
        program: список инструкций IR
        
    Returns:
        Строковое представление программы IR
    """
    return "\n".join(str(instr) for instr in program)

