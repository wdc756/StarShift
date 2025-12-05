from typing import Any, Optional, Union, List, Dict
from starshift import *

class Builtins(Shift):
    boolean: bool
    integer: int
    float: float
    string: str
    lis: list[int]
    tup: tuple[str, int]
    set: set[int]
    dct: dict[str, int]

class Mini(Shift):
    string: str
    integer: int

class Container(Shift):
    string: str
    mini: Mini

class MultiContainer(Shift):
    string: str
    mini_lis: list[Mini]
    mini_tup: tuple[str, Mini]
    mini_set: set[Mini]
    mini_dct: dict[str, Mini]

# We have to use this because any values in Init will be overwritten after pre_init
global_was_pre_init_called = False

class Init(Shift):
    string: str
    integer: int

    post_init = False
    post_init_val = None

    def __pre_init__(self, data: dict[str, Any]) -> None:
        global global_was_pre_init_called
        global_was_pre_init_called = True

    def __post_init__(self, data: dict[str, Any]) -> None:
        self.post_init = True
        self.post_init_val = data['integer']

class Default(Shift):
    string: str
    integer: int = 10

class ShiftValidator(Shift):
    integer: int

    @shift_validator('integer')
    def _validate_integer(self, data) -> bool:
        return data['integer'] > 10

class ShiftSetter(Shift):
    integer: int

    @shift_setter('integer')
    def _set_integer(self, data):
        self.integer = data['integer'] + 1