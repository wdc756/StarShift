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
    class Test(ShiftModel):
        val: int

    test = Test(val=InvalidType)

if __name__ == '__main__':
    run()