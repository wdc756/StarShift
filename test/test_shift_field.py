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



def test_shift_field_type():
    class Test(Shift):
        val = ShiftField(type=int)

    test = Test(val=42)
    assert test.val == 42

    class Test(Shift):
        val = ShiftField()

    test = Test(val=42)
    assert test.val == 42
    test = Test(val='Hello There!')
    assert test.val == 'Hello There!'

    class Test(Shift):
        val = ShiftField(type=int)

    with pytest.raises(ShiftError):
        Test(val=InvalidType)

def test_shift_field_implicit_type():
    class Test(Shift):
        val: int = ShiftField(ge=0)

    test = Test(val=42)
    assert test.val == 42
    with pytest.raises(ShiftError):
        _ = Test(val=-42)

    class Test(Shift):
        val: str = ShiftField(type=int, min_len=3)

    with pytest.raises(ShiftError):
        _ = Test(val=42)
    test = Test(val='Hello There!')
    assert test.val == 'Hello There!'
    with pytest.raises(ShiftError):
        _ = Test(val='')

def test_shift_field_default():
    class Test(Shift):
        val = ShiftField(type=int, default=42)

    test = Test()
    assert test.val == 42
    test = Test(val=81)
    assert test.val == 81

def test_shift_field_default_skips():
    class Test(Shift):
        val: int = ShiftField(default='Hello There!', default_skips=True)

    test = Test(val=42)
    assert test.val == 42
    test = Test()
    assert test.val == 'Hello There!'

def test_shift_field_default_factory():
    def get_int():
        return 42
    class Test(Shift):
        val = ShiftField(type=int, default_factory=get_int)

    test = Test()
    assert test.val == 42

def test_shift_field_transformer():
    def transformer(instance: Any, val: int) -> int:
        return val + 1
    class Test(Shift):
        val = ShiftField(type=int, transformer=transformer)

    test = Test(val=42)
    assert test.val == 43

def test_shift_field_ge():
    class Test(Shift):
        val = ShiftField(type=int, ge=0)

    test = Test(val=42)
    test = Test(val=0)
    with pytest.raises(ShiftError):
        _ = Test(val=-42)

def test_shift_field_eq():
    class Test(Shift):
        val = ShiftField(type=int, eq=0)

    with pytest.raises(ShiftError):
        _ = Test(val=42)
    test = Test(val=0)
    with pytest.raises(ShiftError):
        _ = Test(val=-42)

def test_shift_field_le():
    class Test(Shift):
        val = ShiftField(type=int, le=0)

    with pytest.raises(ShiftError):
        _ = Test(val=42)
    test = Test(val=0)
    test = Test(val=-42)

def test_shift_field_gt():
    class Test(Shift):
        val = ShiftField(type=int, gt=0)

    test = Test(val=42)
    with pytest.raises(ShiftError):
        _ = Test(val=0)
    with pytest.raises(ShiftError):
        _ = Test(val=-42)

def test_shift_field_ne():
    class Test(Shift):
        val = ShiftField(type=int, ne=0)

    test = Test(val=42)
    with pytest.raises(ShiftError):
        _ = Test(val=0)
    test = Test(val=-42)

def test_shift_field_lt():
    class Test(Shift):
        val = ShiftField(type=int, lt=0)

    with pytest.raises(ShiftError):
        _ = Test(val=42)
    with pytest.raises(ShiftError):
        _ = Test(val=0)
    test = Test(val=-42)

def test_shift_field_min_len():
    class Test(Shift):
        val = ShiftField(type=list[int], min_len=3)

    test = Test(val=[4, 5, 6, 1, 2, 3])
    with pytest.raises(ShiftError):
        _ = Test(val=[4, 5, 6])
    with pytest.raises(ShiftError):
        _ = Test(val=[])

def test_shift_field_max_len():
    class Test(Shift):
        val = ShiftField(type=list[int], max_len=3)

    with pytest.raises(ShiftError):
        _ = Test(val=[4, 5, 6, 1, 2, 3])
    with pytest.raises(ShiftError):
        _ = Test(val=[4, 5, 6])
    test = Test(val=[])

def test_shift_field_pattern():
    class Test(Shift):
        val = ShiftField(type=str, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    test = Test(val='wdc23a@acu.edu')
    with pytest.raises(ShiftError):
        test = Test(val='Hello There!')

def test_shift_field_check():
    def check(val: int) -> bool:
        return val > 0
    class Test(Shift):
        val: int = ShiftField(type=int, check=check)

    test = Test(val=42)
    assert test.val == 42
    with pytest.raises(ShiftError):
        _ = Test(val=-42)

def test_shift_field_validator():
    def validator(instance: Any, val: int) -> bool:
        return val > 0
    class Test(Shift):
        val = ShiftField(type=int, validator=validator)

    test = Test(val=42)
    with pytest.raises(ShiftError):
        test = Test(val=-42)

def test_shift_field_validator_skips():
    def validator(instance: Any, val: int) -> bool:
        return True
    class Test(Shift):
        val = ShiftField(type=int, validator=validator, validator_skips=True)

    test = Test(val='Hello There!')
    assert test.val == 'Hello There!'

def test_shift_field_setter():
    def setter(instance: Any, val: int) -> None:
        instance.val = val + 1
    class Test(Shift):
        val = ShiftField(type=int, setter=setter)

    test = Test(val=42)
    assert test.val == 43

def test_shift_field_repr():
    def t_repr(instance: Any, val: Any) -> str:
        return 'val=' + repr(val + 1)
    class Test(Shift):
        val = ShiftField(type=int, repr_func=t_repr)

    test = Test(val=42)
    assert repr(test) == 'Test(val=43)'

def test_shift_field_repr_as():
    class Test(Shift):
        val = ShiftField(type=int, repr_as='v')

    test = Test(val=42)
    assert repr(test) == 'Test(v=42)'

def test_shift_field_repr_exclude():
    class Test(Shift):
        val = ShiftField(type=int, repr_exclude=True)

    test = Test(val=42)
    assert repr(test) == 'Test()'

def test_shift_field_serializer():
    def serializer(instance: Any, val: int) -> Any:
        return { 'val': val + 1 }
    class Test(Shift):
        val = ShiftField(type=int, serializer=serializer)

    test = Test(val=42)
    assert serialize(test) == { 'val': 43 }

def test_shift_field_serializer_as():
    class Test(Shift):
        val = ShiftField(type=int, serialize_as='v')

    test = Test(val=42)
    assert serialize(test) == { 'v': 42 }

def test_shift_field_serializer_exclude():
    class Test(Shift):
        val = ShiftField(type=int, serializer_exclude=True)

    test = Test(val=42)
    assert serialize(test) == {}

def test_shift_field_defer():
    class Test(Shift):
        val: int = ShiftField(defer=True, default=42)

    test = Test()
    assert test.val == ShiftField(defer=True, default=42)
    assert repr(test) == 'Test()'

    test = Test(val=88)
    assert test.val == ShiftField(defer=True, default=42)
    assert repr(test) == 'Test()'

def test_shift_field_defer_transform():
    class Test(Shift):
        val: int | None = ShiftField(defer_transform=True, default=88)

    test = Test()
    assert test.val is Missing

def test_shift_field_defer_validation():
    class Test(Shift):
        val: int = ShiftField(defer_validation=True)

    test = Test(val=42)
    assert test.val == 42

def test_shift_field_defer_set():
    class Test(Shift):
        val: int = ShiftField(defer_set=True)

        def __pre_init__(self) -> None:
            self.val = 42

    test = Test(val=88)
    assert test.val == 42

def test_shift_field_defer_repr():
    class Test(Shift):
        val: int = ShiftField(defer_repr=True)

    test = Test(val=42)
    assert repr(test) == 'Test()'

def test_shift_field_defer_serialize():
    class Test(Shift):
        val: int = ShiftField(defer_serialize=True)

    test = Test(val=42)
    assert serialize(test) == {}
