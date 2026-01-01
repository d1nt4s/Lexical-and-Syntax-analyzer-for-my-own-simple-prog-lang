"""
Пакет для генерации промежуточного кода (IR) для стек-машины.
"""
from intermidiate.ir import (
    IRProgram, IRInstruction, Push, Op, IROp, Label, Jmp, JmpIfFalse,
    ir_to_string
)
from intermidiate.generator import generate_ir, IRGenerator

__all__ = [
    'IRProgram', 'IRInstruction', 'Push', 'Op', 'IROp', 'Label', 'Jmp', 'JmpIfFalse',
    'ir_to_string', 'generate_ir', 'IRGenerator'
]

