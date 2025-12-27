from typing import Any, Callable, Optional, Literal, ForwardRef
from starshift import *



InvalidType = object()



def run():
    class Test(Shift):
        val: int

        def __eq__(self, other):
            return self.val != other.val

    test_1 = Test(val=42)
    print(test_1.val)
    test_2 = Test(val=81)
    print(test_1.val)
    print(test_2.val)
    assert test_1 == test_2

if __name__ == '__main__':
    run()