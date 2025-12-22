# Imports
########################################################################################################################



# Data containers
from dataclasses import dataclass

# Check types in validation
from typing import get_args, get_type_hints, Any, Union, ForwardRef, Type, Callable, Optional, Literal, TypeAlias

# Evaluate forward references and check function signatures
import sys, inspect



# Global Registers & Defaults
########################################################################################################################



# Global type category registers
#   Leave override here in case users want an easy way to add more static types
_shift_types: dict[Type, ShiftType] = {}

# Resolved forward refs registers (cache)
_resolved_forward_refs: dict[str, Type] = {}

# Global info registers (metadata)
#   By leaving this here we can keep global references of static class elements like config and decorated class defs
_model_info: dict[Type, ShiftInfo] = {}

# Global function registers, used to skip inspecting shift-decorated functions
#   True is advanced, False is simple
_shift_functions: dict[Callable, bool] = {}



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

def shift_setter(*fields: str) -> Callable[[_Setter], _Setter]:
    """Decorator to mark a function as a shift setter

    The double any is so we can pass in `self`"""

    def decorator(func):
        func.__shift_setter_for__ = fields
        return func
    return decorator

def shift_repr(*fields: str) -> Callable[[_Repr], _Repr]:
    """Decorator to mark a function as a shift repr"""

    def decorator(func):
        func.__shift_repr_for__ = fields
        return func
    return decorator

def shift_serializer(*fields: str) -> Callable[[_Serializer], _Serializer]:
    """Decorator to mark a function as a shift serializer"""

    def decorator(func):
        func.__shift_serializer_for__ = fields
        return func
    return decorator



## Advanced + Wrapper
############################################################

def shift_advanced(func: _Any_Decorator) -> _Any_Decorator:
    """Decorator to mark a function as an advanced shift decorator"""
    func.__shift_advanced__ = True
    return func

def shift_function_wrapper(field: ShiftField, info: ShiftInfo, func: Callable) -> Any | None:
    """Wrapper to automatically determine if the function is advanced or not, and call appropriately, returning the result"""
    # Check cache first
    if func in _shift_functions:
        if _shift_functions[func]:
            return shift_advanced(func)(info.instance, field, info)
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
MISSING = object()

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
        typ (Any): Type hint of the field; Default: MISSING
        val (Any): Value of the field; Default: MISSING
        default (Any): Default value of the field; Default: MISSING
    """
    name: str
    typ: Any = MISSING
    val: Any = MISSING
    default: Any = MISSING

@dataclass
class ShiftType:
    """Universal type interface for all validation types

    Attributes:
        transformer (Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]): The type transformer function
        validator (Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]): The type validator function
        setter (Callable[[Any, Any], None] | Callable[[ShiftField, ShiftInfo], None]): The type setter function
        repr (Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]): The type repr function
        serializer (Callable[[Any], dict[str, Any]] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]): The type serializer function
    """
    transformer: _Transformer
    validator: _Validator
    setter: _Setter
    repr: _Repr
    serializer: _Serializer

def get_shift_type(typ: Any) -> ShiftType | None:
    # If typ has no hash, we can't use it as a key in a dict
    if not hasattr(typ, "__hash__"):
        return None

    # If in types, return the type
    if typ in _shift_types:
        return _shift_types[typ]

    # If type is a Shift subclass, return shift type
    try:
        if issubclass(typ, Shift):
            return _shift_types[Shift]
    except Exception as e:
        pass

    # Else type is unknown, return None
    return None



## Builtin Type Functions
############################################################

### Transformers
###############################

def _shift_type_transformer(instance: Any, field: ShiftField, info: ShiftInfo) -> Any:
    if field.val is MISSING:
        return field.default if field.default is not MISSING else None
    return field.val

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
    for cls in _model_info.keys():
        if typ == cls.__name__:
            _resolved_forward_refs[typ] = cls
            return cls

    # Check module where class is defined
    try:
        cls_type = type(info.instance)
        module = inspect.getmodule(cls_type.__module__)
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
    return _shift_type_transformer(instance, field, info)

### Validators
###############################

def _shift_missing_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # This function is used for static attributes (non-annotated fields with defaults)

    # If val is MISSING, assume the field is missing, so return False
    if field.val is MISSING:
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

def _shift_one_of_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # Try all args until match is found
    for arg in args:
        if _shift_type_validator(instance, arg, field.val, field, info):
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

    # Check all args
    for val in field.val:
        if not _shift_type_validator(instance, args[0], val, field, info):
            return False

    # All args matched
    return True

def _shift_all_of_many_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # If lens don't match, return False
    if len(field.val) != len(args):
        return False

    # Check all val-arg pairs
    for val, arg in zip(field.val, args):
        if not _shift_type_validator(instance, arg, val, field, info):
            return False

    # All val-arg pairs matched
    return True

def _shift_all_of_pair_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # Check all keys and vals against args
    for key, val in field.val.items():
        if not _shift_type_validator(instance, args[0], key, field, info):
            return False
        if len(args) > 1 and not _shift_type_validator(instance, args[1], val, field, info):
            return False

    # All key-val-arg pairs matched
    return True

def _shift_shift_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # If already the right type, return True
    try:
        if isinstance(field.val, field.typ):
            return True

    # Was not instance - throws on fail
    except ShiftError:
        return False

    # Else if val is a dict, try to validate it
    if isinstance(field.val, dict):
        try:
            if field.typ.validate(**field.val):
                return True

        # Invalid subclass data
        except ShiftError:
            return False

    # No way to validate, possibly improper type assignment?
    return False

def _shift_forward_ref_type_validator(instance: Any, field: ShiftField, info: ShiftInfo) -> bool:
    # Check cache first
    if field.typ in _resolved_forward_refs:
        resolved = _resolved_forward_refs[field.typ]
        return _shift_type_validator(instance, resolved, field.val, field, info)

    # Resolve the forward ref
    try:
        resolved = _resolve_forward_ref(field.typ, info)
        _resolved_forward_refs[field.typ] = resolved
        return _shift_type_validator(instance, resolved, field.val, field, info)
    except Exception as e:
        raise ShiftValidationError(info.model_name, field.name,
                                   f"Could not resolve forward reference: {e}")

def _shift_type_validator(instance: Any, typ: Any, val: Any, field: ShiftField, info: ShiftInfo) -> bool:
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

def _shift_type_setter(instance: Any, field: ShiftField, info: ShiftInfo) -> None:
    try:
        setattr(info.instance, field.name, field.val)
    except Exception as e:
        info.errors.append(ShiftSetError(info.model_name, field.name, f"Exception occurred during set: {e}"))

### Reprs
###############################

def _shift_type_repr(instance: Any, field: ShiftField, info: ShiftInfo) -> str:
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
        vals.append(_shift_type_serializer(instance, type(val), val, field, info))
    return vals

def _shift_all_of_pair_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> dict[str, Any] | None:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    vals = {}
    for key, val in field.val.items():
        vals[key] = _shift_type_serializer(instance, type(val), val, field, info)
    return vals

def _shift_shift_type_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> dict[str, Any] | None:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    return field.val.serialize()

def _shift_forward_ref_type_serializer(instance: Any, field: ShiftField, info: ShiftInfo) -> Any:
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    return _shift_type_serializer(instance, field.typ, field.val, field, info)

def _shift_type_serializer(instance: Any, typ: Any, val: Any, field: ShiftField, info: ShiftInfo) -> Any:
    # Get shift type
    shift_typ = get_shift_type(field.typ)

    # If not a shift type, return the field's value as-is
    if not shift_typ:
        return {field.name: field.val}

    # Build temporary ShiftField for serialization and call serializer
    temp_field = ShiftField(name=f"{field.name}.{typ}", typ=typ, val=val)
    return shift_function_wrapper(temp_field, info, shift_typ.serializer)

## Builtin Types
############################################################

_missing_shift_type = ShiftType(_shift_type_transformer,
                                _shift_missing_type_validator, _shift_type_setter,
                                _shift_type_repr, _shift_missing_type_serializer)
_base_shift_type = ShiftType(_shift_type_transformer,
                             _shift_base_type_validator, _shift_type_setter,
                             _shift_type_repr, _shift_base_type_serializer)
_one_of_shift_type = ShiftType(_shift_type_transformer,
                               _shift_one_of_type_validator, _shift_type_setter,
                               _shift_type_repr, _shift_base_type_serializer)
_all_of_single_shift_type = ShiftType(_shift_type_transformer,
                                      _shift_all_of_single_validator, _shift_type_setter,
                                      _shift_type_repr, _shift_all_of_serializer)
_all_of_many_shift_type = ShiftType(_shift_type_transformer,
                                    _shift_all_of_many_validator, _shift_type_setter,
                                    _shift_type_repr, _shift_all_of_serializer)
_all_of_pair_shift_type = ShiftType(_shift_type_transformer,
                                    _shift_all_of_pair_validator, _shift_type_setter,
                                    _shift_type_repr, _shift_all_of_pair_serializer)
_shift_shift_type = ShiftType(_shift_type_transformer,
                              _shift_shift_type_validator, _shift_type_setter,
                              _shift_type_repr, _shift_shift_type_serializer)
_forward_ref_shift_type = ShiftType(_shift_forward_ref_type_transformer,
                                    _shift_forward_ref_type_validator, _shift_type_setter,
                                    _shift_type_repr, _shift_forward_ref_type_serializer)

_shift_builtin_types: dict[Type, ShiftType] = {
    MISSING: _missing_shift_type,

    None: _base_shift_type,
    int: _base_shift_type,
    bool: _base_shift_type,
    float: _base_shift_type,
    str: _base_shift_type,
    bytes: _base_shift_type,
    bytearray: _base_shift_type,
    Any: _base_shift_type,

    list: _all_of_single_shift_type,
    set: _all_of_single_shift_type,
    frozenset: _all_of_single_shift_type,

    tuple: _all_of_many_shift_type,
    Callable: _all_of_many_shift_type,

    dict: _all_of_pair_shift_type,

    Union: _one_of_shift_type,
    Optional: _one_of_shift_type,
    Literal: _one_of_shift_type,

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
        verbosity (int): Logging level: 0 = silent, 1 = errors, 2 = warnings, 3 = info, 4 = debug; Default: 0
        fail_fast (bool): If True, processing will stop on the first error encountered. Default; False

        //allow_arbitrary_keys (bool): If True, arbitrary keys will be allowed in kwarg constructors; Default: False

        include_default_fields_in_serialization (bool): If True, default value fields will be serialized; Default: False
        //include_private_fields_in_serialization (bool): If True, private fields will be serialized; Default: False

    """
    verbosity: int = 0
    fail_fast: bool = False

    #allow_arbitrary_keys: bool = False

    include_default_fields_in_serialization: bool = False
    #include_private_fields_in_serialization: bool = False



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
    if field.name in info.pre_transformer_skips:
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
    if field.name in info.pre_validator_skips:
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
            info.errors.append(e)

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

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call shift type repr
    return shift_function_wrapper(field, info, shift_typ.repr)

def _repr(info: ShiftInfo) -> str:
    res: list[str] = []
    for field in info.fields:
        r = (_repr_field(field, info))
        if r and len(r):
            res.append(field.name + "=" + r)
    return f"{info.model_name}({', '.join(res)})"



## Serialize
############################################################

def _serialize_field(field: ShiftField, info: ShiftInfo) -> dict[str, Any]:
    # If field serializer, call
    if field.name in info.serializers:
        return shift_function_wrapper(field, info, info.serializers[field.name])

    # Get shift type
    shift_typ = get_shift_type(field.typ)
    if shift_typ is None:
        raise ShiftError(info.model_name, f"Could not resolve shift type for {field.name}: {field.typ}")

    # Call shift type serializer
    return shift_function_wrapper(field, info, shift_typ.serializer)

def _serialize(info: ShiftInfo) -> dict[str, Any]:
    result = {}
    for field in info.fields:
        res = _serialize_field(field, info)
        if res is not None:
            result[field.name] = res
    return result



# Shift Classes
########################################################################################################################



## Class Init Functions
############################################################

def _get_shift_config(cls, fields: dict) -> ShiftConfig | None:
    # Get shift_config from cls if it exists
    shift_config = fields.get("__shift_config__")
    if shift_config and not isinstance(shift_config, ShiftConfig):
        raise ShiftError(cls.__name__, "`__shift_config__` must be a ShiftConfig instance")

    # If no shift config provided, use global default
    if shift_config:
        _log_verbose(shift_config.verbosity, ["", "__shift_config__ set"])
    else:
        shift_config = DEFAULT_SHIFT_CONFIG

    _log_verbose(shift_config.verbosity, ["", "", f"shift_config: {shift_config}"])
    return shift_config

def _get_field_decorators(cls: Any, fields: dict) -> dict[str, list[_Any_Decorator] | list[str]]:
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
        "serializers": {},
    }

    # Find and process decorators in fields
    for field_name in fields.keys():
        # Skip private/magic fields
        if field_name.startswith("_"):
            continue

        # Get value
        try:
            val = getattr(cls, field_name, MISSING)
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

def _get_fields(cls: Any, fields: dict, data: dict) -> list[ShiftField]:
    # Create the return list
    shift_fields: list[ShiftField] = []

    # Get all annotated fields
    annotated = get_type_hints(cls)
    for field_name, field_type in annotated.items():
        # Get default value
        try:
            default = getattr(cls, field_name, MISSING)
        except AttributeError:
            continue

        # Get val from data if exists
        val = MISSING
        if field_name in data:
            val = data[field_name]

        # Add to shift_fields list
        shift_fields.append(ShiftField(name=field_name, typ=field_type, val=val, default=default))

    # Get all non-annotated fields
    for field_name in fields.keys():
        # Skip private/magic fields
        if field_name.startswith("_"):
            continue

        # Skip annotated fields
        if field_name in annotated:
            continue

        # Get value
        try:
            val = getattr(cls, field_name, MISSING)
        except AttributeError:
            continue

        # Skip class/static methods, properties, etc.
        if inspect.ismethod(val) or inspect.isfunction(val) or callable(val):
            continue

        # Get val from data if exists
        default = val
        if field_name in data:
            val = data[field_name]

        # Add to shift_fields list
        shift_fields.append(ShiftField(name=field_name, val=val, default=default))

    # Return shift_fields list
    return shift_fields

def _get_shift_info(cls: Any, data: dict) -> ShiftInfo:
    # If cls is in model_info, return copy so non-persistent data is not kept
    if cls in _model_info:
        cached_info = _model_info[cls]
        # Build new copied info
        info = ShiftInfo(
            instance=cls,
            model_name=cached_info.model_name,
            shift_config=cached_info.shift_config,
            fields=cached_info.fields,
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
    fields = getattr(cls, "__dict__", {}).copy()
    ## Get config, shift_fields, and decorators
    shift_config = _get_shift_config(cls, fields)
    shift_fields = _get_fields(cls, fields, data)
    decorators = _get_field_decorators(cls, fields)
    ## Build info class
    info = ShiftInfo(
        instance=cls,
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
    _model_info[cls] = info
    return info



## Classes
############################################################

class ShiftMeta(type):
    """Helper class to handle namespace resolution and forward refs"""

    def __new__(mcls, name, bases, namespace):
        # Build subclass
        cls = super().__new__(mcls, name, bases, namespace)

        # Return cls instance for usage elsewhere
        return cls

class Shift(metaclass=ShiftMeta):
    """Base class for all shift models"""

    def __init_subclass__(cls):
        # Get class fields (all vars, annotations, defs, etc)
        cls.__fields__ = getattr(cls, "__dict__", {}).copy()
        pass

    def __init__(self, **data):
        # Get shift info
        info = _get_shift_info(self.__class__, data)

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__fields__:
            self.__fields__["__pre_init__"](self, info)

        # Run transform, validation, and set processes
        self.validate(info) # Runs transformer and handles errors internally
        self.set(info)

        # If cls has __post_init__(), call
        if "__post_init__" in self.__fields__:
            self.__fields__["__post_init__"](self, info)



    @classmethod
    def transform(cls, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(cls, data)

        # Run transform process
        _transform(info)

    @classmethod
    def validate(cls, info: ShiftInfo=None, **data) -> bool:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(cls, data)

        # Run transform process
        cls.transform(info, **data)

        # Run validation, throw if fail
        if not _validate(info):
            errors = []
            for e in info.errors:
                errors.append(str(e))
            raise ShiftError(info.model_name, f"Validation failed: {errors}")
        return True

    @classmethod
    def set(cls, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(cls, data)

        # Run set process
        _set(info)

    @classmethod
    def __repr__(cls, info: ShiftInfo=None) -> str:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(cls, {})

        # Run repr process
        return _repr(info)

    @classmethod
    def serialize(cls, info: ShiftInfo=None) -> dict[str, Any]:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(cls, {})

        # Run serialization process
        return _serialize(info)



    @classmethod
    def __eq__(cls, other: Any) -> bool:
        if not isinstance(other, cls):
            return False
        return cls.serialize() == other.serialize()

    @classmethod
    def __ne__(cls, other: Any) -> bool:
        return not cls == other

    @classmethod
    def __hash__(cls) -> int:
        return hash(cls.serialize())

    @classmethod
    def __copy__(cls) -> Any:
        return type(cls)(**cls.serialize())

    @classmethod
    def __deepcopy__(cls, memo: dict[int, Any]) -> Any:
        return type(cls)(**cls.serialize())



# Utilities
########################################################################################################################



## Shift Types
############################################################

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

def generate_shift_info(cls: Any) -> None:
    """Generates shift info for a class"""
    _get_shift_info(cls, {})

def deregister_shift_info(cls: Any) -> None:
    """Deregisters shift info for a class"""
    if cls not in _model_info:
        raise ShiftError("<module>", f"Class `{cls.__name__}` is not registered")
    del _model_info[cls]

def clear_shift_info_cache(cls: Any) -> None:
    """Clears the shift info cache for a shift class"""
    if cls not in _model_info:
        raise ShiftSetError("<module>", "_model_info", f"Class `{cls}` is not registered")
    del _model_info[cls]



## Shift Functions
############################################################

def generate_shift_function(func: Callable) -> None:
    """Generates the shift function inspection data for a shift-decorated function"""
    # Get function signature
    sig = inspect.signature(func)

    # If len(params) == 2, it's a simple function
    if len(sig.parameters) == 2:
        _shift_functions[func] = False

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

def deregister_shift_function(func: Callable) -> None:
    """De-register the inspection data for a shift-decorated function"""
    if func not in _shift_functions:
        raise ShiftError("<module>", f"`{func}` not a registered shift function")
    del _shift_functions[func]

def clear_shift_function_cache() -> None:
    """Clears the shift function cache"""
    _shift_functions.clear()



## Misc
############################################################

# Register Builtin types
_shift_types.update(_shift_builtin_types)
# Register Shift type
_shift_types[Shift] = _shift_shift_type
