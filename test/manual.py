from typing import Any, Callable, Optional, Literal, ForwardRef
from starshift import *



InvalidType = object()



class TForwardRef(Shift):
    val: Optional[ForwardRef("TForwardRef")]

def run():
    test = TForwardRef(val=TForwardRef())
    assert test.val == test

if __name__ == '__main__':
    run()