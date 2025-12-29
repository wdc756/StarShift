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



def test_shift_transformer():
    class Test(Shift):
        val: int

        @shift_transformer('val')
        def transform_val(self, val):
            return val + 1

    test = Test(val=42)
    assert test.val == 43

def test_shift_transformer_advanced():
    class Test(Shift):
        val: int

        @shift_transformer('val')
        def transform_val(self, field: ShiftField, info: ShiftInfo):
            return field.val + 1

    test = Test(val=42)
    assert test.val == 43

def test_shift_transformer_pre():
    class Test(Shift):
        val: int

        @shift_transformer('val', pre=True)
        def transform_val(self, val):
            return int(val)

    test = Test(val="42")
    assert test.val == 42

def test_shift_transformer_pre_skip():
    class Test(Shift):
        val: int

        @shift_transformer('val', pre=True, skip_when_pre=True)
        def transform_val(self, val):
            return str(val)

        @shift_validator('val', pre=True, skip_when_pre=True)
        def validate_val(self, val):
            return True

    test = Test(val=42)
    assert test.val == "42"

def test_shift_validator():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, val):
            return val > 0

    test = Test(val=42)
    assert test.val == 42

    with pytest.raises(ShiftError):
        _ = Test(val=-42)

def test_shift_validator_advanced():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, field: ShiftField, info: ShiftInfo):
            return field.val > 0

    test = Test(val=42)
    assert test.val == 42

    with pytest.raises(ShiftError):
        _ = Test(val=-42)

def test_shift_validator_pre():
    class Test(Shift):
        val: int

        @shift_validator('val', pre=True)
        def validate_val(self, field: ShiftField, info: ShiftInfo):
            for i_field in info.fields:
                if i_field.name == 'val':
                    i_field.val = i_field.val + 1
            return True

    test = Test(val=42)
    assert test.val == 43

def test_shift_validator_pre_skip():
    class Test(Shift):
        val: int

        @shift_validator('val', pre=True, skip_when_pre=True)
        def validate_val(self, field: ShiftField, info: ShiftInfo):
            for i_field in info.fields:
                if i_field.name == 'val':
                    i_field.val = 42
            return True

    test = Test(val="42")
    assert test.val == 42

def test_shift_setter():
    class Test(Shift):
        val: int

        @shift_setter('val')
        def set_val(self, val):
            setattr(self, 'val', val + 1)

    test = Test(val=42)
    assert test.val == 43

def test_shift_setter_advanced():
    class Test(Shift):
        val: int

        @shift_setter('val')
        def set_val(self, field: ShiftField, info: ShiftInfo):
            setattr(self, field.name, field.val + 1)

    test = Test(val=42)
    assert test.val == 43

def test_shift_repr():
    class Test(Shift):
        val: int

        @shift_repr('val')
        def repr_val(self, val):
            return repr(val + 1)

    test = Test(val=42)
    assert repr(test) == "Test(val=43)"

def test_shift_repr_advanced():
    class Test(Shift):
        val: int

        @shift_repr('val')
        def repr_val(self, field: ShiftField, info: ShiftInfo):
            return repr(field.val + 1)

    test = Test(val=42)
    assert repr(test) == "Test(val=43)"

def test_shift_serializer():
    class Test(Shift):
        val: int

        @shift_serializer('val')
        def serialize_val(self, val):
            return val + 1

    test = Test(val=42)
    assert test.serialize() == {"val": 43}

def test_shift_serializer_advanced():
    class Test(Shift):
        val: int

        @shift_serializer('val')
        def serialize_val(self, field: ShiftField, info: ShiftInfo):
            return field.val + 1

    test = Test(val=42)
    assert test.serialize() == {"val": 43}
