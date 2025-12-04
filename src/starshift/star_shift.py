# Used to set up ShiftConfig
from dataclasses import dataclass

# Used to check types in _validate()
from typing import get_origin, get_args, Any, Union



@dataclass
class ShiftConfig:
    """
    This dataclass holds all the configuration options for a Shift class

    Attributes:
        verbosity: int = 0 [0, 3]
            The level of debug messages to print
            0: No debug messages
            1: Validation step messages
            2. Validation var step messages
            3: All config and attribute messages
        allow_any: bool = True
            Whether to allow vars to use the `Any` type
            False: If var is `Any` type throw
            True: If var is `Any` validate var
        allow_defaults: bool = True
            Whether to allow default values for vars
            False: If var.default is not `None` throw
            True: If var.default is not `None` and val.value is `None` attempt validate with default
        allow_non_annotated: bool = True
            Whether to allow non-annotated vars (no type hint)
            False: If var.annotation is `None` throw error
            True: If var.annotation is `None` set var (no type checks for validation unless `shit_validator` is set for
            var)
        allow_shift_validators: bool = True
            Whether to allow custom shift validators (custom validators for vars via decorator:
            `@shift_validator(var) -> bool`) - note if this def sets the field, it will be overwritten
            False: If shift_validator(var) is not `None` throw
            True: If shift_validator(var) is not `None` call and validate var if it returns True
        shift_validators_have_precedence: bool = True
            Whether a shift_validador for a given var has precedence over the default validator (if
            @shift_validator(field): validate var)
            False: If shift_validator(var) is not `None` and returns True, validate again using default validator
            True: If shift_validator(var) is not `None` and returns True, validate var
        allow_shift_setters: bool = True
            Whether to allow custom shift setters (custom setters for vars via decorator: `@shift_setter(var) -> None`)
            False: If shift_setter(var) is not `None` throw error
            True: If shift_setter(var) is not `None` call
    """
    verbosity: int = 0
    allow_any: bool = True
    allow_defaults: bool = True
    allow_non_annotated: bool = True
    allow_shift_validators: bool = True
    shift_validators_have_precedence: bool = True
    allow_shift_setters: bool = True

DEFAULT_SHIFT_CONFIG = ShiftConfig()

def shift_validator(field: str):
    def decorator(func):
        func.__validator_for__ = field
        return func
    return decorator

def shift_setter(field: str):
    def decorator(func):
        func.__validator_for__ = field
        return func
    return decorator



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

# Note that cls is Any here because it can be any class
def _set_validators_and_setters(cls: Any) -> None:
    # Create new fields in cls
    cls.__validators__ = {}
    cls.__setters__ = {}

    # Fill validators and setters
    for name, value in cls.__dict__.items():
        # I would put a debug statement here, but shift_config isn't set yet when this is called

        # If value is callable test if it has a shift marker
        if callable(value):
            # If shift_validator, add to validators
            if hasattr(value, '__validator_for__'):
                field = value.__validator_for__
                cls.__validators__[field] = value
                continue

            # If shift_setter, add to setters
            elif hasattr(value, '__setter_for__'):
                field = value.__setter_for__
                cls.__setters__[field] = value
                continue

# Note that self is not annotated as Shift because that's undefined here
def _get_shift_config(self: Any, model_name: str) -> ShiftConfig:
    # Get ShiftConfig (should always be `__shift_config__`) and check the type
    shift_config = self.__fields__.get("__shift_config__")
    if shift_config and not isinstance(shift_config, ShiftConfig):
        raise TypeError(f"`{model_name}`: __shift_config__ must be a ShiftConfig instance")

    # If no shift config provided, use global default
    if shift_config:
        _log_verbose(shift_config.verbosity,
                     ["", "__shift_config__ set"])
    else:
        shift_config = DEFAULT_SHIFT_CONFIG

    _log_verbose(shift_config.verbosity, ["", "", "", f"shift_config: {shift_config}"])
    return shift_config



def _get_val(self: Any, field: str, data: Any, shift_config: ShiftConfig, model_name: str) -> Any:
    # Get val from data if in data
    if field in data:
        return data[field]
    # Else get default (could be None)
    else:
        # If defaults not allowed, throw
        if not shift_config.allow_defaults:
            raise ValueError(
                f"{model_name}: `{field}` was not set and there is a default, but `shift_config.allow_defaults` is `False`")
        return self.__fields__.get(field)

def _set_field(self: Any, field: str, val: Any, shift_config: ShiftConfig, model_name: str, setters: Any) -> None:
    # If shift_setter(field), use
    if field in setters:
        # If shift_setters not allowed, throw
        if not shift_config.allow_shift_setters:
            raise ValueError(f"`{model_name} has a `@shift_setter({field})` decorator but `shift_config.allow_shift_setters` is `False`")
        setters[field](self, val)
        return
    # Else set here
    setattr(self, field, val)

def _validate_union_optional(typ: Any, val: Any, shift_config: ShiftConfig) -> bool:
    # If typ not a Union (Optional = Union[type, None]), invalidate
    if not get_origin(typ) is Union:
        return False

    # If val is any arg(assume arg is not empty), validate
    args = get_args(typ)
    for arg in args:
        if not _validate_value(arg, val, shift_config):
            return True

    # val is any typ, validate
    return False

def _validate_list(typ: Any, lis: Any, shift_config: ShiftConfig) -> bool:
    # If typ or lis are not a list, return false
    if not get_origin(typ) is list or not isinstance(lis, list):
        return False

    # If typ is un-annotated or lis is empty, validate
    args = get_args(typ)
    if not args or not lis:
        return True

    # If any li in lis is not an arg, return false
    for li in lis:
        if not _validate_value(args[0], li, shift_config):
            return False

    # All li in lis are typ, validate
    return True

def _validate_dict(typ: Any, dct: Any, shift_config: ShiftConfig) -> bool:
    # If typ or dct are not a dict, invalidate
    if not get_origin(typ) is dict or not isinstance(dct, dict):
        return False

    # If typ is un-annotated or dct is empty, validate
    args = get_args(typ)
    if not args or not dct:
        return True

    # If any key is not arg[0], invalidate
    for key in dct.keys():
        if not _validate_value(args[0], key, shift_config):
            return False

    # If args[1] is defined and any val in dct.values is not instance, invalidate
    if len(args) > 1:
        for key in dct.keys():
            if not _validate_value(args[1], dct.get(key), shift_config):
                return False

    # All key-val in dct match typ, validate
    return True

def _validate_value(typ: Any, val: Any, shift_config: ShiftConfig) -> bool:
    _log_verbose(shift_config.verbosity, ["", "", f"Attempting `{val}` validation against `{typ}`"])

    # If complex type validates, return validation
    if shift_config.allow_any and typ is Any:
        return True
    elif _validate_union_optional(typ, val, shift_config):
        return True
    elif _validate_list(typ, val, shift_config):
        return True
    elif _validate_dict(typ, val, shift_config):
        return True

    # If no complex type validated but simple validation works, validate
    # Use try block here to gracefully handle invalid types
    try:
        if isinstance(val, typ):
            return True
    except TypeError:
        pass

    # If no type validated, invalidate
    return False

def _validate_shift_validator(self: Any, shift_config: ShiftConfig, model_name: str, val: Any, field: str, validators: Any) -> bool:
    # If shift_validator(field), handle
    if field in validators:
        # If shift_validators not allowed, throw
        if not shift_config.allow_shift_validators:
            raise ValueError(f"`{model_name}` has a `@shift_validators({field})` decorator but `shift_config.allow_shift_validators` is `False`")

        _log_verbose(shift_config.verbosity, ["", "", f"Using f{validators[field]} to validate `{field}`"])
        return validators[field](self, val)
    # Else false because we can't validate here
    return False

def _validate_field(self: Any, field: str, typ: Any, val: Any, shift_config: ShiftConfig, model_name: str, validators: Any) -> bool:
    _log_verbose(shift_config.verbosity, ["", "", f"Attempting `{field}` validation against `{typ}`"])

    # If shift_validator(field), handle
    if field in validators:
        # If shift_validators not allowed, throw
        if not shift_config.allow_shift_validators:
            raise ValueError(f"`{model_name}`: a shift_validator decorator is being used for `{field}`, but `shift_config.allow_shift_validators` is `False`")
        return validators[field](self, val)
    # Else use default validator
    return _validate_value(typ, val, shift_config)

def _validate_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: Any, annotations: Any, validators: Any, setters: Any) -> None:
    _log_verbose(shift_config.verbosity, ["Validating fields"])

    for field, typ in annotations.items():
        # Get val
        val = _get_val(self, field, data, shift_config, model_name)

        # If val is validated against typ, set (if validation fails throw is done in function)
        if _validate_field(self, field, typ, val, shift_config, model_name, validators):
            _log_verbose(shift_config.verbosity, ["", "", f"Validated field `{field}`, setting"])
            _set_field(self, field, val, shift_config, model_name, setters)

def _validate_un_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: Any, annotations: Any, validators: Any, setters: Any) -> None:
    _log_verbose(shift_config.verbosity, ["Setting un-annotated fields"])

    # Get all fields
    fields = {}
    for field in self.__fields__:
        if shift_config.verbosity > 2:
            print(f"Attempting to add `{field}` to un-annotated fields")

        # Filter all magic fields (__ex__) out
        if field not in annotations and not field.startswith("__") and not field.endswith("__"):

            # Filter out all callables (def/function)
            attr = self.__fields__.get(field)
            if not callable(attr):
                if shift_config.verbosity > 2:
                    print(f"Adding `{field}` to un-annotated fields")
                fields[field] = attr
    _log_verbose(shift_config.verbosity, ["", "", f"non-annotated fields: {fields}"])

    # Check if non-annotated fields allowed
    if fields and len(fields) > 0 and not shift_config.allow_non_annotated:
        raise TypeError(f"`{model_name}` has non-annotated fields when `shift_config.allow_non_annotated` is `False`")

    # Set each field (assume user/interpreter validation)
    for field in fields.keys():
        # Get val
        val = _get_val(self, field, data, shift_config, model_name)

        # Set (setter errors are handled in function)
        _set_field(self, field, val, shift_config, model_name, setters)

def _validate(self: Any, shift_config: ShiftConfig, model_name: str, data: Any, validators: Any, setters: Any) -> None:
    _log_verbose(shift_config.verbosity, [f"Validating class `{model_name}`"])

    # Get annotation vars (dict[field, typ])
    annotations = getattr(self.__class__, "__annotations__", {})
    _log_verbose(shift_config.verbosity, ["", "", f"annotated fields {annotations}"])

    # Validate all vars
    _validate_annotated(self, shift_config, model_name, data, annotations, validators, setters)
    _validate_un_annotated(self, shift_config, model_name, data, annotations, validators, setters)

    _log_verbose(shift_config.verbosity, [f"Validated class `{model_name}`"])

class Shift:
    """
    This is a helper base class that can be used on any normal python class to automatically validate class casting
    from dicts (`cls(**dict)`)

    To use this class, have any other class you want to validate inherit `Shift`. Then annotate each var or cls
    attribute you want to validate and build the class from your dict.

    Parameters:
        __shift_config__: ShiftConfig = None
            A ShiftConfig instance used to configure Shift validation, if left as `None` it will take the value of
            `DEFAULT_SHIFT_CONFIG` - which can be globally configured
        __pre_init__(data)
            A def that Shift will call prior to validation, passing in the constructor dict data
        @shift_validator(var)
            A decorator that marks a class def as a validator for `var` - this def must return a bool for its validation
        @shift_setter(var)
            A decorator that marks a class def as a setter for `var` - returned values are discarded
        __post_init__(data)
            A def that Shift will call after validation, passing in the constructor dict data
    """

    def __init_subclass__(cls):
        # Get class fields (all vars, annotations, defs, etc)
        cls.__fields__ = getattr(cls, "__dict__", {}).copy()

        # Find all validators and setters
        _set_validators_and_setters(cls)

    def __init__(self, **data):
        # Get the class name to print useful log/error messages
        model_name = self.__class__.__name__

        # Get ShiftConfig (should always be `__shift_config__`) and check type
        shift_config = _get_shift_config(self, model_name)

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__fields__:
            _log_verbose(shift_config.verbosity, [f"Calling __pre_init__ for `{model_name}`"])
            self.__fields__["__pre_init__"](self, data)

        # Get validators and setters
        validators = self.__validators__
        _log_verbose(shift_config.verbosity, ["", "", f"validators: {validators}"])
        setters = self.__setters__
        _log_verbose(shift_config.verbosity, ["", "", f"setters: {setters}"])

        # Run validation
        _validate(self, shift_config, model_name, data, validators, setters)

        # If cls has __post_init__(), call
        if "__post_init__" in self.__fields__:
            _log_verbose(shift_config.verbosity, [f"Calling __post_init__ for `{model_name}`"])
            self.__fields__["__post_init__"](self, data)

