from starshift import shift_validatorfrom starshift import shift_setterfrom typing import AnyStrfrom doctest import Example

# Star Shift



A lightweight python class validation library that mimics pydantic's BaseModel dict 
casting validation.

Created by William Dean Coker

### This is not uploaded yet, the link is dead for now

This package is on the [PyPI](<add link here>), and can be installed with:

```bash
pip install starshift
```


# Under development

## This library is nearly complete, but is still early access with bugs


---



## Quick Start


Any class you want to automatically validate, simply set as a subclass of `Shift`:

```python
from starshift import *

class Example(Shift):
    string: str
    integer: int
    float: float

# This works
example = Example(string='Hello World!', integer=10, float=3.14)

# This throws a TypeError
example = Example(string='Invalid type', integer="Invalid type", float=3.14)

# This throws a ValueError
example = Example(string="Missing arguments!")
```


### Important Note!

Inheriting `Shift` will overwrite the default `__init__` and function, and attempting to use
it will cause several errors in the `Shift` validation process! However `Shift` will
automatically call two functions when you make a class instance, `__pre_init__` (before
validation) and `__post_init__` after (see documentation for more info). Additionally
`Shift` relies on `__init_subclass__`, so creating a subclass with `Shift` and using that
as a base class that implements `__init_subclass__` could cause problems.



---



## Documentation


### ShiftConfig

`ShiftConfig` provides a method to control how `Shift` validates subclasses, allowing you
to turn off/on certain features or validation standards. To set one, either change the 
global `DEFAULT_SHIFT_CONFIG` which will be used by all `Shift` instances, or set it on a
per-class basis using the `__shift_config__` key:

```python
class Example(Shift):
    # This will disable the `Any` type, meaning all attributes that are `Any` will throw errors
    __shift_config__ = ShiftConfig(allow_any=False) 
```

#### Attributes

##### `verbosity: int = 0`
Controls how much diagnostic output is produced.
- `0` – No debug output  
- `1` – Validation step messages  
- `2` – Validation-per-variable messages  
- `3` – All configuration and attribute messages

##### `do_validation: bool = True`
Determines whether variables are validated on initialization.
- `False` – Skip validation and **do not set** variables  
- `True` – Validate variables and then set them

##### `allow_unmatched_args: bool = False`
Handles arguments that do not correspond to class attributes.
- `False` – Raise an error when an unknown argument is passed  
- `True` – Create a new attribute for any unknown argument

##### `allow_any: bool = True`
Controls whether variables may use the `Any` type.
- `False` – Reject variables annotated as `Any`  
- `True` – Allow and validate `Any`  

##### `allow_defaults: bool = True`
Controls the use of default values.
- `False` – Reject variables whose default is not `None`  
- `True` – If no value is provided, attempt validation using the default  

##### `allow_non_annotated: bool = True`
Controls handling of variables without annotations.
- `False` – Reject variables without a type annotation  
- `True` – Allow setting variables with no annotation (validated only if a validator is defined)  

##### `allow_shift_validators: bool = True`
Controls custom per-variable validators (`@shift_validator(var)`).
- `False` – Reject variables that have a custom shift validator  
- `True` – Invoke the custom validator; the variable is valid only if it returns `True`  

##### `shift_validators_have_precedence: bool = True`
Determines whether custom validators override defaults.
- `False` – If a custom validator returns `True`, run default validation afterward  
- `True` – If a custom validator returns `True`, accept the value immediately  

#### `use_shift_validators_first: bool = False`
Controls the order of validation when a shift_validator exists for a field
- `False`: If shift_validator(var) is not `None`, use it after default validation
- `True`: If shift_validator(var) is not `None`, use it before default validation

##### `allow_shift_setters: bool = True`
Controls custom setters (`@shift_setter(var)`).
- `False` – Reject variables with a custom shift setter  
- `True` – Invoke the custom setter  

##### `allow_nested_shift_classes: bool = True`
Controls validation of nested `Shift` subclasses.
- `False` – Reject fields that are themselves `Shift` subclasses  
- `True` – Validate nested `Shift` subclasses normally


### ShiftValidator

`shift_validator` is a function decorator you can apply to `Shift` subclass functions
to validate vars using user-defined logic:

```python
class Example(Shift):
    integer: int

    @shift_validator('integer')
    def _validate_integer(self, data: dict[str, Any], field: str) -> bool:
        return 0 <= data.get(field) <= 10

# This will fail
example = Example(integer=12)
```

You can even have a single shift_validator validate multiple fields:

```python
class Example(Shift):
    integer: int
    float: float

    @shift_validator('integer', 'float')
    def _validate_number(self, data: dict[str, Any], field: str) -> bool:
        return 0 <= data.get(field) <= 10

# This will fail because of float, but integer is still validated
example = Example(integer=3, float=-3.14)
```

#### Usage

For an `@shift_validator(field)` to work properly, all functions with the decorator
must accept:
- `self`: the class instance being validated
- `data`: the arguments used to build the class instance
- `field`: the field being validated (used mainly when there are multiple fields for 
1 shift_validator)

Additionally the function must return `True` otherwise `Shift` will assume the 
argument was invalid.


## ShiftSetter

`shift_setter` is a function decorator that functions the same as `shift_validator`, 
except this decorator is expected to set the value after validation, and doesn't 
need to return anything:

```python
class Example(Shift):
    integer: int

    @shift_setter('integer')
    def _set_integer(self, data: dict[str, Any], field: str) -> None:
        self.integer = data.get(field) + 10

# This will have integer == 20
example = Example(integer=10)
```

#### Usage

For an `@shift_setter(field)` to work properly, all functions with the decorator
must accept:
- `self`: the class instance being validated/set
- `data`: the arguments used to build the class instance
- `field`: the field being set (used mainly when there are multiple fields for 
1 shift_validator)


### Shift

`Shift` is the main base class that holds all the validation logic. To make any class
automatically validate, set that class to inherit `Shift`:

```python
class Example(Shift):
    validated_integer: int

# This will fail
example = Example(validated_integer=3.14)
```

#### Parameters

##### `__shift_config__: ShiftConfig = None`
A ShiftConfig instance used to configure Shift validation, if left as `None` it will take 
the value of `DEFAULT_SHIFT_CONFIG` - which can be globally configured

#### `__pre_init__(data)`
A def that Shift will call prior to validation, passing in the constructor dict data

#### `@shift_validator(var)`
A decorator that marks a class def as a validator for `var` - this def must return a 
bool for its validation

#### `@shift_setter(var)`
A decorator that marks a class def as a setter for `var` - returned values are discarded

#### `__post_init__(data)`
A def that Shift will call after validation, passing in the constructor dict data


---


## Other Notes


### Dict Parameterization

All `Shift` subclasses allow you to validate either using arguments or dictionaries:

```python
class Example(Shift):
    integer: int

# These do the same validation checks
args_example = Example(integer=10)
dict_example = Example(**{"integer": 10})
```

This is the real power of StarShift, as you can write massive dictionaries or import
them from JSON and pass all the data through a simple `Class(**data)` statement to
validate everything in one go.


### Validation/Setting Order

The order attributes are defined in is the same order they will be validated and set
in:

```python
class Example(Shift):
    integer: int
    float: float
    list = [False, True]
    string: str
    dict = {"hello": 0, "world": 1}
```

In this case the order of validation/setting will be:
1. Validate `integer`
2. Set `integer`
3. V/S `float`
4. V/S `string`
5. Validate `list` if @shift_validator
6. Set `list`
7. V/S `dict`

It's important to note here that all annotated attributes (those with type
annotations) are always validated and set before all un-annotated attributes.


### Example Usage

For an example on how to use StarShift on a larger scale, check out one of my other
python libraries called [StarTrace](https://github.com/wdc756/StarTrace).


---


## License

This project is under the GNU General Public License, feel free to modify or distribute this 
code however you see fit

<font color=#6E6E6E>Though a little link back to here would be nice</font>