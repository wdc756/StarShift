import pytest

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

    with pytest.raises(TypeError):
        test = B(nest="Invalid Type")

    with pytest.raises(TypeError):
        test = B(nest=A(val="Invalid Type"))

    with pytest.raises(TypeError):
        test = B(**{"nest": "Invalid Type"})

    with pytest.raises(TypeError):
        test = B(**{"nest": {"nest": "Invalid Type"}})

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

    with pytest.raises(TypeError):
        test = C(nested="Invalid Type")

    with pytest.raises(TypeError):
        test = C(nested=B(nest="Invalid Type"))

    with pytest.raises(TypeError):
        test = C(nested=B(nest=A(val="Invalid Type")))

    with pytest.raises(TypeError):
        test = C(**{"nested": "Invalid Type"})

    with pytest.raises(TypeError):
        test = C(**{"nested": {"nest": "Invalid Type"}})

    with pytest.raises(TypeError):
        test = C(**{"nested": {"nest": {"val": "Invalid Type"}}})

def test_recursive_nest():
    class A(Shift):
        nest: 'A'

