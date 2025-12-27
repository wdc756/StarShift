from typing import Any, Callable, Optional, Literal, ForwardRef
from starshift import *



InvalidType = object()



def run():
    class Test(Shift):
        val: int = 42

    test = Test()
    test.transform(**{"val": 81})


if __name__ == '__main__':
    run()