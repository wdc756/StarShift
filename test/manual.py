import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from abc import ABC, abstractmethod
from datetime import datetime, timedelta



InvalidType = object()



def run():
    class Test(ShiftModel):
        val: Callable[[int], str]
    @staticmethod # noqa
    def func(x: int) -> str: return str(x)

    test = Test(val=func)
    assert test.val(42) == "42"
    test = Test(**{"val": func})
    assert test.val(42) == "42"

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    @staticmethod # noqa
    def func(y: str) -> str: return y
    with pytest.raises(ShiftError):
        _ = Test(val=func)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": func})

    @staticmethod # noqa
    def func(x: int) -> int: return x
    with pytest.raises(ShiftError):
        _ = Test(val=func)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": func})

if __name__ == '__main__':
    run()