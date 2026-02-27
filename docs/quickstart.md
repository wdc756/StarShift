# StarShift Quickstart Guide



## Introduction To StarShift

### Why do we need validation?
The main reason for StarShift's existence is the same reason Pydantic exists: Python is
often TOO flexible:

```python
from dataclasses import dataclass

# For example, I can define a class with an int
@dataclass
class Class:
    val: int

# but can set it with a string value
cls = Class(val='Hello There!')
_ = cls.val # Will be `'Hello There!'`
```

Now while this might be an odd problem to run into while instantiating classes like above, 
as modern IDEs and type checkers can catch these errors. The problem happens when we want to 
do something like this:

```python
from dataclasses import dataclass

@dataclass
class Class:
    val: int

dct = {
    'val': 'Hello There!'
}
cls = Class(**dct)
_ = cls.val # `'Hello There!'`
```

The problem here is that unlike before the IDE or type checkers aren't able to correctly validate
this instantiation. This problem becomes even worse whenever you are loading dicts from external 
files, potentially made by users who don't know the right class variables, or who just make a 
simple mistake.

```json
{
  "val": "Hello There!"
}
```

If we were to load this json into the class instance, we would get an incorrectly configured class
and no errors or warnings. Now admittedly this example doesn't seem too bad, after all it's just a value.
However, what if we were loading config files into an early warning program that checks nuclear reactor 
devices for invalid or dangerous readings? What if someone incorrectly configures a config file to have an
IP address that doesn't lead anywhere, or doesn't exist? Sure this problem COULD be solved by enforcing
rigorous type checks for every singe class and variable, but that leads to hundreds of lines of boilerplate
making future work on the program more difficult. But no matter what, we need validation for config files.

### Why Not Use Pydantic?

So if we need validation, why not use Pydantic, the industry standard for this type of work, and so
much more? Well Pydantic is useful, but it also has some issues depending on the use case. For 
large projects and enterprise, Pydantic is a no-brainer with it's deep integration capabilities,
and the fact that its validation loop is compiled means it can handle 50k - 250k validations per second. 

However, Pydantic is MASSIVE compared to StarShift, and is roughly 50k lines while StarShift has 
just under 2k. And while the fact that it's compiled is amazing for 90% of use cases, it does 
mean if you need to deploy across multiple platforms that maintaining the correct versions 
and builds becomes cumbersome. And maybe most importantly, Pydantic is very rigid in how it
handles types and validation logic. There's not a good way to override it for most small users
who can't afford the time or effort to make their own Pydantic validators. Wheras StarShift is
easily extendable and customizable.

So the question of whether to use StarShift or Pydantic comes down to what your use case is:

| Use Case            | Should Use Pydantic                                               | Should Use StarShift                                     |
|---------------------|-------------------------------------------------------------------|----------------------------------------------------------|
| Small hobby project | If the classes are straightforward to validate                    | If classes require custom validation or handling         |
| Small work project  | Use company preference, unlesss...                                | ...classes require custom validation                     |
| Large hobby project | If you need the speed and classes are straightforward to validate | If you don't need the speed and need customization       |
| Large work project  | Use company preference                                            | Don't use unless you can't use Pydantic, for some reason |

I, William Dean Coker, choose to make StarShift because I worked at a small company that 
didn't need the speed and needed custom validation logic, and we develop applications that run
on a wide variety of machines, and maintaining different Pydantic packages did not seem
like a worthy investment of our time. But I didn't want to write tons of boilerplate, thus
StarShift was born.

### Why Not Write Custom Validation

Say you want to make a basic `User` class to manage people in python. You could create something like this:

```python
class User:
    name: str
    age: int
    email: str
```

And this is good as long as your code is good, and most IDEs will catch errors for you. But if you're loading
data from external config files or python `dict`, then you could very easily run into invalid class 
instances, where `int` are set to `str`, and `str` to `int`. So you write this: 

```python
class User:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email
```

This helps as now missing arguments will raise errors, and we get warnings when setting invalid types.
But how do you guard against obviously incorrect values like `age=-42` or 
`name=According to all known laws of aviation...`, or `email=not_an_email.exe`? Well now you need checks:

```python
import re

class User:
    def __init__(self, name: str, age: int, email: str):
        if len(name) == 0 or 64 < len(name):
            raise ValueError(f"`len(name)`={len(name)} out of range")
        if age < 0 or 128 < age:
            raise ValueError(f"`age`={age} out of range")
        if not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
            raise ValueError('`email` is not valid')
        
        self.name = name
        self.age = age
        self.email = email
```

This works and covers all our cases, but if we follow this pattern then we need to do this validation for
every field of every class, which depending on the project could be simply too much work. But if we
use StarShift we can turn the above init logic into just this:

```python
from starshift import ShiftModel, ShiftField


class User:
    name: str = ShiftField(min_len=1, max_len=128)
    age: int = ShiftField(ge=0, le=128)
    email: str = ShiftField(pattern=r'^[\w.-]+@[\w.-]+\.\w+$')
```

This does the exact same validation, but in 3 lines instead of 9, and allows us to use all the other
StarShift features like automatic deserialization, representation, and more.



## Introduction To Using StarShift

### Making A Simple StarShift-Validated Class

Let's go back to the `User` class I used earlier:

```python
class User:
    name: str
    age: int
    email: str
```

In this example, we need to make sure that..
1. attributes have the right type
2. attributes have reasonable values

We can solve the 1st problem just by making `User` and subclass of `ShiftModel`:

```python
from starshift import ShiftModel


class User(ShiftModel):
    name: str
    age: int
    email: str
```

Then to solve the 2nd problem we can set the values equal to `ShiftFields`:

```python
from starshift import ShiftModel, ShiftField


class User(ShiftModel):
    name: str = ShiftField(min_len=1, max_len=64)
    age: int = ShiftField(gt=0, lt=128)
    email: str = ShiftField(pattern=r'^[\w.-]+@[\w.-]+\.\w+$')
```

Now we can automatically validate instances of `User`
```python
# This works
_ = User(name='John', age=42, email='john@email.com')

# These fail
_ = User(name='John') # Missing fields
_ = User(name=42, age='John', email=['john@email.com']) # Invalid types
_ = User(name='', age=42, email='john@email.com') # name too short
_ = User(name='', age=360, email='john@email.com') # age too big
_ = User(name='John', age=42, email='@email.com') # invalid email format
```

Additionally, we can now instantiate `User` using dicts:

```python
dct = {
    'name': 'John',
    'age': 42,
    'email': 'john@email.com'
}

_ = User(**dct)
```

### An Introduction to `ShiftModel`

`ShiftModel` is the main class in StarShift, and one you will always need to import, as
without it there's not much point in using StarShift. Any time you define a `ShiftModel` 
subclass you need to note a few things:

#### 1. `ShiftModel` overrides `__init__`, so you must construct instances with kwargs

```python
from starshift import ShiftModel


class Class(ShiftModel):
    val: int


# This works
_ = Class(val=42)
# This does not
_ = Class(42)


# This will override ShiftModel, and is not recommended
class BadClass(ShiftModel):
    def __init__(self, val: int):
        self.val = val


# Will technically work, but will break other ShiftModel functions
_ = BadClass(42)
```

To some this may seem like an arbitrary constraint, but to me I see it as enforcing
a standard of self-documenting code. No matter what you always know what you're setting
each attribute to by nature of how ShiftModel expects inputs. And if you still need
some sort of `__init__` functionality or on-instantiation checks, you can use
`__pre_init__` and `__post_init__` - see the 
[ShiftModel API](https://github.com/wdc756/StarShift/blob/main/docs/api/shift.md) for more info.

#### 2. `ShiftModel` only works when you define type hints or defaults

If you create a class with an unannotated non-default attribute, ShiftModel can't manage the
attribute:

```python
from starshift import ShiftModel


class Class(ShiftModel):
    val
```

Now not even python will let you do this, but a good practice with starshift (and in
general) is to **always annotate types**. Even if you need the type to flexible, just 
use `Any`:

```python
from typing import Any
from starshift import ShiftModel


class Class(ShiftModel):
    val: Any
```

#### 3. `ShiftModel` manages classes via 5 processes...

1. Transformation: Pre-validation modifications
2. Validation - Ensuring data is correct
3. Setting - Storing values in class attributes
4. Representation - String representations of instances
5. Serialization - Dict representations of instances

#### ...and 4. `ShiftModel` processes can be overridden / extended on a global or per-attribute level

```python
# Main classes
from starshift import ShiftModel, ShiftField, shift_transformer, shift_validator


class User(ShiftModel):
    # This checks if the str matches the regex pattern, and hides field in repr
    email: str = ShiftField(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                            repr_exclude=True)
    # This field will be called user_age in repr
    age: int = ShiftField(repr_as='user_age')
    # This checks if the name is empty
    name: str = ShiftField(min_len=1)

    # If age is invalid set to valid number
    @shift_transformer('age')
    def transform_age(self, val):
        return val if val > 0 else 42

    @shift_validator('email')
    def validate_email(self, val):
        return val in email_database

    def __post_init__(self, info):
        # Send confirmation email
        send_email(self.email, f"Hello {self.name}, this is a...")
```

See the [API](https://github.com/wdc756/StarShift/blob/main/docs/api.md) for more
info on each of the overrides used.

### An Introduction to `ShiftField`

The 2nd most useful feature of StarShift is `ShiftField`. It has a set
of basic checks and validation extensions that are generally applicable
and can validate 90% of simple cases.

```python
from starshift import ShiftModel, ShiftField


class Class(ShiftModel):
    # This validates the int is between 0 and 42
    index: int = ShiftField(ge=0, le=42)
    # This validates the str is not empty but not over 32 chars
    string: str = ShiftField(min_len=1, max_len=32)
    # This checks if the string matches a regex pattern
    email: str = ShiftField(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
```

But these are just a few of the options available. Go 
[here](https://github.com/wdc756/StarShift/blob/main/docs/api/shiftfield.md)
to see the full list of checks.

### Understanding StarShift's design philosophy

StarShift is built around the core idea of trusting class definitions, but not
trusting class instantiation arguments. StarShift will always assume the class
definition was written correctly, thus will not check for errors like infinite
nesting or circular references. All Starshift will do is validate data passed
during class instance creation.

Another core pillar of StarShift is type extendability and custom logic. The original
reason StarShift was made was because Pydantic didn't supply the necessary 
customization in the form of defining custom per-type logic or per-field validation.

#### ShiftModel Processes

All ShiftModel classes contain 5 processes:
1. Transformation
2. Validation
3. Setting
4. Representation
5. Serialization

When a class is created the first 3 processes will run, and then later the instance of
the class can be represented or serialized

### An Introduction To Overrides

Work in process, come back later...



## API

A full API is available [here](https://github.com/wdc756/StarShift/blob/main/docs/api.md)
that covers all aspects of StarShift and how to use each feature in far more detail.