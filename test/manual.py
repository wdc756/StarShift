from typing import Any, Optional, Union, List, Dict
from starshift import *

class Mini(Shift):
    string: str
    integer: int

class Iter(Shift):
    """Iterates over a range of values"""

    __shift_config__: ShiftConfig = ShiftConfig()



    value: Any = None
    start: Any
    end: Any
    step: Any

    mini: Mini




    @shift_repr('value')
    def repr_value(self, field, val, default) -> Union[str, None]:
        if self.value != self.start:
            return f"value={self.value}"
        return None

    @shift_serialize('value')
    def to_dict_value(self, field, val, default) -> Union[dict[str, Any], None]:
        if self.value != self.start:
            return {"value": self.value}
        return None


    def __post_init__(self, data: dict[str, Any]) -> None:
        # Automatically set value if not provided
        if self.value is None:
            self.value = self.start

        # Make sure whatever types value and step are, they can be added together
        try:
            _ = self.value + self.step
        except Exception as e:
            raise TypeError(f"Iter: could not increment value by step")

        # Make sure whatever types value, start, and end are they can be compared
        try:
            _ = self.value <= self.start
            _ = self.value <= self.end
            _ = self.value <= self.step
        except Exception as e:
            raise TypeError("Iter: could not compare value, start, end, or step")

        # If step is 0, we can't progress, so throw
        if self.step == 0:
            raise ValueError("Iter: step cannot be zero.")

        # If step +, value must be > start and < end
        if self.step > 0:
            if self.value < self.start:
                raise ValueError("Iter: value must be > start.")
            if self.value > self.end:
                raise ValueError("Iter: value must be < end.")
        # If step -, value must be < start and > end
        else:
            if self.value > self.start:
                raise ValueError("Iter: value must be < start.")
            if self.value < self.end:
                raise ValueError("Iter: value must be > end.")

        # If start > end and step > 0 the range is invalid, so throw
        if self.start > self.end and self.step > 0:
            raise ValueError("Iter: start must be < end when stepping up.")
        # If start < end and step < 0 the range is invalid, so throw
        if self.start < self.end and self.step < 0:
            raise ValueError("Iter: start must be > end when stepping down.")



    def __len__(self) -> Union[int, None]:
        """Return the number of iterations left in the range"""
        return self.count_iterations()

    def count_iterations(self) -> int:
        """Return the number of iterations left in the range"""
        return (self.end - self.value) // self.step + 1

    def next(self) -> bool:
        """Increments the current iterator value to the next and returns True if it had space to increment, False otherwise"""
        if self.step > 0:
            if self.value < self.end:
                self.value += self.step
                return True
            else:
                self.value = self.start
                return False
        else:
            if self.value > self.end:
                self.value += self.step
                return True
            else:
                self.value = self.start
                return False

    def last(self) -> bool:
        """Decrement the current token value to the last and returns True if it had space to decrement, False otherwise"""
        if self.step > 0:
            if self.value > self.start:
                self.value -= self.step
                return True
            else:
                self.value = self.end
                return False
        else:
            if self.value < self.start:
                self.value -= self.step
                return True
            else:
                self.value = self.end
                return False

    def __iter__(self) -> Iter:
        """Used to iterate over `for item in instance` syntax"""
        return self

    def __next__(self) -> Any:
        """Used by iterables to get the next value until StopIteration is raised"""
        if self.next():
            return self.value
        else:
            raise StopIteration



def manual_test():
    test = Iter(start=1, end=10, step=2, mini=Mini(string="hello", integer=10))
    print(repr(test))
    print(test.serialize())
    test.next()
    print(repr(test))
    print(test.serialize())

if __name__ == '__main__':
    manual_test()