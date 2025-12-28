import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()



def test_default():
    class Test(Shift):
        val: int

    test = Test(val=42)
    info = get_shift_info(Test, test, {})
    assert info.shift_config == DEFAULT_SHIFT_CONFIG

    DEFAULT_SHIFT_CONFIG.verbosity = 1
    test = Test(val=81)
    info = get_shift_info(Test, test, {})
    assert info.shift_config.verbosity == 1
    DEFAULT_SHIFT_CONFIG.verbosity = 0

def test_override():
    class Test(Shift):
        __shift_config__ = ShiftConfig(verbosity=1)
        val: int

    test = Test(val=42)
    info = get_shift_info(Test, test, {})
    assert info.shift_config.verbosity == 1

# There's not a good way to test verbosity because its print() calls

def test_do_processing():
    # Default is tested implicitly by most other tests

    class Test(Shift):
        __shift_config__ = ShiftConfig(do_processing=False)
        val: int

        def __post_init__(self, info: ShiftInfo):
            self.val = info.data["val"]

    test = Test(val="hello there")
    assert test.val == "hello there"

# There's not a good way to test fail_fast because we can't read errors

def test_try_coerce_types():
    class Test(Shift):
        val: int

    with pytest.raises(ShiftError):
        _ = Test(val="hello there")

    class Test(Shift):
        __shift_config__ = ShiftConfig(try_coerce_types=True)
        val: int

    test = Test(val="42")
    assert test.val == 42

def test_include_default_fields_in_serialization():
    class Test(Shift):
        val: int = 42

    test = Test(val=42)
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    class Test(Shift):
        __shift_config__ = ShiftConfig(include_default_fields_in_serialization=True)
        val: int = 42

    test = Test(val=42)
    assert repr(test) == "Test(val=42)"
    assert test.serialize() == {"val": 42}

def test_include_private_fields_in_serialization():
    class Test(Shift):
        _val: int

    test = Test(_val=42)
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    shift_config = ShiftConfig(include_private_fields_in_serialization=True)
    class Test(Shift):
        __shift_config__ = shift_config
        _val: int

    test = Test(_val=42)
    assert repr(test) == f"Test(__shift_config__={shift_config}, _val=42)"
    assert test.serialize() == {"__shift_config__": shift_config, "_val": 42}
