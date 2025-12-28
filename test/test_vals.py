import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()



def test_default():
    class Test(Shift):
        val: int = 42

    test = Test()
    assert test.val == 42

def test_un_annotated():
    class Test(Shift):
        val = 42

    test = Test()
    assert test.val == 42

    test = Test(val=81)
    assert test.val == 81

def test_arbitrary_keys():
    class Test(Shift):
        val: int

    test = Test(val=42, arbitrary_key="hello there")
    assert test.val == 42
    assert not hasattr(test, "arbitrary_key")
