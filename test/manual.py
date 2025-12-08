from typing import Any, Optional, Union, List, Dict
from starshift import *

DEFAULT_SHIFT_CONFIG.verbosity = 3

def manual_test():
    class Test(Shift):
        forward_ref: "ForwardTest"

    class ForwardTest(Shift):
        ref: int

    test = Test(forward_ref=ForwardTest(ref=10))
    assert test.forward_ref.ref == 10

    test = Test(**{"forward_ref": {"ref": 10}})
    assert test.forward_ref.ref == 10

    with pytest.raises(TypeError):
        test = Test(forward_ref="Invalid type")

    with pytest.raises(TypeError):
        test = Test(**{"forward_ref": "Invalid type"})

    with pytest.raises(TypeError):
        test = Test(forward_ref=ForwardTest(ref="Invalid type"))

    with pytest.raises(TypeError):
        test = Test(**{"forward_ref": {"ref": "Invalid type"}})

if __name__ == '__main__':
    manual_test()