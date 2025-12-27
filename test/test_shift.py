import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()



def test_changing_vals():
    class Test(Shift):
        val: int

    test = Test(val=42)
    assert test.val == 42
    test = Test(val=81)
    assert test.val == 81

def test_static_vals():
    class Test(Shift):
        val: int

    test_1 = Test(val=42)
    assert test_1.val == 42
    test_2 = Test(val=81)
    assert test_1.val == 42
    assert test_2.val == 81

def test_shift_methods():
    class Test(Shift):
        val: int

    test = Test(val=42)
    assert hasattr(test, "__init__")
    assert hasattr(test, "transform")
    assert hasattr(test, "validate")
    assert hasattr(test, "set")
    assert hasattr(test, "__repr__")
    assert hasattr(test, "serialize")
    assert hasattr(test, "__eq__")
    assert hasattr(test, "__ne__")
    assert hasattr(test, "__hash__")
    assert hasattr(test, "__copy__")
    assert hasattr(test, "__deepcopy__")

def test_pre_init():
    class Test(Shift):
        val: int = 42

        def __pre_init__(self, info: ShiftInfo):
            info.data["val"] = 81
            info.fields = get_updated_fields(info.fields, info.data)

    test = Test()
    assert test.val == 81

def test_post_init():
    class Test(Shift):
        val: int = 42

        def __post_init__(self, info: ShiftInfo):
            self.val = 81

    test = Test()
    assert test.val == 81

def test_override_shift_methods():
    class Test(Shift):
        val: int

        def __eq__(self, other):
            return self.val != other.val

    test_1 = Test(val=42)
    test_2 = Test(val=81)
    assert test_1 == test_2

def test_new_shift_method():
    class Test(Shift):
        val: int

        def __str__(self):
            return str(self.val)

    test = Test(val=42)
    assert str(test) == "42"

