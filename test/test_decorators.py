import pytest
from typing import Any, Union, Optional

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



def test_shift_validator():
    class Test(Shift):
        val: int

        @shift_validator('val')
        def validate_val(self, data: dict[str, Any], field) -> bool:
            return data['val'] > 0

    test = Test(val=10)
    with pytest.raises(ShiftValidationError):
        test = Test(val=0)

def test_shift_setter():
    class Test(Shift):
        val: int

        @shift_setter('val')
        def set_val(self, data: dict[str, Any], field) -> None:
            setattr(self, field, data['val'] + 1)

    test = Test(val=10)
    assert test.val == 11

def test_shift_repr():
    class Test(Shift):
        val: int

        @shift_repr('val')
        def repr_val(self, field: str, val: Any, default: Any) -> str:
            return "custom"

    test = Test(val=10)
    assert repr(test) == 'Test(val=custom)'

def test_shift_serializer():
    class Test(Shift):
        val: int

        @shift_serializer('val')
        def serialize_val(self, field: str, val: Any, default: Any) -> Any:
            return "custom"

    test = Test(val=10)
    assert test.serialize() == {'val': "custom"}
