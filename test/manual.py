import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from abc import ABC, abstractmethod
from datetime import datetime, timedelta



InvalidType = object()



def run():
    """"""
    class Test(Shift):
        val: int = ShiftField(defer_set=True)

        def __pre_init__(self) -> None:
            self.val = 42

    test = Test(val=88)
    assert test.val == 42

if __name__ == '__main__':
    run()