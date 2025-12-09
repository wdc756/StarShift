from typing import Any, Optional, Union, List, Dict, get_type_hints
from starshift import *

DEFAULT_SHIFT_CONFIG.verbosity = 0



def test():
    class A(Shift):
        nest: 'A' = None

    a = A(nest=A())

    class A(Shift):
        nest: Optional['A'] = None

    a = A(nest=A())



if __name__ == '__main__':
    test()