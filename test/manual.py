import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime, timedelta



InvalidType = object()



def run():
    class Test(Shift):
        val: int | None = ShiftField(defer_transform=True, default=88)

    test = Test()
    assert test.val is Missing

if __name__ == '__main__':
    run()