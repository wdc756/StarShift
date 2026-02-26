import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime, timedelta



InvalidType = object()



def run():
    class Test(Shift):
        val: set[int]

    test = Test(val={4, 5, 6, 1, 2, 3})
    assert test.val == {4, 5, 6, 1, 2, 3}
    test = Test(**{"val": {4, 5, 6, 1, 2, 3}})
    assert test.val == {4, 5, 6, 1, 2, 3}

    with pytest.raises(ShiftError):
        _ = Test(val=InvalidType)
    with pytest.raises(ShiftError):
        _ = Test(**{"val": InvalidType})

    with pytest.raises(ShiftError):
        _ = Test(val={4, 5, 6, 1, 2, InvalidType})
    with pytest.raises(ShiftError):
        _ = Test(**{"val": {4, 5, 6, 1, 2, InvalidType}})

if __name__ == '__main__':
    run()