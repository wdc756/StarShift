# Imports
########################################################################################################################



# Data containers
from dataclasses import dataclass

# Check types in validation
from enum import Enum
from typing import get_origin, get_args, get_type_hints, Any, Union, ForwardRef, Type, Callable, Optional

# Evaluate forward references
import sys, inspect



# Errors
########################################################################################################################



class ShiftError(Exception):
    """Base class for all starshift errors"""
    def __init__(self, model_name: str, msg: str):
        super().__init__(f"StarShift: {model_name}: {msg}")

class ShiftConfigError(ShiftError):
    """Raised when an invalid ShiftConfig setting is encountered"""
    def __init__(self, model_name: str, invalid_config: str, invalid_config_val: Any, msg: str):
        super().__init__(model_name, f"Invalid ShiftConfig: `{invalid_config}` was set to `{invalid_config_val}`, but {msg}")

class ShiftTransformError(ShiftError):
    """Raised when a transform fails"""
    def __init__(self, model_name: str, field: str, msg: str):
        super().__init__(model_name, f"Field `{field}` encountered an error during transform: {msg}")

class ShiftValidationError(ShiftError):
    """Raised when any validation fails"""
    def __init__(self, model_name: str, field: str, msg: str):
        super().__init__(model_name, f"Validation failed for field `{field}`: {msg}")

class ShiftSetError(ShiftError):
    """Raised when any set operation fails"""
    def __init__(self, model_name: str, field: str, msg: str):
        super().__init__(model_name, f"Field `{field}` encountered an error during set: {msg}")



# Decorators
########################################################################################################################



## Global
############################################################

def shift_type_transformer(*types: Type) -> Callable[[Any], Any]:
    """Decorator to mark a function as a global shift type transformer"""


def shift_type_validator(*types: Type) -> Callable[[Any], bool]:
    """Decorator to mark a function as a global shift type validator"""


def shift_type_setter(*types: Type) -> Callable[[Any], None]:
    """Decorator to mark a function as a global shift type setter"""


def shift_type_repr(*types: Type) -> Callable[[Any], str]:
    """Decorator to mark a function as a global shift type repr"""


def shift_type_serializer(*types: Type) -> Callable[[Any], dict[str, Any]]:
    """Decorator to mark a function as a global shift type serializer"""



## Field
############################################################

def shift_transformer(*fields: str) -> Callable[[Any], Any]:
    """Decorator to mark a function as a shift transformer"""


def shift_validator(*fields: str, pre: bool=False, skip_when_pre: bool=True) -> Callable[[Any], bool]:
    """Decorator to mark a function as a shift validator

    pre: marks this function to run in the pre-validation phase
    skip_when_pre: skips shift validation when running in the pre-validation phase
    """


def shift_setter(*fields: str) -> Callable[[Any, Any], None]:
    """Decorator to mark a function as a shift setter

    The double any is so we can pass in `self`"""


def shift_repr(*fields: str) -> Callable[[Any], str]:
    """Decorator to mark a function as a shift repr"""


def shift_serializer(*fields: str) -> Callable[[Any], dict[str, Any]]:
    """Decorator to mark a function as a shift serializer"""



# Types
########################################################################################################################



class _Missing:
    """Basic class to represent a missing value or type hint"""
    pass

## Containers
############################################################

class ShiftTypeCategory(Enum):
    """Enum for type categories"""
    ALL_OF = "all_of"
    ONE_OF = "one_of"
    SHIFT = "shift"
    FORWARD_REF = "forward_ref"
    BASE = "base"

@dataclass
class ShiftType:
    """Universal type interface for all validation types"""
    category: ShiftTypeCategory
    validator: Callable[[Any], bool]
    setter: Callable[[Any, Any], None]
    repr: Callable[[Any], str]
    serializer: Callable[[Any], dict[str, Any]]



## Builtin Type Functions
############################################################

### Simple Types
##############################

def _shift_builtin_type_transformer(val: Any) -> None:
    pass # We don't need to do anything for builtin types

def _shift_builtin_type_validator(val: Any) -> bool:
    return True # Link to the recursive shift validation loop?

def _shift_builtin_type_setter(self: Any, val: Any) -> None:
    pass # Set the field

def _shift_builtin_type_repr(val: Any) -> str:
    return repr(val) # Use default repr

def _shift_builtin_type_serializer(val: Any) -> dict[str, Any]:
    pass # Link to the recursive shift serialization loop?

### Complex Types
##############################

def _shift_forward_ref_validator(val: Any) -> bool:
    return True # Link to the forward ref resolver, then to normal validation loop?



## Builtin Types
############################################################

_shift_builtin_type_base = ShiftType(ShiftTypeCategory.BASE, _shift_builtin_type_validator, _shift_builtin_type_setter,
                                      _shift_builtin_type_repr, _shift_builtin_type_serializer)
_shift_builtin_type_all_of = ShiftType(ShiftTypeCategory.ALL_OF, _shift_builtin_type_validator, _shift_builtin_type_setter,
                                       _shift_builtin_type_repr, _shift_builtin_type_serializer)
_shift_builtin_type_one_of = ShiftType(ShiftTypeCategory.ONE_OF, _shift_builtin_type_validator, _shift_builtin_type_setter,
                                       _shift_builtin_type_repr, _shift_builtin_type_serializer)
_shift_builtin_type_shift = ShiftType(ShiftTypeCategory.SHIFT, _shift_builtin_type_validator, _shift_builtin_type_setter,
                                      _shift_builtin_type_repr, _shift_builtin_type_serializer)
_shift_builtin_type_forward_ref = ShiftType(ShiftTypeCategory.FORWARD_REF, _shift_forward_ref_validator, _shift_builtin_type_setter,
                                            _shift_builtin_type_repr, _shift_builtin_type_serializer)

_shift_builtin_types: dict[Type, ShiftType] = {
    None: _shift_builtin_type_base,
    int: _shift_builtin_type_base,
    bool: _shift_builtin_type_base,
    float: _shift_builtin_type_base,
    str: _shift_builtin_type_base,
    bytes: _shift_builtin_type_base,
    bytearray: _shift_builtin_type_base,
    Any: _shift_builtin_type_base,

    list: _shift_builtin_type_all_of,
    tuple: _shift_builtin_type_all_of,
    set: _shift_builtin_type_all_of,
    frozenset: _shift_builtin_type_all_of,
    dict: _shift_builtin_type_all_of,
    Callable: _shift_builtin_type_all_of,

    Union: _shift_builtin_type_one_of,
    Optional: _shift_builtin_type_one_of,

    # This is resolved later
    "Shift": _shift_builtin_type_shift,

    ForwardRef: _shift_builtin_type_forward_ref,
}



# Config
########################################################################################################################



@dataclass
class ShiftConfig:
    """Configuration for shift phases"""
    verbosity: int = 0
    # Put some more values here later



## Presets
############################################################

StrictConfig = ShiftConfig(verbosity=1)
RelaxedConfig = ShiftConfig(verbosity=0)
# Add more later



# Global Registers & Defaults
########################################################################################################################



# Leave this override here in case people want an easy way to add more types globally
_shift_types: dict[Type, ShiftType] = {}
_shift_types.update(_shift_builtin_types)

_resolved_forward_refs: dict[ForwardRef, Type] = {}



# Logging
########################################################################################################################



def _log(msg: str) -> None:
    # Only print if msg has text
    if msg and len(msg):
        print(msg)

def _log_verbose(verbosity: int, msg: list[str]):
    # Return if verbosity 0 or msg empty
    if verbosity == 0 or len(msg) == 0:
        return

    # If verbosity !> len(msg) print msg[verbosity]
    if verbosity < len(msg):
        _log(msg[verbosity - 1])
        return
    # Else decrement verbosity until it matches len(msg) and print
    else:
        while len(msg) < verbosity:
            verbosity -= 1
        _log(msg[verbosity - 1])
        return



# Class Init
########################################################################################################################



def _get_shift_config(self: Any, model_name: str) -> ShiftConfig | None:
    return None # Get the `__shift_config__` attribute from the model, if it exists

def _set_field_decorators(cls: Type, shift_config: ShiftConfig, model_name: str) -> None:
    pass # Find the decorators and process them



# Shift Processing Phases
########################################################################################################################



@dataclass
class _ShiftInfo:
    """Data class for storing validation info"""
    shift_config: ShiftConfig
    model_name: str
    validators: list[Callable[[Any], bool]]
    setters: list[Callable[[Any, Any], None]]
    errors: list[ShiftError]

@dataclass
class _ShiftField:
    """Data class for storing validation info"""
    field: str
    typ: Any = _Missing
    val: Any = _Missing
    default: Any = _Missing

def _get_category(typ: Any) -> ShiftTypeCategory | _Missing:
    if typ in _shift_types:
        return _shift_types[typ].category
    return _Missing()



## Transformation
############################################################

def _transform() -> None:
    pass # Loop through all fields, get category, call category transform



## Validation
############################################################

def _validate_field(field: _ShiftField, info: _ShiftInfo) -> None:
    pass # Check for custom class validator, else get category, call category validator, add to shift errors if validation fails



## Setting
############################################################

def _set_field(field: _ShiftField, info: _ShiftInfo) -> None:
    pass # Check for custom class setter, else get category, call category setter



# Repr & Serialization
########################################################################################################################



# Do these later



# Shift Classes
########################################################################################################################



class ShiftMeta(type):
    """Helper class to handle namespace resolution and forward refs"""

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        # walk up frames adding context until we get this function call

        return cls

class Shift(metaclass=ShiftMeta):
    """Base class for all shift models"""



# Misc
########################################################################################################################



# Fix forward refs for Shift in type categories
_shift_builtin_types[Shift] = _shift_builtin_type_shift
_shift_types[Shift] = _shift_builtin_type_shift