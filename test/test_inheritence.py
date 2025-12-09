import pytest
from typing import Any, Union, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



def test_model_name():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert repr(test).startswith("Test")

def test_model_type():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert isinstance(test, Test)

def test_pre_init():
    class Test(Shift):
        val: int

        def __pre_init__(self, data: dict[str, Any]) -> None:
            val = data.get("val")
            if val is not None:
                data["val"] = val + 1

    test = Test(val=10)
    assert test.val == 11

    class Test(Shift):
        val: int

        def __pre_init__(self, data: dict[str, Any]) -> None:
            val = data.get("val")
            if val is not None:
                self.val = val + 1

    test = Test(val=10)
    assert test.val == 10

def test_post_init():
    class Test(Shift):
        val: int

        def __post_init__(self, data: dict[str, Any]) -> None:
            self.val += 1

    test = Test(val=10)
    assert test.val == 11

def test_has_repr():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert has_repr(test)

def test_has_serializer():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert has_serializer(test)

def test_eq():
    class Test(Shift):
        val: int

    test1 = Test(val=10)
    test2 = Test(val=10)

    assert test1 == test2

    test1 = Test(val=10)
    test2 = Test(val=20)
    assert test1 != test2

def test_copy():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert test.__copy__() == test

# def test_deepcopy():

def test_has_decorators():
    class Test(Shift):
        val: int

    test = Test(val=10)
    assert hasattr(test, "__validators__")
    assert hasattr(test, "__setters__")
    assert hasattr(test, "__reprs__")
    assert hasattr(test, "__serializers__")

def test_all_data_passed():
    class Test(Shift):
        __shift_config__ = ShiftConfig(allow_unmatched_args=True)
        val: int

        def __pre_init__(self, data: dict[str, Any]) -> None:
            if data["other"]:
                data["val"] += 1

    test = Test(val=10, other=True)
    assert test.val == 11