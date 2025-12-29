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
    class Test(Shift):
        val: int = 42

    test = Test()
    assert test.val == 42

def test_un_annotated():
    class Test(Shift):
        val = 42

    test = Test()
    assert test.val == 42

    test = Test(val=81)
    assert test.val == 81

def test_arbitrary_keys():
    class Test(Shift):
        val: int

    test = Test(val=42, arbitrary_key="hello there")
    assert test.val == 42
    assert not hasattr(test, "arbitrary_key")

def test_inline_shift_config():
    class Test(Shift):
        val: int

    test = Test(__shift_config__=ShiftConfig(verbosity=1), val=42)
    assert test.val == 42
    assert not hasattr(test, "__shift_config__")
    assert get_shift_info(Test, test, {}).shift_config.verbosity == 0

def test_set_to_private():
    class Test(Shift):
        _val: int = 42

    with pytest.raises(ShiftError):
        _ = Test(_val=42)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_private_field_setting=True)
        _val: int = 42

    test = Test(_val=81)
    assert test._val == 81

def test_shift_setter_to_private():
    class Test(Shift):
        val: int
        _private: int = 42

        @shift_setter('_private')
        def set_val(self, val):
            self._private = self.val

    test = Test(val=81)
    print(test._private)
    assert test._private == 81
