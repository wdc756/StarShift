import pytest
from typing import Any, Union, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



def test_none():
    class Test(Shift):
        none: None

    with pytest.raises(ShiftValidationError):
        test = Test(none=None)

    with pytest.raises(ShiftValidationError):
        test = Test(**{"none": None})

def test_bool():
    class Test(Shift):
        boolean: bool

    test = Test(boolean=True)
    assert test.boolean is True

    test = Test(**{"boolean": True})
    assert test.boolean is True

    with pytest.raises(ShiftValidationError):
        test = Test(boolean="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"boolean": "Invalid type"})

def test_int():
    class Test(Shift):
        integer: int

    test = Test(integer=10)
    assert test.integer == 10

    test = Test(**{"integer": 10})
    assert test.integer == 10

    with pytest.raises(ShiftValidationError):
        test = Test(integer="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"integer": "Invalid type"})

def test_float():
    class Test(Shift):
        flt: float

    test = Test(flt=3.14)
    assert test.flt == 3.14

    test = Test(**{"flt": 3.14})
    assert test.flt == 3.14

    with pytest.raises(ShiftValidationError):
        test = Test(flt="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"flt": "Invalid type"})

def test_str():
    class Test(Shift):
        string: str

    test = Test(string="hello")
    assert test.string == "hello"

    test = Test(**{"string": "hello"})
    assert test.string == "hello"

    with pytest.raises(ShiftValidationError):
        test = Test(string=False)

    with pytest.raises(ShiftValidationError):
        test = Test(**{"string": False})

def test_list():
    class Test(Shift):
        lst: list

    test = Test(lst=[1, 2, 3])
    assert test.lst == [1, 2, 3]

    test = Test(**{"lst": [1, 2, 3]})
    assert test.lst == [1, 2, 3]

    with pytest.raises(ShiftValidationError):
        test = Test(lst="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"lst": "Invalid type"})

    class Test(Shift):
        lst: list[int]

    with pytest.raises(ShiftValidationError):
        test = Test(lst=[1, 2, "Invalid type"])

    with pytest.raises(ShiftValidationError):
        test = Test(**{"lst": [1, 2, "Invalid type"]})

def test_tuple():
    class Test(Shift):
        tup: tuple

    test = Test(tup=("hello", 10))
    assert test.tup == ("hello", 10)

    test = Test(**{"tup": ("hello", 10)})
    assert test.tup == ("hello", 10)

    with pytest.raises(ShiftValidationError):
        test = Test(tup="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"tup": "Invalid type"})

    class Test(Shift):
        tup: tuple[str, int]

    with pytest.raises(ShiftValidationError):
        test = Test(tup=("hello", "Invalid type"))

    with pytest.raises(ShiftValidationError):
        test = Test(**{"tup": ["hello", "Invalid type"]})

def test_set():
    class Test(Shift):
        st: set

    test = Test(st={1, 2, 3})
    assert test.st == {1, 2, 3}

    test = Test(**{"st": {1, 2, 3}})
    assert test.st == {1, 2, 3}

    with pytest.raises(ShiftValidationError):
        test = Test(st="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"st": "Invalid type"})

    class Test(Shift):
        st: set[int]

    with pytest.raises(ShiftValidationError):
        test = Test(st={1, 2, "Invalid type"})

    with pytest.raises(ShiftValidationError):
        test = Test(**{"st": [1, 2, "Invalid type"]})

def test_frozenset():
    class Test(Shift):
        fset: frozenset

    test = Test(fset=frozenset([1, 2, 3]))
    assert test.fset == frozenset([1, 2, 3])

    test = Test(**{"fset": {1, 2, 3}})
    assert test.fset == {1, 2, 3}

    with pytest.raises(ShiftValidationError):
        test = Test(fset="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"fset": "Invalid type"})

    class Test(Shift):
        fset: frozenset[int]

    with pytest.raises(ShiftValidationError):
        test = Test(fset=frozenset([1, 2, "Invalid type"]))

    with pytest.raises(ShiftValidationError):
        test = Test(**{"fset": {1, 2, "Invalid type"}})

def test_dict():
    class Test(Shift):
        dct: dict

    test = Test(dct={"Hello": 10})
    assert test.dct["Hello"] == 10

    test = Test(**{"dct": {"Hello": 10}})
    assert test.dct["Hello"] == 10

    with pytest.raises(ShiftValidationError):
        test = Test(dct="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"dct": "Invalid type"})

    class Test(Shift):
        dct: dict[str, int]

    with pytest.raises(ShiftValidationError):
        test = Test(dct={"Hello": "Invalid type"})

    with pytest.raises(ShiftValidationError):
        test = Test(**{"dct": {"Hello": "Invalid type"}})

def test_bytes():
    class Test(Shift):
        bts: bytes

    test = Test(bts=b"Hello")
    assert test.bts == b"Hello"

    test = Test(**{"bts": b"Hello"})
    assert test.bts == b"Hello"

    with pytest.raises(ShiftValidationError):
        test = Test(bts="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"bts": "Invalid type"})

def test_bytearray():
    class Test(Shift):
        bts_arr: bytearray

    test = Test(bts_arr=bytearray(b"Hello"))
    assert test.bts_arr == bytearray(b"Hello")

    test = Test(**{"bts_arr": bytearray(b"Hello")})
    assert test.bts_arr == bytearray(b"Hello")

def test_any():
    class Test(Shift):
        any: Any

    test = Test(any=1)
    assert test.any == 1

    test = Test(**{"any": 1})
    assert test.any == 1

    test = Test(any="Hello")
    assert test.any == "Hello"

    test = Test(**{"any": "Hello"})
    assert test.any == "Hello"

def test_union():
    class Test(Shift):
        union: Union[str, int]

    test = Test(union=10)
    assert test.union == 10

    test = Test(**{"union": 10})
    assert test.union == 10

    test = Test(union="Hello")
    assert test.union == "Hello"

    test = Test(**{"union": "Hello"})
    assert test.union == "Hello"

    with pytest.raises(ShiftValidationError):
        test = Test(union=3.14)

    with pytest.raises(ShiftValidationError):
        test = Test(**{"union": 3.14})

def test_optional():
    class Test(Shift):
        optional: Optional[bool]

    test = Test()
    assert test.optional is None

    test = Test(**{})
    assert test.optional is None

    test = Test(optional=True)
    assert test.optional is True

    test = Test(**{"optional": True})
    assert test.optional is True

    with pytest.raises(ShiftValidationError):
        test = Test(optional="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"optional": "Invalid type"})

def test_forward_ref():
    class Test(Shift):
        forward_ref: "ForwardTest"

    class ForwardTest(Shift):
        ref: int

    test = Test(forward_ref=ForwardTest(ref=10))
    assert test.forward_ref.ref == 10

    test = Test(**{"forward_ref": {"ref": 10}})
    assert test.forward_ref.ref == 10

    with pytest.raises(ShiftValidationError):
        test = Test(forward_ref="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"forward_ref": "Invalid type"})

    with pytest.raises(ShiftValidationError):
        test = Test(forward_ref=ForwardTest(ref="Invalid type"))

    with pytest.raises(ShiftValidationError):
        test = Test(**{"forward_ref": {"ref": "Invalid type"}})

def test_function():
    def f(val: int) -> int:
        return val + 1

    class Test(Shift):
        function: Callable[[int], int]

    test = Test(function=f)
    assert test.function(1) == 2

    test = Test(**{"function": f})
    assert test.function(1) == 2

    with pytest.raises(ShiftValidationError):
        test = Test(function="Invalid type")

    with pytest.raises(ShiftValidationError):
        test = Test(**{"function": "Invalid type"})
