# Imports
########################################################################################################################



# Data containers
from dataclasses import dataclass

# Check types in validation
from typing import get_origin, get_args, get_type_hints, Any, Union, ForwardRef, Type, Optional, Literal, TypeAlias
from collections.abc import Iterable, Callable

# Evaluate forward references and check function signatures
import inspect, sys



# Global Registers & Defaults
########################################################################################################################



# Global type category registers
#   Leave override here in case users want an easy way to add more static types
_shift_types: dict[Type, ShiftType] = {}

# Resolved forward refs registers (cache)
_resolved_forward_refs: dict[str, Type] = {}

# Global info registers (metadata)
#   By leaving this here we can keep global references of static class elements like config and decorated class defs
_shift_info_registry: dict[Type, ShiftInfo] = {}

# Global function registers, used to skip inspecting shift-decorated functions
#   True is advanced, False is simple
_shift_functions: dict[Callable, bool] = {}



# Logging & Errors
########################################################################################################################



def _log(msg: str) -> None:
    # Only print if msg has text
    if msg and len(msg):
        print(msg)

def log_verbose(verbosity: int, msg: list[str]):
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

class ShiftError(Exception):
    """Base class for all starshift errors"""
    def __init__(self, model_name: str, msg: str):
        super().__init__(f"StarShift: {model_name}: {msg}")



# Decorators
########################################################################################################################



## Type Aliases
############################################################

_SimpleTransformer: TypeAlias = Callable[[Any, Any], Any]
_AdvancedTransformer: TypeAlias = Callable[[Any, "ShiftField", "ShiftInfo"], Any]
_Transformer: TypeAlias = _SimpleTransformer | _AdvancedTransformer

_SimpleValidator: TypeAlias = Callable[[Any, Any], bool]
_AdvancedValidator: TypeAlias = Callable[[Any, "ShiftField", "ShiftInfo"], bool]
_Validator: TypeAlias = _SimpleValidator | _AdvancedValidator

_SimpleSetter: TypeAlias = Callable[[Any, Any], None]
_AdvancedSetter: TypeAlias = Callable[[Any, "ShiftField", "ShiftInfo"], None]
_Setter: TypeAlias = _SimpleSetter | _AdvancedSetter

_SimpleRepr: TypeAlias = Callable[[Any, Any], str]
_AdvancedRepr: TypeAlias = Callable[[Any, "ShiftField", "ShiftInfo"], str]
_Repr: TypeAlias = _SimpleRepr | _AdvancedRepr

_SimpleSerializer: TypeAlias = Callable[[Any, Any], Any]
_AdvancedSerializer: TypeAlias = Callable[[Any, "ShiftField", "ShiftInfo"], Any]
_Serializer: TypeAlias = _SimpleSerializer | _AdvancedSerializer

_Any_Decorator: TypeAlias = _Transformer | _Validator | _Setter | _Repr | _Serializer



## Decorator Defs
############################################################

# noinspection PyTypeChecker
def shift_transformer(*fields: str, pre: bool=False, skip_when_pre: bool=True) -> Callable[[_Transformer], _Transformer]:
    """Decorator to mark a function as a shift transformer

    pre: marks this function to run before global type transformers
    skip_when_pre: skips global type transformers when running before global type transformers
    """

    def decorator(func):
        func.__shift_transformer_for__ = fields
        func.__shift_transformer_pre__ = pre
        func.__shift_transformer_skip__ = skip_when_pre if pre else False
        return func
    return decorator

# noinspection PyTypeChecker
def shift_validator(*fields: str, pre: bool=False, skip_when_pre: bool=True) -> Callable[[_Validator], _Validator]:
    """Decorator to mark a function as a shift validator

    pre: marks this function to run in the pre-validation phase
    skip_when_pre: skips shift validation when running in the pre-validation phase
    """

    def decorator(func):
        func.__shift_validator_for__ = fields
        func.__shift_validator_pre__ = pre
        func.__shift_validator_skip__ = skip_when_pre if pre else False
        return func
    return decorator

# noinspection PyTypeChecker
def shift_setter(*fields: str) -> Callable[[_Setter], _Setter]:
    """Decorator to mark a function as a shift setter"""

    def decorator(func):
        func.__shift_setter_for__ = fields
        return func
    return decorator

# noinspection PyTypeChecker
def shift_repr(*fields: str) -> Callable[[_Repr], _Repr]:
    """Decorator to mark a function as a shift repr"""

    def decorator(func):
        func.__shift_repr_for__ = fields
        return func
    return decorator

# noinspection PyTypeChecker
def shift_serializer(*fields: str) -> Callable[[_Serializer], _Serializer]:
    """Decorator to mark a function as a shift serializer"""

    def decorator(func):
        func.__shift_serializer_for__ = fields
        return func
    return decorator



## Wrapper
############################################################

def shift_function_wrapper(field: ShiftField, info: ShiftInfo, func: Callable) -> Any | None:
    """Wrapper to automatically determine if the function is advanced or not, and call appropriately, returning the result"""
    # Check cache first
    if func in _shift_functions:
        if _shift_functions[func]:
            return func(info.instance, field, info)
        return func(info.instance, field.val)

    # Get function signature
    sig = inspect.signature(func)

    # If len(params) == 2, it's a simple function
    if len(sig.parameters) == 2:
        _shift_functions[func] = False
        return func(info.instance, field.val)

    # Else if len(params) == 3 and it expects a ShiftField and ShiftInfo, it's an advanced function
    expects_shift_field = False
    expects_shift_info = False
    for param in sig.parameters.values():
        if param.annotation == ShiftField:
            expects_shift_field = True
        elif param.annotation == ShiftInfo:
            expects_shift_info = True
    if len(sig.parameters) == 3 and expects_shift_field and expects_shift_info:
        _shift_functions[func] = True
        return func(info.instance, field, info)

    # Else invalid signature
    raise ShiftError(info.model_name, f"Invalid signature for {field.name}: {func.__name__}")



# Shift Types
########################################################################################################################



# Sentinel object to check for missing values
class Missing:
    def __repr__(self):
        return 'Missing'
    def __bool__(self) -> bool:
        return False

@dataclass
class ShiftInfo:
    """Data class for storing validation info

    Attributes:
        instance (Any): The class instance being validated
        model_name (str): Name of the model/class being validated
        shift_config (ShiftConfig): All config options to govern
        fields (list[ShiftField]): List of fields
        pre_transformer_skips (list[str]): List of field names to skip after pre-transformers run
        pre_transformers (dict[str, Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]]): Dict of field names to pre-transformer
        transformers (dict[str, Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]]): Dict of field names to transformers
        pre_validator_skips (list[str]): List of field names to skip after pre-validators run
        pre_validators (dict[str, Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]]): Dict of field names to pre-validators
        validators (dict[str, Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]]): Dict of field names to validators
        setters (dict[str, Callable[[Any], None] | Callable[[ShiftField, ShiftInfo], None]]): Dict of field names to setters
        reprs (dict[str, Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]]): Dict of field names to reprs
        serializers (dict[str, Callable[[Any], dict[str, Any] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]]]): Dict of field names to serializers
        data (dict[str, Any]): Dict of field names to values (kwargs)
        errors (list[ShiftError]): List of errors accumulated during validation
    """
    instance: Any
    model_name: str
    shift_config: ShiftConfig
    fields: list[ShiftField]
    pre_transformer_skips: list[str]
    pre_transformers: dict[str, _Transformer]
    transformers: dict[str, _Transformer]
    pre_validator_skips: list[str]
    pre_validators: dict[str, _Validator]
    validators: dict[str, _Validator]
    setters: dict[str, _Setter]
    reprs: dict[str, _Repr]
    serializers: dict[str, _Serializer]
    data: dict[str, Any]
    errors: list[ShiftError]

@dataclass
class ShiftField:
    """Data class for storing validation info

    Attributes:
        name (str): Name of the field
        typ (Any): Type hint of the field; Default: _missing
        val (Any): Value of the field; Default: _missing
        default (Any): Default value of the field; Default: _missing
    """
    name: str
    typ: Any = Missing
    val: Any = Missing
    default: Any = Missing



## Builtin Type Functions
############################################################

### Transformers
###############################

def _resolve_forward_ref(typ: str | ForwardRef, info: ShiftInfo) -> Type:
    # Convert forward ref to string
    if isinstance(typ, ForwardRef):
        typ = typ.__forward_arg__

    # Check if already resolved
    if typ in _resolved_forward_refs:
        return _resolved_forward_refs[typ]

    # Check if typ is the current class
    if typ == info.model_name:
        _resolved_forward_refs[typ] = info.instance.__class__
        return info.instance.__class__

    # Check if typ is in global model info cache
    for cls in _shift_info_registry.keys():
        if typ == cls.__name__:
            _resolved_forward_refs[typ] = cls
            return cls

    # Check module where class is defined
    try:
        cls_type = type(info.instance)
        module = sys.modules.get(cls_type.__module__)
        if module and hasattr(module, typ):
            resolved = getattr(module, typ)
            _resolved_forward_refs[typ] = resolved
            return resolved
    except (AttributeError, KeyError):
        pass

    # Check builtins
    import builtins
    if hasattr(builtins, typ):
        resolved = getattr(builtins, typ)
        _resolved_forward_refs[typ] = resolved
        return resolved

    # Else raise exception
    raise ShiftError(info.model_name, f"Could not resolve forward reference: {typ}")

def _shift_forward_ref_type_transformer(instance: Any, field: ShiftField, info: ShiftInfo) -> Any:
    # Resolve forward ref
    _ = _resolve_forward_ref(field.typ, info)

    # Run normal transformer
    return shift_type_transformer(instance, field, info)

def shift_type_transformer(instance: Any, field: ShiftField, info: ShiftInfo) -> Any:
    if field.val is Missing:
        return field.default if field.default is not Missing else None
    return field.val

### Validators
###############################

def _shift_missing_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # This function is used for static attributes (non-annotated fields with defaults)

    # If val is _missing, assume the field is missing, so return False
    if field.val is Missing:
        return False

    # Else assume valid (no type hint to compare against)
    return True

def _shift_base_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # If base type, check if instance of typ
    try:
        return isinstance(field.val, field.typ)

    # Was not instance - broad exception to catch all errors, we can handle them later
    except Exception:
        return False

def _shift_any_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    return True

def _shift_literal_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no literal args, nothing to validate
    if not args:
        return True

    # If val is not in literal args, return False
    return field.val in args

def _shift_one_of_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # Try all args until match is found
    for arg in args:
        if shift_type_validator(instance, arg, field.val, field, info):
            return True

    # No matches found
    return False

def _shift_all_of_single_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # If more args than single can handle, return False
    if len(args) > 1:
        return False

    # If val is not iterable, return False
    if not isinstance(field.val, Iterable):
        return False

    # Check all args
    for val in field.val:
        if not shift_type_validator(instance, args[0], val, field, info):
            return False

    # All args matched
    return True

def _shift_all_of_many_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # If val does not have a len, return False
    if not isinstance(field.val, Iterable):
        return False

    # If lens don't match, return False
    # noinspection PyTypeChecker
    if len(field.val) != len(args):
        return False

    # Check all val-arg pairs
    for val, arg in zip(field.val, args):
        if not shift_type_validator(instance, arg, val, field, info):
            return False

    # All val-arg pairs matched
    return True

def _shift_all_of_pair_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # If val does not have items(), return False
    if not hasattr(field.val, "items"):
        return False

    # Check all keys and vals against args
    for key, val in field.val.items():
        if not shift_type_validator(instance, args[0], key, field, info):
            return False
        if len(args) > 1 and not shift_type_validator(instance, args[1], val, field, info):
            return False

    # All key-val-arg pairs matched
    return True

def _shift_callable_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # If val is not callable, return False
    if not callable(field.val):
        return False

    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # Callable type args should be [param_types, return_type]
    if len(args) != 2:
        return False
    param_types = args[0]
    return_type = args[1]

    # Get the actual function signature
    try:
        sig = inspect.signature(field.val)
    except (ValueError, TypeError):
        # Some callables don't have inspectable signatures (built-ins, C extensions)
        return True

    # Check parameter count
    params = list(sig.parameters.values())

    # Handle special case: Callable[..., ReturnType] means "any params"
    if param_types is Ellipsis or param_types == ...:
        # Just check return type
        if return_type is not inspect.Signature.empty:
            if sig.return_annotation == inspect.Signature.empty:
                return False  # Expected return type but function has none
            if sig.return_annotation != return_type:
                return False
        return True

    # Check parameter count matches
    if len(params) != len(param_types):
        return False

    # Check each parameter's annotation matches expected type
    for param, expected_type in zip(params, param_types):
        if param.annotation == inspect.Parameter.empty:
            # Function has no annotation for this parameter
            continue

        # Check if annotation matches expected type
        if param.annotation != expected_type:
            return False

    # Check return type annotation
    if return_type is not inspect.Signature.empty:
        if sig.return_annotation == inspect.Signature.empty:
            return False  # Expected return type but function has none
        if sig.return_annotation != return_type:
            return False

    return True

def _shift_shift_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # If already the right type, return True
    ## Save cached val because isinstance will change it
    cached_val = field.val
    try:
        if isinstance(field.val, field.typ):
            return True

    # Was not instance - throws on fail
    except Exception:
        return False

    # Else if val is a dict, try to validate it
    field.val = cached_val
    if isinstance(field.val, dict):
        try:
            # Try to instantiate it, store value for later
            field.val = field.typ(**field.val) # noqa
            return True

        # Invalid subclass data
        except ShiftError as e:
            # Raise again to get collected upstream
            raise e

        # Not a shift subclass?
        except Exception as e:
            info.errors.append(ShiftError(info.model_name, f"Attempt to instantiate shift subclass failed: {e}"))

    # No way to validate, possibly improper type assignment?
    return False

def _shift_forward_ref_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # Check cache first
    if field.typ in _resolved_forward_refs:
        resolved = _resolved_forward_refs[field.typ]
        return shift_type_validator(instance, resolved, field.val, field, info)

    # Resolve the forward ref
    try:
        resolved = _resolve_forward_ref(field.typ, info)
        _resolved_forward_refs[field.typ] = resolved
        return shift_type_validator(instance, resolved, field.val, field, info)
    except Exception as e:
        raise ShiftError(info.model_name, f"Could not resolve forward reference for {field.name}: {e}")

def shift_type_validator(instance: Any, typ: Any, val: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # Get shift type
    shift_typ = get_shift_type(typ)

    # If not a shift type, try a simple isinstance check
    if not shift_typ:
        try:
            return isinstance(val, typ)
        except Exception:
            return False

    # Build temporary ShiftField for validation, and call validator
    temp_field = ShiftField(name=f"{field.name}.{typ}", typ=typ, val=val)
    return shift_typ.validator(instance, temp_field, info)

### Setters
###############################

def shift_type_setter(instance: Any, field: ShiftField, info: ShiftInfo) -> None:
    try:
        setattr(info.instance, field.name, field.val)
    except Exception as e:
        info.errors.append(ShiftError(info.model_name, f"Error occurred while setting {field.name}: {e}"))

### Reprs
###############################

def shift_type_repr(instance: Any, field: ShiftField, info: ShiftInfo) -> str:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return ""
    return repr(field.val)

### Serializers
###############################

def _shift_missing_type_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> None:
    return None

def _shift_base_type_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> Any:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None
    return field.val

def _shift_all_of_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> list[Any] | None:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    vals = []
    for val in field.val:
        vals.append(shift_type_serializer(instance, type(val), val, field, info))
    return vals

def _shift_all_of_pair_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> dict[str, Any] | None:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    vals = {}
    for key, val in field.val.items():
        vals[key] = shift_type_serializer(instance, type(val), val, field, info)
    return vals

def _shift_shift_type_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> dict[str, Any] | None:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    return field.val.serialize()

def _shift_forward_ref_type_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> Any:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    return shift_type_serializer(instance, field.typ, field.val, field, info)

def shift_type_serializer(instance: Any, typ: Any, val: Any, field: ShiftField, info: ShiftInfo) -> Any:
    # Get shift type
    shift_typ = get_shift_type(field.typ)

    # If not a shift type, return the field's value as-is
    if not shift_typ:
        return {field.name: field.val}

    # Build temporary ShiftField for serialization and call serializer
    temp_field = ShiftField(name=f"{field.name}.{typ}", typ=typ, val=val)
    return shift_function_wrapper(temp_field, info, shift_typ.serializer)



## Shift Type
############################################################

@dataclass
class ShiftType:
    """Universal type interface for all validation types

    Attributes:
        transformer (Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]): The type transformer function; Default: shift_transformer
        validator (Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]): The type validator function; Default: shift_validator
        setter (Callable[[Any, Any], None] | Callable[[ShiftField, ShiftInfo], None]): The type setter function; Default: shift_setter
        repr (Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]): The type repr function; Default: shift_repr
        serializer (Callable[[Any], dict[str, Any]] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]): The type serializer function; Default: shift_serializer
    """
    transformer: _Transformer = shift_type_transformer
    validator: _Validator = _shift_base_type_validator
    setter: _Setter = shift_type_setter
    repr: _Repr = shift_type_repr
    serializer: _Serializer = _shift_base_type_serializer

def get_shift_type(typ: Any) -> ShiftType | None:
    # If typ has no hash, we can't use it as a key in a dict
    if not hasattr(typ, "__hash__"):
        return None

    # If in types, return the type
    if typ in _shift_types:
        return _shift_types[typ]

    # If origin in types, return the type
    origin = get_origin(typ)
    if origin in _shift_types:
        return _shift_types[origin]

    # If type is a ForwardRef, return the type
    if isinstance(typ, ForwardRef):
        return _shift_types[ForwardRef]

    # If type is a Shift subclass, return shift type
    try:
        if issubclass(typ, Shift):
            return _shift_types[Shift]
    except Exception:
        pass

    # Get type of object and check if it's in the registry
    typ = type(typ)
    if typ in _shift_types:
        return _shift_types[typ]

    # Else type is unknown, return None
    return None



## Builtin Types
############################################################

_missing_shift_type = ShiftType(shift_type_transformer,
                                _shift_missing_type_validator, shift_type_setter,
                                shift_type_repr, _shift_missing_type_serializer)
_base_shift_type = ShiftType(shift_type_transformer,
                             _shift_base_type_validator, shift_type_setter,
                             shift_type_repr, _shift_base_type_serializer)
_any_shift_type = ShiftType(shift_type_transformer,
                            _shift_any_type_validator, shift_type_setter,
                            shift_type_repr, _shift_base_type_serializer)
_literal_shift_type = ShiftType(shift_type_transformer,
                                _shift_literal_type_validator, shift_type_setter,
                                shift_type_repr, _shift_base_type_serializer)
_one_of_shift_type = ShiftType(shift_type_transformer,
                               _shift_one_of_type_validator, shift_type_setter,
                               shift_type_repr, _shift_base_type_serializer)
_all_of_single_shift_type = ShiftType(shift_type_transformer,
                                      _shift_all_of_single_validator, shift_type_setter,
                                      shift_type_repr, _shift_all_of_serializer)
_all_of_many_shift_type = ShiftType(shift_type_transformer,
                                    _shift_all_of_many_validator, shift_type_setter,
                                    shift_type_repr, _shift_all_of_serializer)
_all_of_pair_shift_type = ShiftType(shift_type_transformer,
                                    _shift_all_of_pair_validator, shift_type_setter,
                                    shift_type_repr, _shift_all_of_pair_serializer)
_shift_callable_shift_type = ShiftType(shift_type_transformer,
                                       _shift_callable_validator, shift_type_setter,
                                       shift_type_repr, _shift_base_type_serializer)
_shift_shift_type = ShiftType(shift_type_transformer,
                              _shift_shift_type_validator, shift_type_setter,
                              shift_type_repr, _shift_shift_type_serializer)
_forward_ref_shift_type = ShiftType(_shift_forward_ref_type_transformer,
                                    _shift_forward_ref_type_validator, shift_type_setter,
                                    shift_type_repr, _shift_forward_ref_type_serializer)

_shift_builtin_types: dict[Type, ShiftType] = {
    Missing: _missing_shift_type,

    type(None): _base_shift_type,
    int: _base_shift_type,
    bool: _base_shift_type,
    float: _base_shift_type,
    str: _base_shift_type,
    bytes: _base_shift_type,
    bytearray: _base_shift_type,

    Any: _any_shift_type,

    list: _all_of_single_shift_type,
    set: _all_of_single_shift_type,
    frozenset: _all_of_single_shift_type,

    tuple: _all_of_many_shift_type,

    Callable: _shift_callable_shift_type,

    dict: _all_of_pair_shift_type,

    Union: _one_of_shift_type,
    Optional: _one_of_shift_type,

    Literal: _literal_shift_type,

    # This is registered after Shift is defined
    #Shift: _shift_shift_type,

    ForwardRef: _forward_ref_shift_type,
}



# Config
########################################################################################################################



@dataclass
class ShiftConfig:
    """Configuration for shift phases

    Attributes:
        verbosity (int): Logging level: 0 = silent, 1 = error, 2 = warnings, 3 = info, 4 = debug; Default: 0
        fail_fast (bool): If True, processing will stop on the first error encountered. Default; False
        do_processing (bool): If True, on init all fields will be transformed, validated, and set. If False, you must manually set everything (use __post_init__); Default: True
        try_coerce_types (bool): If True, Shift will attempt to coerce types where possible. If False, all types must match exactly; Default: False
        allow_private_field_setting (bool): If False, Shift will not throw when a class is instantiated with a private field val; Default: False
        include_default_fields_in_serialization (bool): If True, default value fields will be serialized (used in repr too); Default: False
        include_private_fields_in_serialization (bool): If True, private fields will be serialized (used in repr too); Default: False
    """
    verbosity: int = 0
    do_processing: bool = True
    fail_fast: bool = False
    try_coerce_types: bool = False
    allow_private_field_setting: bool = False
    include_default_fields_in_serialization: bool = False
    include_private_fields_in_serialization: bool = False



    def __eq__(self, other):
        if not isinstance(other, ShiftConfig):
            return False
        return serialize(self) == serialize(other)

    def __ne__(self, other):
        return not self == other

    def __bool__(self):
        return self is not None

    def __repr__(self) -> str:
        result: list[str] = []
        if self.verbosity != 0:
            result.append(f"verbosity={self.verbosity}")
        if not self.do_processing:
            result.append(f"do_processing={self.do_processing}")
        if self.fail_fast:
            result.append(f"fail_fast={self.fail_fast}")
        if self.try_coerce_types:
            result.append(f"try_coerce_types={self.try_coerce_types}")
        if self.allow_private_field_setting:
            result.append(f"allow_private_field_setting={self.allow_private_field_setting}")
        if self.include_default_fields_in_serialization:
            result.append(f"include_default_fields_in_serialization={self.include_default_fields_in_serialization}")
        if self.include_private_fields_in_serialization:
            result.append(f"include_private_fields_in_serialization={self.include_private_fields_in_serialization}")
        return f"ShiftConfig({', '.join(result)})"

    def serialize(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.verbosity != 0:
            result['verbosity'] = self.verbosity
        if not self.do_processing:
            result['do_processing'] = self.do_processing
        if self.fail_fast:
            result['fail_fast'] = self.fail_fast
        if self.try_coerce_types:
            result['try_coerce_types'] = self.try_coerce_types
        if self.allow_private_field_setting:
            result['allow_private_field_setting'] = self.allow_private_field_setting
        if self.include_default_fields_in_serialization:
            result['include_default_fields_in_serialization'] = self.include_default_fields_in_serialization
        if self.include_private_fields_in_serialization:
            result['include_private_fields_in_serialization'] = self.include_private_fields_in_serialization
        return result

    def __copy__(self) -> ShiftConfig:
        return ShiftConfig(
            verbosity=self.verbosity,
            fail_fast=self.fail_fast,
            do_processing=self.do_processing,
            try_coerce_types=self.try_coerce_types,
            allow_private_field_setting=self.allow_private_field_setting,
            include_default_fields_in_serialization=self.include_default_fields_in_serialization,
            include_private_fields_in_serialization=self.include_private_fields_in_serialization,
        )



## Presets
############################################################

DEFAULT_SHIFT_CONFIG = ShiftConfig()



# Shift Processing Functions
########################################################################################################################



## Transform
############################################################

def _transform_field(field: ShiftField, info: ShiftInfo) -> None:
    # Call pre-transformer if present
    if field.name in info.pre_transformers:
        field.val = shift_function_wrapper(field, info, info.pre_transformers[field.name])
    if field.name in info.pre_transformers and field.name in info.pre_transformer_skips:
        return

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call transformer
    field.val = shift_function_wrapper(field, info, shift_typ.transformer)

    # Call field transformer if present
    if field.name in info.transformers:
        field.val = shift_function_wrapper(field, info, info.transformers[field.name])

def _transform(info: ShiftInfo) -> None:
    # Transform all class fields
    for field in info.fields:
        try:
            _transform_field(field, info)
        except ShiftError as e:
            info.errors.append(e)



## Validate
############################################################

def _validate_field(field: ShiftField, info: ShiftInfo) -> bool:
    # Call pre-validator if present
    if field.name in info.pre_validators and not shift_function_wrapper(field, info, info.pre_validators[field.name]):
        return False
    if field.name in info.pre_validators and field.name in info.pre_validator_skips:
        return True

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call validator
    if not shift_function_wrapper(field, info, shift_typ.validator):
        return False

    # Call field validator if present
    if field.name in info.validators and not shift_function_wrapper(field, info, info.validators[field.name]):
        return False

    return True

def _validate(info: ShiftInfo) -> bool:
    all_valid = True
    for field in info.fields:
        try:
            if not _validate_field(field, info):
                all_valid = False
                raise ShiftError(info.model_name, f"Validation failed for {field.name}")
        except ShiftError as e:
            info.errors.append(ShiftError(info.model_name, f"Validation failed for {field.name}: {e}"))

    return all_valid



## Set
############################################################

def _set_field(field: ShiftField, info: ShiftInfo) -> None:
    # If field setter, call
    if field.name in info.setters:
        shift_function_wrapper(field, info, info.setters[field.name])
        return

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call shift type setter
    shift_function_wrapper(field, info, shift_typ.setter)

def _set(info: ShiftInfo) -> None:
    for field in info.fields:
        try:
            _set_field(field, info)
        except ShiftError as e:
            info.errors.append(e)



## Repr
############################################################

def _repr_field(field: ShiftField, info: ShiftInfo) -> str:
    # If field repr, call
    if field.name in info.reprs:
        return shift_function_wrapper(field, info, info.reprs[field.name])

    # If field name is private and config set to exclude, return
    if field.name.startswith("_") and not info.shift_config.include_private_fields_in_serialization:
        return ""

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call shift type repr
    return shift_function_wrapper(field, info, shift_typ.repr)

def _repr(info: ShiftInfo) -> str:
    res: list[str] = []
    if info.shift_config.include_private_fields_in_serialization and (info.shift_config != DEFAULT_SHIFT_CONFIG or info.shift_config.include_default_fields_in_serialization):
        res.append(f"__shift_config__={repr(info.shift_config)}")
    for field in info.fields:
        r = (_repr_field(field, info))
        if r and len(r):
            res.append(field.name + "=" + r)
    return f"{info.model_name}({', '.join(res)})"



## Serialize
############################################################

def _serialize_field(field: ShiftField, info: ShiftInfo) -> dict[str, Any] | None:
    # If field serializer, call
    if field.name in info.serializers:
        return shift_function_wrapper(field, info, info.serializers[field.name])

    # If field name is private and config set to exclude, return
    if field.name.startswith("_") and not info.shift_config.include_private_fields_in_serialization:
        return None

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call shift type serializer
    return shift_function_wrapper(field, info, shift_typ.serializer)

def _serialize(info: ShiftInfo) -> dict[str, Any]:
    result = {}
    if info.shift_config.include_private_fields_in_serialization and (info.shift_config != DEFAULT_SHIFT_CONFIG or info.shift_config.include_default_fields_in_serialization):
        result["__shift_config__"] = serialize(info.shift_config)
    for field in info.fields:
        res = _serialize_field(field, info)
        if res is not None:
            result[field.name] = res
    return result



# Shift Classes
########################################################################################################################



## Class Init Functions
############################################################

def get_shift_config(cls, fields: dict) -> ShiftConfig | None:
    # Get shift_config from cls if it exists
    shift_config = fields.get("__shift_config__")
    if shift_config and not isinstance(shift_config, ShiftConfig):
        raise ShiftError(cls.__name__, "`__shift_config__` must be a ShiftConfig instance")

    # If no shift config provided, use global default
    if shift_config:
        log_verbose(shift_config.verbosity, ["", "__shift_config__ set"])
    else:
        shift_config = DEFAULT_SHIFT_CONFIG

    log_verbose(shift_config.verbosity, ["", "", f"shift_config: {shift_config}"])
    return shift_config.__copy__()

def get_field_decorators(cls: Any, fields: dict) -> dict[str, list[_Any_Decorator] | list[str]]:
    # Create the return dict structure
    dct = {
        "pre_transformer_skips": [],
        "pre_transformers": {},
        "transformers": {},
        "pre_validator_skips": [],
        "pre_validators": {},
        "validators": {},
        "setters": {},
        "reprs": {},
        "serializers": {}
    }

    # Find and process decorators in fields
    for field_name in fields.keys():
        # Skip magic fields
        if field_name.startswith("__") and field_name.endswith("__"):
            continue

        # Get value
        try:
            val = getattr(cls, field_name, Missing)
        except AttributeError:
            continue

        # Skip non-callable fields
        if not inspect.ismethod(val) and not inspect.isfunction(val) and not callable(val):
            continue

        # If transformer, check if pre and if skip, add
        if hasattr(val, '__shift_transformer_for__'):
            field_names = val.__shift_transformer_for__
            pre = getattr(val, '__shift_transformer_pre__', False)
            skip = getattr(val, '__shift_transformer_skip__', False)
            for field_name in field_names:
                if pre:
                    dct["pre_transformers"][field_name] = val
                    if skip:
                        dct["pre_transformer_skips"].append(field_name)
                else:
                    dct["transformers"][field_name] = val

        # If validator, check if pre and if skip, add
        if hasattr(val, '__shift_validator_for__'):
            field_names = val.__shift_validator_for__
            pre = getattr(val, '__shift_validator_pre__', False)
            skip = getattr(val, '__shift_validator_skip__', False)
            for field_name in field_names:
                if pre:
                    dct["pre_validators"][field_name] = val
                    if skip:
                        dct["pre_validator_skips"].append(field_name)
                else:
                    dct["validators"][field_name] = val

        # If setter, add
        if hasattr(val, '__shift_setter_for__'):
            field_names = val.__shift_setter_for__
            for field_name in field_names:
                dct["setters"][field_name] = val

        # If repr, add
        if hasattr(val, '__shift_repr_for__'):
            field_names = val.__shift_repr_for__
            for field_name in field_names:
                dct["reprs"][field_name] = val

        # If serializer, add
        if hasattr(val, '__shift_serializer_for__'):
            field_names = val.__shift_serializer_for__
            for field_name in field_names:
                dct["serializers"][field_name] = val

    # Return decorators dict
    return dct

def get_fields(cls: Any, fields: dict, data: dict, shift_config: ShiftConfig = DEFAULT_SHIFT_CONFIG) -> list[ShiftField]:
    shift_fields: list[ShiftField] = []

    # Get all annotated fields - use try because forward references break get_type_hints
    try:
        annotated = get_type_hints(cls)
    except NameError:
        annotated = cls.__annotations__.copy() if hasattr(cls, "__annotations__") else {}

    for field_name, field_type in annotated.items():
        # Skip magic fields
        if field_name.startswith("__") and field_name.endswith("__"):
            continue

        # Get default value
        try:
            default = getattr(cls, field_name, Missing)
        except AttributeError:
            continue

        # Get val from data if exists
        val = Missing
        if field_name in data:
            val = data[field_name]

        # If field is private, has a data-set value, and allow setting is false, throw
        if field_name.startswith("_") and val is not Missing and not shift_config.allow_private_field_setting:
            raise ShiftError(cls.__name__, f"{field_name} has a set value in data, but allow_private_field_setting is False")

        # Add to shift_fields list
        shift_fields.append(ShiftField(name=field_name, typ=field_type, val=val, default=default))

    # Get all non-annotated fields
    for field_name in fields.keys():
        # Skip annotated fields
        if field_name in annotated:
            continue

        # Skip magic fields
        if field_name.startswith("__") and field_name.endswith("__"):
            continue

        # Get value
        try:
            val = getattr(cls, field_name, Missing)
        except AttributeError:
            continue

        # Skip class/static methods, properties, etc.
        if inspect.ismethod(val) or inspect.isfunction(val) or callable(val):
            continue

        # Get val from data if exists
        default = val
        if field_name in data:
            val = data[field_name]

            # If field is private, has a data-set value, and allow setting is false, throw
            if field_name.startswith("_") and val is not Missing and not shift_config.allow_private_field_setting:
                raise ShiftError(cls.__name__,f"{field_name} has a set value in data, but allow_private_field_setting is False")

        # Add to shift_fields list
        shift_fields.append(ShiftField(name=field_name, val=val, default=default))

    # Return shift_fields list
    return shift_fields

def get_updated_fields(instance: Any, fields: list[ShiftField], data: dict, shift_config: ShiftConfig = DEFAULT_SHIFT_CONFIG) -> list[ShiftField]:
    updated_fields = []
    for field in fields:
        # If name is private, a data val is present, and allow setting is false, throw
        if field.name.startswith("_") and field.name in data and not shift_config.allow_private_field_setting:
            raise ShiftError(instance.__class__.__name__, f"{field.name} has a set value in data, but allow_private_field_setting is False")

        # Create a NEW ShiftField instead of mutating the cached one
        new_val = data.get(field.name, field.default)
        updated_fields.append(ShiftField(
            name=field.name,
            typ=field.typ,
            val=new_val,
            default=field.default
        ))
    return updated_fields

def get_val_fields(instance: Any, fields: list[ShiftField]) -> list[ShiftField]:
    val_fields = []
    for field in fields:
        if hasattr(instance, field.name):
            val_fields.append(ShiftField(
                name=field.name,
                typ=field.typ,
                val=getattr(instance, field.name),
                default=field.default
            ))
    return val_fields

# noinspection PyTypeChecker
def get_shift_info(cls: Any, instance: Any, data: dict) -> ShiftInfo:
    # If cls is in model_info, return copy so non-persistent data is not kept
    if cls in _shift_info_registry:
        cached_info = _shift_info_registry[cls]
        # Build new copied info
        info = ShiftInfo(
            instance=instance,
            model_name=cached_info.model_name,
            shift_config=cached_info.shift_config,
            # This always needs to be updated with the new data
            fields=get_updated_fields(instance, cached_info.fields, data, cached_info.shift_config),
            pre_transformer_skips=cached_info.pre_transformer_skips,
            pre_transformers=cached_info.pre_transformers,
            transformers=cached_info.transformers,
            pre_validator_skips=cached_info.pre_validator_skips,
            pre_validators=cached_info.pre_validators,
            validators=cached_info.validators,
            setters=cached_info.setters,
            reprs=cached_info.reprs,
            serializers=cached_info.serializers,
            data=data,
            errors=[]
        )
        return info

    # Else build new info and add to model_info
    ## Get all fields (annotated, non-annotated, functions, etc
    cls_dict = getattr(cls, "__dict__", {}).copy()
    ## Get config, shift_fields, and decorators
    shift_config = get_shift_config(cls, cls_dict)
    shift_fields = get_fields(cls, cls_dict, data, shift_config)
    decorators = get_field_decorators(cls, cls_dict)
    ## Build info class
    info = ShiftInfo(
        instance=instance,
        model_name=cls.__name__,
        shift_config=shift_config,
        fields=shift_fields,
        pre_transformer_skips=decorators["pre_transformer_skips"],
        pre_transformers=decorators["pre_transformers"],
        transformers=decorators["transformers"],
        pre_validator_skips=decorators["pre_validator_skips"],
        pre_validators=decorators["pre_validators"],
        validators=decorators["validators"],
        setters=decorators["setters"],
        reprs=decorators["reprs"],
        serializers=decorators["serializers"],
        data=data,
        errors=[]
    )

    # Register info and return it
    _shift_info_registry[cls] = info
    return info



## Classes
############################################################

class Shift:
    """Base class for all shift models"""

    def __init__(self, **data):
        # Get shift info
        info = get_shift_info(self.__class__, self, data)

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__class__.__dict__:
            self.__class__.__dict__["__pre_init__"](self, info)

        # Run transform, validation, and set processes
        if info.shift_config.do_processing:
            self.validate(info) # Runs transform
            self.set(info)

        # If cls has __post_init__(), call
        if "__post_init__" in self.__class__.__dict__:
            self.__class__.__dict__["__post_init__"](self, info)



    def transform(self, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, data)

        # Run transform process
        _transform(info)

    def validate(self, info: ShiftInfo=None, **data) -> bool:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, data)

        # Run transform process
        self.transform(info, **data)

        # Run validation, throw if fail
        if not _validate(info):
            errors = []
            for e in info.errors:
                errors.append(str(e))
            raise ShiftError(info.model_name, f"Validation failed: {errors}")
        return True

    def set(self, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, data)

        # Run set process
        _set(info)
        if len(info.errors):
            errors = []
            for e in info.errors:
                errors.append(str(e))
            raise ShiftError(info.model_name, f"Set failed: {errors}")

    def __repr__(self, info: ShiftInfo=None) -> str:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, {})

        # Get fields with current values
        info.fields = get_val_fields(self, info.fields)

        # Run repr process
        return _repr(info)

    def serialize(self, info: ShiftInfo=None) -> dict[str, Any]:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, {})

        # Get fields with current values
        info.fields = get_val_fields(self, info.fields)

        # Run serialization process
        return _serialize(info)



    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.serialize() == other.serialize()

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.serialize().items())))

    def __copy__(self) -> Any:
        return type(self)(**self.serialize())

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        return type(self)(**self.serialize())



# Utilities
########################################################################################################################



## Shift Types
############################################################

def get_shift_type_registry() -> dict[Type, ShiftType]:
    """Returns a copy of the shift type registry"""
    return _shift_types.copy()

def register_shift_type(typ: Type, shift_type: ShiftType) -> None:
    """Registers a shift type"""
    _shift_types[typ] = shift_type

def deregister_shift_type(typ: Type) -> None:
    """Deregisters a shift type"""
    if typ not in _shift_types:
        raise ShiftError("<module>", f"Type `{typ}` is not registered")
    del _shift_types[typ]

def clear_shift_types() -> None:
    """Clears all registered shift types"""
    _shift_types.clear()



## Forward Refs
############################################################

def get_forward_ref_registry() -> dict[str, Type]:
    """Returns a copy of the forward ref registry"""
    return _resolved_forward_refs.copy()

def register_forward_ref(ref: str | ForwardRef, typ: Type) -> None:
    """Registers a forward ref to a resolved type"""
    if isinstance(ref, ForwardRef):
        ref = ref.__forward_arg__
    _resolved_forward_refs[ref] = typ

def deregister_forward_ref(ref: str | ForwardRef) -> None:
    """Deregisters a resolved forward ref"""
    if isinstance(ref, ForwardRef):
        ref = ref.__forward_arg__
    if ref not in _resolved_forward_refs:
        raise ShiftError("<module>", f"Forward ref `{ref}` is not registered")
    del _resolved_forward_refs[ref]

def clear_forward_refs() -> None:
    """Clears all registered forward refs"""
    _resolved_forward_refs.clear()



## Shift Infos
############################################################

def get_shift_info_registry() -> dict[Any, ShiftInfo]:
    """Returns a copy of the model info registry"""
    return _shift_info_registry.copy()

def clear_shift_info_registry() -> None:
    """Clears the shift info cache for a shift class"""
    _shift_info_registry.clear()



## Shift Functions
############################################################

def get_shift_function_registry() -> dict[Callable[[_Any_Decorator], bool], bool]:
    """Returns a copy of the shift function registry"""
    return _shift_functions.copy()

def clear_shift_function_registry() -> None:
    """Clears the shift function cache"""
    _shift_functions.clear()



## Misc
############################################################

def serialize(instance: Any, throw: bool = True) -> dict[str, Any] | None:
    """Try to call instance.serialize() if the instance has the attribute, else it conditionally throws an error"""
    if not hasattr(instance, "serialize") or not callable(instance.serialize):
        if throw:
            raise ShiftError(instance.__class__.__name__, f".serialize() does not exist on the given instance, but serialize was called")
        return None
    return instance.serialize() # noqa

def reset_starshift_globals() -> None:
    """Reset all global registers and values"""
    _shift_types.clear()
    _shift_types.update(_shift_builtin_types)
    _shift_types[Shift] = _shift_shift_type
    _resolved_forward_refs.clear()
    _shift_info_registry.clear()
    _shift_functions.clear()

    # Re-use existing default config to avoid val vs ref errors
    global DEFAULT_SHIFT_CONFIG
    DEFAULT_SHIFT_CONFIG.verbosity = 0
    DEFAULT_SHIFT_CONFIG.do_processing = True
    DEFAULT_SHIFT_CONFIG.fail_fast = False
    DEFAULT_SHIFT_CONFIG.try_coerce_types = False
    DEFAULT_SHIFT_CONFIG.include_default_fields_in_serialization = False
    DEFAULT_SHIFT_CONFIG.include_private_fields_in_serialization = False

# Setup starshift
reset_starshift_globals()
