from typing import Any, Optional, Union, List, Dict, get_type_hints
from starshift import *

DEFAULT_SHIFT_CONFIG.verbosity = 3



class Test():
    val: int
    ref: Optional["Test"]

print(Test.__annotations__)
print(get_type_hints(Test))

def test():
    class A():
        test: Optional["Test"]
        ref: Optional["A"]

    print(A.__annotations__)
    print(get_type_hints(A))

if __name__ == '__main__':
    test()