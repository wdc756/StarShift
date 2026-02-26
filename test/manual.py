import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime, timedelta



InvalidType = object()



def run():
    class Test(Shift):
        val = ShiftField(type=int)

    test = Test(val=42)
    assert test.val == 42

    test = Test(**{"val": 42})
    assert test.val == 42

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)

    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

if __name__ == '__main__':
    run()