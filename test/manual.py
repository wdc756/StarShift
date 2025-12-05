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
    __shift_config__ = ShiftConfig(verbosity=3)

    string: str
    integer: int
    float: float

    @shift_validator('string')
    def _validate_string(self, data, field) -> bool:
        return len(data[field]) > 0

    @shift_validator('integer', 'float')
    def _validate_numbers(self, data, field) -> bool:
        return data[field] > 10.0

class ShiftSetter(Shift):
    integer: int

    @shift_setter('integer')
    def _set_integer(self, data):
        self.integer = data['integer'] + 1



def manual_test():
    # shift_validator = ShiftValidator(string='hello', integer=11, float=11.0)
    # assert shift_validator.string == 'hello'
    # assert shift_validator.integer == 11
    # assert shift_validator.float == 11.0

    # with pytest.raises(ValueError):
    shift_validator = ShiftValidator(string='', integer=11, float=11.0)

    # with pytest.raises(ValueError):
    # shift_validator = ShiftValidator(string='hello', integer=0, float=11.0)

    # with pytest.raises(ValueError):
    # shift_validator = ShiftValidator(string='hello', integer=11, float=0.0)
if __name__ == '__main__':
    manual_test()