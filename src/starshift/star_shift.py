# Imports
########################################################################################################################



# Data containers
from dataclasses import dataclass

# Check types in validation
from enum import Enum
from typing import get_origin, get_args, get_type_hints, Any, Union, ForwardRef, Type, Callable, Optional, Literal

# Evaluate forward references
import sys, inspect



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



## Type
############################################################

def shift_type_transformer(*types: Type)\
        -> Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]:
    """Decorator to mark a function as a global shift type transformer"""
    raise NotImplementedError("Global type transformers are not yet supported")

def shift_type_validator(*types: Type)\
        -> Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]:
    """Decorator to mark a function as a global shift type validator"""
    raise NotImplementedError("Global type validators are not yet supported")

def shift_type_setter(*types: Type)\
        -> Callable[[Any], None] | Callable[[ShiftField, ShiftInfo], None]:
    """Decorator to mark a function as a global shift type setter"""
    raise NotImplementedError("Global type setters are not yet supported")

def shift_type_repr(*types: Type)\
        -> Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]:
    """Decorator to mark a function as a global shift type repr"""
    raise NotImplementedError("Global type reprs are not yet supported")

def shift_type_serializer(*types: Type)\
        -> Callable[[Any], dict[str, Any] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]]:
    """Decorator to mark a function as a global shift type serializer"""
    raise NotImplementedError("Global type serializers are not yet supported")


## Field
############################################################

def shift_transformer(*fields: str, pre: bool=False, skip_when_pre: bool=True)\
        -> Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]:
    """Decorator to mark a function as a shift transformer

    pre: marks this function to run before global type transformers
    skip_when_pre: skips global type transformers when running before global type transformers
    """
    raise NotImplementedError("Field transformers are not yet supported")

def shift_validator(*fields: str, pre: bool=False, skip_when_pre: bool=True)\
        -> Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]:
    """Decorator to mark a function as a shift validator

    pre: marks this function to run in the pre-validation phase
    skip_when_pre: skips shift validation when running in the pre-validation phase
    """
    raise NotImplementedError("Field validators are not yet supported")

def shift_setter(*fields: str)\
        -> Callable[[Any, Any], None] | Callable[[ShiftField, ShiftInfo], None]:
    """Decorator to mark a function as a shift setter

    The double any is so we can pass in `self`"""
    raise NotImplementedError("Field setters are not yet supported")

def shift_repr(*fields: str)\
        -> Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]:
    """Decorator to mark a function as a shift repr"""
    raise NotImplementedError("Field reprs are not yet supported")

def shift_serializer(*fields: str)\
        -> Callable[[Any], dict[str, Any]] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]:
    """Decorator to mark a function as a shift serializer"""
    raise NotImplementedError("Field serializers are not yet supported")



## Advanced + Wrapper
############################################################

def shift_advanced() -> Callable:
    """Decorator to mark a function as an advanced shift decorator"""
    raise NotImplementedError("Advanced shift decorators are not yet supported")

def shift_function_wrapper(field: ShiftField, info: ShiftInfo, func: Callable) -> Any:
    """Wrapper to automatically determine if the decorator is advanced or not, and call appropriately, returning the result"""
    raise NotImplementedError("Advanced shift decorator wrapping is not yet supported")



# Types
########################################################################################################################



# Sentinel object to check for missing values
MISSING = object()

@dataclass
class ShiftInfo:
    """Data class for storing validation info

    Attributes:
        self (Any): The class instance being validated
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
    self: Any
    model_name: str
    shift_config: ShiftConfig
    fields: list[ShiftField]
    pre_transformer_skips: list[str]
    pre_transformers: dict[str, Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]]
    transformers: dict[str, Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]]
    pre_validator_skips: list[str]
    pre_validators: dict[str, Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]]
    validators: dict[str, Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]]
    setters: dict[str, Callable[[Any], None] | Callable[[ShiftField, ShiftInfo], None]]
    reprs: dict[str, Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]]
    serializers: dict[str, Callable[[Any], dict[str, Any] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]]]
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

class ShiftTypeCategory(Enum):
    """Enum for type categories"""
    BASE = "base"
    ONE_OF = "one_of"
    ALL_OF_SINGLE = "all_of_single"
    ALL_OF_MANY = "all_of_many"
    ALL_OF_PAIR = "all_of_pair"
    SHIFT = "shift"
    FORWARD_REF = "forward_ref"

@dataclass
class ShiftType:
    """Universal type interface for all validation types"""
    category: ShiftTypeCategory
    transformer: Callable[[Any], Any] | Callable[[ShiftField, ShiftInfo], Any]
    validator: Callable[[Any], bool] | Callable[[ShiftField, ShiftInfo], bool]
    setter: Callable[[Any, Any], None] | Callable[[ShiftField, ShiftInfo], None]
    repr: Callable[[Any], str] | Callable[[ShiftField, ShiftInfo], str]
    serializer: Callable[[Any], dict[str, Any]] | Callable[[ShiftField, ShiftInfo], dict[str, Any]]

def _get_shift_type(typ: Any) -> ShiftType | None:
    # If typ has no hash, we can't use it as a key in a dict
    if not hasattr(typ, "__hash__"):
        return None

    # If in types, return the type
    if typ in _shift_types:
        return _shift_types[typ]

    # Else type is unknown, return None
    return None



## Builtin Type Functions
############################################################

### Transformers
###############################

def _shift_type_transformer(field: ShiftField, info: ShiftInfo) -> Any:
    if field.val is MISSING:
        return field.default if field.default is not MISSING else None
    return field.val

### Validators
###############################

def _shift_base_type_validator(field: ShiftField, info: ShiftInfo) -> bool:
    # If base type, check if instance of typ
    try:
        return isinstance(field.val, field.typ)

    # Was not instance - broad exception to catch all errors, we can handle them later
    except Exception:
        return False

def _shift_one_of_type_validator(field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # Try all args until match is found
    for arg in args:
        if _shift_type_validator(arg, field.val, info):
            return True

    # No matches found
    return False

def _shift_all_of_single_validator(field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # If more args than single can handle, return False
    if len(args) > 1:
        return False

    # Check all args
    for val in field.val:
        if not _shift_type_validator(args[0], val, info):
            return False

    # All args matched
    return True

def _shift_all_of_many_validator(field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # If lens don't match, return False
    if len(field.val) != len(args):
        return False

    # Check all val-arg pairs
    for val, arg in zip(field.val, args):
        if not _shift_type_validator(arg, val, info):
            return False

    # All val-arg pairs matched
    return True

def _shift_all_of_pair_validator(field: ShiftField, info: ShiftInfo) -> bool:
    args = get_args(field.typ)

    # If no type args nothing to check
    if not args:
        return True

    # Check all keys and vals against args
    for key, val in field.val.items():
        if not _shift_type_validator(args[0], key, info):
            return False
        if len(args) > 1 and not _shift_type_validator(args[1], val, info):
            return False

    # All key-val-arg pairs matched
    return True

def _shift_shift_type_validator(field: ShiftField, info: ShiftInfo) -> bool:
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

def _resolve_forward_ref(typ: str | ForwardRef, info: ShiftInfo) -> Type:
    raise NotImplementedError("Forward ref resolvers are not implemented yet")

def _shift_forward_ref_type_validator(field: ShiftField, info: ShiftInfo) -> bool:
    # Check cache first
    if field.typ in _resolved_forward_refs:
        resolved = _resolved_forward_refs[field.typ]
        return _shift_type_validator(resolved, field.val, info)

    # Resolve the forward ref
    try:
        resolved = _resolve_forward_ref(field.typ, info)
        _resolved_forward_refs[field.typ] = resolved
        return _shift_type_validator(resolved, field.val, info)
    except Exception as e:
        raise ShiftValidationError(info.model_name, field.name,
                                   f"Could not resolve forward reference: {e}")

def _shift_type_validator(typ: Any, val: Any, info: ShiftInfo) -> bool:
    # Get shift type
    shift_typ = _get_shift_type(typ)
    if not shift_typ:
        return False

    # Build temporary ShiftField for validation
    field = ShiftField(name="temp", typ=typ, val=val)

    # Call validator
    return shift_typ.validator(field, info)

### Setters
###############################

def _shift_type_setter(field: ShiftField, info: ShiftInfo) -> None:
    # Set the field
    raise NotImplementedError("Builtin type setters are not implemented yet")

### Reprs
###############################

def _shift_type_repr(field: ShiftField, info: ShiftInfo) -> str:
    # Link to the recursive shift repr loop?
    raise NotImplementedError("Builtin type reprs are not implemented yet")

### Serializers
###############################

def _shift_type_serializer(field: ShiftField, info: ShiftInfo) -> dict[str, Any]:
    # Link to the recursive shift serialization loop?
    raise NotImplementedError("Builtin type serializers are not implemented yet")



## Builtin Types
############################################################

_base_shift_type = ShiftType(ShiftTypeCategory.BASE, _shift_type_transformer,
                             _shift_base_type_validator, _shift_type_setter,
                             _shift_type_repr, _shift_type_serializer)
_one_of_shift_type = ShiftType(ShiftTypeCategory.ONE_OF, _shift_type_transformer,
                               _shift_one_of_type_validator, _shift_type_setter,
                               _shift_type_repr, _shift_type_serializer)
_all_of_single_shift_type = ShiftType(ShiftTypeCategory.ALL_OF_SINGLE, _shift_type_transformer,
                                      _shift_all_of_single_validator, _shift_type_setter,
                                      _shift_type_repr, _shift_type_serializer)
_all_of_many_shift_type = ShiftType(ShiftTypeCategory.ALL_OF_MANY, _shift_type_transformer,
                                    _shift_all_of_many_validator, _shift_type_setter,
                                    _shift_type_repr, _shift_type_serializer)
_all_of_pair_shift_type = ShiftType(ShiftTypeCategory.ALL_OF_PAIR, _shift_type_transformer,
                                    _shift_all_of_pair_validator, _shift_type_setter,
                                    _shift_type_repr, _shift_type_serializer)
_shift_shift_type = ShiftType(ShiftTypeCategory.SHIFT, _shift_type_transformer,
                              _shift_shift_type_validator, _shift_type_setter,
                              _shift_type_repr, _shift_type_serializer)
_forward_ref_shift_type = ShiftType(ShiftTypeCategory.FORWARD_REF, _shift_type_transformer,
                                    _shift_forward_ref_type_validator, _shift_type_setter,
                                    _shift_type_repr, _shift_type_serializer)

_shift_builtin_types: dict[Type, ShiftType] = {
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

    "Shift": _shift_shift_type,

    ForwardRef: _forward_ref_shift_type,
}



# Config
########################################################################################################################



@dataclass
class ShiftConfig:
    """Configuration for shift phases

    Attributes:
        verbosity (int): Logging level: 0 = silent, 1 = errors, 2 = warnings, 3 = info, 4 = debug; Default: 0
        fail_fast (bool): If True, processing will stop on the first error encountered. Default: False
    """
    verbosity: int = 0
    fail_fast: bool = False
    # Put some more values here later



## Presets
############################################################

StrictConfig = ShiftConfig(verbosity=1, fail_fast=True)
DefaultConfig = ShiftConfig()
RelaxedConfig = ShiftConfig(verbosity=2)
# Add more later



# Global Registers & Defaults
########################################################################################################################



# Global type category registers
#   Leave override here in case users want an easy way to add more static types
_shift_types: dict[Type, ShiftType] = {

}
_shift_types.update(_shift_builtin_types)

# Resolved forward refs registers (cache)
_resolved_forward_refs: dict[ForwardRef, Type] = {}

# Global info registers (metadata)
#   By leaving this here we can keep global references of static class elements like config and decorated class defs
_model_info: dict[Type, ShiftInfo] = {}



# Shift Processing Functions
########################################################################################################################



## Generic
############################################################

_ProcessType = Literal["transform", "validate", "set", "repr", "serialize"]

@dataclass
class _ProcessConfig:
    """Configuration for a specific process execution."""
    skip_on_pre: bool
    has_pre: bool
    pre_func: Callable | None
    has_post: bool
    post_func: Callable | None

def _get_process_config(field: ShiftField, info: ShiftInfo, process_type: _ProcessType) -> _ProcessConfig:
    """Get the configuration for a specific phase."""

    if process_type == "transform":
        return _ProcessConfig(
            skip_on_pre=field.name in info.pre_transformer_skips,
            has_pre=field.name in info.pre_transformers,
            pre_func=info.pre_transformers.get(field.name),
            has_post=field.name in info.transformers,
            post_func=info.transformers.get(field.name)
        )

    elif process_type == "validate":
        return _ProcessConfig(
            skip_on_pre=field.name in info.pre_validator_skips,
            has_pre=field.name in info.pre_validators,
            pre_func=info.pre_validators.get(field.name),
            has_post=field.name in info.validators,
            post_func=info.validators.get(field.name)
        )

    elif process_type == "set":
        return _ProcessConfig(
            skip_on_pre=False,
            has_pre=False,
            pre_func=None,
            has_post=field.name in info.setters,
            post_func=info.setters.get(field.name)
        )

    elif process_type == "repr":
        return _ProcessConfig(
            skip_on_pre=False,
            has_pre=False,
            pre_func=None,
            has_post=field.name in info.reprs,
            post_func=info.reprs.get(field.name)
        )

    elif process_type == "serialize":
        return _ProcessConfig(
            skip_on_pre=False,
            has_pre=False,
            pre_func=None,
            has_post=field.name in info.serializers,
            post_func=info.serializers.get(field.name)
        )

    else:
        raise ValueError(f"Invalid phase type: {process_type}")

def _process_field(field: ShiftField, info: ShiftInfo, process_type: _ProcessType) -> Any | None:
    # Get process config
    process_config = _get_process_config(field, info, process_type)

    # If pre-phase, use
    if process_config.has_pre:
        res = shift_function_wrapper(field, info, process_config.pre_func)

        # If pre-phase skip is true, return
        if process_config.skip_on_pre:
            return res

    # Get and use shift type function
    shift_typ = _get_shift_type(field.typ)
    if not shift_typ:
        raise ShiftError(info.model_name,
                         f"Type `{field.typ}` is not a known shift type for process `{process_type}`")
    res = shift_function_wrapper(field, info, getattr(shift_typ, process_type))

    # For validation, early return on failure
    if process_type == "validate" and res is False:
        return False

    # If post-phase, use
    if process_config.has_post:
        res = shift_function_wrapper(field, info, process_config.post_func)

    return res

def _process(info: ShiftInfo, process_type: _ProcessType) -> bool | None:
    # Tracks validation of all fields
    all_valid = True

    # Process each field
    for field in info.fields:
        try:
            res = _process_field(field, info, process_type)

            # Update field value for transform
            if process_type == "transform":
                field.val = res

            # Track validation results
            elif process_type == "validate" and res is False:
                all_valid = False
                if info.shift_config.fail_fast:
                    return False

        except ShiftError as e:
            info.errors.append(e)
            if info.shift_config.fail_fast:
                return False
            all_valid = False

    return all_valid if process_type == "validate" else None



## Processes
############################################################

def _transform(info: ShiftInfo) -> None:
    _process(info, "transform")

def _validate(info: ShiftInfo) -> bool:
    return _process(info, "validate")

def _set(info: ShiftInfo) -> None:
    _process(info, "set")

def _repr(info: ShiftInfo) -> str:
    repr: list[str] = []
    for field in info.fields:
        res = _process_field(field, info, "repr")
        if res:
            repr.append(f"{field.name}={res}")
    return f"{info.model_name}({', '.join(repr)})"

def _serialize(info: ShiftInfo) -> dict[str, Any]:
    result = {}
    for field in info.fields:
        res = _process_field(field, info, "serialize")
        if res is not MISSING:
            result[field.name] = res
    return result



# Shift Classes
########################################################################################################################



## Class Init Functions
############################################################

def _get_shift_config(self: Any) -> ShiftConfig | None:
    # Get the `__shift_config__` attribute from the model, if it exists
    raise NotImplementedError("Finding class shift config not supported yet")

def _set_field_decorators(cls: Type, info: ShiftInfo) -> None:
    # Find the decorators and process them
    raise NotImplementedError("Finding class decorators are not yet supported")

def _get_shift_info(cls: Any) -> ShiftInfo:
    # If cls is in model_info, return copy so non-persistent data is not kept
    if cls in _model_info:
        return _model_info[cls].__copy__()

    # Else build new info and add to model_info
    info = ShiftInfo(
        self=cls,
        model_name=cls.__name__,
        shift_config=_get_shift_config(cls),
        fields=[],
        pre_transformer_skips=[],
        pre_transformers={},
        transformers={},
        pre_validator_skips=[],
        pre_validators={},
        validators={},
        setters={},
        reprs={},
        serializers={},
        data={},
        errors=[]
    )
    _model_info[cls] = info
    return info



## Classes
############################################################

class ShiftMeta(type):
    """Helper class to handle namespace resolution and forward refs"""

    def __new__(mcls, name, bases, namespace):
        # Build subclass
        cls = super().__new__(mcls, name, bases, namespace)

        # walk up frames adding context until we get this function call - used later to resolve forward refs

        return cls

class Shift(metaclass=ShiftMeta):
    """Base class for all shift models"""

    def __init_subclass__(cls):
        # Get class fields (all vars, annotations, defs, etc)
        cls.__fields__ = getattr(cls, "__dict__", {}).copy()

    def __init__(self, **data):
        # Get shift info
        info = _get_shift_info(self.__class__)
        info.data = data

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__fields__:
            self.__fields__["__pre_init__"](self, info)

        # Run transform, validation, and set processes
        self.transform(info)
        if not self.validate(info):
            # Raise list of errors in info.errors - somehow?
            raise NotImplementedError("Validation errors not yet supported")
        self.set(info)

        # If cls has __post_init__(), call
        if "__post_init__" in self.__fields__:
            self.__fields__["__post_init__"](self, info)



    @classmethod
    def transform(self, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(self.__class__)
            info.data = data

        # Run transform process
        _transform(info)

    @classmethod
    def validate(self, info: ShiftInfo=None, **data) -> bool:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(self.__class__)
            info.data = data

        # Run validation process
        return _validate(info)

    @classmethod
    def set(self, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(self.__class__)
            info.data = data

        # Run set process
        _set(info)

    @classmethod
    def __repr__(self, info: ShiftInfo=None) -> str:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(self.__class__)

        # Run repr process
        return _repr(info)

    @classmethod
    def serialize(self, info: ShiftInfo=None) -> dict[str, Any]:
        # Get shift info if not provided
        if info is None:
            info = _get_shift_info(self.__class__)

        # Run serialization process
        return _serialize(info)



    @classmethod
    def __eq__(self, other: Any) -> bool:
        return self.serialize() == other.serialize()

    @classmethod
    def __ne__(self, other: Any) -> bool:
        return not self == other

    @classmethod
    def __hash__(self) -> int:
        return hash(self.serialize())

    @classmethod
    def __copy__(self) -> Any:
        return type(self)(**self.serialize())

    @classmethod
    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        return type(self)(**self.serialize())



# Utilities
########################################################################################################################



def register_type(typ: Type, shift_type: ShiftType) -> None:
    _shift_types[typ] = shift_type

def register_forward_ref(ref: ForwardRef, typ: Type) -> None:
    _resolved_forward_refs[ref] = typ