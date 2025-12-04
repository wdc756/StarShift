from typing import Any, Optional, Union, List, Dict
from starshift import *


class Test(Shift):
    __shift_config__ = ShiftConfig(verbosity=3)


    string: str = "Hello"
    integer: int
    any: Any
    optional: Optional[str]
    union: Union[str, int]
    list_var: List[str]
    dict_var: Dict[str, int]
    unannotated = False


    @shift_validator("integer")
    def validate_func(self, val: int) -> bool:
        if val < 0 or val > 100:
            raise ValueError("`integer` must be between 0 and 100")
        return True

    @shift_setter("dict_var")
    def set_dict_var(self, val: dict) -> None:
        val["new_key"] = 0
        self.dict_var = val



    def __post_init__(self):
        print("Post Init")


    def print_func(self):
        print(self.string)
        print(self.integer)
        print(self.any)
        print(self.optional)
        print(self.union)
        print(self.list_var)
        print(self.dict_var)
        print(self.unannotated)

t1 = Test(string="Hello World!", integer=100, any=Test, optional="Hello There!", union="Hello", list_var=["Hello", "0"], dict_var={"0": 1, "str2": 2}, unannotated="Hello")
print()
print()
print()
t1.print_func()