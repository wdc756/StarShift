import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()



def test_changing_fields():
    class Test(Shift):
        val: int

    test = Test(val=42)
    assert test.val == 42
    test = Test(val=81)
    assert test.val == 81