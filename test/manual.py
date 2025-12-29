import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime, timedelta



InvalidType = object()



def run():
    class Test(Shift):
        val = 42

    _missing = Missing()
    print(_missing)
    print(type(_missing))
    test = Test()
    assert test.val == 42

if __name__ == '__main__':
    run()