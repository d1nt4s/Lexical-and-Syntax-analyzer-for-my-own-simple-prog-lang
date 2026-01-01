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
    """Условный переход: если на стеке false, перейти к метке."""
    label: str
    
    def __str__(self) -> str:
        return f"jmp_if_false {self.label}"


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

