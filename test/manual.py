import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()



def run():
    shift_config = ShiftConfig(include_default_fields_in_serialization=True)

    class Test(Shift):
        __shift_config__ = shift_config
        _val: int

    test = Test(_val=42)
    assert repr(test) == f"Test(__shift_config__={shift_config}, _val=42)"
    assert test.serialize() == {"__shift_config__": shift_config, "_val": 42}

if __name__ == '__main__':
    run()