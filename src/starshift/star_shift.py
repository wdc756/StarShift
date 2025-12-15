# Imports
########################################################################################################################



# Used to set up ShiftConfig
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields

# Used to check types in _validate()
from typing import get_origin, get_args, get_type_hints, Any, Union, ForwardRef, Type, Callable

# Used to evaluate str forward refs
import sys
import inspect



# Exceptions
########################################################################################################################



class ShiftError(Exception):
    def __init__(self, model_name: str, msg: str):
        super().__init__(f"StarShift: {model_name}: {msg}")

class ShiftConfigError(Exception):
    def __init__(self, model_name: str, invalid_config: str, invalid_config_val: Any, msg: str):
        super().__init__(f"StarShift: {model_name}: Invalid ShiftConfig: `{invalid_config}` was set to "
                         f"`{invalid_config_val}`, but {msg}")

class ShiftValidationError(Exception):
    def __init__(self, model_name: str, field: str, msg: str):
        super().__init__(f"StarShift: {model_name}: Validation failed for field `{field}`: {msg}")



# Config
########################################################################################################################



@dataclass
class ShiftConfig:
    """
    This dataclass holds all the configuration options for a Shift class

    Attributes:
        verbosity (int): Level of logging Default: 0

        lazy_validate_decorators (bool): Validate decorators after __pre_init__; Default: False
        use_custom_shift_validators_first (bool): Use @shift_validators before builtin validation; Default: False
        custom_shift_validators_bypass_validation (bool): If @shift_validator(), skip builtin validation; Default: False

        skip_validation (bool): Skip all validation and set steps; Default: False
        validate_infinite_nesting (bool): Check for infinite nesting; Default: True
        use_builtin_shift_repr (bool): Use the builtin Shift __repr__; Default: True
        use_builtin_shift_serializer (bool): Use the builtin Shift serializer; Default: True
        include_shift_config_in_serialization (bool): Include shift config in serialization; Default: False
        include_defaults_in_serialization (bool): Include all annotated keys in serialization; Default: False
        include_private_fields_in_serialization (bool): Include all `_` private fields in serialization; Default: False

        allow_unmatched_args (bool): Allow args that don't match any attributes; Default: False
        allow_any (bool): Allow type hint to be Any; Default: True
        allow_defaults (bool): Allow default values; Default: True
        allow_non_annotated (bool): Allow non-annotated values; Default: False
        allow_forward_refs (bool): Allow forward refs; Default: True
        allow_nested_shift_classes (bool): Allow shift classes inside Shift class; Default: True

        allow_decorators (bool): Allow any @shift_* decorators; Default: True
        allow_shift_validators (bool): Allow @shift_validator decorators; Default: True
        allow_shift_setters (bool): Allow @shift_setter decorators; Default: True
        allow_shift_reprs (bool): Allow @shift_repr decorators; Default: True
        allow_shift_serializers (bool): Allow @shift_serializer decorators; Default: True
    """

    # Logging
    verbosity: int = 0

    # When things happen
    lazy_validate_decorators: bool = False
    use_custom_shift_validators_first: bool = False
    custom_shift_validators_bypass_validation: bool = False

    # Whether things happen
    skip_validation: bool = False
    validate_infinite_nesting: bool = True
    use_builtin_shift_repr: bool = True
    use_builtin_shift_serializer: bool = True
    include_shift_config_in_serialization: bool = False
    include_defaults_in_serialization: bool = False
    include_private_fields_in_serialization: bool = False

    # What is allowed
    allow_unmatched_args: bool = False
    allow_any: bool = True
    allow_defaults: bool = True
    allow_non_annotated: bool = False
    allow_forward_refs: bool = True
    allow_nested_shift_classes: bool = True

    allow_decorators: bool = True
    allow_shift_validators: bool = True
    allow_shift_setters: bool = True
    allow_shift_reprs: bool = True
    allow_shift_serializers: bool = True



    def __repr__(self):
        parts = []
        for field in dataclass_fields(self):
            val = getattr(self, field.name)
            if val != field.default:
                parts.append(f"{field}={val}")

        args = ", ".join(parts)
        return f"ShiftConfig({args})"

    def serialize(self) -> dict[str, Any]:
        result = {}
        for field in dataclass_fields(self):
            val = getattr(self, field.name)
            if val != field.default:
                result[field] = val
        return result

DEFAULT_SHIFT_CONFIG = ShiftConfig()



# Decorators
########################################################################################################################



def shift_validator(*fields: str) -> Callable:
    """
    Decorator to mark a function as a validator for one or more fields.
    This must return `True` else the whole validation will fail.

    Usage:
        @shift_validator('age')
        def validate_age(self, data: dict[str, Any], field: str) -> bool:
            return data['age'] > 0

        @shift_validator('age', 'height', 'weight')
        def validate_positive(self, data: dict[str, Any], field: str) -> bool:
            return data[field] > 0

    Note data is the whole dictionary used to build the shift subclass, and field is the attribute being validated
    """

    def decorator(func) -> Callable:
        # Store as a tuple of fields instead of a single field to allow multiple args
        func.__validator_for__ = fields
        return func

    return decorator

def shift_setter(*fields: str) -> Callable:
    """
    Decorator to mark a function as a setter for one or more fields.

    Usage:
        @shift_setter('name')
        def set_name(self, data: dict[str, Any], field: str) -> None:
            setattr(self, 'name', data['name'].upper())

        @shift_setter('first_name', 'last_name')
        def set_names(self, data: dict[str, Any], field: str) -> None:
            setattr(self, field, data[field].upper())

    Note data is the whole dictionary used to build the shift subclass, and field is the attribute being set
    """

    def decorator(func) -> Callable:
        func.__setter_for__ = fields
        return func

    return decorator

def has_repr(val: Any) -> bool:
    """Returns whether the val has a callable attribute repr"""
    return val is not None and hasattr(val, '__repr__') and callable(val.__repr__)

def shift_repr(*fields: str) -> Callable:
    """
    Decorator to mark a function as a repr for one or more fields.
    This marked function must return a str of the value, NOT including the field= part of the repr

    Usage:
        @shift_repr('name')
        def repr_name(self, field: str, val: Any, default: Any) -> Union[str, None]:
            if val != default:
                if has_repr(val):
                    return repr(val)
                return val
            return None

        @shift_repr('first_name', 'last_name')
        def repr_names(self, field: str, val: Any, default: Any) -> Union[str, None]:
            if val != default:
                if has_repr(val):
                    return repr(val)
                return val
            return None

    Note that field is the attribute being repr'd, val is the current value of the attribute, and default is the
    annotated default value if set
    """

    def decorator(func) -> Callable:
        func.__repr_for__ = fields
        return func

    return decorator

def has_serializer(val: Any) -> bool:
    """Returns whether the val has a callable attribute serialize"""
    return val is not None and hasattr(val, 'serialize') and callable(val.serialize)

def shift_serializer(*fields: str) -> Callable:
    """
    Decorator to mark a function as a serializer for one or more fields.
    This marked function must return an Any value that does NOT include the field: part of the dict

    Usage:
        @shift_serialize('name')
        def serialize_name(self, field: str, val: Any) -> Union[Any, None]:
            if val != default:
                if has_serialize(val):
                    return val.serialize()
                return val
            return None

        @shift_serialize('first_name', 'last_name')
        def serialize_names(self, field: str, val: Any) -> Union[Any, None]:
            if val != default:
                if has_serialize(val):
                    return val.serialize()
                return val
            return None

    Note that field is the attribute being serialized, val is the current value of the attribute, and default is the
    annotated default value if set
    """

    def decorator(func) -> Callable:
        func.__serialize_for__ = fields
        return func

    return decorator



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



# Init/Setup
########################################################################################################################



def _get_shift_config(self: Any, model_name: str) -> ShiftConfig:
    # Get shift_config from self if it exists
    shift_config = self.__fields__.get("__shift_config__")
    if shift_config and not isinstance(shift_config, ShiftConfig):
        raise ShiftError(model_name, "`__shift_config__` must be a ShiftConfig instance")

    # If no shift config provided, use global default
    if shift_config:
        _log_verbose(shift_config.verbosity,["", "__shift_config__ set"])
    else:
        shift_config = DEFAULT_SHIFT_CONFIG

    _log_verbose(shift_config.verbosity, ["", "", f"shift_config: {shift_config}"])
    return shift_config

def _set_decorators(cls: Type, shift_config: ShiftConfig, model_name: str) -> None:
    _log_verbose(shift_config.verbosity, ["Getting decorators"])

    # Create new fields in cls
    cls.__validators__ = {}
    cls.__setters__ = {}
    cls.__reprs__ = {}
    cls.__serializers__ = {}

    # Fill decorators
    for name, value in cls.__dict__.items():
        _log_verbose(shift_config.verbosity, ["", "", f"Checking `{name}`"])

        # If value is callable test if it has a shift marker
        if callable(value):
            _log_verbose(shift_config.verbosity, ["", "", f"Checking `{name}` for shift decorator"])

            # If shift_validator, add to validators for each field
            if hasattr(value, '__validator_for__'):
                _log_verbose(shift_config.verbosity, ["", "", "found shift_validator, getting fields"])

                fields = value.__validator_for__
                for field in fields:
                    _log_verbose(shift_config.verbosity, ["", f"Adding shift validator for `{field}`"])
                    cls.__validators__[field] = value

            # If shift_setter, add to setters for each field
            elif hasattr(value, '__setter_for__'):
                _log_verbose(shift_config.verbosity, ["", "", "found shift_setter, getting fields"])

                fields = value.__setter_for__
                for field in fields:
                    _log_verbose(shift_config.verbosity, ["", f"Adding shift setter for `{field}`"])
                    cls.__setters__[field] = value

            # If shift_repr, add to reprs for each field
            elif hasattr(value, '__repr_for__'):
                _log_verbose(shift_config.verbosity, ["", "", "found shift_repr, getting fields"])

                fields = value.__repr_for__
                for field in fields:
                    _log_verbose(shift_config.verbosity, ["", f"Adding shift repr for `{field}`"])
                    cls.__reprs__[field] = value

            # If shift_serialize_for, add to __serialize_for__ for each field
            elif hasattr(value, '__serialize_for__'):
                _log_verbose(shift_config.verbosity, ["", "", "found shift_serialize_for, getting fields"])

                fields = value.__serialize_for__
                for field in fields:
                    _log_verbose(shift_config.verbosity, ["", f"Adding shift serializer for `{field}`"])
                    cls.__serializers__[field] = value

    _log_verbose(shift_config.verbosity, ["", "", f"shift_validators: {cls.__validators__}"])
    _log_verbose(shift_config.verbosity, ["", "", f"shift_setters: {cls.__setters__}"])
    _log_verbose(shift_config.verbosity, ["", "", f"shift_reprs: {cls.__reprs__}"])
    _log_verbose(shift_config.verbosity, ["", "", f"shift_serializers: {cls.__serializers__}"])



# Value Management
########################################################################################################################



def _get_val(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any], field: str) -> Any:
    _log_verbose(shift_config.verbosity, ["", "", f"Getting val for `{field}`"])

    # Get val from data if in data
    if field in data:
        return data[field]

    # Else get default (could be None)
    else:
        # If defaults not allowed, throw
        if not shift_config.allow_defaults:
            raise ShiftConfigError(model_name, "allow_defaults", False,
                                   f"`{field}` was not defined and has a default")
        return self.__fields__.get(field)

def _is_shift_subclass(shift_config: ShiftConfig, model_name: str, field: str, typ: Any) -> bool:
    try:
        if isinstance(typ, type) and issubclass(typ, Shift):
            if not shift_config.allow_nested_shift_classes:
                raise ShiftConfigError(model_name, "allow_nested_shift_classes", False,
                                       f"`{field}` is a Shift class")
            return True
    except TypeError:
        # issubclass raises TypeError for non-classes like Union, List, etc. but we don't care about those
        return False
    return False

def _resolve_forward_ref(cls, shift_config: ShiftConfig, model_name: str, field: str) -> Any:
    _log_verbose(shift_config.verbosity, ["", "", f"Resolving forward ref for `{field}`"])

    # Get the module where the class was defined
    module = sys.modules[cls.__module__]
    global_namespace = module.__dict__

    # Start with creation namespace
    local_namespace = getattr(cls, "__creation_ns__", {}).copy()

    # Add frame locals captured at class definition
    frame_locals = getattr(cls, "__frame_locals__", {})
    local_namespace.update(frame_locals)

    # CRITICAL: Walk up the stack to find the calling context
    # This handles cases where classes are defined in functions
    frame = inspect.currentframe()
    try:
        # Walk up the stack looking for the type
        search_frame = frame
        while search_frame is not None:
            frame_locals = search_frame.f_locals
            if frame_locals:
                # Check if the forward ref exists in this frame
                annotation_str = cls.__annotations__.get(field)
                if isinstance(annotation_str, str) and annotation_str in frame_locals:
                    local_namespace[annotation_str] = frame_locals[annotation_str]
                    break
                # Also add all locals from this frame (might contain the type)
                local_namespace.update(frame_locals)
            search_frame = search_frame.f_back
    finally:
        del frame

    # Add the class itself
    local_namespace[cls.__name__] = cls

    try:
        hints = get_type_hints(cls, globalns=global_namespace, localns=local_namespace)
        return hints[field]
    except NameError as e:
        raise ShiftValidationError(model_name, field, f"has an invalid forward reference: {e}")

def _set_field(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
               setters: dict[str, Callable], field: str, typ: Any, val: Any) -> None:
    _log_verbose(shift_config.verbosity, ["", "", f"Setting `{field}` to `{val}`"])

    # If shift_setter(field), use
    if field in setters:
        if not shift_config.allow_shift_setters:
            raise ShiftConfigError(model_name, "allow_shift_setters", False,
                                   f"`{field}` has a `@shift_setter` decorator")
        _log_verbose(shift_config.verbosity, ["", "", f"Using shift_setter for `{field}`"])
        setters[field](self, data, field)
        return

    # If val is None, just set it (don't try to construct)
    if val is None:
        setattr(self, field, None)
        return

    # Else if typ is a shift subclass and val is a dict, set with validation
    elif _is_shift_subclass(shift_config, model_name, field, typ) and isinstance(val, dict):
        _log_verbose(shift_config.verbosity, ["", "", f"Constructing `{field}` as Shift subclass"])
        try:
            setattr(self, field, typ(**val))
        except ShiftValidationError as e:
            raise ShiftValidationError(model_name, field,  f"failed to construct `{typ.__name__}`: {e}")
        except ShiftError as e:
            raise ShiftError(model_name, f"failed to construct `{field}`: `{typ.__name__}`: {e}")
        return

    # Else set as normal value
    try:
        setattr(self, field, val)
    except Exception as e:
        # Throw a ShiftError here because a basic (non-shift) type failed to construct - different from Shift failure
        raise ShiftError(model_name, f"failed to set `{field}`: {e}")



# Validation Functions
########################################################################################################################


def _validate_decorators(shift_config: ShiftConfig, model_name: str,
                         validators: dict[str, Callable], setters: dict[str, Callable],
                         reprs: dict[str, Callable], serializers: dict[str, Callable]) -> None:
    # Validate all decorators
    if not shift_config.allow_decorators:
        if validators:
            raise ShiftConfigError(model_name, "allow_decorators", False,
                                   "validation decorators are set")
        if setters:
            raise ShiftConfigError(model_name, "allow_decorators", False,
                                   "setter decorators are set")
        if reprs:
            raise ShiftConfigError(model_name, "allow_decorators", False,
                                   "repr decorators are set")
        if serializers:
            raise ShiftConfigError(model_name, "allow_decorators", False,
                                   "serializer decorators are set")

    # Validate individual decorators
    if not shift_config.allow_shift_validators:
        if validators:
            raise ShiftConfigError(model_name, "allow_shift_validators", False,
                                   "shift_validators are set")
    if not shift_config.allow_shift_setters:
        if setters:
            raise ShiftConfigError(model_name, "allow_shift_setters", False,
                                   "shift_setters are set")
    if not shift_config.allow_shift_reprs:
        if reprs:
            raise ShiftConfigError(model_name, "allow_shift_reprs", False,
                                   "shift_reprs are set")
    if not shift_config.allow_shift_serializers:
        if serializers:
            raise ShiftConfigError(model_name, "allow_shift_serializers", False,
                                   "shift_serializers are set")

def _validate_infinite_nesting(cls: Type, shift_config: ShiftConfig, model_name: str) -> None:
    _log_verbose(shift_config.verbosity, ["", "", "Checking for infinite nesting"])

    # Build proper namespaces
    module = sys.modules[cls.__module__]
    global_namespace = module.__dict__
    local_namespace = getattr(cls, "__creation_ns__", {}).copy()

    frame_locals = getattr(cls, "__frame_locals__", {})
    local_namespace.update(frame_locals)

    local_namespace[cls.__name__] = cls

    try:
        annotations = get_type_hints(cls, globalns=global_namespace, localns=local_namespace)
    except NameError:
        return

    for field, typ in annotations.items():
        # Check if field is the same type as the class (not Optional)
        if typ is cls:
            # Check if a default value EXISTS (even if it's None)
            # The key is to check if the field is IN __dict__, not if its value is None
            has_default = field in cls.__dict__ or hasattr(cls, field)

            if not has_default:
                raise ShiftValidationError(model_name, field,
                                           "has infinite nesting (self-reference without default or Optional)")

        # Check if it's a Union containing the class
        if get_origin(typ) is Union:
            args = get_args(typ)
            if cls in args and type(None) not in args:
                raise ShiftValidationError(model_name, field,
                                           "has infinite nesting (Union with self but not Optional)")

def _validate_union_optional(shift_config: ShiftConfig, model_name: str, field: str, typ: Any, val: Any) -> bool:
    # If typ not a Union (Optional = Union[type, None]), invalidate
    if not get_origin(typ) is Union:
        return False

    # If val is any arg(assume arg is not empty), validate
    args = get_args(typ)
    _log_verbose(shift_config.verbosity, ["", "", f"`{field}` is a Union, validating against union args: {args}"])
    for arg in args:
        if _validate_value(shift_config, model_name, field, arg, val):
            return True

    # val is any typ, validate
    return False

def _validate_list_set_tuple(shift_config: ShiftConfig, model_name: str, field: str, typ: Any, var: Any) -> bool:
    # If typ or var are not a list or set, return false
    origin = get_origin(typ)
    if not (origin is list or origin is set or origin is tuple
            or isinstance(var, list) or isinstance(var, set) or isinstance(var, tuple)):
        return False

    _log_verbose(shift_config.verbosity, ["", "", f"`{var}` is a list, set, or tuple"])

    # If typ is un-annotated or var is empty, validate
    args = get_args(typ)
    _log_verbose(shift_config.verbosity, ["", "", f"args: {args}"])
    if not args or not var:
        return True

    # If len(args) == len(var), iterate over both
    if len(args) == len(var):
        for item, arg in zip(var, args):
            if not _validate_value(shift_config, model_name, field, arg, item):
                return False

    # Else iterate over var comparing to arg[0]
    else:
        # If any item in var is not an arg, return false
        for item in var:
            if not _validate_value(shift_config, model_name, field, args[0], item):
                return False

    # All item in var are valid typ, validate
    return True

def _validate_dict(shift_config: ShiftConfig, model_name: str, field: str, typ: Any, dct: Any) -> bool:
    # If typ or dct are not a dict, invalidate
    if not get_origin(typ) is dict or not isinstance(dct, dict):
        return False

    # If typ is un-annotated or dct is empty, validate
    args = get_args(typ)
    _log_verbose(shift_config.verbosity, ["", "", f"`{field}` is a dict, validating against dict args: {args}"])
    if not args or not dct:
        return True

    # If any key is not arg[0], invalidate
    for key in dct.keys():
        if not _validate_value(shift_config, model_name, field, args[0], key):
            return False

    # If args[1] is defined and any val in dct.values is not instance, invalidate
    if len(args) > 1:
        for key in dct.keys():
            if not _validate_value(shift_config, model_name, field, args[1], dct.get(key)):
                return False

    # All key-val in dct match typ, validate
    return True

def _validate_callable(shift_config: ShiftConfig, model_name: str, field: str, typ: Any, func: Any) -> bool:
    # If not callable, invalidate
    if not (get_origin(typ) is Callable or callable(func)):
        return False

    # If typ is unannotated or func is empty, validate
    args = get_args(typ)
    _log_verbose(shift_config.verbosity, ["", "", f"`{field}` is a callable, validating against callable args: {args}"])
    if not args or not func:
        return True

    # Make sure args are formatted correctly
    if len(args) != 2 or not isinstance(args[0], list) or isinstance(args[1], list):
        raise ShiftError(model_name, f"`{field}`: callable type has invalid argument annotations - "
                                     f"should be Callable[[pass_args], return_arg], but Shift got: {args}")

    # Validate passing types
    for arg in args[0]:
        if not _validate_value(shift_config, model_name, field, arg, typ):
            return False

    # Validate returning type
    if not _validate_value(shift_config, model_name, field, args[1], func):
        return False

    # Else validate
    return True

def _validate_shift_validator(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                              validators: dict[str, Any], field: str) -> bool:
    # If shift_validators not allowed, throw
    if not shift_config.allow_shift_validators:
        raise ShiftConfigError(model_name, "allow_shift_validators", False,
                               f"`{field}` has a shift_validator decorator")

    # If invalid, throw
    if not validators[field](self, data, field):
        raise ShiftValidationError(model_name, field, f"`custom shift_validator returned `False`")

    # Validate
    return True

def _validate_value(shift_config: ShiftConfig, model_name: str, field: str, typ: Any, val: Any) -> bool:
    _log_verbose(shift_config.verbosity, ["", "", f"Attempting `{val}` validation against `{typ}`"])

    # If complex type validates, return validation
    if typ is Any:
        if not shift_config.allow_any:
            raise ShiftConfigError(model_name, "allow_any", False,
                                   f"`{field}` is `Any`")
        return True
    elif _validate_union_optional(shift_config, model_name, field, typ, val):
        return True
    elif _validate_list_set_tuple(shift_config, model_name, field, typ, val):
        return True
    elif _validate_dict(shift_config, model_name, field, typ, val):
        return True
    elif _validate_callable(shift_config, model_name, field, typ, val):
        return True

    # If shift subclass, it can validate itself, so validate on this level
    elif _is_shift_subclass(shift_config, model_name, field, typ):
        # If already a type, validate
        if isinstance(val, typ):
            return True
        # If it's a dict, we'll construct it in _set_field, so validate
        elif isinstance(val, dict):
            return True
        # Otherwise invalid
        return False

    # If string or forward ref, validate later
    elif isinstance(typ, str) or isinstance(typ, ForwardRef):
        return True

    # If no complex type validated but simple validation works, validate
    # Use try block here to gracefully handle invalid types
    try:
        if isinstance(val, typ):
            return True
    except Exception as _:
        pass

    # If no type validated, invalidate
    return False

def _validate_field(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                    validators: dict[str, Callable], field: str, typ: Any, val: Any) -> bool:
    _log_verbose(shift_config.verbosity, ["", "", f"Attempting `{field}` validation against `{typ}`"])

    # If shift_validator(field), handle
    if field in validators:
        _log_verbose(shift_config.verbosity, ["", "", f"`{field}` has a shift_validator decorator"])

        # If use shift_validators first or they bypass validation, run first
        if shift_config.use_custom_shift_validators_first or shift_config.custom_shift_validators_bypass_validation:
            # If shift_validator failed, return false
            if not _validate_shift_validator(self, shift_config, model_name, data, validators, field):
                return False

            # If shift_validators bypass, validate
            if shift_config.custom_shift_validators_bypass_validation:
                return True

            # Else validate normally too
            return _validate_value(shift_config, model_name, field, typ, data)

        # Else use default validator then shift_validator
        else:
            # If normal validation failed, return false
            if not _validate_value(shift_config, model_name, field, typ, val):
                return False

            # Then use shift_validator
            if not _validate_shift_validator(self, shift_config, model_name, data, validators, field):
                return False

            # Validate
            return True

    # If typ is a string or forward ref, assume it's a forward ref that will be resolved later
    if isinstance(typ, str) or isinstance(typ, ForwardRef):
        _log_verbose(shift_config.verbosity, ["", "", f"`{field}` is a str or forward ref, validating later"])
        return True

    # Else use default validator
    return _validate_value(shift_config, model_name, field, typ, val)

def _validate_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                        annotations: dict[str, Any], validators: dict[str, Callable],
                        setters: dict[str, Callable]) -> None:
    _log_verbose(shift_config.verbosity, ["", "Validating fields"])

    for field, typ in annotations.items():
        # Get val
        val = _get_val(self, shift_config, model_name, data, field)

        # If val is validated against typ, set (validation errors are handled inside _validate_field)
        if _validate_field(self, shift_config, model_name, data, validators, field, typ, val):
            _log_verbose(shift_config.verbosity, ["", "", f"Validated field `{field}`, setting"])

            # Resolve val again in case it was updated in @shift_validator
            val = _get_val(self, shift_config, model_name, data, field)

            # If typ is a string or forward ref, try to resolve typ
            if isinstance(typ, str) or isinstance(typ, ForwardRef):
                if not shift_config.allow_forward_refs:
                    raise ShiftConfigError(model_name, "allow_forward_refs", False,
                                           f"`{field}` is a str forward ref")

                try:
                    # Resolve typ
                    typ = _resolve_forward_ref(self.__class__, shift_config, model_name, field)

                    # Validate val against resolved typ
                    if _validate_field(self, shift_config, model_name, data, validators, field, typ, val):
                        _set_field(self, shift_config, model_name, data, setters, field, typ, val)
                        continue

                    # If validation failed with val but default exists and is allowed, set with that
                    MISSING = object() # Because this needs to handle default=None, we need a different object
                    if shift_config.allow_defaults and self.__fields__.get(field, MISSING) is not MISSING:
                            continue
                except Exception as e:
                    raise ShiftValidationError(model_name, field,
                                               f"forward ref could not be resolved: {e}")

            # Else set field normally
            else:
                _set_field(self, shift_config, model_name, data, setters, field, typ, val)
                continue

        # Else assume invalid (catch all throw)
        raise ShiftValidationError(model_name, field, f"failed validation against `{typ}`")

def _validate_un_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                           annotations: dict[str, Any], validators: dict[str, Callable],
                           setters: dict[str, Callable]) -> None:
    _log_verbose(shift_config.verbosity, ["", "Setting non-annotated fields"])

    # Get all fields
    fields = {}
    for field in self.__fields__:

        # Filter all magic fields (__ex__) out
        if field not in annotations and not field.startswith("__") and not field.endswith("__"):

            # Filter out all callables (def/function)
            attr = self.__fields__.get(field)
            if not callable(attr):
                fields[field] = attr

    _log_verbose(shift_config.verbosity, ["", "", f"non-annotated fields: {fields}"])

    # Check if non-annotated fields allowed
    if fields and len(fields) > 0 and not shift_config.allow_non_annotated:
        raise ShiftConfigError(model_name, "allow_non_annotated", False,
                               f"non-annotated fields found")

    # Set each field (assume user/interpreter validation)
    for field in fields.keys():
        # If shift_validator for field, validate against that first
        if field in validators and not _validate_shift_validator(self, shift_config, model_name, data, validators,
                                                                 field):
            raise ShiftValidationError(model_name, field, f"custom shift_validator returned `False`")

        # Get val
        val = _get_val(self, shift_config, model_name, data, field)

        # Set (setter errors are handled in function)
        # Note that typ is None here because it's unannotated
        _set_field(self, shift_config, model_name, data, setters, field, None, val)

def _validate(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
              validators: dict[str, Callable], setters: dict[str, Callable]) -> None:
    _log_verbose(shift_config.verbosity, ["", f"Validating class `{model_name}`"])

    # Get annotation vars (dict[field, typ])
    annotations = getattr(self.__class__, "__annotations__", {})
    _log_verbose(shift_config.verbosity, ["", "", f"annotated fields {annotations}"])

    # Validate all vars
    _validate_annotated(self, shift_config, model_name, data, annotations, validators, setters)
    _validate_un_annotated(self, shift_config, model_name, data, annotations, validators, setters)

    _log_verbose(shift_config.verbosity, [f"Validated class `{model_name}`"])

def _handle_unmatched_fields(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                             validators: dict[str, Callable], setters: dict[str, Callable]):
    _log_verbose(shift_config.verbosity, ["", "Checking for unmatched fields"])

    # Get all keys in data that aren't in fields
    args = []
    fields = list(self.__fields__.keys())
    annotations = getattr(self.__class__, "__annotations__", {})
    fields.extend(annotations.keys())
    for arg in data:
        if arg not in fields:
            args.append(arg)

    # If any unmatched fields left, they're unmatched
    if len(args) > 0:
        if not shift_config.allow_unmatched_args:
            raise ShiftConfigError(model_name, "allow_unmatched_args", False,
                                   f"unmatched keys found")
        _log_verbose(shift_config.verbosity, ["", "unmatched keys found, setting", f"Setting unmatched keys: {args}"])

        # For arg add new attr and set
        for arg in args:
            # If shift_validator for field, validate against that first
            if arg in validators:
                _log_verbose(shift_config.verbosity, ["", "", f"`{arg}` has a shift_validator decorator"])

                if not shift_config.allow_shift_validators:
                    raise ShiftConfigError(model_name, "allow_shift_validators", False,
                                           f"`{arg}` has a shift_validator decorator")

                if not _validate_shift_validator(self, shift_config, model_name, data, validators, arg):
                    raise ShiftValidationError(model_name, arg, f" custom shift_validator returned `False`")

            _set_field(self, shift_config, model_name, data, setters, arg, None, data[arg])



# Serialization Functions
########################################################################################################################



def _get_all_fields_with_values(self: Any) -> dict[str, tuple[Any, Any]]:
    fields = {}

    # Annotated fields
    annotations = getattr(self.__class__, "__annotations__", {})
    for field in annotations.keys():
        val = getattr(self, field, None)
        default = self.__fields__.get(field)
        fields[field] = (val, default)

    # Non-annotated and unmatched fields
    for field in self.__fields__.keys():
        if (field not in annotations and not field.startswith("__") and not field.endswith("__") and
                not callable(getattr(self, field, None))):
            val = getattr(self, field, None)
            default = self.__fields__.get(field)
            fields[field] = (val, default)

    # Remove __shift_config__ from fields
    fields.pop("__shift_config__", None)

    return fields

def _repr_field(self: Any, shift_config: ShiftConfig, model_name: str, reprs: dict[str, Callable],
                field: str, val: Any, default: Any) -> Union[str, None]:
    # If field is private not include private fields, return None
    if field.startswith("_") and not shift_config.include_private_fields_in_serialization:
        return None

    # If field in reprs and reprs allowed, use
    if field in reprs:
        if not shift_config.allow_shift_reprs:
            raise ShiftConfigError(model_name, "allow_shift_reprs", False,
                                   "shift repr was called")

        return reprs[field](self, field, val, default)

    # if val is default and not include defaults, return None
    elif val == default and not shift_config.include_defaults_in_serialization:
        return None

    # If val is a str, add quotations and return
    if isinstance(val, str):
        return "\"" + val + "\""

    # If val has __repr__, use
    if has_repr(val):
        # If val equals default, only include if set to
        if not shift_config.include_defaults_in_serialization and val == default:
            return None

        return repr(val)

    # Else return val
    return val

def _serialize_value(val: Any) -> Union[Any, None]:
    # If val has serialize, use
    if has_serializer(val):
        return val.serialize()

    # Elif val is a list, serialize list items
    elif isinstance(val, list):
        return [_serialize_value(item) for item in val]

    # Elif val is dict, serialize items
    elif isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}

    # Elif val is tuple, serialize items
    elif isinstance(val, tuple):
        return tuple(_serialize_value(item) for item in val)

    # Elif val is set, serialize as list
    elif isinstance(val, set):
        return [_serialize_value(item) for item in val]

    # Elif val is any other type, return val
    return val

def _serialize_field(self: Any, shift_config: ShiftConfig, model_name: str, serializers: dict[str, Callable],
                     field: str, val: Any, default: Any) -> Any:
    # If field is private not include private fields, return None
    if field.startswith("_") and not shift_config.include_private_fields_in_serialization:
        return None

    # If field in serializers and serializers allowed, use
    if field in serializers:
        if not shift_config.allow_shift_serializers:
            raise ShiftConfigError(model_name, "allow_shift_serializers", False,
                                   "shift serializer was called")

        return serializers[field](self, field, val, default)

    # Elif val is default and not include defaults, return None
    elif val == default and not shift_config.include_defaults_in_serialization:
        return None

    # Else serialize val
    return _serialize_value(val)



# Shift
########################################################################################################################



class ShiftMeta(type):
    """This is a helper metaclass used in namespace resolution to resolve forward references"""

    def __new__(mcls, name, bases, namespace):
        # Call normal class __new__ and save
        cls = super().__new__(mcls, name, bases, namespace)

        # Get class local namespace (class body)
        cls.__creation_ns__ = namespace.copy()

        # Capture frame locals - we need to go back TWO frames
        # Frame 0: __new__ (this function)
        # Frame 1: type.__call__ (Python's class creation)
        # Frame 2: Where the class is actually defined (what we want!)
        frame = inspect.currentframe()
        try:
            if frame is not None:
                # Go back two frames to get the actual definition location
                caller_frame = frame.f_back
                if caller_frame is not None:
                    caller_frame = caller_frame.f_back
                    if caller_frame is not None:
                        cls.__frame_locals__ = caller_frame.f_locals.copy()
                    else:
                        cls.__frame_locals__ = {}
                else:
                    cls.__frame_locals__ = {}
            else:
                cls.__frame_locals__ = {}
        finally:
            # Clean up frame reference to avoid reference cycles
            del frame

        return cls

class Shift(metaclass=ShiftMeta):
    """Base class that enables automatic validation of annotated class attributes.

    Any class that inherits from this one can declare annotated attributes,
    and instances may then be constructed from dictionaries or keyword
    arguments with validation automatically applied.

    Attributes:
        __shift_config__ (ShiftConfig): Configuration object controlling
            validation behavior. If ``None``, the global
            ``DEFAULT_SHIFT_CONFIG`` is used.
    """



    def __init_subclass__(cls):
        # Get class fields (all vars, annotations, defs, etc)
        cls.__fields__ = getattr(cls, "__dict__", {}).copy()

    def __init__(self, **data):
        # Get the class name to print useful log/error messages
        model_name = self.__class__.__name__

        # Get ShiftConfig (should always be `__shift_config__`)
        shift_config = _get_shift_config(self, model_name)

        # Get decorators
        _set_decorators(self.__class__, shift_config, model_name)

        # Check decorators now if configured to
        if not shift_config.lazy_validate_decorators:
            _validate_decorators(shift_config, model_name,
                                 self.__class__.__validators__, self.__class__.__setters__,
                                 self.__class__.__reprs__, self.__class__.__serializers__)

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__fields__:
            _log_verbose(shift_config.verbosity, [f"Calling __pre_init__ for `{model_name}`"])
            self.__fields__["__pre_init__"](self, data)

        # Only run validation steps if configured to
        if not shift_config.skip_validation:

            # Check decorators now if configured to
            if shift_config.lazy_validate_decorators:
                _validate_decorators(shift_config, model_name,
                                     self.__class__.__validators__, self.__class__.__setters__,
                                     self.__class__.__reprs__, self.__class__.__serializers__)

            # Validate infinite nesting if configured to
            if shift_config.validate_infinite_nesting:
                _validate_infinite_nesting(self.__class__, shift_config, model_name)

            # Get validators and setters
            validators = self.__validators__
            _log_verbose(shift_config.verbosity, ["", "", f"validators: {validators}"])
            setters = self.__setters__
            _log_verbose(shift_config.verbosity, ["", "", f"setters: {setters}"])

            # Log class attributes
            _log_verbose(shift_config.verbosity, ["", "", f"class attributes: {self.__fields__}"])

            # Run validation
            _validate(self, shift_config, model_name, data, validators, setters)

            # Handle unmatched fields
            _handle_unmatched_fields(self, shift_config, model_name, data, validators, setters)

        # If cls has __post_init__(), call
        if "__post_init__" in self.__fields__:
            _log_verbose(shift_config.verbosity, [f"Calling __post_init__ for `{model_name}`"])
            self.__fields__["__post_init__"](self, data)



    def __repr__(self) -> str:
        """
        Returns a string representation of the object inheriting Shift, such that that str representation could be
        used to rebuild that specific instance.

        Inheriting classes can use this function either by not implementing __repr__ or by calling super().__repr__()
        """

        # Get inheriting class name and shift config
        model_name = self.__class__.__name__
        shift_config = _get_shift_config(self, model_name)

        if not shift_config.use_builtin_shift_repr:
            raise ShiftConfigError(model_name, "use_builtin_shift_repr", False,
                                   " the builtin shift repr was called")

        args: list[str] = []

        # Add shift config when set to
        if shift_config.include_shift_config_in_serialization:
            # Add __shift_config__ if it's not the default value
            if shift_config.include_defaults_in_serialization and shift_config != DEFAULT_SHIFT_CONFIG:
                args.append(f"__shift_config__={repr(shift_config)}")

        # Add all fields
        for field, (val, default) in _get_all_fields_with_values(self).items():
            arg = _repr_field(self, shift_config, model_name, self.__reprs__, field, val, default)
            if arg is not None:
                args.append(f"{field}={arg}")

        # Return string representation of class with args
        return f"{model_name}({', '.join(args)})"

    def serialize(self) -> dict[str, Any]:
        """
        Returns a dict representation of the object inheriting Shift, such that that dict representation could be used
        to rebuild that specific instance.

        Inheriting classes can use this function either by not implementing to_dict or by calling super().to_dict()
        """

        # Get inheriting class name and shift config
        model_name = self.__class__.__name__
        shift_config = _get_shift_config(self, model_name)

        if not shift_config.use_builtin_shift_serializer:
            raise ShiftConfigError(model_name, "use_builtin_shift_serializer", False,
                                   " the builtin shift serializer was called")

        result: dict[str, Any] = {}

        # Add shift config when set to
        if shift_config.include_shift_config_in_serialization:
            # Add __shift_config__ if it's not the default value
            if shift_config.include_defaults_in_serialization and shift_config != DEFAULT_SHIFT_CONFIG:
                result["__shift_config__"] = shift_config.serialize()

        # Add all fields
        for field, (val, default) in _get_all_fields_with_values(self).items():
            arg = _serialize_field(self, shift_config, model_name, self.__serializers__, field, val, default)
            if arg is not None:
                result[field] = arg

        # Return dict representation of class
        return result

    def __eq__(self, other: Any) -> bool:
        """Returns whether the other instance has all the same attribute settings as this instance"""
        if has_serializer(other):
            return self.serialize() == other.serialize()
        return False

    def __copy__(self) -> Any:
        """Returns a copy of this instance"""
        return self.__class__(**self.serialize())

    def __deepcopy__(self, memo: dict) -> Any:
        """Returns a deep copy of this instance"""
        return self.__class__(**self.serialize())
