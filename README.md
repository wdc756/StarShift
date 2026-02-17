# Star Shift



A lightweight python validation library aiming to make "better dataclasses" by mimicking 
Pydantic's `BaseModel` validation, but adding extensive customization and control.

Created by William Dean Coker.



## Installation

This project is hosted on the PyPi as `starshift`, so simply call

```bash
pip install starshift
```

to get the latest version. Alternatively the latest version will always be hosted in the
[GitHub](https://github.com/wdc756/StarShift) repository 
[here](https://github.com/wdc756/StarShift/releases).

### Custom Builds
For custom builds refer to this 
[guide](https://github.com/wdc756/StarShift/blob/main/docs/build.md).



## Quickstart Guide

Starshift has the ability to handle simple validation cases like just checking that all vars
have the right type:

```python
from starshift import Shift

class Person(Shift):
    name: str
    age: int

# This works:
_ = Person(name='John', age=42)

# But these all fail:
_ = Person(age=42) # Missing name
_ = Person(name='John') # Missing age
_ = Person(name=81, age=42) # name str set to int
_ = Person(name='John', age='Doe') # age int set to str
```

all classes can be set with dicts:

```python
from typing import Optional
from starshift import Shift

class User(Shift):
    name: str
    age: int

class Task(Shift):
    name: str
    description: Optional[str]
    assignee: User

# These create the same thing
_ = Task(name='Fix code', assignee=User(name='John', age=42))
dct = {
    'name': 'Fix code',
    'assignee': {
        'name': 'John',
        'age': 42
    }
}
_ = Task(**dct)
```

comprehensive value checks:

```python
from starshift import Shift, ShiftField

class User(Shift):
    name: str = ShiftField(min_len=1)
    age: int = ShiftField(ge=0)
    email: str = ShiftField(pattern=r'^[\w.-]+@[\w.-]+\.\w+$')

# This is valid:
_ = User(name='John Doe', age=42, email='jd@mail.com')

# This fails:
_ = User(name='', age=-42, email='email')
# - name too short
# - age too young
# - email not valid format
```

fully customizable engine:

```python
from starshift import Shift, ShiftField, shift_validator, shift_transformer

valid_hosts = [
    'localhost',
    '192.168.1.253',
    '1.1.1.1'
]


def can_connect(host, port):
    # ...
    return True


def get_api_keys_for_host(host, port):
    # ...
    return ['key1', 'key2']


class Server(Shift):
    host: str = 'localhost'
    port: int = ShiftField(default=8080, ge=0, le=65535)
    _api_keys: list[str]

    @shift_transformer('host')
    def transform_host(self, val):
        return val.strip()
    
    @shift_validator('host')
    def validate_host(self, val):
        return val in valid_hosts

    def __post_init__(self):
        if not can_connect(self.host, self.port):
            raise ValueError(f'Could not connect to {self.host}:{self.port}')
        self._api_keys = get_api_keys_for_host(self.host, self.port)

    def get_api_keys(self):
        return self._api_keys


# This works
server = Server(host='   192.168.1.253', port=22)
_ = server.host # `192.168.1.253`
_ = server.port # `22`
_ = server.get_api_keys()  # Returns `['key1', 'key2']`

# This fails
_ = Server(host='8.8.8.8', port=7000, _api_keys=['key'])
# - host isn't in list
# - port is out of range
# - can't set private vars without config
```

custom type support:

```python
from starshift import Shift, ShiftType


```

and all classes have default `repr`, `serializer`, `eq`, and more.

### Full Quickstart Guide 

Above are just a few examples for how to use starshift, but 
[this](https://github.com/wdc756/StarShift/blob/main/docs/quickstart.md) is the full quickstart
that covers all major features and how/where to use them.



## API

The StarShift API can be found 
[here](https://github.com/wdc756/StarShift/blob/main/docs/api.md).



## License

This project is licensed under the MIT license