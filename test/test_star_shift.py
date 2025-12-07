import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from starshift.star_shift import *


# Class examples
################


class Builtins(Shift):
    boolean: bool
    integer: int
    float: float
    string: str
    lis: list[int]
    tup: tuple[str, int]
    set: set[int]
    dct: dict[str, int]

class Mini(Shift):
    string: str
    integer: int

class Container(Shift):
    string: str
    mini: Mini

class MultiContainer(Shift):
    string: str
    mini_lis: list[Mini]
    mini_tup: tuple[str, Mini]
    mini_set: set[Mini]
    mini_dct: dict[str, Mini]

# We have to use this because any values in Init will be overwritten after pre_init
global_was_pre_init_called = False

class Init(Shift):
    string: str
    integer: int

    post_init = False
    post_init_val = None

    def __pre_init__(self, data: dict[str, Any]) -> None:
        global global_was_pre_init_called
        global_was_pre_init_called = True

    def __post_init__(self, data: dict[str, Any]) -> None:
        self.post_init = True
        self.post_init_val = data['integer']

class Default(Shift):
    string: str
    integer: int = 10

class ShiftValidator(Shift):
    string: str
    integer: int
    float: float

    @shift_validator('string')
    def _validate_string(self, data, field) -> bool:
        return len(data[field]) > 0

    @shift_validator('integer', 'float')
    def _validate_numbers(self, data, field) -> bool:
        return data[field] > 10.0

class ShiftSetter(Shift):
    string: str
    integer: int
    float: float

    @shift_setter('string')
    def _set_integer(self, data, field):
        setattr(self, field, data[field] + " world")

    @shift_setter('integer', 'float')
    def _set_numbers(self, data, field):
        setattr(self, field, data[field] + 1)

# Validation
############


def test_builtin_validation():
    builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                        tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})
    assert builtins.boolean == True
    assert builtins.integer == 10
    assert builtins.float == 3.14
    assert builtins.string == 'hello'
    assert builtins.lis == [1, 2, 3]
    assert builtins.tup == ('hello', 3)
    assert builtins.set == {1, 2, 3}
    assert builtins.dct == {'Hello': 3, 'World': 1}

def test_builtins_dict_validation():
    builtins_dict = {
        'boolean': True,
        'integer': 10,
        'float': 10.0,
        'string': 'hello',
        'lis': [1, 2, 3],
        'tup': ('Hello', 3),
        'set': {1, 2, 3},
        'dct': {"Hello": 0, "World": 1},
    }
    builtins = Builtins(**builtins_dict)
    assert builtins.boolean == builtins_dict['boolean']
    assert builtins.integer == builtins_dict['integer']
    assert builtins.float == builtins_dict['float']
    assert builtins.string == builtins_dict['string']
    assert builtins.lis == builtins_dict['lis']
    assert builtins.tup == builtins_dict['tup']
    assert builtins.set == builtins_dict['set']
    assert builtins.dct == builtins_dict['dct']

def test_container_validation():
    container = Container(string='hello', mini=Mini(string='world', integer=10))
    assert container.string == 'hello'
    assert container.mini.string == 'world'
    assert container.mini.integer == 10

def test_container_dict_validation():
    container_dict = {
        'string': 'hello',
        'mini': {
            'string': 'world',
            'integer': 10,
        }
    }
    container = Container(**container_dict)
    assert container.string == container_dict['string']
    assert container.mini.string == 'world'
    assert container.mini.integer == 10

def test_multi_container_validation():
    multi_container = MultiContainer(string='hello',
                                     mini_lis=[Mini(string='world', integer=10), Mini(string='world', integer=10)],
                                     mini_tup=('hello', Mini(string='world', integer=10)),
                                     mini_set={Mini(string='hello', integer=10), Mini(string='world', integer=10)},
                                     mini_dct={'hello': Mini(string='world', integer=10),
                                               'world': Mini(string='world', integer=10)})
    assert multi_container.string == 'hello'
    assert multi_container.mini_lis[0].string == 'world'
    assert multi_container.mini_lis[0].integer == 10
    assert multi_container.mini_lis[1].string == 'world'
    assert multi_container.mini_lis[1].integer == 10
    assert multi_container.mini_tup[0] == 'hello'
    assert multi_container.mini_tup[1].string == 'world'
    assert multi_container.mini_tup[1].integer == 10
    # There's no easy way to validate sets...
    assert multi_container.mini_dct['hello'].string == 'world'
    assert multi_container.mini_dct['hello'].integer == 10
    assert multi_container.mini_dct['world'].string == 'world'

def test_multi_container_dict_validation():
    multi_container_dict = {
        "string": "hello",
        "mini_lis": [
            Mini(string="world", integer=10),
            Mini(string="world", integer=10),
        ],
        "mini_tup": (
            "hello",
            Mini(string="world", integer=10),
        ),
        "mini_set": {
            Mini(string="hello", integer=10),
            Mini(string="world", integer=10),
        },
        "mini_dct": {
            "hello": Mini(string="world", integer=10),
            "world": Mini(string="world", integer=10),
        },
    }
    multi_container = MultiContainer(**multi_container_dict)
    assert multi_container.string == 'hello'
    assert multi_container.mini_lis[0].string == 'world'
    assert multi_container.mini_lis[0].integer == 10
    assert multi_container.mini_lis[1].string == 'world'
    assert multi_container.mini_lis[1].integer == 10
    assert multi_container.mini_tup[0] == 'hello'
    assert multi_container.mini_tup[1].string == 'world'
    assert multi_container.mini_tup[1].integer == 10
    # There's no easy way to validate sets...
    assert multi_container.mini_dct['hello'].string == 'world'
    assert multi_container.mini_dct['hello'].integer == 10
    assert multi_container.mini_dct['world'].string == 'world'

def test_default():
    default = Default(string='hello')
    assert default.integer == 10

def test_shift_validator():
    shift_validator = ShiftValidator(string='hello', integer=11, float=11.0)
    assert shift_validator.string == 'hello'
    assert shift_validator.integer == 11
    assert shift_validator.float == 11.0

    with pytest.raises(ValueError):
        shift_validator = ShiftValidator(string='', integer=11, float=11.0)

    with pytest.raises(ValueError):
        shift_validator = ShiftValidator(string='hello', integer=0, float=11.0)

    with pytest.raises(ValueError):
        shift_validator = ShiftValidator(string='hello', integer=11, float=0.0)

def test_shift_setter():
    shift_setter = ShiftSetter(string='hello', integer=11, float=11.0)
    assert shift_setter.string == 'hello world'
    assert shift_setter.integer == 12
    assert shift_setter.float == 12.0


# Pre-Post Init
###############


def test_pre_init():
    init = Init(string='hello', integer=10)
    global global_was_pre_init_called
    assert global_was_pre_init_called == True

def test_post_init():
    init = Init(string='hello', integer=10)
    assert init.post_init == True
    assert init.post_init_val == 10


# Invalid
#########


def test_missing():
    with pytest.raises(TypeError):
        mini = Mini(string='world')

def test_missing_dict():
    with pytest.raises(TypeError):
        mini_dict = {
            "string": "world"
        }
        mini = Mini(**mini_dict)

def test_invalid_boolean():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=10, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})

def test_invalid_integer():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer="False", float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})

def test_invalid_float():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=False, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})

def test_invalid_string():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string=False, lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})

def test_invalid_lis():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=["False", 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, "False"],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})

def test_invalid_tup():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=(False, 3), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', "False"), set={1, 2, 3}, dct={'Hello': 3, 'World': 1})

def test_invalid_set():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={"False", 2, 3}, dct={'Hello': 3, 'World': 1})
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, "False"}, dct={'Hello': 3, 'World': 1})

def test_invalid_dct():
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={False: 3, 'World': 1})
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': "False", 'World': 1})
    with pytest.raises(TypeError):
        builtins = Builtins(boolean=True, integer=10, float=3.14, string='hello', lis=[1, 2, 3],
                            tup=('hello', 3), set={1, 2, 3}, dct={'Hello': 3, 'World': "False"})

def test_invalid_subclass():
    with pytest.raises(TypeError):
        container = Container(string='hello', mini=False)
    with pytest.raises(TypeError):
        container = Container(string='hello', mini=Mini(string='world', integer="False"))


# Config
########


def test_shift_config_default_config():
    # There's not really a way to check if Shift.shift_config = DEFAULT_SHIFT_CONFIG directly, so create a class and
    #   change the default config so it throws an error

    class TestShiftConfig(Shift):
        allow_default: bool = True
    DEFAULT_SHIFT_CONFIG.allow_defaults = False
    assert DEFAULT_SHIFT_CONFIG.allow_defaults == False
    shift_config = ShiftConfig()
    assert shift_config.allow_defaults == True
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig()
    DEFAULT_SHIFT_CONFIG.allow_defaults = True

def test_shift_config_verbosity():
    # There's not really a good way to assert this

    shift_config = ShiftConfig()
    assert shift_config.verbosity == 0

def test_shift_config_do_validation():
    class TestShiftConfig(Shift):
        do_validation = True
        def __post_init__(self, data):
            do_validation = data['do_validation']
    test_shift_config = TestShiftConfig(do_validation=0)
    assert test_shift_config.do_validation == 0

def test_shift_config_allow_unmatched_args():
    class TestShiftConfig(Shift):
        """This is a string to make python happy"""
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig(allow_unmatched_args=True)

    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_unmatched_args=True)
    test_shift_config = TestShiftConfig(allow_unmatched_args=True)
    assert test_shift_config.allow_unmatched_args == True

def test_shift_config_allow_any():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_any=False)
        any: Any
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig()

def test_shift_config_allow_defaults():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_defaults=False)
        allow_defaults: bool = True
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig()

def test_shift_config_allow_non_annotated():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_non_annotated=False)
        allow_non_annotated = True
    with pytest.raises(TypeError):
        test_shift_config = TestShiftConfig()

def test_shift_config_allow_shift_validators():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_shift_validators=False)
        allow_shift_validators: bool = True
        @shift_validator("allow_shift_validators")
        def _allow_shift_validators(self, data):
            return data['allow_shift_validators']
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig()

def test_shift_config_shift_validators_have_precedence():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(shift_validators_have_precedence=False)
        shift_validators = True
        @shift_validator("shift_validators")
        def _shift_validators(self, data, field):
            return data['shift_validators'] > 10
    test_shift_config = TestShiftConfig(shift_validators=11)
    assert test_shift_config.shift_validators == 11

def test_shift_config_use_shift_validators_first():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(use_shift_validators_first=True)
        use_shift_validators_first = True
        @shift_validator("use_shift_validators_first")
        def _use_shift_validators_first(self, data, field):
            if isinstance(data['use_shift_validators_first'], float):
                raise AttributeError("use_shift_validators_first")
            return data['use_shift_validators_first']
    with pytest.raises(AttributeError):
        test_shift_config = TestShiftConfig(use_shift_validators_first=3.14)


def test_shift_config_allow_shift_setters():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_shift_setters=False)
        allow_shift_setters = True
        @shift_setter("allow_shift_setters")
        def _allow_shift_setters(self, data):
            self.allow_shift_setters = 10
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig(allow_shift_setters=False)

def test_shift_config_allow_nested_shift_classes():
    class TestShiftConfig(Shift):
        __shift_config__ = ShiftConfig(allow_nested_shift_classes=False)
        allow_nested_shift_classes: Mini
    with pytest.raises(ValueError):
        test_shift_config = TestShiftConfig(allow_nested_shift_classes=Mini(string='world', integer=10))