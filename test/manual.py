from typing import Any
from starshift import *



InvalidType = object()



def run():
    class Test(Shift):
        val: Any

    test = Test(val=42)
    assert test.val == 42

if __name__ == '__main__':
    run()