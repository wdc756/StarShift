from typing import Any, Optional, Union, Callable, get_type_hints
from starshift import *

DEFAULT_SHIFT_CONFIG.verbosity = 0



def test():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field) -> bool:
            return True

    test = Test(val=10)

if __name__ == '__main__':
    test()