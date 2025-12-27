from typing import Any, Callable, Optional, Literal, ForwardRef
from starshift import *



InvalidType = object()



def run():
    class Test(Shift):
        val: int

        @shift_repr('val')
        def repr_val(self, val):
            return repr(val + 1)

    test = Test(val=42)
    assert repr(test) == "Test(val=43)"

if __name__ == '__main__':
    run()