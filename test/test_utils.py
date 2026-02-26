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



# Can't test log_verbose because it prints

def test_get_shift_type():
    shift_types = get_shift_type_registry()
    int_type = shift_types[int]
    assert get_shift_type(int) == int_type

    class Test:
        val: int

        def __init__(self, val):
            self.val = val

    assert get_shift_type(Test) is None

def test_get_shift_config():
    reset_starshift_globals() # Call this to fix weird pytest globals bug
    class Test(Shift):
        val: int

    assert get_shift_config(Test, Test.__dict__.copy()) == DEFAULT_SHIFT_CONFIG

    class Test(Shift):
        __shift_config__ = ShiftConfig(fail_fast=True)

    assert get_shift_config(Test, Test.__dict__.copy()).fail_fast == True

def test_get_field_decorators():
    class Test(Shift):
        val: int

        @shift_transformer('val')
        def transform_val(self, val):
            return val + 1

        @shift_validator('val')
        def validate_val(self, val):
            return val > 0

        @shift_setter('val')
        def set_val(self, val):
            self.val = val + 1

        @shift_repr('val')
        def repr_val(self, val):
            return str(val)

        @shift_serializer('val')
        def serialize_val(self, val):
            return val

    field_decorators = {
        "pre_transformer_skips": [],
        "pre_transformers": {},
        "transformers": {
            "val": Test.transform_val
        },
        "pre_validator_skips": [],
        "pre_validators": {},
        "validators": {
            "val": Test.validate_val
        },
        "setters": {
            "val": Test.set_val
        },
        "reprs": {
            "val": Test.repr_val
        },
        "serializers": {
            "val": Test.serialize_val
        }
    }
    assert get_field_decorators(Test, Test.__dict__.copy()) == field_decorators

    class Test(Shift):
        val: int

        @shift_transformer('val', pre=True)
        def transform_val(self, val):
            return val + 1

        @shift_validator('val', pre=True)
        def validate_val(self, val):
            return val > 0

    field_decorators = {
        "pre_transformer_skips": [
            "val"
        ],
        "pre_transformers": {
            "val": Test.transform_val
        },
        "transformers": {},
        "pre_validator_skips": [
            "val"
        ],
        "pre_validators": {
            "val": Test.validate_val
        },
        "validators": {},
        "setters": {},
        "reprs": {},
        "serializers": {}
    }
    assert get_field_decorators(Test, Test.__dict__.copy()) == field_decorators

    class Test(Shift):
        val: int

        @shift_transformer('val', pre=True, skip_when_pre=False)
        def transform_val(self, val):
            return val + 1

        @shift_validator('val', pre=True, skip_when_pre=False)
        def validate_val(self, val):
            return val > 0

    field_decorators = {
        "pre_transformer_skips": [],
        "pre_transformers": {
            "val": Test.transform_val
        },
        "transformers": {},
        "pre_validator_skips": [],
        "pre_validators": {
            "val": Test.validate_val
        },
        "validators": {},
        "setters": {},
        "reprs": {},
        "serializers": {}
    }
    assert get_field_decorators(Test, Test.__dict__.copy()) == field_decorators

def test_get_fields():
    class Test(Shift):
        val: int

    fields = [
        ShiftFieldInfo(typ=int, name='val')
    ]
    assert get_fields(Test, Test.__dict__.copy(), {}) == fields

    class Test(Shift):
        val: int = 42

    fields = [
        ShiftFieldInfo(typ=int, name='val', val=81, default=42)
    ]
    assert get_fields(Test, Test.__dict__.copy(), {"val": 81}) == fields

    class Test(Shift):
        val: int

        def do_something(self):
            print("hello there")

    fields = [
        ShiftFieldInfo(typ=int, name='val')
    ]
    assert get_fields(Test, Test.__dict__.copy(), {}) == fields

def test_get_updated_fields():
    class Test(Shift):
        val: int

    test_1 = Test(val=42)
    test_2 = Test(val=81)
    fields = [
        ShiftFieldInfo(typ= int, name='val', val=81)
    ]
    assert get_updated_fields(test_2, get_fields(Test, Test.__dict__.copy(), {}), {"val": 81}) == fields

def test_get_val_fields():
    class Test(Shift):
        val: int

    test = Test(val=42)
    fields = [
        ShiftFieldInfo(typ= int, name='val', val=42)
    ]
    assert get_val_fields(test, get_fields(Test, Test.__dict__.copy(), {})) == fields

def test_get_shift_info():
    class Test(Shift):
        val: int

    test = Test(val=42)
    info = ShiftInfo(
        instance=test,
        model_name='Test',
        shift_config=DEFAULT_SHIFT_CONFIG,
        fields=[
            ShiftFieldInfo(typ=int, name='val', val=42)
        ],
        pre_transformer_skips=[],
        pre_transformers={},
        transformers={},
        pre_validator_skips=[],
        pre_validators={},
        validators={},
        setters={},
        reprs={},
        serializers={},
        data={
            "val": 42
        },
        errors=[]
    )
    assert get_shift_info(Test, test, {"val": 42}) == info

def test_serialize():
    class Test(Shift):
        val: int

    test = Test(val=42)
    assert serialize(test) == {"val": 42}

    class Test:
        val: int

        def __init__(self, val):
            self.val = val

    test = Test(val=42)

    with pytest.raises(ShiftFieldError):
        _ = serialize(test)

    assert serialize(test, throw=False) is None

def test_get_shift_type_registry():
    def func():
        pass
    class Test:
        val: int

        def __init__(self, val):
            self.val = val

    test = Test(val=42)
    clear_shift_types()
    shift_type = ShiftType(
        transformer=func,
        validator=func,
        setter=func,
        repr=func,
        serializer=func
    )
    register_shift_type(Test, shift_type)
    assert get_shift_type_registry() == {Test: shift_type}

def test_register_shift_type():
    int_type = get_shift_type(int)
    clear_shift_types()
    register_shift_type(int, int_type)
    assert get_shift_type_registry() == {int: int_type}

def test_deregister_shift_type():
    int_type = get_shift_type(int)
    clear_shift_types()
    register_shift_type(int, int_type)
    deregister_shift_type(int)
    assert get_shift_type_registry() == {}

def test_clear_shift_types():
    clear_shift_types()
    assert get_shift_type_registry() == {}

def test_get_forward_ref_registry():
    class A:
        ref: "B"

        def __init__(self, ref):
            self.val = ref
    class B:
        val: int

        def __init__(self, val):
            self.val = val

    assert get_forward_ref_registry() == {}
    register_forward_ref("B", B)
    assert get_forward_ref_registry() == {"B": B}

def test_register_forward_ref():
    class A:
        ref: "B"

        def __init__(self, ref):
            self.val = ref
    class B:
        val: int

        def __init__(self, val):
            self.val = val

    register_forward_ref("B", B)
    assert get_forward_ref_registry() == {"B": B}

def test_deregister_forward_ref():
    class A:
        ref: "B"

        def __init__(self, ref):
            self.val = ref

    class B:
        val: int

        def __init__(self, val):
            self.val = val

    register_forward_ref("B", B)
    assert get_forward_ref_registry() == {"B": B}
    deregister_forward_ref("B")
    assert get_forward_ref_registry() == {}

def test_clear_forward_refs():
    class A:
        ref: "B"

        def __init__(self, ref):
            self.val = ref
    class B:
        val: int

        def __init__(self, val):
            self.val = val

    register_forward_ref("B", B)
    clear_forward_refs()
    assert get_forward_ref_registry() == {}

def test_get_model_info_registry():
    class Test(Shift):
        val: int

    assert get_shift_info_registry() == {}
    test = Test(val=42)
    info = get_shift_info(Test, test, {"val": 42})
    assert get_shift_info_registry() == {Test: info}

def test_clear_model_info_registry():
    class Test(Shift):
        val: int

    test = Test(val=42)
    clear_shift_info_registry()
    assert get_shift_info_registry() == {}

def test_get_shift_function_registry():
    class Test(Shift):
        val: int

        @shift_transformer('val')
        def transform_val(self, val):
            return val + 1

        @shift_validator('val')
        def validate_val(self, field: ShiftFieldInfo, info: ShiftInfo):
            return field.val > 0

    _ = Test(val=42)
    registry = get_shift_function_registry()
    assert Test.transform_val in registry
    assert registry[Test.transform_val] == False
    assert Test.validate_val in registry
    assert registry[Test.validate_val] == True

def test_clear_shift_function_registry():
    class Test(Shift):
        val: int

        @shift_transformer('val')
        def transform_val(self, val):
            return val + 1

        @shift_validator('val')
        def validate_val(self, field: ShiftFieldInfo, info: ShiftInfo):
            return field.val > 0

    test = Test(val=42)
    clear_shift_function_registry()
    assert get_shift_function_registry() == {}
