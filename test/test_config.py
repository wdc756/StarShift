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



def test_default_config():
    class Test(Shift):
        val: int

    test = Test(val=42)
    info = get_shift_info(Test, test, {})
    assert info.shift_config == DEFAULT_SHIFT_CONFIG

    DEFAULT_SHIFT_CONFIG.fail_fast = True
    clear_shift_info_registry()
    test = Test(val=42)
    info = get_shift_info(Test, test, {})
    assert info.shift_config.fail_fast == True

    DEFAULT_SHIFT_CONFIG.fail_fast = False

def test_config_override():
    class Test(Shift):
        __shift_config__ = ShiftConfig(fail_fast=True)
        val: int

    test = Test(val=42)
    info = get_shift_info(Test, test, {})
    assert info.shift_config.fail_fast == True

def test_do_processing():
    # Default is tested implicitly by most other tests

    class Test(Shift):
        __shift_config__ = ShiftConfig(do_processing=False)
        val: int

        def __post_init__(self, info: ShiftInfo):
            self.val = info.data["val"]

    test = Test(val="hello there")
    assert test.val == "hello there"

    class Test(Shift):
        __do_processing__ = False
        val: int

        def __post_init__(self, info: ShiftInfo):
            self.val = info.data["val"]

    test = Test(val="hello there")
    assert test.val == "hello there"

# There's not a good way to test fail_fast because we can't read errors

# def try_coerce_types()

def test_allow_private_field_setting():
    class Test(Shift):
        _val: int = 42

    with pytest.raises(ShiftFieldError):
        _ = Test(_val=42)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_private_field_setting=True)
        _val: int

    test = Test(_val=42)
    assert test._val == 42

    class Test(Shift):
        __allow_private_field_setting__ = True
        _val: int

    test = Test(_val=42)
    assert test._val == 42

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

    class Test(Shift):
        __include_default_fields_in_serialization__ = True
        val: int = 42

    test = Test(val=42)
    assert repr(test) == "Test(val=42)"
    assert test.serialize() == {"val": 42}

def test_include_private_fields_in_serialization():
    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_private_field_setting=True)
        _val: int

    test = Test(_val=42)
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    class Test(Shift):
        __allow_private_field_setting__ = True
        _val: int

    test = Test(_val=42)
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    shift_config = ShiftConfig(include_private_fields_in_serialization=True, allow_private_field_setting=True)

    class Test(Shift):
        __shift_config__ = shift_config
        _val: int

    test = Test(_val=42)
    assert repr(test) == f"Test(__shift_config__={shift_config}, _val=42)"
    assert serialize(test) == {"__shift_config__": serialize(shift_config), "_val": 42}

    class Test(Shift):
        __include_private_fields_in_serialization__ = True
        __allow_private_field_setting__ = True
        _val: int

    test = Test(_val=42)
    assert repr(test) == f"Test(__shift_config__={shift_config}, _val=42)"
    assert serialize(test) == {"__shift_config__": serialize(shift_config), "_val": 42}
