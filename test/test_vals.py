import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()

@pytest.fixture(autouse=True)
def reset_starshift():
    reset_starshift_globals()
    yield
    reset_starshift_globals()



def test_default():
    class Test(ShiftModel):
        val: int = 42

    test = Test()
    assert test.val == 42

def test_un_annotated():
    class Test(ShiftModel):
        val = 42

    test = Test()
    assert test.val == 42

    test = Test(val=81)
    assert test.val == 81

def test_arbitrary_keys():
    class Test(ShiftModel):
        val: int

    test = Test(val=42, arbitrary_key="hello there")
    assert test.val == 42
    assert not hasattr(test, "arbitrary_key")

# def test_inline_shift_config():
#     class Test(ShiftModel):
#         val: int
#
#     test = Test(__shift_config__=ShiftConfig(fail_fast=True), val=42)
#     assert test.val == 42
#     assert not hasattr(test, "__shift_config__")
#     assert get_shift_info(Test, test, {}).shift_config.fail_fast == True

def test_ignore_private():
    class Test(ShiftModel):
        _val: int

        def __post_init__(self):
            self._val = 42

    test = Test()
    assert test._val == 42

def test_set_to_private():
    class Test(ShiftModel):
        _val: int = 42

    with pytest.raises(ShiftFieldError):
        _ = Test(_val=42)

    class Test(ShiftModel):
        __shift_config__ = ShiftConfig(allow_private_field_setting=True)
        _val: int = 42

    test = Test(_val=81)
    assert test._val == 81

def test_shift_setter_to_private():
    class Test(ShiftModel):
        val: int
        _private: int = 42

        @shift_setter('_private')
        def set_val(self, val):
            self._private = 88

    test = Test(val=81)
    assert test._private == 88
