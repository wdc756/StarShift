import pytest
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



def test_single_nest():
    class A(Shift):
        val: int

    class B(Shift):
        nest: A

    test = B(nest=A(val=10))
    assert test.nest == A(val=10)

    test = B(**{"nest": {"val": 10}})
    assert test.nest == A(val=10)

    with pytest.raises(ShiftValidationError):
        test = B(nest="Invalid Type")

    with pytest.raises(ShiftValidationError):
        test = B(**{"nest": "Invalid Type"})

    with pytest.raises(ShiftValidationError):
        test = B(nest=A(val="Invalid Type"))

    with pytest.raises(ShiftValidationError):
        test = B(**{"nest": {"val": "Invalid Type"}})

def test_double_nest():
    class A(Shift):
        val: int

    class B(Shift):
        nest: A

    class C(Shift):
        nested: B

    test = C(nested=B(nest=A(val=10)))
    assert test.nested == B(nest=A(val=10))
    assert test.nested.nest == A(val=10)

    test = C(**{"nested": {"nest": {"val": 10}}})
    assert test.nested == B(nest=A(val=10))
    assert test.nested.nest == A(val=10)

    with pytest.raises(ShiftValidationError):
        test = C(nested="Invalid Type")

    with pytest.raises(ShiftValidationError):
        test = C(nested=B(nest="Invalid Type"))

    with pytest.raises(ShiftValidationError):
        test = C(nested=B(nest=A(val="Invalid Type")))

    with pytest.raises(ShiftValidationError):
        test = C(**{"nested": "Invalid Type"})

    with pytest.raises(ShiftValidationError):
        test = C(**{"nested": {"nest": "Invalid Type"}})

    with pytest.raises(ShiftValidationError):
        test = C(**{"nested": {"nest": {"val": "Invalid Type"}}})

def test_recursive_nest():
    class A(Shift):
        nest: 'A' = None

    a = A(nest=A())

    class A(Shift):
        nest: Optional['A'] = None

    a = A(nest=A())

    class A(Shift):
        nest: 'A'

    with pytest.raises(ShiftValidationError):
        a = A(nest=A())
