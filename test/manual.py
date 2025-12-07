from typing import Any, Optional, Union, List, Dict
from starshift import *

class Iter(Shift):
    """Iterates over a range of values"""

    __shift_config__ = ShiftConfig(verbosity=3)


    value: Any = None
    start: Any
    end: Any
    step: Any



def manual_test():
    test = Iter(start=1, end=10, step=2)
if __name__ == '__main__':
    manual_test()