# Imports
########################################################################################################################



# Used to set up ShiftConfig
from dataclasses import dataclass

# Used to check types in _validate()
from typing import get_origin, get_args, get_type_hints, Any, Union

# used for type hints in functions
from typing import Type, Callable

# Used to evaluate str forward refs
import sys
import inspect



# Misc Classes & Decorators
########################################################################################################################



# This just helps with ShiftConfig __repr__ and to_dict
_shift_config_defaults: dict[str, Any] = {
    "verbosity": 0,
    "do_validation": True,
    "allow_unmatched_args": False,
    "allow_any": True,
    "allow_defaults": True,
    "allow_non_annotated": True,
    "allow_shift_validators": True,
    "shift_validators_have_precedence": True,
    "use_shift_validators_first": False,
}

@dataclass
class ShiftConfig:
    """
    This dataclass holds all the configuration options for a Shift class

    Attributes:

        Misc:
            verbosity: int = 0 [0, 3]
                The level of debug messages to print
                0: No debug messages
                1: Validation step messages
                2. Validation var step messages
                3: All config and attribute messages
            catch_decorator_errors_early: bool = True
                Whether to check decorator allowed config options early or to wait until they are called
                False: If decorator is found when it is not allowed, wait to throw until decorator called
                True: If decorator is found when it is not allowed, throw immediately

        Validation:
            do_validation: bool = True
                Whether to validate any vars
                False: When instantiated skip validation and DONT SET VARS!
                True: When instantiated validate vars and set vars
            allow_unmatched_args: bool = False
                Whether allow unmatched arguments (args that don't match any cls attributes)
                False: When unmatched arg is passed throw
                True: When unmatched arg is passed create new class attribute and set
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
                False: If var.annotation is `None` throw
                True: If var.annotation is `None` set var (no type checks for validation unless `shit_validator` is set for
                var)
            allow_forward_refs: bool = True
                Whether to allow forward refs via str
                False: If type annotation is str, throw
                True: If type annotation is str, try to resolve type name and validate with it
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
            use_shift_validators_first: bool = False
                Whether to perform built-in validation first or use a shift validator first for a given var
                (if shift_validators_have_precedence is True, this will be ignored)
                False: If shift_validator(var) is not `None`, use it after default validation
                True: If shift_validator(var) is not `None`, use it before default validation
            allow_shift_setters: bool = True
                Whether to allow custom shift setters (custom setters for vars via decorator: `@shift_setter(var) -> None`)
                False: If shift_setter(var) is not `None` throw
                True: If shift_setter(var) is not `None` call
            allow_nested_shift_classes: bool = True
                Whether to allow Shift subclasses during validation
                False: If any field is a Shift sub class throw
                True: If any field is a Shift sub class validate var

        repr/to_dict:
            use_shift_repr: bool = True
                Whether to do anything if shift_subclass.__repr__ is called
                False: If shift_subclass.__repr__ is called, return None
                True: If shift_subclass.__repr__ is called, return shift-generated repr
            use_shift_serializers: bool = True
                Whether to do anything if shift_subclass.serialize is called
                False: If shift_subclass.serialize is called, return None
                True: If shift_subclass.serialize is called, return shift-generated dict
            include_defaults: bool = False
                Whether to include default values in repr/to_dict output
                False: If field.val == field.default, do not include field in repr/to_dict output
                True: If field.val == field.default, include field in repr/to_dict output
            include_private_fields: bool = False
                Whether to include private fields in repr/to_dict output
                False: If field.name.startswith('_'), do not include field in repr/to_dict output
                True: If field.name.startswith('_'), include field in repr/to_dict output
            allow_shift_reprs: bool = True
                Whether to allow custom shift repr (custom repr for vars via decorator: `@shift_repr(var) -> str`)
                False: If shift_repr(var) is not `None` throw
                True: If shift_repr(var) is not `None` call
            allow_shift_serializers: bool = True
                Whether to allow custom shift serialize (custom to_dict for vars via decorator:
                `@shift_to_dict(var) -> dict[str, Any]`)
                False: If shift_to_dict(var) is not `None` throw
                True: If shift_to_dict(var) is not `None` call

    """

    verbosity: int = 0
    catch_decorator_errors_early: bool = True

    do_validation: bool = True
    allow_unmatched_args: bool = False
    allow_any: bool = True
    allow_defaults: bool = True
    allow_non_annotated: bool = True
    allow_forward_refs: bool = True
    allow_shift_validators: bool = True
    shift_validators_have_precedence: bool = True
    use_shift_validators_first: bool = False
    allow_shift_setters: bool = True
    allow_nested_shift_classes: bool = True

    use_shift_repr: bool = True
    use_shift_serializers: bool = True
    include_defaults: bool = False
    include_private_fields: bool = False
    allow_shift_reprs: bool = True
    allow_shift_serializers: bool = True



    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ShiftConfig) and self.serialize() == other.serialize()

    def __repr__(self):
        parts = []
        for key, default_val in _shift_config_defaults.items():
            val = getattr(self, key)
            if val != default_val:
                parts.append(f"{key}={val}")

        args = ", ".join(parts)
        return f"ShiftConfig({args})"

    def serialize(self) -> dict[str, Any]:
        result = {}
        for key, default_val in _shift_config_defaults.items():
            val = getattr(self, key)
            if val != default_val:
                result[key] = val
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



# Value Management Functions
########################################################################################################################



def _set_decorators(cls: Type) -> None:
    # Create new fields in cls
    cls.__validators__ = {}
    cls.__setters__ = {}
    cls.__reprs__ = {}
    cls.__serializers__ = {}

    # Fill decorators
    for name, value in cls.__dict__.items():
        # If value is callable test if it has a shift marker
        if callable(value):

            # If shift_validator, add to validators for each field
            if hasattr(value, '__validator_for__'):
                fields = value.__validator_for__
                for field in fields:
                    cls.__validators__[field] = value
                continue

            # If shift_setter, add to setters for each field
            elif hasattr(value, '__setter_for__'):
                fields = value.__setter_for__
                for field in fields:
                    cls.__setters__[field] = value
                continue

            # If shift_repr, add to reprs for each field
            elif hasattr(value, '__repr_for__'):
                fields = value.__repr_for__
                for field in fields:
                    cls.__reprs__[field] = value

            # If shift_serialize_for, add to __serialize_for__ for each field
            elif hasattr(value, '__serialize_for__'):
                fields = value.__serialize_for__
                for field in fields:
                    cls.__serializers__[field] = value

# Note that self is not annotated as Shift because that's undefined here
def _get_shift_config(self: Any, model_name: str) -> ShiftConfig:
    # Get ShiftConfig (should always be `__shift_config__`) and check the type
    shift_config = self.__fields__.get("__shift_config__")
    if shift_config and not isinstance(shift_config, ShiftConfig):
        raise TypeError(f"`{model_name}`: __shift_config__ must be a ShiftConfig instance")

    # If no shift config provided, use global default
    if shift_config:
        _log_verbose(shift_config.verbosity,["", "__shift_config__ set"])
    else:
        shift_config = DEFAULT_SHIFT_CONFIG

    _log_verbose(shift_config.verbosity, ["", "", "", f"shift_config: {shift_config}"])
    return shift_config

def _resolve_forward_ref(cls, field) -> Any:
    # Start with the class's own namespace
    local_namespace = getattr(cls, "__creation_namespace__", {}).copy()

    # Try to get locals from the calling context by walking up the stack
    frame = inspect.currentframe()
    # Walk up the stack to find frames that might contain the forward-referenced class
    search_frame = frame
    while search_frame is not None:
        frame_locals = search_frame.f_locals
        # Merge locals from each frame in the stack
        if frame_locals:
            local_namespace.update(frame_locals)
        search_frame = search_frame.f_back

    # Fallback to module globals
    global_namespace = sys.modules[cls.__module__].__dict__

    hints = get_type_hints(cls, globalns=global_namespace, localns=local_namespace)
    return hints[field]

def _get_val(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any], field: str) -> Any:
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

def _is_shift_subclass(shift_config: ShiftConfig, typ: Any) -> bool:
    try:
        if isinstance(typ, type) and issubclass(typ, Shift):
            if not shift_config.allow_nested_shift_classes:
                raise ValueError(
                    f"`{typ}` is a nested Shift class, but `shift_config.allow_nested_shift_classes` is `False`")
            return True
    except TypeError:
        # issubclass raises TypeError for non-classes like Union, List, etc.
        return False
    return False

def _set_field(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
               setters: dict[str, Callable], field: str, typ: Any, val: Any) -> None:
    # If shift_setter(field), use
    if field in setters:
        # If shift_setters not allowed, throw
        if not shift_config.allow_shift_setters:
            raise ValueError(f"`{model_name} has a `@shift_setter({field})` decorator but `shift_config.allow_shift_setters` is `False`")
        setters[field](self, data, field)
        return

    # Else if typ is a shift subclass and val is a dict, set with validation
    elif _is_shift_subclass(shift_config, typ) and isinstance(val, dict):
        try:
            setattr(self, field, typ(**val))
        except Exception as e:
            raise TypeError(f"`{model_name}`: Failed to construct `{typ.__name__}` for field `{field}`: {e}")
        return

    # Else set as normal value
    setattr(self, field, val)



# Validation Functions
########################################################################################################################



def _validate_union_optional(shift_config: ShiftConfig, typ: Any, val: Any) -> bool:
    # If typ not a Union (Optional = Union[type, None]), invalidate
    if not get_origin(typ) is Union:
        return False

    # If val is any arg(assume arg is not empty), validate
    args = get_args(typ)
    for arg in args:
        if _validate_value(shift_config, arg, val):
            return True

    # val is any typ, validate
    return False

def _validate_list_set_tuple(shift_config: ShiftConfig, typ: Any, var: Any) -> bool:
    # If typ or var are not a list or set, return false
    origin = get_origin(typ)
    if not (origin is list or origin is set or origin is tuple
            or isinstance(var, list) or isinstance(var, set) or isinstance(var, tuple)):
        return False

    # If typ is un-annotated or var is empty, validate
    args = get_args(typ)
    if not args or not var:
        return True

    # If len(args) == len(var), iterate over both
    if len(args) == len(var):
        for item, arg in zip(var, args):
            if not _validate_value(shift_config, arg, item):
                return False

    # Else iterate over var comparing to arg[0]
    else:
        # If any item in var is not an arg, return false
        for item in var:
            if not _validate_value(shift_config, args[0], item):
                return False

    # All item in var are valid typ, validate
    return True

def _validate_dict(shift_config: ShiftConfig, typ: Any, dct: Any) -> bool:
    # If typ or dct are not a dict, invalidate
    if not get_origin(typ) is dict or not isinstance(dct, dict):
        return False

    # If typ is un-annotated or dct is empty, validate
    args = get_args(typ)
    if not args or not dct:
        return True

    # If any key is not arg[0], invalidate
    for key in dct.keys():
        if not _validate_value(shift_config, args[0], key):
            return False

    # If args[1] is defined and any val in dct.values is not instance, invalidate
    if len(args) > 1:
        for key in dct.keys():
            if not _validate_value(shift_config, args[1], dct.get(key)):
                return False

    # All key-val in dct match typ, validate
    return True

def _validate_shift_validator(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                              validators: dict[str, Any], field: str) -> bool:
    # If shift_validators not allowed, throw
    if not shift_config.allow_shift_validators:
        raise ValueError(f"`{model_name}`: a shift_validator decorator is being used for `{field}`, but `shift_config.allow_shift_validators` is `False`")

    # If invalid, throw
    if not validators[field](self, data, field):
        raise ValueError(f"`{model_name}`: `shift_validator({field})` validation failed (did not return True)")

    # Validate
    return True

def _validate_value(shift_config: ShiftConfig, typ: Any, val: Any) -> bool:
    _log_verbose(shift_config.verbosity, ["", "", f"Attempting `{val}` validation against `{typ}`"])

    # If complex type validates, return validation
    if typ is Any:
        if not shift_config.allow_any:
            raise ValueError(f"Type is `Any` but shift_config.allow_any is `False`")
        return True
    elif _validate_union_optional(shift_config, typ, val):
        return True
    elif _validate_list_set_tuple(shift_config, typ, val):
        return True
    elif _validate_dict(shift_config, typ, val):
        return True

    # If shift subclass, it can validate itself, so validate on this level
    elif _is_shift_subclass(shift_config, typ):
        # If already a type, validate
        if isinstance(val, typ):
            return True
        # If it's a dict, we'll construct it in _set_field, so validate
        elif isinstance(val, dict):
            return True
        # Otherwise invalid
        return False

    # If no complex type validated but simple validation works, validate
    # Use try block here to gracefully handle invalid types
    try:
        if isinstance(val, typ):
            return True
    except TypeError:
        pass

    # If no type validated, invalidate
    return False

def _validate_field(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                    validators: dict[str, Callable], field: str, typ: Any, val: Any) -> bool:
    _log_verbose(shift_config.verbosity, ["", "", f"Attempting `{field}` validation against `{typ}`"])

    # If shift_validator(field), handle
    if field in validators:
        # If use shift_validators before or they have precedence, use
        if shift_config.use_shift_validators_first or shift_config.shift_validators_have_precedence:
            # If shift_validator failed, return false
            if not _validate_shift_validator(self, shift_config, model_name, data, validators, field):
                return False

            # If shift_validators have precedence, validate
            if shift_config.shift_validators_have_precedence:
                return True

            # Else validate normally too
            return _validate_value(shift_config, typ, data)

        # Else use default validator then shift_validator
        else:
            # If normal validation failed, return false
            if not _validate_value(shift_config, typ, data):
                return False

            # Then use shift_validator
            if not _validate_shift_validator(self, shift_config, model_name, data, validators, field):
                return False

            # Validate
            return True

    # If typ is a string, assume it's a forward ref that will be resolved later
    if isinstance(typ, str):
        return True

    # Else use default validator
    return _validate_value(shift_config, typ, val)

def _validate_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                        annotations: dict[str, Any], validators: dict[str, Callable],
                        setters: dict[str, Callable]) -> None:
    _log_verbose(shift_config.verbosity, ["Validating fields"])

    for field, typ in annotations.items():
        # Get val
        val = _get_val(self, shift_config, model_name, data, field)

        # If val is validated against typ, set (if validation fails throw is done in function)
        if _validate_field(self, shift_config, model_name, data, validators, field, typ, val):
            _log_verbose(shift_config.verbosity, ["", "", f"Validated field `{field}`, setting"])

            # If typ is a string, try to resolve it
            if isinstance(typ, str):
                if not shift_config.allow_forward_refs:
                    raise ValueError(f"Type is a str forward ref, but `shift_config.allow_forward_refs` is `False`")
                try:
                    # Resolve typ
                    typ = _resolve_forward_ref(self.__class__, field)

                    # Validate typ
                    if _validate_field(self, shift_config, model_name, data, validators, field, typ, val):
                        _set_field(self, shift_config, model_name, data, setters, field, typ, val)
                        continue
                except Exception as e:
                    raise TypeError(f"`{model_name}`: `{field}`'s forward ref could not be resolved") from e

            # Else set field normally
            else:
                _set_field(self, shift_config, model_name, data, setters, field, typ, val)
                continue

        # Else assume invalid (catch all throw)
        raise TypeError(f"`{model_name}`: `{field}` has invalid type")

def _validate_un_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                           annotations: dict[str, Any], validators: dict[str, Callable],
                           setters: dict[str, Callable]) -> None:
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
        # If shift_validator for field, validate against that first
        if field in validators and not _validate_shift_validator(self, shift_config, model_name, data, validators, field):
            raise ValueError(f"`{model_name}`: `{field}` shift_validator failed")


        # Get val
        val = _get_val(self, shift_config, model_name, data, field)

        # Set (setter errors are handled in function)
        # Note that typ is None here because it's unannotated
        _set_field(self, shift_config, model_name, data, setters, field, None, val)

def _validate(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
              validators: dict[str, Callable], setters: dict[str, Callable]) -> None:
    _log_verbose(shift_config.verbosity, [f"Validating class `{model_name}`"])

    # Get annotation vars (dict[field, typ])
    annotations = getattr(self.__class__, "__annotations__", {})
    _log_verbose(shift_config.verbosity, ["", "", f"annotated fields {annotations}"])

    # Validate all vars
    _validate_annotated(self, shift_config, model_name, data, annotations, validators, setters)
    _validate_un_annotated(self, shift_config, model_name, data, annotations, validators, setters)

    _log_verbose(shift_config.verbosity, [f"Validated class `{model_name}`"])

def _handle_unmatched_fields(self: Any, shift_config: ShiftConfig, model_name: str, data: dict[str, Any],
                             setters: dict[str, Callable]):
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
            raise ValueError(
                f"`{model_name}` has unmatched args fields but `shift_config.allow_unmatched_args` is `False`")
        _log_verbose(shift_config.verbosity, ["", "unmatched keys found, setting", f"Unmatched keys: {args}"])

        # For arg add new attr and set
        for arg in args:
            _log_verbose(shift_config.verbosity, ["", "", f"set {arg}"])
            _set_field(self, shift_config, model_name, data, setters, arg, None, data[arg])



# repr/to_dict Functions
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
    if field.startswith("_") and not shift_config.include_private_fields:
        return None

    # If field in reprs and reprs allowed, use
    if field in reprs:
        if not shift_config.allow_shift_reprs:
            raise ValueError(f"`{model_name}`: a shift_repr decorator is being used for `{field}`, but `shift_config.allow_shift_repr` is `False`")
        return reprs[field](self, field, val, default)

    # if val is default and not include defaults, return None
    elif val == default and not shift_config.include_defaults:
        return None

    # If val has __repr__, use
    if has_repr(val):
        # If val equals default, only include if set to
        if not shift_config.include_defaults and val == default:
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
    if field.startswith("_") and not shift_config.include_private_fields:
        return None

    # If field in serializers and serializers allowed, use
    if field in serializers:
        if not shift_config.allow_shift_serializers:
            raise ValueError(f"`{model_name}`: a shift_serialize decorator is being used for `{field}`, but `shift_config.allow_shift_serialize` is `False`")
        return serializers[field](self, field, val, default)

    # Elif val is default and not include defaults, return None
    elif val == default and not shift_config.include_defaults:
        return None

    # Else serialize val
    return _serialize_value(val)



# Shift
########################################################################################################################



class ShiftMeta(type):
    """This is a helper metaclass used in namespace resolution to resolve forward references"""

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        cls.__creation_namespace__ = namespace
        return cls

class Shift(metaclass=ShiftMeta):
    """
    This is a helper base class that can be used on any normal python class to automatically validate class attributes.

    To use this class, have any other class you want to validate inherit `Shift`. Then annotate each var or cls
    attribute you want to validate and build the class from a dict or using named-args

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
        __repr__() -> str
            Returns a string representation of the object inheriting Shift
        __to_dict__() -> dict[str, Any]
            Returns a dict representation of the object inheriting Shift
    """



    def __init_subclass__(cls):
        # Get class fields (all vars, annotations, defs, etc)
        cls.__fields__ = getattr(cls, "__dict__", {}).copy()

        # Find all decorators
        _set_decorators(cls)

    def __init__(self, **data):
        # Get the class name to print useful log/error messages
        model_name = self.__class__.__name__

        # Get ShiftConfig (should always be `__shift_config__`) and check type
        shift_config = _get_shift_config(self, model_name)

        # Check decorators
        if shift_config.catch_decorator_errors_early:
            _log_verbose(shift_config.verbosity, [f"Checking decorators for `{model_name}`"])

            if not shift_config.allow_shift_validators and "__shift_validator__" in self.__fields__ and len(self.__validators__) > 0:
                raise ValueError(f"`{model_name}`: has shift_validator decorators but `shift_config.allow_shift_validators` is `False`")

            if not shift_config.allow_shift_setters and "__shift_setter__" in self.__fields__ and len(self.__setters__) > 0:
                raise ValueError(f"`{model_name}`: has shift_setter decorators but `shift_config.allow_shift_setters` is `False`")

            if not shift_config.allow_shift_reprs and "__shift_repr__" in self.__fields__ and len(self.__reprs__) > 0:
                raise ValueError(f"`{model_name}`: has shift_repr decorators but `shift_config.allow_shift_repr` is `False`")

            if not shift_config.allow_shift_serializers and "__shift_serializers__" in self.__fields__ and len(self.__to_dicts__) > 0:
                raise ValueError(f"`{model_name}`: has shift_to_dict decorators but `shift_config.allow_shift_to_dict` is `False`")

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__fields__:
            _log_verbose(shift_config.verbosity, [f"Calling __pre_init__ for `{model_name}`"])
            self.__fields__["__pre_init__"](self, data)

        # Only run validation steps if configured to
        if shift_config.do_validation:
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
            _handle_unmatched_fields(self, shift_config, model_name, data, setters)

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

        if not shift_config.use_shift_repr:
            return ""

        args: list[str] = []

        # Add __shift_config__ if it's not the default value
        if shift_config != DEFAULT_SHIFT_CONFIG:
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

        if not shift_config.use_shift_serializers:
            return {}

        result: dict[str, Any] = {}

        # Add __shift_config__ if it's not the default value
        if shift_config != DEFAULT_SHIFT_CONFIG:
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