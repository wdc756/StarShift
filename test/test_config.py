import pytest
from typing import Any, Union, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



def test_config_not_persistent():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert not hasattr(test, '__shift_config__')

def test_default_config():
    class Test(Shift):
        __shift_config__: ShiftConfig = DEFAULT_SHIFT_CONFIG

        val: int

    test = Test(val=10)
    assert test.__shift_config__ == DEFAULT_SHIFT_CONFIG

    DEFAULT_SHIFT_CONFIG.skip_validation = True
    test = Test(val=10)
    assert test.__shift_config__.skip_validation == DEFAULT_SHIFT_CONFIG.skip_validation == True

    DEFAULT_SHIFT_CONFIG.skip_validation = False

# def test_verbosity(): - not sure how to test print statements

def test_lazy_validate_decorators():
    was_lazy = False
    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_decorators=False)
        val: int

        def __pre_init__(self, data: dict[str, Any]) -> None:
            nonlocal was_lazy
            was_lazy = True

        @shift_setter('val')
        def set_val(self, data: dict[str, Any], field: str) -> None:
            setattr(self, "val", data["val"])

    with pytest.raises(ShiftConfigError):
        Test(val=10)
    assert was_lazy == False

    class Test(Shift):
        __shift_config__ = ShiftConfig(lazy_validate_decorators=True,
                                       allow_decorators=False, allow_unmatched_args=True)
        val: int

        def __pre_init__(self, data: dict[str, Any]) -> None:
            if data['override']:
                self.__shift_config__.allow_decorators = True

        @shift_setter('val')
        def set_val(self, data: dict[str, Any], field: str) -> None:
            setattr(self, "val", data["val"])

    test = Test(val=10, override=True)

def test_use_custom_shift_validators_first():
    shift_validator_first = False
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field: str) -> bool:
            nonlocal shift_validator_first
            shift_validator_first = True
            return True

    with pytest.raises(ShiftValidationError):
        test = Test(val="Invalid type")
    assert shift_validator_first == False

    shift_validator_first = False
    class Test(Shift):
        __shift_config__ = ShiftConfig(use_custom_shift_validators_first=True,
                                       custom_shift_validators_bypass_validation=True)
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field: str) -> bool:
            nonlocal shift_validator_first
            shift_validator_first = True
            data['val'] = 0
            return True

        @shift_setter('val')
        def set_val(self, data: dict[str, Any], field: str) -> None:
            print(data['val'])
            setattr(self, "val", data["val"])

    test = Test(val=10)
    assert shift_validator_first == True
    assert test.val == 0

def test_custom_shift_validators_bypass_validation():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field: str) -> bool:
            data['val'] = 0
            return True

    with pytest.raises(ShiftValidationError):
        test = Test(val="Invalid type")

    class Test(Shift):
        __shift_config__ = ShiftConfig(custom_shift_validators_bypass_validation=True)
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field: str) -> bool:
            data['val'] = 0
            return True

    test = Test(val="Invalid type")
    assert test.val == 0

def test_skip_validation():
    class Test(Shift):
        val: int

    with pytest.raises(ShiftValidationError):
        test = Test(val="Invalid type")

    class Test(Shift):
        __shift_config__ = ShiftConfig(skip_validation=True)
        val: int

    test = Test(val="Invalid type")
    assert not hasattr(test, 'val')

def test_validate_infinite_nesting():
    class Test(Shift):
        nest: "Test"

    with pytest.raises(ShiftValidationError):
        test = Test(nest="Placeholder")

    class Test(Shift):
        __shift_config__ = ShiftConfig(validate_infinite_nesting=False,
                                       use_custom_shift_validators_first=True,
                                       custom_shift_validators_bypass_validation=True)
        nest: "Test"

        @shift_validator('nest')
        def validate_nest(self, data: dict[str, Any], field: str) -> bool:
            data['nest'] = 0
            return True

        @shift_setter('nest')
        def set_nest(self, data: dict[str, Any], field: str) -> None:
            setattr(self, 'nest', None)

    # This would break without the shift_validators and shift_setters
    test = Test(nest="Placeholder")

def test_use_builtin_shift_repr():
    class Test(Shift):
        val: int

    test = Test(val=10)
    _ = repr(test)

    class Test(Shift):
        __shift_config__ = ShiftConfig(use_builtin_shift_repr=False)
        val: int

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)
        _ = repr(test)

def test_use_builtin_shift_serializer():
    class Test(Shift):
        val: int

    test = Test(val=10)
    _ = test.serialize()

    class Test(Shift):
        __shift_config__ = ShiftConfig(use_builtin_shift_serializer=False)
        val: int

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)
        _ = test.serialize()

def test_include_defaults_in_serialization():
    class Test(Shift):
        val: int = 10

    test = Test()
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    test = Test(val=10)
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    class Test(Shift):
        __shift_config__ = ShiftConfig(include_defaults_in_serialization=True)
        val: int = 10

    test = Test()
    assert repr(test) == "Test(val=10)"
    assert test.serialize() == {"val": 10}

    test = Test(val=10)
    assert repr(test) == "Test(val=10)"
    assert test.serialize() == {"val": 10}

def test_include_private_fields_in_serialization():
    class Test(Shift):
        _val: int

    test = Test(_val=10)
    assert repr(test) == "Test()"
    assert test.serialize() == {}

    class Test(Shift):
        __shift_config__ = ShiftConfig(include_private_fields_in_serialization=True)
        _val: int

    test = Test(_val=10)
    assert repr(test) == "Test(_val=10)"
    assert test.serialize() == {"_val": 10}

def test_allow_unmatched_args():
    class Test(Shift):
        val: int

    with pytest.raises(ShiftConfigError):
        test = Test(val=10, unmatched=0)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_unmatched_args=True)
        val: int

    test = Test(val=10, unmatched=0)
    assert getattr(test, 'unmatched') == 0

def test_allow_any():
    class Test(Shift):
        val: Any

    test = Test(val=10)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_any=False)
        val: Any

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)

def test_allow_defaults():
    class Test(Shift):
        val: int = 0

    test = Test()

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_defaults=False)
        val: int = 0

    test = Test(val=10)
    with pytest.raises(ShiftConfigError):
        test = Test()

def test_allow_non_annotated():
    class Test(Shift):
        val = 0

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)
    with pytest.raises(ShiftConfigError):
        test = Test()

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_non_annotated=True)
        val = 0

    test = Test(val=10)
    test = Test()

def test_allow_forward_refs():
    class Test(Shift):
        val: "Test" = None

    test = Test(val=None)
    test = Test()

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_forward_refs=False)
        val: "Test" = None

    with pytest.raises(ShiftConfigError):
        test = Test(val=None)
    with pytest.raises(ShiftConfigError):
        test = Test()

def test_allow_nested_shift_classes():
    class A(Shift):
        val: int
    class Test(Shift):
        nest: A

    test = Test(nest=A(val=10))

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_nested_shift_classes=False)
        nest: A

    with pytest.raises(ShiftConfigError):
        test = Test(nest=A(val=10))

def test_allow_decorators():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field) -> bool:
            return True

    test = Test(val=10)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_decorators=False)
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field) -> bool:
            return True

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)

def test_allow_shift_validators():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field) -> bool:
            return True

    test = Test(val=10)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_shift_validators=False)
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field) -> bool:
            return True

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)

def test_allow_shift_setters():
    class Test(Shift):
        val: int

        @shift_setter('val')
        def set_val(self, data: dict[str, Any], field) -> None:
            pass

    test = Test(val=10)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_shift_setters=False)
        val: int

        @shift_setter('val')
        def set_val(self, data: dict[str, Any], field) -> None:
            pass

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)

def test_allow_shift_reprs():
    class Test(Shift):
        val: int

        @shift_repr('val')
        def repr_val(self, data: dict[str, Any], field) -> str:
            return ""

    test = Test(val=10)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_shift_reprs=False)
        val: int

        @shift_repr('val')
        def repr_val(self, data: dict[str, Any], field) -> str:
            return ""

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)

def test_allow_shift_serializers():
    class Test(Shift):
        val: int

        @shift_serializer('val')
        def serialize_val(self, data: dict[str, Any], field) -> Any:
            return ""

    test = Test(val=10)

    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_shift_serializers=False)
        val: int

        @shift_serializer('val')
        def serialize_val(self, data: dict[str, Any], field) -> Any:
            return ""

    with pytest.raises(ShiftConfigError):
        test = Test(val=10)
