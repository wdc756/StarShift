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
    assert repr(test) == "Test(val=None)"
    assert serialize(test) == {"val": None}
    test = Test(**{'val': None})
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
    assert repr(test) == "Test(val=None)"
    assert serialize(test) == {"val": None}
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
    assert repr(test) == "Test(val=42)"
    assert serialize(test) == {"val": 42}

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

def test_bool():
    class Test(ShiftModel):
        val: bool

    test = Test(val=True)
    assert test.val is True
    assert repr(test) == "Test(val=True)"
    assert serialize(test) == {"val": True}
    test = Test(**{'val': True})
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
    assert repr(test) == "Test(val=1.21)"
    assert serialize(test) == {"val": 1.21}
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
    assert repr(test) == "Test(val='hello there')"
    assert serialize(test) == {"val": "hello there"}
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
    assert repr(test) == "Test(val=b'hello there')"
    assert serialize(test) == {"val": b"hello there"}
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
    assert repr(test) == "Test(val=bytearray(b'hello there'))"
    assert serialize(test) == {"val": bytearray(b"hello there")}
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
    assert repr(test) == "Test(val=42)"
    assert serialize(test) == {"val": 42}
    test = Test(**{"val": 42})
    assert test.val == 42

    # Any doesn't have a fail case

def test_list():
    class Test(ShiftModel):
        val: list[int]

    test = Test(val=[4, 5, 6, 1, 2, 3])
    assert test.val == [4, 5, 6, 1, 2, 3]
    assert repr(test) == "Test(val=[4, 5, 6, 1, 2, 3])"
    assert serialize(test) == {"val": [4, 5, 6, 1, 2, 3]}
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
    r = repr(test)
    assert '4' in r
    assert '5' in r
    assert '6' in r
    assert '1' in r
    assert '2' in r
    assert '3' in r
    assert serialize(test) == {"val": {4, 5, 6, 1, 2, 3}}
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
    r = repr(test)
    assert 'frozenset' in r
    assert '4' in r
    assert '5' in r
    assert '6' in r
    assert '1' in r
    assert '2' in r
    assert '3' in r
    assert serialize(test) == {"val": frozenset({4, 5, 6, 1, 2, 3})}
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
    assert repr(test) == "Test(val=('hello there', 42))"
    assert serialize(test) == {"val": ("hello there", 42)}
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

def test_callable():
    class Test(ShiftModel):
        val: Callable[[int], str]
    @staticmethod # noqa
    def func(x: int) -> str: return str(x)

    test = Test(val=func)
    assert test.val(42) == "42"
    test = Test(**{"val": func})
    assert test.val(42) == "42"

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    @staticmethod # noqa
    def func(y: str) -> str: return y
    with pytest.raises(ShiftError):
        _ = Test(val=func)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": func})

    @staticmethod # noqa
    def func(x: int) -> int: return x
    with pytest.raises(ShiftError):
        _ = Test(val=func)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": func})

def test_dict():
    class Test(ShiftModel):
        val: dict[str, int]

    test = Test(val={"hello there": 42})
    assert test.val == {"hello there": 42}
    assert repr(test) == "Test(val={'hello there': 42})"
    assert serialize(test) == {"val": {"hello there": 42}}
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
    assert repr(test) == "Test(val=42)"
    assert serialize(test) == {"val": 42}
    test = Test(**{"val": 42})
    assert test.val == 42

    test = Test(val="hello there")
    assert test.val == "hello there"
    assert repr(test) == "Test(val='hello there')"
    assert serialize(test) == {"val": "hello there"}
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
    assert repr(test) == "Test(val=42)"
    assert serialize(test) == {"val": 42}
    test = Test(**{"val": 42})
    assert test.val == 42

    test = Test()
    assert test.val is None
    assert repr(test) == "Test(val=None)"
    assert serialize(test) == {"val": None}
    test = Test(**{})
    assert test.val is None

def test_literal():
    class Test(ShiftModel):
        val: Literal["hello there", "I have a bad feeling about this"]

    test = Test(val="hello there")
    assert test.val == "hello there"
    assert repr(test) == "Test(val='hello there')"
    assert serialize(test) == {"val": "hello there"}
    test = Test(**{"val": "hello there"})
    assert test.val == "hello there"

    test = Test(val="I have a bad feeling about this")
    assert test.val == "I have a bad feeling about this"
    assert repr(test) == "Test(val='I have a bad feeling about this')"
    assert serialize(test) == {"val": "I have a bad feeling about this"}
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

def test_shift():
    class A(ShiftModel):
        val: int
    class B(ShiftModel):
        ref: A

    test = B(ref=A(val=42))
    assert test.ref.val == 42
    assert repr(test) == "B(ref=A(val=42))"
    assert serialize(test) == {"ref": {"val": 42}}
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

class TForwardRef(ShiftModel):
    standard: Optional["TForwardRef"]
    formal: Optional[ForwardRef("TForwardRef")]

def test_forwardref():
    ref = TForwardRef()
    test = TForwardRef(standard=ref, formal=ref)
    assert test.standard == ref
    assert test.formal == ref
    assert repr(test) == 'TForwardRef(standard=TForwardRef(standard=None, formal=None), formal=TForwardRef(standard=None, formal=None))'
    assert serialize(test) == {'standard': {'standard': None, 'formal': None}, 'formal': {'standard': None, 'formal': None}}

    test = TForwardRef(**{"standard": ref})
    assert test.standard == ref

    with pytest.raises(ShiftError):
        _ = TForwardRef(standard=InvalidType)
    with pytest.raises(ShiftError):
        _ = TForwardRef(**{"standard": InvalidType})

def test_shift_field_basic():
    class Test(ShiftModel):
        val = ShiftField(type=int)

    test = Test(val=42)
    assert test.val == 42
    assert repr(test) == "Test(val=42)"
    assert serialize(test) == {"val": 42}
    test = Test(**{"val": 42})
    assert test.val == 42

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})
