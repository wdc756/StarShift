import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *



InvalidType = object()



def run():
    class Test(Shift):
        val: int
        _private: int = 42

        @shift_setter('_private')
        def set_val(self, field: ShiftField, info: ShiftInfo):
            self._private = self.val

    test = Test(val=81)
    print(test._private)
    assert test._private == 81

if __name__ == '__main__':
    run()