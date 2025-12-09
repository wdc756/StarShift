import pytest
from typing import Any, Union, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



# def test_none():
#     class Test(Shift):
#         val: None
#
#     test = Test(val=None)
#     assert repr(test) == "Test(val=None)"
#     assert test.serialize() == {"val": None}

def test_bool():
    class Test(Shift):
        val: bool

    test = Test(val=True)
    assert repr(test) == "Test(val=True)"
    assert test.serialize() == {"val": True}

def test_int():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert repr(test) == "Test(val=10)"
    assert test.serialize() == {"val": 10}

def test_float():
    class Test(Shift):
        val: float

    test = Test(val=3.14)
    assert repr(test) == "Test(val=3.14)"
    assert test.serialize() == {"val": 3.14}

def test_str():
    class Test(Shift):
        val: str

    test = Test(val="hello")
    assert repr(test) == "Test(val=\"hello\")"
    assert test.serialize() == {"val": "hello"}

def test_list():
    class Test(Shift):
        val: list

    test = Test(val=[1, 2, 3])
    assert repr(test) == "Test(val=[1, 2, 3])"
    assert test.serialize() == {"val": [1, 2, 3]}

def test_tuple():
    class Test(Shift):
        val: tuple

    test = Test(val=("hello", 10))
    assert repr(test) == "Test(val=('hello', 10))"
    assert test.serialize() == {"val": ("hello", 10)}

def test_dict():
    class Test(Shift):
        val: dict

    test = Test(val={"hello": 10})
    assert repr(test) == "Test(val={'hello': 10})"
    assert test.serialize() == {"val": {"hello": 10}}

def test_bytes():
    class Test(Shift):
        val: bytes

    test = Test(val=b"hello")
    assert repr(test) == "Test(val=b'hello')"
    assert test.serialize() == {"val": b"hello"}
