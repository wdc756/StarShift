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



def test_none():
    class Test(ShiftModel):
        val: None

    test = Test(val=None)
    assert test.val is None
    test = Test(**{"val": None})
    assert test.val is None

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_missing_to_none():
    class Test(ShiftModel):
        val: None

    test = Test()
    assert test.val is None
    test = Test(**{})
    assert test.val is None

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_int():
    class Test(ShiftModel):
        val: int

    test = Test(val=42)
    assert test.val == 42
    test = Test(**{"val": 42})
    assert test.val == 42

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_bool():
    class Test(ShiftModel):
        val: bool

    test = Test(val=True)
    assert test.val is True
    test = Test(**{"val": True})
    assert test.val is True

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_float():
    class Test(ShiftModel):
        val: float

    test = Test(val=1.21)
    assert test.val == 1.21
    test = Test(**{"val": 1.21})
    assert test.val == 1.21

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_str():
    class Test(ShiftModel):
        val: str

    test = Test(val="hello there")
    assert test.val == "hello there"
    test = Test(**{"val": "hello there"})
    assert test.val == "hello there"

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_bytes():
    class Test(ShiftModel):
        val: bytes

    test = Test(val=b"hello there")
    assert test.val == b"hello there"
    test = Test(**{"val": b"hello there"})
    assert test.val == b"hello there"

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_bytearray():
    class Test(ShiftModel):
        val: bytearray

    test = Test(val=bytearray(b"hello there"))
    assert test.val == bytearray(b"hello there")
    test = Test(**{"val": bytearray(b"hello there")})
    assert test.val == bytearray(b"hello there")

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_any():
    class Test(ShiftModel):
        val: Any

    test = Test(val=42)
    assert test.val == 42
    test = Test(**{"val": 42})
    assert test.val == 42

    # Any doesn't have a fail case

def test_list():
    class Test(ShiftModel):
        val: list[int]

    test = Test(val=[4, 5, 6, 1, 2, 3])
    assert test.val == [4, 5, 6, 1, 2, 3]
    test = Test(**{"val": [4, 5, 6, 1, 2, 3]})
    assert test.val == [4, 5, 6, 1, 2, 3]

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val=[4, 5, 6, 1, 2, InvalidType])
    with pytest.raises(ShiftError):
        _ = Test(**{"val": [4, 5, 6, 1, 2, InvalidType]})

def test_set():
    class Test(ShiftModel):
        val: set[int]

    test = Test(val={4, 5, 6, 1, 2, 3})
    assert test.val == {4, 5, 6, 1, 2, 3}
    test = Test(**{"val": {4, 5, 6, 1, 2, 3}})
    assert test.val == {4, 5, 6, 1, 2, 3}

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val={4, 5, 6, 1, 2, InvalidType})
    with pytest.raises(ShiftError):
        _ = Test(**{"val": {4, 5, 6, 1, 2, InvalidType}})

def test_frozenset():
    class Test(ShiftModel):
        val: frozenset[int]

    test = Test(val=frozenset({4, 5, 6, 1, 2, 3}))
    assert test.val == frozenset({4, 5, 6, 1, 2, 3})
    test = Test(**{"val": frozenset({4, 5, 6, 1, 2, 3})})
    assert test.val == frozenset({4, 5, 6, 1, 2, 3})

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val=frozenset({4, 5, 6, 1, 2, InvalidType}))
    with pytest.raises(ShiftError):
        _ = Test(**{"val": frozenset({4, 5, 6, 1, 2, InvalidType})})

def test_tuple():
    class Test(ShiftModel):
        val: tuple[str, int]

    test = Test(val=("hello there", 42))
    assert test.val == ("hello there", 42)
    test = Test(**{"val": ("hello there", 42)})
    assert test.val == ("hello there", 42)

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val=("hello there", InvalidType))
    with pytest.raises(ShiftError):
        _ = Test(**{"val": ("hello there", InvalidType)})

# def test_callable():
#     class Test(ShiftModel):
#         val: Callable[[int], str]
#     @staticmethod
#     def func(x: int) -> str: return str(x)
#
#     test = Test(val=func)
#     assert test.val(42) == "42"
#     test = Test(**{"val": func})
#     assert test.val(42) == "42"
#
#     with pytest.raises(ShiftError):
#         _ = Test(val=InvalidType)
#     with pytest.raises(ShiftError):
#         _ = Test(**{"val": InvalidType})
#
#     @staticmethod
#     def func(y: str) -> str: return y
#     with pytest.raises(ShiftError):
#         _ = Test(val=func)
#     with pytest.raises(ShiftError):
#         _ = Test(**{"val": func})
#
#     @staticmethod
#     def func(x: int) -> int: return x
#     with pytest.raises(ShiftError):
#         _ = Test(val=func)
#     with pytest.raises(ShiftError):
#         _ = Test(**{"val": func})

def test_dict():
    class Test(ShiftModel):
        val: dict[str, int]

    test = Test(val={"hello there": 42})
    assert test.val == {"hello there": 42}
    test = Test(**{"val": {"hello there": 42}})
    assert test.val == {"hello there": 42}

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val={"hello there": InvalidType})
    with pytest.raises(ShiftError):
        _ = Test(**{"val": {"hello there": InvalidType}})

def test_union():
    class Test(ShiftModel):
        val: Union[int, str]

    test = Test(val=42)
    assert test.val == 42
    test = Test(**{"val": 42})
    assert test.val == 42

    test = Test(val="hello there")
    assert test.val == "hello there"
    test = Test(**{"val": "hello there"})
    assert test.val == "hello there"

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_optional():
    class Test(ShiftModel):
        val: Optional[int]

    test = Test(val=42)
    assert test.val == 42
    test = Test(**{"val": 42})
    assert test.val == 42

    test = Test()
    assert test.val is None

def test_literal():
    class Test(ShiftModel):
        val: Literal["hello there", "I have a bad feeling about this"]

    test = Test(val="hello there")
    assert test.val == "hello there"
    test = Test(**{"val": "hello there"})
    assert test.val == "hello there"

    test = Test(val="I have a bad feeling about this")
    assert test.val == "I have a bad feeling about this"
    test = Test(**{"val": "I have a bad feeling about this"})
    assert test.val == "I have a bad feeling about this"

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val="invalid")
    with pytest.raises(ShiftError):
        _ = Test(**{"val": "invalid"})

class TForwardRef(ShiftModel):
    val: Optional[ForwardRef("TForwardRef")]

def test_shift():
    class A(ShiftModel):
        val: int
    class B(ShiftModel):
        ref: A

    test = B(ref=A(val=42))
    assert test.ref.val == 42
    test = B(**{"ref": A(val=42)})
    assert test.ref.val == 42

    with pytest.raises(ShiftError):
        _ = B(ref=InvalidType)
    with pytest.raises(ShiftError):
        _ = B(**{"ref": InvalidType})

    with pytest.raises(ShiftError):
        _ = B(ref=A(val=InvalidType))
    with pytest.raises(ShiftError):
        _ = B(**{"ref": A(val=InvalidType)})

def test_forwardref():
    ref = TForwardRef()
    test = TForwardRef(val=ref)
    assert test.val == ref
    test = TForwardRef(**{"val": ref})
    assert test.val == ref

    with pytest.raises(ShiftError):
        _ = TForwardRef(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = TForwardRef(**{"val": InvalidType})

def test_shift_field_basic():
    class Test(ShiftModel):
        val = ShiftField(type=int)

    test = Test(val=42)
    assert test.val == 42

    test = Test(**{"val": 42})
    assert test.val == 42

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)

    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})
