# region Imports


# To allow backwards compatibility with type hints
from __future__ import annotations

# Data containers
from dataclasses import dataclass

# Check types in validation
from typing import get_origin, get_args, get_type_hints, cast, Any, Union, ForwardRef, Type, Optional, Literal, TypeAlias
from collections.abc import Iterable, Callable

# Evaluate regex
import re

# Evaluate forward references and check function signatures
import inspect, sys


# endregion
# region Global Registers & Defaults



# Global type category registers
#   Leave override here in case users want an easy way to add more static types
_shift_types: dict[Type, ShiftType] = {}

# Resolved forward refs registers (cache)
_resolved_forward_refs: dict[str, Type] = {}

# Global info registers (metadata)
#   By leaving this here we can keep global references of static class elements like config and decorated class defs
_shift_info_registry: dict[Type, ShiftInfo] = {}

# Global function registers, used to skip inspecting shift functions
#   True is advanced, False is simple
_shift_functions: dict[Callable, bool] = {}
_shift_init_functions: dict[Callable, bool] = {}



# endregion
# region ShiftModel Types



## Errors
#########

def _str_depth(depth: int) -> str:
    return "   " * depth

class ShiftError(Exception):
    """Base class for all starshift errors"""
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.msg)

    def __repr__(self) -> str:
        return self.msg

class ShiftModelError(ShiftError):
    """Model-related errors"""
    def __init__(self, model_name: str, process: str, field_errors: list):
        self.model_name = model_name
        self.process = process
        self.field_errors = field_errors
        super().__init__(self.__repr__())

    def __repr__(self, depth: int = 0) -> str:
        errors = "\n" if depth == 0 else ""
        for field_error in self.field_errors:
            errors += _str_depth(depth + 1)  # Add 1 level of indentation for child errors
            if isinstance(field_error, ShiftModelError):
                errors += field_error.__repr__(depth + 1)
            else:
                errors += f"{field_error}"
            errors += "\n"  # Add newline after each error
        return f"{self.model_name}: encountered {len(self.field_errors)} errors during {self.process}:\n{errors}"


class ShiftFieldError(ShiftError):
    """Field-related errors"""
    def __init__(self, field_name: str, msg: str):
        self.field_name = field_name
        self.msg = msg
        super().__init__(self.__repr__())

    def __repr__(self) -> str:
        return f"{self.field_name}: {self.msg}"

class ShiftTypeMismatchError(ShiftError):
    """Raised when a field's type does not match the expected type"""
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.__repr__())

    def __repr__(self) -> str:
        return f"{self.msg}"

class UnknownShiftTypeError(ShiftError):
    """Raised when a field's type is not registered"""
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.__repr__())

    def __repr__(self) -> str:
        return f"{self.msg}"



## Metadata
###########

class Missing:
    """Sentinel class to check for missing values"""
    def __repr__(self):
        return 'Missing'
    def __bool__(self) -> bool:
        return False

@dataclass
class ShiftConfig:
    """Configuration for shift phases

    Attributes:
        fail_fast (bool): If True, processing will stop on the first error encountered. Default; False
        do_processing (bool): If True, on init all fields will be transformed, validated, and set. If False, you must manually set everything (use __post_init__); Default: True
        try_coerce_types (bool): If True, ShiftModel will attempt to coerce types where possible. If False, all types must match exactly; Default: False
        allow_private_field_setting (bool): If False, ShiftModel will not throw when a class is instantiated with a private field val; Default: False
        include_default_fields_in_serialization (bool): If True, default value fields will be serialized (used in repr too); Default: False
        include_private_fields_in_serialization (bool): If True, private fields will be serialized (used in repr too); Default: False
    """
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
            fail_fast=self.fail_fast,
            do_processing=self.do_processing,
            try_coerce_types=self.try_coerce_types,
            allow_private_field_setting=self.allow_private_field_setting,
            include_default_fields_in_serialization=self.include_default_fields_in_serialization,
            include_private_fields_in_serialization=self.include_private_fields_in_serialization,
        )

DEFAULT_SHIFT_CONFIG = ShiftConfig()

@dataclass
class ShiftInfo:
    """Data class for storing validation info

    Attributes:
        instance (Any): The class instance being validated
        model_name (str): Name of the model/class being validated
        shift_config (ShiftConfig): All config options to govern
        fields (list[ShiftFieldInfo]): List of fields
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
        transform_errors (list[ShiftFieldError]): List of errors accumulated during transform
        validation_errors (list[ShiftFieldError]): List of errors accumulated during validation
        set_errors (list[ShiftFieldError]): List of errors accumulated during set
    """
    instance: Any
    model_name: str
    shift_config: ShiftConfig
    fields: list[ShiftFieldInfo]
    pre_transformer_skips: list[str]
    pre_transformers: dict[str, ShiftTransformer]
    transformers: dict[str, ShiftTransformer]
    pre_validator_skips: list[str]
    pre_validators: dict[str, ShiftValidator]
    validators: dict[str, ShiftValidator]
    setters: dict[str, ShiftSetter]
    reprs: dict[str, ShiftRepr]
    serializers: dict[str, ShiftSerializer]
    data: dict[str, Any]
    transform_errors: list[ShiftFieldError]
    validation_errors: list[ShiftFieldError]
    set_errors: list[ShiftFieldError]



    def __repr__(self) -> str:
        return f'ShiftInfo for `{self.model_name}`'

@dataclass
class ShiftFieldInfo:
    """Data class for storing validation info

    Attributes:
        name (str): Name of the field
        typ (Any): Type hint of the field; Default: Missing
        val (Any): Value of the field; Default: Missing
        default (Any): Default value of the field; Default: Missing
    """
    name: str
    typ: Any = Missing
    val: Any = Missing
    default: Any = Missing



    def __repr__(self) -> str:
        return f'ShiftFieldInfo for `{self.name}` of type `{self.typ}`'

@dataclass
class ShiftField:
    """Class for simple inline validation checks

    Attributes:
        type (Any): Type hint of the field; Default: Missing
        default (Any): Default value of the field; Default: Missing
        default_factory (Callable[[], Any]): Default factory function; Default: None
        default_skips (bool): Whether to skip validation when default is the value; Default: False
        transformer (Callable[[Any, Any], Any]): ShiftTransformer function; Default: None
        ge (Any): val >= ge; Default: None
        eq (Any): val == eq; Default: None
        le (Any): val <= le; Default: None
        gt (Any): val > gt; Default: None
        ne (Any): val != ne; Default: None
        lt (Any): val < lt; Default: None
        min_len (int): Minimum length of the field; Default: None
        max_len (int): Maximum length of the field; Default: None
        pattern (str): Regex pattern match; Default: None
        check (Callable[[Any], bool]: A simple validator function that just passes the field value; Default = None
        validator (Callable[[Any, Any], bool]): ShiftValidator function; Default: None
        validator_skips (bool): Whether to skip builtin validation when validator is set; Default: False
        setter (Callable[[Any, Any], None] | None): ShiftSetter function; Default: None
        repr_func (Callable[[Any, Any], str] | None): Representation function; Default: None
        repr_as (str): Representation field name; Default: None
        repr_exclude (bool): Whether to exclude this field in repr: Default: False
        serializer (Callable[[Any, Any], dict | None]): ShiftSerializer function; Default: None
        serialize_as (str): ShiftSerializer field name; Default: None
        serializer_exclude (bool): Whether to exclude this field in serializer: Default: False
        defer (bool): Whether StarShift will completely ignore this field; Default = False
        defer_transform (bool): Whether StarShift will ignore this field for all transform operations; Default = False
        defer_validation (bool): Whether StarShift will ignore this field for all validation operations; Default = False
        defer_set (bool): Whether StarShift will ignore this field for all set operations; Default = False
        defer_repr (bool): Whether StarShift will ignore this field for all repr operations; Default = False
        defer_serialize (bool): Whether StarShift will ignore this field for all serialize operations; Default = False
    """

    # Type
    type: Any = Missing

    # Defaults
    default: Any = Missing
    default_factory: Callable[[], Any] | None = None
    default_skips: bool = False

    # Transform
    transformer: Callable[[Any, Any], Any] | None = None

    # Validation
    ge: Any = None
    eq: Any = None
    le: Any = None
    gt: Any = None
    ne: Any = None
    lt: Any = None
    min_len: int | None = None
    max_len: int | None = None
    pattern: str | None = None
    check: Callable[[Any], bool] | None = None
    validator: Callable[[Any, Any], bool] | None = None
    validator_skips: bool = False

    # Setting
    setter: Callable[[Any, Any], Any] | None = None

    # ShiftRepr
    repr_func: Callable[[Any, Any], str] | None = None
    repr_as: str | None = None
    repr_exclude: bool = False

    # Serialize
    serializer: Callable[[Any, Any], Any] | None = None
    serialize_as: str | None = None
    serializer_exclude: bool = False

    # Other
    defer: bool = False
    defer_transform: bool = False
    defer_validation: bool = False
    defer_set: bool = False
    defer_repr: bool = False
    defer_serialize: bool = False



    def __hash__(self) -> int:
        return hash('ShiftField') # Used for ShiftTypes registry

    def __repr__(self) -> str:
        return f'ShiftField with type `{self.type}`'



    def get_default(self) -> Any:
        """Get the default value, calling factory if needed"""
        if self.default is not Missing:
            return self.default
        elif self.default_factory is not None:
            return self.default_factory()
        return Missing

    def validate(self, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> list[str]:
        """Check the value against the constraints when set"""
        errors = []

        val = field_info.val

        # Simple checks
        if self.ge is not None:
            try:
                if val < self.ge:
                    errors.append(f"Must be >= {self.ge}")
            except (TypeError, NotImplementedError):
                errors.append(f"ge was set, but val could not be compared to ge")
        if self.eq is not None:
            try:
                if val != self.eq:
                    errors.append(f"Must be == {self.eq}")
            except (TypeError, NotImplementedError):
                errors.append(f"eq was set, but val could not be compared to eq")
        if self.le is not None:
            try:
                if val > self.le:
                    errors.append(f"Must be <= {self.le}")
            except (TypeError, NotImplementedError):
                errors.append(f"le was set, but val could not be compared to le")
        if self.gt is not None:
            try:
                if val <= self.gt:
                    errors.append(f"Must be > {self.gt}")
            except (TypeError, NotImplementedError):
                errors.append(f"gt was set, but val could not be compared to gt")
        if self.ne is not None:
            try:
                if val == self.ne:
                    errors.append(f"Must be != {self.ne}")
            except (TypeError, NotImplementedError):
                errors.append(f"ne was set, but val could not be compared to ne")
        if self.lt is not None:
            try:
                if val >= self.lt:
                    errors.append(f"Must be < {self.lt}")
            except (TypeError, NotImplementedError):
                errors.append(f"lt was set, but val could not be compared to lt")
        if self.min_len is not None:
            try:
                if len(val) <= self.min_len:
                    errors.append(f"len(val) must be > {self.min_len}")
            except (TypeError, NotImplementedError):
                errors.append(f"min_len was set, but len(val) could not be compared to min_len")
        if self.max_len is not None:
            try:
                if len(val) >= self.max_len:
                    errors.append(f"len(val) must be < {self.max_len}")
            except (TypeError, NotImplementedError):
                errors.append(f"max_len was set, but len(val) could not be compared to max_len")
        if self.pattern is not None:
            try:
                if not re.match(self.pattern, str(val)):
                    errors.append(f"str(val) must match the pattern {self.pattern}")
            except (TypeError, NotImplementedError):
                errors.append(f"pattern was set, but str(val) could not be compared to pattern")

        # Custom check
        if self.check is not None:
            try:
                if not self.check(val):
                    errors.append(f"val failed custom check")
            except Exception as e:
                errors.append(f"Check raised {type(e).__name__}: {e}")
        # Custom validator
        if self.validator is not None:
            try:
                if not shift_function_wrapper(field_info, shift_info, self.validator):
                    errors.append(f"val failed custom validator")
            except Exception as e:
                errors.append(f"ShiftValidator raised {type(e).__name__}: {e}")

        return errors



## Type Aliases
###############

ShiftSimpleTransformer: TypeAlias = Callable[[Any, Any], Any]
ShiftAdvancedTransformer: TypeAlias = Callable[[Any, ShiftFieldInfo, ShiftInfo], Any]
ShiftTransformer: TypeAlias = ShiftSimpleTransformer | ShiftAdvancedTransformer

ShiftSimpleValidator: TypeAlias = Callable[[Any, Any], bool]
ShiftAdvancedValidator: TypeAlias = Callable[[Any, ShiftFieldInfo, ShiftInfo], bool]
ShiftValidator: TypeAlias = ShiftSimpleValidator | ShiftAdvancedValidator

ShiftSimpleSetter: TypeAlias = Callable[[Any, Any], Any | None]
ShiftAdvancedSetter: TypeAlias = Callable[[Any, ShiftFieldInfo, ShiftInfo], Any | None]
ShiftSetter: TypeAlias = ShiftSimpleSetter | ShiftAdvancedSetter

ShiftSimpleRepr: TypeAlias = Callable[[Any, Any], str | None]
ShiftAdvancedRepr: TypeAlias = Callable[[Any, ShiftFieldInfo, ShiftInfo], str | None]
ShiftRepr: TypeAlias = ShiftSimpleRepr | ShiftAdvancedRepr

ShiftSimpleSerializer: TypeAlias = Callable[[Any, Any], Any | None]
ShiftAdvancedSerializer: TypeAlias = Callable[[Any, ShiftFieldInfo, ShiftInfo], Any | None]
ShiftSerializer: TypeAlias = ShiftSimpleSerializer | ShiftAdvancedSerializer

AnyShiftDecorator: TypeAlias = ShiftTransformer | ShiftValidator | ShiftSetter | ShiftRepr | ShiftSerializer



## ShiftModel Type Class & Functions
###############################

def _shift_base_transformer_wrapper(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """Wrapper for shift_base_type_transformer"""
    return shift_base_type_transformer(instance, field_info, shift_info)

def _shift_base_validator_wrapper(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """Wrapper for shift_base_type_validator"""
    return shift_base_type_validator(instance, field_info, shift_info)

def _shift_base_setter_wrapper(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """Wrapper for shift_base_type_setter"""
    return shift_base_type_setter(instance, field_info, shift_info)

def _shift_base_repr_wrapper(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """Wrapper for shift_base_type_repr"""
    return shift_base_type_repr(instance, field_info, shift_info)

def _shift_base_serializer_wrapper(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """Wrapper for shift_base_type_serializer"""
    return shift_base_type_serializer(instance, field_info, shift_info)

@dataclass
class ShiftType:
    """Universal type interface for all validation types

    Attributes:
        transformer (Callable[[Any, Any], Any] | Callable[[Any, ShiftFieldInfo, ShiftInfo], Any]): The type transformer function; Default: base_type_transformer
        validator (Callable[[Any, Any], bool] | Callable[[Any, ShiftFieldInfo, ShiftInfo], bool]): The type validator function; Default: base_type_validator
        setter (Callable[[Any, Any], Any] | Callable[[Any, ShiftFieldInfo, ShiftInfo], Any]): The type setter function; Default: base_type_setter
        repr (Callable[[Any, Any], str] | Callable[[Any, ShiftFieldInfo, ShiftInfo], str]): The type repr function; Default: base_type_repr
        serializer (Callable[[Any, Any], Any] | Callable[[Any, ShiftFieldInfo, ShiftInfo], Any]): The type serializer function; Default: base_type_serializer
    """

    transformer: ShiftTransformer = _shift_base_transformer_wrapper
    validator: ShiftValidator = _shift_base_validator_wrapper
    setter: ShiftSetter = _shift_base_setter_wrapper
    repr: ShiftRepr = _shift_base_repr_wrapper
    serializer: ShiftSerializer = _shift_base_serializer_wrapper

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

    # If type is a ShiftModel subclass, return shift type
    try:
        if issubclass(typ, ShiftModel):
            return _shift_types[ShiftModel]
    except Exception:
        pass

    # Get type of object and check if it's in the registry
    typ = type(typ)
    if typ in _shift_types:
        return _shift_types[typ]

    # Else type is unknown, return None
    return None



# endregion
# region Decorators



# noinspection PyTypeChecker
def shift_transformer(*fields: str, pre: bool=False, skip_when_pre: bool=True) -> Callable[[ShiftTransformer], ShiftTransformer]:
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
def shift_validator(*fields: str, pre: bool=False, skip_when_pre: bool=True) -> Callable[[ShiftValidator], ShiftValidator]:
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
def shift_setter(*fields: str) -> Callable[[ShiftSetter], ShiftSetter]:
    """Decorator to mark a function as a shift setter"""

    def decorator(func):
        func.__shift_setter_for__ = fields
        return func
    return decorator

# noinspection PyTypeChecker
def shift_repr(*fields: str) -> Callable[[ShiftRepr], ShiftRepr]:
    """Decorator to mark a function as a shift repr"""

    def decorator(func):
        func.__shift_repr_for__ = fields
        return func
    return decorator

# noinspection PyTypeChecker
def shift_serializer(*fields: str) -> Callable[[ShiftSerializer], ShiftSerializer]:
    """Decorator to mark a function as a shift serializer"""

    def decorator(func):
        func.__shift_serializer_for__ = fields
        return func
    return decorator



# endregion
# region Wrappers



def shift_function_wrapper(field: ShiftFieldInfo, info: ShiftInfo, func: Callable) -> Any | None:
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

    # Else if len(params) == 3, it's an advanced function
    if len(sig.parameters) == 3:
        _shift_functions[func] = True
        return func(info.instance, field, info)

    # Else invalid signature
    raise ShiftFieldError(info.model_name, f"Invalid signature for {field.name}: {func.__name__}")

def shift_init_function_wrapper(info: ShiftInfo, func: Callable) -> None:
    """Wrapper to automatically determine if the init function is advanced or not, and call appropriately"""
    # Check cache first
    if func in _shift_init_functions:
        if _shift_init_functions[func]:
            return func(info.instance, info)
        return func(info.instance)

    # Get function signature
    sig = inspect.signature(func)

    # If len(params) == 1, it's a simple function
    if len(sig.parameters) == 1:
        _shift_init_functions[func] = False
        return func(info.instance)

    # If len(params) == 2, it's an advanced function
    if len(sig.parameters) == 2:
        _shift_init_functions[func] = True
        return func(info.instance, info)

    # Else invalid signature
    raise ShiftFieldError(info.model_name, f"Invalid signature for {func.__name__}")


# endregion
# region Builtin Type Functions

## Misc
#######

def _can_index(val: Any) -> bool:
    """Returns True if val can be indexed, False otherwise"""
    try:
        _ = val[0]
        val[0] = val[0]
    except Exception:
        return False
    return True

## Transform
############

def shift_missing_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is not Missing (no type hint but value was set)
    Raises ShiftTypeMismatchError if field_info.val is Missing
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return field_info.val

def shift_base_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is a different type than field_info.typ.
    """

    if not isinstance(field_info.val, field_info.typ):
        raise ShiftTypeMismatchError(f"expected type `{field_info.typ.__name__}`, got `{type(field_info.val).__name__}`")
    return field_info.val

def shift_none_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is None or Missing
    Raises ShiftTypeMismatchError if field_info.val is not None or Missing
    """

    if field_info.val is not None and field_info.val is not Missing:
        raise ShiftTypeMismatchError(f"expected type `None` or Missing, got `{type(field_info.val).__name__}`")
    return None

def shift_any_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is MISSING.
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return field_info.val

def shift_one_of_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to transform field_info.val for each type in field_info.typ.args, returning the first successful transformed value.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # One arg must match
    for arg in args:
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, field_info.val)
            return shift_type_transformer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            pass
    raise ShiftTypeMismatchError(f"expected one of types `{args}`, got `{type(field_info.val).__name__}`")

def shift_one_of_val_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val if val is in field_info.typ.args.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # One val must match
    if not field_info.val in args:
        raise ShiftTypeMismatchError(f"expected one of values `{args}`, got `{field_info.val}`")
    return field_info.val

# noinspection PyTypeChecker
def shift_all_of_single_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to, for all field_info.val, transform field_info.val[i] as the type field_info.typ.args[0].
    Raises ShiftTypeMismatchError if any field_info.val is a different type than field_info.typ.args[0].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Must have one arg and val must be list-like
    if len(args) != 1:
        raise ShiftTypeMismatchError(f"expected one type arg, got `{args}`")
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")

    # Handle case where typ is not indexable
    indexable = _can_index(field_info.val)
    if not indexable:
        field_info.val = list(field_info.val)

    # All values must be of type args[0]
    for i, val in enumerate(field_info.val):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{args[0].__name__}[{i}]", args[0], val)
        try:
            field_info.val[i] = shift_type_transformer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            raise ShiftTypeMismatchError(f"expected all values to be of type `{args[0].__name__}`, but got `{type(val).__name__}` at index {i}")

    # Convert back typ if needed
    if not indexable:
        field_info.val = get_origin(field_info.typ)(field_info.val)
    return field_info.val

# noinspection PyTypeChecker
def shift_all_of_many_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to, for all field_info.val, transform field_info.val[i] as the type field_info.typ.args[i].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[i].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Val must be list-like, and must have same len as args
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")
    if len(field_info.val) != len(args):
        raise ShiftTypeMismatchError(f"expected {len(args)} values, got {len(field_info.val)}")

    # Handle case where typ is not indexable
    indexable = _can_index(field_info.val)
    if not indexable:
        field_info.val = list(field_info.val)

    # All values must be of type args[i]
    for i, (val, arg) in enumerate(zip(field_info.val, args)):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, val)
        try:
            field_info.val[i] = shift_type_transformer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected value at index {i} to be of type `{arg.__name__}`, but got `{type(val).__name__}`: {e}")

    # Convert back typ if needed
    if not indexable:
        field_info.val = get_origin(field_info.typ)(field_info.val)
    return field_info.val

def shift_all_of_pair_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to, for all field_info.val, transform field_info.val[i].key as field_info.typ.args[0] and transform field_info.val[i].val as field_info.typ.args[1].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[0] or field_info.typ.args[1].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Must be dict-like
    if not hasattr(field_info.val, "items"):
        raise ShiftTypeMismatchError(f"expected value to be dict-like, got `{field_info.val}`")

    # All key-val pairs must match type
    new_val = {}
    for i, (key, val) in enumerate(field_info.val.items()):
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(key).__name__}", args[0], key)
            key = shift_type_transformer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected key at index {i} to be of type `{args[0].__name__}`, but got `{type(key).__name__}`: {e}")

        try:
            if len(args) > 1:
                tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(val).__name__}", args[1], val)
                new_val[key] = shift_type_transformer(instance, tmp_field_info, shift_info)
            else:
                new_val[key] = val
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected val at index {i} to be of type `{args[1].__name__}`, but got `{type(val).__name__}`: {e}")

    return new_val

def shift_callable_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to check if value is callable and has a readable signature.
    Raises ShiftTypeMismatchError if value is not callable or has an unreadable signature.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Value must be callable
    if not callable(field_info.val):
        raise ShiftTypeMismatchError(f"expected callable, got `{type(field_info.val).__name__}`")
    if len(args) != 2:
        raise ShiftTypeMismatchError(f"expected type signature `(param_types, return_type)`, got `{args}`")

    try:
        sig = inspect.signature(field_info.val)
    except (ValueError, TypeError):
        raise ShiftTypeMismatchError(f"could not inspect function signature")
    return field_info.val

def shift_forward_ref_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to resolve forward references for field.typ, then calls shift_type_transformer for the resolved type.
    Raises ShiftTypeMismatchError if field.typ cannot be resolved.
    """

    # Check cache first
    if field_info.typ in _resolved_forward_refs:
        field_info.typ = _resolved_forward_refs[field_info.typ]
        return shift_type_transformer(instance, field_info, shift_info)

    # Attempt to resolve the forward ref
    try:
        resolved = resolve_forward_ref(field_info.typ, shift_info)
        register_forward_ref(field_info.typ, resolved)
        field_info.typ = resolved
        return shift_type_transformer(instance, field_info, shift_info)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not resolve forward reference `{field_info.typ}`: {e}")

def shift_shift_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    When the field.val is a ShiftModel subclass instance or dict, returns value.
    Raises ShiftTypeMismatchError if the field.val is not a ShiftModel subclass, or class construction fails.
    """

    try:
        if isinstance(field_info.val, ShiftModel) or issubclass(field_info.val, ShiftModel):
            return field_info.val
    except Exception:
        pass
    if isinstance(field_info.val, dict):
        return field_info.val
    raise ShiftTypeMismatchError(f"expected ShiftModel subclass or dict, got `{type(field_info.val).__name__}`")

def shift_shift_field_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Transforms a field according to ShiftField parameters.
    Raises ShiftTypeMismatchError if the field is not a ShiftField or transform fails.
    """

    if not isinstance(field_info.default, ShiftField):
        raise ShiftTypeMismatchError(f"expected ShiftField default, got `{type(field_info.default).__name__}`")

    if field_info.default.defer or field_info.default.defer_transform:
        return field_info.val

    if field_info.val is Missing or field_info.val is None:
        field_info.val = field_info.default.get_default()
        if field_info.default.default_skips:
            return field_info.val

    tmp_field = ShiftFieldInfo(f"{field_info.name}.{field_info.default.type.__name__}", field_info.default.type, field_info.val)
    field_info.val = shift_type_transformer(instance, tmp_field, shift_info)

    if field_info.default.transformer is not None:
        return shift_function_wrapper(field_info, shift_info, field_info.default.transformer)
    return field_info.val

def shift_type_transformer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Calls the type transformer for a field, returning the transformed value.
    Raises UnknownShiftTypeError if the field type is not registered in the ShiftTypes registry.
    """

    shift_typ = get_shift_type(field_info.typ)
    if shift_typ is None:
        raise UnknownShiftTypeError(f"has unknown type `{field_info.typ}`")
    return shift_function_wrapper(field_info, shift_info, shift_typ.transformer)

## Validate
###########

def shift_missing_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns True when field_info.val is not Missing (no type hint but value was set)
    Raises ShiftTypeMismatchError if field_info.val is Missing
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return True

def shift_base_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    If val is not an instance of field_info.typ, returns False. Otherwise, returns True.
    """

    if not isinstance(field_info.val, field_info.typ):
        raise ShiftTypeMismatchError(f"expected type `{field_info.typ.__name__}`, got `{type(field_info.val).__name__}`")
    return True

def shift_none_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns True when field_info.val is None or Missing
    Raises ShiftTypeMismatchError if field_info.val is not None or Missing
    """

    if field_info.val is not None and field_info.val is not Missing:
        raise ShiftTypeMismatchError(f"expected type `None` or Missing, got `{type(field_info.val).__name__}`")
    return True

def shift_any_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns true when field_info.val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is MISSING.
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return True

def shift_one_of_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Attempts to validate field_info.val for each type in field_info.typ.args, returning True on the first successful validation.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return True

    # One arg must match
    for arg in args:
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, field_info.val)
            return shift_type_validator(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            pass
    raise ShiftTypeMismatchError(f"expected one of types `{args}`, got `{type(field_info.val).__name__}`")

def shift_one_of_val_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns if field_info.val is in field_info.typ.args.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return True

    # One val must match
    if not field_info.val in args:
        raise ShiftTypeMismatchError(f"expected one of values `{args}`, got `{field_info.val}`")
    return True

def shift_all_of_single_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns if, for all field_info.val, field_info.val[i] is the same type as field_info.typ.args[0].
    Raises ShiftTypeMismatchError if any field_info.val is a different type than field_info.typ.args[0].
    """

    args = get_args(field_info.typ)
    if not args:
        return True

    # Must have one arg and val must be list-like
    if len(args) != 1:
        raise ShiftTypeMismatchError(f"expected one type arg, got `{args}`")
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")

    # All values must be of type args[0]
    for i, val in enumerate(field_info.val):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{args[0].__name__}[i]", args[0], val)
        try:
            if not shift_type_validator(instance, tmp_field_info, shift_info):
                raise ShiftTypeMismatchError(f"expected all values to be of type `{args[0].__name__}`, but got `{type(val).__name__}` at index {i}")
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected all values to be of type `{args[0].__name__}`, but got `{type(val).__name__}` at index {i}: {e}")
    return True

# noinspection PyTypeChecker
def shift_all_of_many_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns if, for all field_info.val, field_info.val[i] is the same type as field_info.typ.args[i].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[i].
    """

    args = get_args(field_info.typ)
    if not args:
        return True

    # Val must be list-like, and must have same len as args
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")
    if len(field_info.val) != len(args):
        raise ShiftTypeMismatchError(f"expected {len(args)} values, got {len(field_info.val)}")

    # All values must be of type args[i]
    for i, (val, arg) in enumerate(zip(field_info.val, args)):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, val)
        try:
            if not shift_type_validator(instance, tmp_field_info, shift_info):
                raise ShiftTypeMismatchError(f"expected value at index {i} to be of type `{arg.__name__}`, but got `{type(val).__name__}`")
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected value at index {i} to be of type `{arg.__name__}`, but got `{type(val).__name__}`: {e}")
    return True

def shift_all_of_pair_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns if, for all field_info.val, field_info.val[i].key is the same type as field_info.typ.args[0] and field_info.val[i].val is the same type as field_info.typ.args[1].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[0] or field_info.typ.args[1].
    """

    args = get_args(field_info.typ)
    if not args:
        return True

    # Must be dict-like
    if not hasattr(field_info.val, "items"):
        raise ShiftTypeMismatchError(f"expected value to be dict-like, got `{field_info.val}`")

    # All key-val pairs must match type
    for i, (key, val) in enumerate(field_info.val.items()):
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(key).__name__}", args[0], key)
            if not shift_type_validator(instance, tmp_field_info, shift_info):
                raise ShiftTypeMismatchError(f"expected key at index {i} to be of type `{args[0].__name__}`, but got `{type(key).__name__}`")
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected key at index {i} to be of type `{args[0].__name__}`, but got `{type(key).__name__}`: {e}")

        try:
            if len(args) > 1:
                tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(val).__name__}", args[1], val)
                if not shift_type_validator(instance, tmp_field_info, shift_info):
                    raise ShiftTypeMismatchError(f"expected val at index {i} to be of type `{args[1].__name__}`, but got `{type(val).__name__}`")
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected val at index {i} to be of type `{args[1].__name__}`, but got `{type(val).__name__}`: {e}")

    return True

def shift_callable_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Returns if field.val is callable and matches the expected signature.
    Raises ShiftTypeMismatchError if field.val is not callable or has an invalid signature.
    """

    args = get_args(field_info.typ)
    if not args:
        return True

    # Value must be callable
    if not callable(field_info.val):
        raise ShiftTypeMismatchError(f"expected callable, got `{type(field_info.val).__name__}`")
    if len(args) != 2:
        raise ShiftTypeMismatchError(f"expected type signature `(param_types, return_type)`, got `{args}`")
    param_types = args[0]
    return_type = args[1]

    try:
        sig = inspect.signature(field_info.val)
    except (ValueError, TypeError):
        raise ShiftTypeMismatchError(f"could not inspect function signature")
    params = list(sig.parameters.values())

    # Handle special case: Callable[..., ReturnType] means "any params"
    if param_types is Ellipsis or param_types == ...:
        # Just check the return type
        if return_type is not inspect.Signature.empty:
            if sig.return_annotation == inspect.Signature.empty:
                raise ShiftTypeMismatchError(f"expected return type, but val has none")
            try:
                tmp_field_info = ShiftFieldInfo(f"{field_info.name}.return_type", return_type, sig.return_annotation)
                if not shift_type_validator(instance, tmp_field_info, shift_info):
                    raise ShiftTypeMismatchError(f"expected return type `{type(return_type).__name__}`, but got `{type(sig.return_annotation).__name__}`")
            except ShiftTypeMismatchError as e:
                raise ShiftTypeMismatchError(f"expected return type `{type(return_type).__name__}`, got `{type(sig.return_annotation).__name__}`: {e}")
        return True

    # Check parameter annotations
    if len(params) != len(param_types):
        raise ShiftTypeMismatchError(f"expected {len(param_types)} parameters, got {len(params)}")
    for i, (param, expected_type) in enumerate(zip(params, param_types)):
        if param.annotation == inspect.Parameter.empty:
            # Function has no annotation for this parameter
            continue
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{param.name}", expected_type, param)
            if not shift_type_validator(instance, tmp_field_info, shift_info):
                raise ShiftTypeMismatchError(f"expected parameter `{param.name}` to be of type `{type(expected_type).__name__}`, but got `{type(param.annotation).__name__}`")
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected parameter `{param.name}` to be of type `{type(expected_type).__name__}`, got `{type(param.annotation).__name__}`: {e}")

    # Check return type annotation
    if return_type is not inspect.Signature.empty:
        if sig.return_annotation == inspect.Signature.empty:
            raise ShiftTypeMismatchError(f"expected return type, but val has none")
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.return_type", return_type, sig.return_annotation)
            if not shift_type_validator(instance, tmp_field_info, shift_info):
                raise ShiftTypeMismatchError(f"expected return type `{type(return_type).__name__}`, but got `{type(sig.return_annotation).__name__}`")
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected return type `{type(return_type).__name__}`, got `{type(sig.return_annotation).__name__}`: {e}")
    return True

def shift_forward_ref_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Attempts to resolve forward references for field.typ, then calls shift_type_validator for the resolved type.
    Raises ShiftTypeMismatchError if field.typ cannot be resolved.
    """

    # Check cache first
    if field_info.typ in _resolved_forward_refs:
        field_info.typ = _resolved_forward_refs[field_info.typ]
        return shift_type_validator(instance, field_info, shift_info)

    # Attempt to resolve the forward ref
    try:
        resolved = resolve_forward_ref(field_info.typ, shift_info)
        register_forward_ref(field_info.typ, resolved)
        field_info.typ = resolved
        return shift_type_validator(instance, field_info, shift_info)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not resolve forward reference `{field_info.typ}`: {e}")

def shift_shift_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    When the field.val is a ShiftModel subclass instance return True, otherwise if the field.val is a dict, save construction for set
    Raises ShiftTypeMismatchError if the field.val is not a ShiftModel subclass, or class construction fails.
    """

    try:
        if isinstance(field_info.val, ShiftModel) or issubclass(field_info.val, ShiftModel):
            return True
    except Exception:
        pass
    if isinstance(field_info.val, dict):
        return True
    raise ShiftTypeMismatchError(f"expected ShiftModel subclass or dict, got `{type(field_info.val).__name__}`")

def shift_shift_field_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Validates a field according to ShiftField parameters.
    Raises ShiftTypeMismatchError if the field fails validation.
    """

    if not isinstance(field_info.default, ShiftField):
        raise ShiftTypeMismatchError(f"expected ShiftField default, got `{type(field_info.default).__name__}`")

    if field_info.default.defer or field_info.default.defer_validation:
        return True

    if field_info.default.default_skips:
        return True

    errors = field_info.default.validate(field_info, shift_info)
    if not errors:
        return True

    errors_str = ', '.join(str(error) for error in errors)
    raise ShiftTypeMismatchError(f"failed ShiftField validation: {errors_str}")

def shift_type_validator(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> bool:
    """
    Calls the type validator for a field, returning True if the field passes validation, False otherwise.
    Raises UnknownShiftTypeError if the field type is not registered in the ShiftTypes registry.
    """

    shift_typ = get_shift_type(field_info.typ)
    if shift_typ is None:
        raise UnknownShiftTypeError(f"has unknown type `{field_info.typ}`")
    return shift_function_wrapper(field_info, shift_info, shift_typ.validator)

## Set
######

def shift_missing_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is not Missing (no type hint but value was set)
    Raises ShiftTypeMismatchError if field_info.val is Missing
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return field_info.val

def shift_base_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is not MISSING
    Raises ShiftTypeMismatchError if field_info.val is a different type than field_info.typ.
    """

    if not isinstance(field_info.val, field_info.typ):
        raise ShiftTypeMismatchError(f"expected type `{field_info.typ.__name__}`, got `{type(field_info.val).__name__}`")
    return field_info.val

def shift_none_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is None or Missing
    Raises ShiftTypeMismatchError if field_info.val is not None or Missing
    """

    if field_info.val is not None and field_info.val is not Missing:
        raise ShiftTypeMismatchError(f"expected type `None` or Missing, got `{type(field_info.val).__name__}`")
    return None

def shift_any_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is MISSING.
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return field_info.val

def shift_one_of_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to set field_info.val for each type in field_info.typ.args, returning the first successful set value.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # One arg must match
    for arg in args:
        try:
            arg_typ = arg if isinstance(arg, type) else type(arg)
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg_typ, field_info.val)
            return shift_type_setter(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            pass
    raise ShiftTypeMismatchError(f"expected one of types `{args}`, got `{type(field_info.val).__name__}`")

def shift_one_of_val_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Returns field_info.val if val is in field_info.typ.args.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # One val must match
    if not field_info.val in args:
        raise ShiftTypeMismatchError(f"expected one of values `{args}`, got `{field_info.val}`")
    return field_info.val

# noinspection PyTypeChecker
def shift_all_of_single_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to, for all field_info.val, set field_info.val[i] as the type field_info.typ.args[0].
    Raises ShiftTypeMismatchError if any field_info.val is a different type than field_info.typ.args[0].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Must have one arg and val must be list-like
    if len(args) != 1:
        raise ShiftTypeMismatchError(f"expected one type arg, got `{args}`")
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")

    # Handle case where typ is not indexable
    indexable = _can_index(field_info.val)
    if not indexable:
        field_info.val = list(field_info.val)

    # All values must be of type args[0]
    for i, val in enumerate(field_info.val):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{args[0].__name__}[i]", args[0], val)
        try:
            field_info.val[i] = shift_type_setter(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            raise ShiftTypeMismatchError(f"expected all values to be of type `{args[0].__name__}`, but got `{type(val).__name__}` at index {i}")

    # Convert back typ if needed
    if not indexable:
        field_info.val = get_origin(field_info.typ)(field_info.val)
    return field_info.val

# noinspection PyTypeChecker
def shift_all_of_many_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to, for all field_info.val, set field_info.val[i] as the type field_info.typ.args[i].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[i].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Val must be list-like, and must have same len as args
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")
    if len(field_info.val) != len(args):
        raise ShiftTypeMismatchError(f"expected {len(args)} values, got {len(field_info.val)}")

    # Handle case where typ is not indexable
    indexable = _can_index(field_info.val)
    if not indexable:
        field_info.val = list(field_info.val)

    # All values must be of type args[i]
    for i, (val, arg) in enumerate(zip(field_info.val, args)):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, val)
        try:
            field_info.val[i] = shift_type_setter(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected value at index {i} to be of type `{arg.__name__}`, but got `{type(val).__name__}`: {e}")

    # Convert back typ if needed
    if not indexable:
        field_info.val = get_origin(field_info.typ)(field_info.val)
    return field_info.val

def shift_all_of_pair_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to, for all field_info.val, set field_info.val[i].key as field_info.typ.args[0] and set field_info.val[i].val as field_info.typ.args[1].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[0] or field_info.typ.args[1].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Must be dict-like
    if not hasattr(field_info.val, "items"):
        raise ShiftTypeMismatchError(f"expected value to be dict-like, got `{field_info.val}`")

    # All key-val pairs must match type
    new_val = {}
    for i, (key, val) in enumerate(field_info.val.items()):
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(key).__name__}", args[0], key)
            key = shift_type_setter(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected key at index {i} to be of type `{args[0].__name__}`, but got `{type(key).__name__}`: {e}")

        try:
            if len(args) > 1:
                tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(val).__name__}", args[1], val)
                new_val[key] = shift_type_setter(instance, tmp_field_info, shift_info)
            else:
                new_val[key] = val
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected val at index {i} to be of type `{args[1].__name__}`, but got `{type(val).__name__}`: {e}")

    return new_val

def shift_callable_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to check if value is callable and has a readable signature.
    Raises ShiftTypeMismatchError if value is not callable or has an unreadable signature.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Value must be callable
    if not callable(field_info.val):
        raise ShiftTypeMismatchError(f"expected callable, got `{type(field_info.val).__name__}`")
    if len(args) != 2:
        raise ShiftTypeMismatchError(f"expected type signature `(param_types, return_type)`, got `{args}`")

    try:
        sig = inspect.signature(field_info.val)
    except (ValueError, TypeError):
        raise ShiftTypeMismatchError(f"could not inspect function signature")
    return field_info.val

def shift_forward_ref_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Attempts to resolve forward references for field.typ, then calls setter for the resolved type.
    Raises ShiftTypeMismatchError if field.typ cannot be resolved.
    """

    # Check cache first
    if field_info.typ in _resolved_forward_refs:
        field_info.typ = _resolved_forward_refs[field_info.typ]
        return shift_type_setter(instance, field_info, shift_info)

    # Attempt to resolve the forward ref
    try:
        resolved = resolve_forward_ref(field_info.typ, shift_info)
        register_forward_ref(field_info.typ, resolved)
        field_info.typ = resolved
        return shift_type_setter(instance, field_info, shift_info)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not resolve forward reference `{field_info.typ}`: {e}")

def shift_shift_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    When the field.val is a ShiftModel subclass return, else if dict try building the instance
    Raises ShiftTypeMismatchError if the field.val is not a ShiftModel subclass, or class construction fails.
    """

    try:
        if isinstance(field_info.val, ShiftModel) or issubclass(field_info.val, ShiftModel):
            return field_info.val
    except Exception:
        pass
    if isinstance(field_info.val, dict) and isinstance(field_info.typ, type):
        return field_info.typ(**field_info.val)
    raise ShiftTypeMismatchError(f"expected ShiftModel subclass or dict, got `{type(field_info.val).__name__}`")

def shift_shift_field_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Sets a field according to ShiftField parameters.
    Raises ShiftTypeMismatchError if the field is not a ShiftField or set fails.
    """

    if not isinstance(field_info.default, ShiftField):
        raise ShiftTypeMismatchError(f"expected ShiftField default, got `{type(field_info.default).__name__}`")

    if field_info.default.defer or field_info.default.defer_set:
        return field_info.val

    if field_info.default.default_skips:
        return field_info.val

    tmp_field = ShiftFieldInfo(f"{field_info.name}.{field_info.default.type.__name__}", field_info.default.type, field_info.val)
    field_info.val = shift_type_setter(instance, tmp_field, shift_info)

    if field_info.default.setter is not None:
        return shift_function_wrapper(field_info, shift_info, field_info.default.setter)
    return field_info.val

def shift_type_setter(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any:
    """
    Calls the type setter for a field, returning the set value.
    Raises UnknownShiftTypeError if the field type is not registered in the ShiftTypes registry.
    """

    shift_typ = get_shift_type(field_info.typ)
    if shift_typ is None:
        raise UnknownShiftTypeError(f"has unknown type `{field_info.typ}`")
    return shift_function_wrapper(field_info, shift_info, shift_typ.setter)

## ShiftRepr
############

def shift_missing_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Returns repr(field_info.val) when val is not Missing (no type hint but value was set)
    Raises ShiftTypeMismatchError if field_info.val is Missing
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return repr(field_info.val)

def shift_base_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Returns repr(field_info.val) when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is a different type than field_info.typ.
    """

    if not isinstance(field_info.val, field_info.typ):
        raise ShiftTypeMismatchError(f"expected type `{field_info.typ.__name__}`, got `{type(field_info.val).__name__}`")
    return repr(field_info.val)

def shift_none_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Returns repr(field_info.val) when val is None or Missing
    Raises ShiftTypeMismatchError if field_info.val is not None or Missing
    """

    if field_info.val is not None and field_info.val is not Missing:
        raise ShiftTypeMismatchError(f"expected type `None` or Missing, got `{type(field_info.val).__name__}`")
    return repr(field_info.val)

def shift_any_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Returns repr(field_info.val) when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is MISSING.
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return repr(field_info.val)

def shift_one_of_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Attempts to repr field_info.val for each type in field_info.typ.args, returning the first successful repred value.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return repr(field_info.val)

    # One arg must match
    for arg in args:
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, field_info.val)
            return shift_type_repr(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            pass
    raise ShiftTypeMismatchError(f"expected one of types `{args}`, got `{type(field_info.val).__name__}`")

def shift_one_of_val_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Returns repr(field_info.val) if val is in field_info.typ.args.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return repr(field_info.val)

    # One val must match
    if not field_info.val in args:
        raise ShiftTypeMismatchError(f"expected one of values `{args}`, got `{field_info.val}`")
    return repr(field_info.val)

# noinspection PyTypeChecker
def shift_all_of_single_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Attempts to, for all field_info.val, repr field_info.val[i] as the type field_info.typ.args[0].
    Raises ShiftTypeMismatchError if any field_info.val is a different type than field_info.typ.args[0].
    """

    args = get_args(field_info.typ)
    if not args:
        return repr(field_info.val)

    # Must have one arg and val must be list-like
    if len(args) != 1:
        raise ShiftTypeMismatchError(f"expected one type arg, got `{args}`")
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")

    # All values must be of type args[0]
    for i, val in enumerate(field_info.val):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{args[0].__name__}[i]", args[0], val)
        try:
            field_info.val[i] = shift_type_repr(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            raise ShiftTypeMismatchError(f"expected all values to be of type `{args[0].__name__}`, but got `{type(val).__name__}` at index {i}")
    return repr(field_info.val)

# noinspection PyTypeChecker
def shift_all_of_many_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Attempts to, for all field_info.val, repr field_info.val[i] as the type field_info.typ.args[i].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[i].
    """

    args = get_args(field_info.typ)
    if not args:
        return repr(field_info.val)

    # Val must be list-like, and must have same len as args
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")
    if len(field_info.val) != len(args):
        raise ShiftTypeMismatchError(f"expected {len(args)} values, got {len(field_info.val)}")

    # All values must be of type args[i]
    for i, (val, arg) in enumerate(zip(field_info.val, args)):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, val)
        try:
            field_info.val[i] = shift_type_repr(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected value at index {i} to be of type `{arg.__name__}`, but got `{type(val).__name__}`: {e}")
    return repr(field_info.val)

def shift_all_of_pair_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Attempts to, for all field_info.val, repr field_info.val[i].key as field_info.typ.args[0] and repr field_info.val[i].val as field_info.typ.args[1].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[0] or field_info.typ.args[1].
    """

    args = get_args(field_info.typ)
    if not args:
        return repr(field_info.val)

    # Must be dict-like
    if not hasattr(field_info.val, "items"):
        raise ShiftTypeMismatchError(f"expected value to be dict-like, got `{field_info.val}`")

    # All key-val pairs must match type
    new_val = {}
    for i, (key, val) in enumerate(field_info.val.items()):
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(key).__name__}", args[0], key)
            key = shift_type_repr(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected key at index {i} to be of type `{args[0].__name__}`, but got `{type(key).__name__}`: {e}")

        try:
            if len(args) > 1:
                tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(val).__name__}", args[1], val)
                new_val[key] = shift_type_repr(instance, tmp_field_info, shift_info)
            else:
                new_val[key] = val
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected val at index {i} to be of type `{args[1].__name__}`, but got `{type(val).__name__}`: {e}")

    return repr(new_val)

def shift_callable_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Attempts to check if value is callable and has a readable signature.
    Raises ShiftTypeMismatchError if value is not callable or has an unreadable signature.
    """

    args = get_args(field_info.typ)
    if not args:
        return repr(field_info.val)

    # Value must be callable
    if not callable(field_info.val):
        raise ShiftTypeMismatchError(f"expected callable, got `{type(field_info.val).__name__}`")
    if len(args) != 2:
        raise ShiftTypeMismatchError(f"expected type signature `(param_types, return_type)`, got `{args}`")

    try:
        sig = inspect.signature(field_info.val)
    except (ValueError, TypeError):
        raise ShiftTypeMismatchError(f"could not inspect function signature")
    return repr(field_info.val)

def shift_forward_ref_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Attempts to resolve forward references for field.typ, then calls repr for the resolved type.
    Raises ShiftTypeMismatchError if field.typ cannot be resolved.
    """

    # Check cache first
    if field_info.typ in _resolved_forward_refs:
        field_info.typ = _resolved_forward_refs[field_info.typ]
        return shift_type_repr(instance, field_info, shift_info)

    # Attempt to resolve the forward ref
    try:
        resolved = resolve_forward_ref(field_info.typ, shift_info)
        register_forward_ref(field_info.typ, resolved)
        field_info.typ = resolved
        return shift_type_repr(instance, field_info, shift_info)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not resolve forward reference `{field_info.typ}`: {e}")
    
def shift_shift_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    When the field.val is a ShiftModel subclass instance return the repred class
    Raises ShiftTypeMismatchError if the field.val is not a ShiftModel subclass, or class construction fails.
    """

    try:
        if isinstance(field_info.val, ShiftModel) or issubclass(field_info.val, ShiftModel):
            return repr(field_info.val)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not inspect value: {e}")
    raise ShiftTypeMismatchError(f"expected ShiftModel subclass or dict, got `{type(field_info.val).__name__}`")

def shift_shift_field_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Reprs a field according to ShiftField parameters.
    Raises ShiftTypeMismatchError if the field is not a ShiftField or repr fails.
    """

    if not isinstance(field_info.default, ShiftField):
        raise ShiftTypeMismatchError(f"expected ShiftField default, got `{type(field_info.default).__name__}`")

    if field_info.default.defer or field_info.default.defer_repr:
        return None

    if field_info.default.repr_func is not None:
        return shift_function_wrapper(field_info, shift_info, field_info.default.repr_func)

    tmp_field = ShiftFieldInfo(f"{field_info.name}.{field_info.default.type.__name__}", field_info.default.type, field_info.val)
    return shift_type_repr(instance, tmp_field, shift_info)

def shift_type_repr(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> str | None:
    """
    Calls the type repr for a field, returning the repr value.
    Raises UnknownShiftTypeError if the field type is not registered in the ShiftTypes registry.
    """

    shift_typ = get_shift_type(field_info.typ)
    if shift_typ is None:
        raise UnknownShiftTypeError(f"has unknown type `{field_info.typ}`")
    return shift_function_wrapper(field_info, shift_info, shift_typ.repr)

## Serialize
############

def shift_missing_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Returns field_info.val when val is not Missing (no type hint but value was set)
    Raises ShiftTypeMismatchError if field_info.val is Missing
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return field_info.val

def shift_base_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Returns field_info.val when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is a different type than field_info.typ.
    """

    if not isinstance(field_info.val, field_info.typ):
        raise ShiftTypeMismatchError(f"expected type `{field_info.typ.__name__}`, got `{type(field_info.val).__name__}`")
    return field_info.val

def shift_none_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Returns field_info.val when val is None or Missing
    Raises ShiftTypeMismatchError if field_info.val is not None or Missing
    """

    if field_info.val is not None and field_info.val is not Missing:
        raise ShiftTypeMismatchError(f"expected type `None` or Missing, got `{type(field_info.val).__name__}`")
    return field_info.val

def shift_any_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Returns field_info.val when val is not MISSING.
    Raises ShiftTypeMismatchError if field_info.val is MISSING.
    """

    if field_info.val is Missing:
        raise ShiftTypeMismatchError(f"expected a value, got `MISSING`")
    return field_info.val

def shift_one_of_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Attempts to serialize field_info.val for each type in field_info.typ.args, returning the first successful serialized value.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # One arg must match
    for arg in args:
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, field_info.val)
            return shift_type_serializer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            pass
    raise ShiftTypeMismatchError(f"expected one of types `{args}`, got `{type(field_info.val).__name__}`")

def shift_one_of_val_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Returns field_info.val if val is in field_info.typ.args.
    Raises ShiftTypeMismatchError if no type in field_info.typ.args matches field_info.val.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # One val must match
    if not field_info.val in args:
        raise ShiftTypeMismatchError(f"expected one of values `{args}`, got `{field_info.val}`")
    return field_info.val

# noinspection PyTypeChecker
def shift_all_of_single_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Attempts to, for all field_info.val, serialize field_info.val[i] as the type field_info.typ.args[0].
    Raises ShiftTypeMismatchError if any field_info.val is a different type than field_info.typ.args[0].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Must have one arg and val must be list-like
    if len(args) != 1:
        raise ShiftTypeMismatchError(f"expected one type arg, got `{args}`")
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")

    # All values must be of type args[0]
    for i, val in enumerate(field_info.val):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{args[0].__name__}[i]", args[0], val)
        try:
            field_info.val[i] = shift_type_serializer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError:
            raise ShiftTypeMismatchError(f"expected all values to be of type `{args[0].__name__}`, but got `{type(val).__name__}` at index {i}")
    return field_info.val

# noinspection PyTypeChecker
def shift_all_of_many_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Attempts to, for all field_info.val, serialize field_info.val[i] as the type field_info.typ.args[i].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[i].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Val must be list-like, and must have same len as args
    if not isinstance(field_info.val, Iterable):
        raise ShiftTypeMismatchError(f"expected value to be list-like, got `{field_info.val}`")
    if len(field_info.val) != len(args):
        raise ShiftTypeMismatchError(f"expected {len(args)} values, got {len(field_info.val)}")

    # All values must be of type args[i]
    for i, (val, arg) in enumerate(zip(field_info.val, args)):
        tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{arg.__name__}", arg, val)
        try:
            field_info.val[i] = shift_type_serializer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected value at index {i} to be of type `{arg.__name__}`, but got `{type(val).__name__}`: {e}")
    return field_info.val

def shift_all_of_pair_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Attempts to, for all field_info.val, serialize field_info.val[i].key as field_info.typ.args[0] and serialize field_info.val[i].val as field_info.typ.args[1].
    Raises ShiftTypeMismatchError if any field_info.val[i] is a different type than field_info.typ.args[0] or field_info.typ.args[1].
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Must be dict-like
    if not hasattr(field_info.val, "items"):
        raise ShiftTypeMismatchError(f"expected value to be dict-like, got `{field_info.val}`")

    # All key-val pairs must match type
    new_val = {}
    for i, (key, val) in enumerate(field_info.val.items()):
        try:
            tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(key).__name__}", args[0], key)
            key = shift_type_serializer(instance, tmp_field_info, shift_info)
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected key at index {i} to be of type `{args[0].__name__}`, but got `{type(key).__name__}`: {e}")

        try:
            if len(args) > 1:
                tmp_field_info = ShiftFieldInfo(f"{field_info.name}.{type(val).__name__}", args[1], val)
                new_val[key] = shift_type_serializer(instance, tmp_field_info, shift_info)
            else:
                new_val[key] = val
        except ShiftTypeMismatchError as e:
            raise ShiftTypeMismatchError(f"expected val at index {i} to be of type `{args[1].__name__}`, but got `{type(val).__name__}`: {e}")

    return new_val

def shift_callable_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Attempts to check if value is callable and has a readable signature.
    Raises ShiftTypeMismatchError if value is not callable or has an unreadable signature.
    """

    args = get_args(field_info.typ)
    if not args:
        return field_info.val

    # Value must be callable
    if not callable(field_info.val):
        raise ShiftTypeMismatchError(f"expected callable, got `{type(field_info.val).__name__}`")
    if len(args) != 2:
        raise ShiftTypeMismatchError(f"expected type signature `(param_types, return_type)`, got `{args}`")

    try:
        sig = inspect.signature(field_info.val)
    except (ValueError, TypeError):
        raise ShiftTypeMismatchError(f"could not inspect function signature")
    return field_info.val

def shift_forward_ref_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Attempts to resolve forward references for field.typ, then calls serializer for the resolved type.
    Raises ShiftTypeMismatchError if field.typ cannot be resolved.
    """

    # Check cache first
    if field_info.typ in _resolved_forward_refs:
        field_info.typ = _resolved_forward_refs[field_info.typ]
        return shift_type_repr(instance, field_info, shift_info)

    # Attempt to resolve the forward ref
    try:
        resolved = resolve_forward_ref(field_info.typ, shift_info)
        register_forward_ref(field_info.typ, resolved)
        field_info.typ = resolved
        return shift_type_serializer(instance, field_info, shift_info)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not resolve forward reference `{field_info.typ}`: {e}")
    
def shift_shift_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    When the field.val is a ShiftModel subclass instance return the serialized class
    Raises ShiftTypeMismatchError if the field.val is not a ShiftModel subclass, or class construction fails.
    """

    try:
        if isinstance(field_info.val, ShiftModel) or issubclass(field_info.val, ShiftModel):
            return serialize(field_info.val)
    except Exception as e:
        raise ShiftTypeMismatchError(f"could not inspect value: {e}")
    raise ShiftTypeMismatchError(f"expected ShiftModel subclass or dict, got `{type(field_info.val).__name__}`")

def shift_shift_field_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Serializes a field according to ShiftField parameters.
    Raises ShiftTypeMismatchError if the field is not a ShiftField or repr fails.
    """

    if not isinstance(field_info.default, ShiftField):
        raise ShiftTypeMismatchError(f"expected ShiftField default, got `{type(field_info.default).__name__}`")

    if field_info.default.defer or field_info.default.defer_serialize:
        return None

    if field_info.default.serializer is not None:
        return shift_function_wrapper(field_info, shift_info, field_info.default.serializer)

    tmp_field = ShiftFieldInfo(f"{field_info.name}.{field_info.default.type.__name__}", field_info.default.type, field_info.val)
    return shift_type_serializer(instance, tmp_field, shift_info)

def shift_type_serializer(instance: Any, field_info: ShiftFieldInfo, shift_info: ShiftInfo) -> Any | None:
    """
    Calls the type serializer for a field, returning the serialized value.
    Raises UnknownShiftTypeError if the field type is not registered in the ShiftTypes registry.
    """

    shift_typ = get_shift_type(field_info.typ)
    if shift_typ is None:
        raise UnknownShiftTypeError(f"has unknown type `{field_info.typ}`")
    return shift_function_wrapper(field_info, shift_info, shift_typ.serializer)



# endregion
# region ShiftModel Processing Functions



## Misc
############

def _build_field_error(field_name: str, error: Exception) -> ShiftFieldError | Exception:
    # Don't wrap if it's already a ShiftFieldError
    if isinstance(error, ShiftFieldError):
        return error
    if isinstance(error, ShiftTypeMismatchError) or isinstance(error, UnknownShiftTypeError):
        return ShiftFieldError(field_name, error.msg)
    return error



## Transform
############

def _transform_field(field: ShiftFieldInfo, info: ShiftInfo) -> None:
    # Call pre-transformer if present
    if field.name in info.pre_transformers:
        field.val = shift_function_wrapper(field, info, info.pre_transformers[field.name])
    if field.name in info.pre_transformers and field.name in info.pre_transformer_skips:
        return

    # Run type transformation
    if field.val is Missing:
        # Only do the default set here as long as the value is not a ShiftField
        if not isinstance(field.default, ShiftField):
            field.val = field.default
    field.val = shift_type_transformer(field.val, field, info)

    # Call field transformer if present
    if field.name in info.transformers:
        field.val = shift_function_wrapper(field, info, info.transformers[field.name])

def _transform(info: ShiftInfo) -> None:
    # Transform all class fields
    for field in info.fields:
        try:
            _transform_field(field, info)
        except ShiftError as e:
            e = _build_field_error(field.name, e)
            if info.shift_config.fail_fast:
                raise e
            info.transform_errors.append(e)



## Validate
###########

def _validate_field(field: ShiftFieldInfo, info: ShiftInfo) -> bool:
    # Call pre-validator if present
    if field.name in info.pre_validators and not shift_function_wrapper(field, info, info.pre_validators[field.name]):
        return False
    if field.name in info.pre_validators and field.name in info.pre_validator_skips:
        return True

    # Run type validation
    if not shift_type_validator(field.val, field, info):
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
                raise ShiftFieldError(field.name, 'failed validation')
        except ShiftError as e:
            e = _build_field_error(field.name, e)
            if info.shift_config.fail_fast:
                raise e
            info.validation_errors.append(e)
            all_valid = False

    return all_valid



## Set
######

def _set_field(field: ShiftFieldInfo, info: ShiftInfo) -> None:
    # If field setter, call (assume set in function)
    if field.name in info.setters:
        field.val = shift_function_wrapper(field, info, info.setters[field.name])
        return

    # Run type set
    setattr(info.instance, field.name, shift_type_setter(field.val, field, info))

def _set(info: ShiftInfo) -> None:
    for field in info.fields:
        try:
            _set_field(field, info)
        except ShiftError as e:
            e = _build_field_error(field.name, e)
            if info.shift_config.fail_fast:
                raise e
            info.set_errors.append(e)



## Repr
#######

def _repr_field(field: ShiftFieldInfo, info: ShiftInfo) -> str | None:
    # If field repr, call
    if field.name in info.reprs:
        return str(shift_function_wrapper(field, info, info.reprs[field.name]))

    # If field name is private and config set to exclude, return
    if field.name.startswith("_") and not info.shift_config.include_private_fields_in_serialization:
        return None

    # If field is default value and config set to exclude, return default value repr
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    # Run type repr
    return shift_type_repr(info.instance, field, info)

def _repr(info: ShiftInfo) -> str:
    result: list[str] = []
    if info.shift_config.include_private_fields_in_serialization and (info.shift_config != DEFAULT_SHIFT_CONFIG or info.shift_config.include_default_fields_in_serialization):
        result.append(f"__shift_config__={repr(info.shift_config)}")
    for field in info.fields:
        res = (_repr_field(field, info))

        # Handle field name
        if res is not None and isinstance(field.default, ShiftField):
            if field.default.repr_exclude:
                continue
            if field.default.repr_as:
                res = f"{field.default.repr_as}={res}"
        elif res is not None:
            res = f"{field.name}={res}"

        if res is not None:
            result.append(res)
    return f"{info.model_name}({', '.join(result)})"



## Serialize
############

def _serialize_field(field: ShiftFieldInfo, info: ShiftInfo) -> dict | None:
    # If field serializer, call
    if field.name in info.serializers:
        return shift_function_wrapper(field, info, info.serializers[field.name])

    # If field name is private and config set to exclude, return
    if field.name.startswith("_") and not info.shift_config.include_private_fields_in_serialization:
        return None

    # If field is default value and config set to exclude, return default value repr
    if field.val == field.default and not info.shift_config.include_default_fields_in_serialization:
        return None

    # Run type serializer
    return shift_type_serializer(info.instance, field, info)

def _serialize(info: ShiftInfo) -> dict:
    result = {}
    if info.shift_config.include_private_fields_in_serialization and (info.shift_config != DEFAULT_SHIFT_CONFIG or info.shift_config.include_default_fields_in_serialization):
        result["__shift_config__"] = serialize(info.shift_config)
    for field in info.fields:
        res = _serialize_field(field, info)

        # Handle field name
        if res is not None and isinstance(field.default, ShiftField):
            if field.default.serializer_exclude:
                continue
            if field.default.serialize_as:
                res = {field.default.serialize_as: res}
        elif res is not None:
            res = {field.name: res}

        if res is not None:
            result.update(res)
    return result



# endregion
# region ShiftModel Classes



## Class Init Functions
#######################

def get_shift_config(cls, fields: dict) -> ShiftConfig | None:
    # Get shift_config from cls if it exists
    shift_config = fields.get("__shift_config__")
    if shift_config and not isinstance(shift_config, ShiftConfig):
        raise ShiftFieldError(cls.__name__, "`__shift_config__` must be a ShiftConfig instance")

    # Get shift_config from cls attributes if kwargs present
    config_kwargs = {}
    if hasattr(cls, '__do_processing__'):
        config_kwargs['do_processing'] = cls.__do_processing__
    if hasattr(cls, '__fail_fast__'):
        config_kwargs['fail_fast'] = cls.__fail_fast__
    if hasattr(cls, '__try_coerce_types__'):
        config_kwargs['try_coerce_types'] = cls.__try_coerce_types__
    if hasattr(cls, '__allow_private_field_setting__'):
        config_kwargs['allow_private_field_setting'] = cls.__allow_private_field_setting__
    if hasattr(cls, '__include_default_fields_in_serialization__'):
        config_kwargs['include_default_fields_in_serialization'] = cls.__include_default_fields_in_serialization__
    if hasattr(cls, '__include_private_fields_in_serialization__'):
        config_kwargs['include_private_fields_in_serialization'] = cls.__include_private_fields_in_serialization__
    if config_kwargs:
        shift_config = ShiftConfig(**config_kwargs)

    # If no shift config provided, use global default
    if not shift_config:
        shift_config = DEFAULT_SHIFT_CONFIG
    return shift_config.__copy__()

def get_field_decorators(cls: Any, fields: dict) -> dict[str, list[AnyShiftDecorator] | list[str]]:
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

def get_fields(cls: Any, fields: dict, data: dict, shift_config: ShiftConfig = DEFAULT_SHIFT_CONFIG) -> list[ShiftFieldInfo]:
    shift_fields: list[ShiftFieldInfo] = []

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
            raise ShiftFieldError(cls.__name__, f"{field_name} has a set value in data, but allow_private_field_setting is False")

        # If field is private and no default is set, add an implicit None default and change type to Optional[typ]
        if field_name.startswith('_') and default is Missing:
            default = None
            field_type = Optional[field_type]

        # If default is a ShiftField, get implicit type
        if isinstance(default, ShiftField):
            # If field is marked as deferred, continue to ignore field
            if default.defer:
                continue

            default.type = field_type
            shift_fields.append(ShiftFieldInfo(name=field_name, typ=ShiftField, val=val, default=default))
            continue

        # Add to shift_fields list
        shift_fields.append(ShiftFieldInfo(name=field_name, typ=field_type, val=val, default=default))

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
            default = getattr(cls, field_name, Missing)
        except AttributeError:
            continue

        # Skip class/static methods, properties, etc.
        if inspect.ismethod(default) or inspect.isfunction(default) or callable(default):
            continue

        # Get val from data if exists
        val = Missing
        if field_name in data:
            val = data[field_name]

            # If field is private, has a data-set value, and allow setting is false, throw
            if field_name.startswith("_") and val is not Missing and not shift_config.allow_private_field_setting:
                raise ShiftFieldError(cls.__name__, f"{field_name} has a set value in data, but allow_private_field_setting is False")

        # If field is private and no default is set, add an implicit None default
        if field_name.startswith('_') and default is Missing:
            default = None

        # If the value is a ShiftField, set the type
        if isinstance(default, ShiftField):
            # If field is marked as deferred, continue to ignore field
            if default.defer:
                continue

            shift_fields.append(ShiftFieldInfo(name=field_name, typ=ShiftField, val=val, default=default))
            continue

        # Add to shift_fields list
        shift_fields.append(ShiftFieldInfo(name=field_name, val=val, default=default))

    # Return shift_fields list
    return shift_fields

def get_updated_fields(instance: Any, fields: list[ShiftFieldInfo], data: dict, shift_config: ShiftConfig = DEFAULT_SHIFT_CONFIG) -> list[ShiftFieldInfo]:
    updated_fields = []
    for field in fields:
        # If name is private, a data val is present, and allow setting is false, throw
        if field.name.startswith("_") and field.name in data and not shift_config.allow_private_field_setting:
            raise ShiftFieldError(instance.__class__.__name__, f"{field.name} has a set value in data, but allow_private_field_setting is False")

        new_val = data.get(field.name, field.default)

        # If val is a ShiftField, set default to new_val and val to Missing
        if isinstance(new_val, ShiftField):
            updated_fields.append(ShiftFieldInfo(
                name=field.name,
                typ=field.typ,
                val=Missing,
                default=new_val
            ))
            continue

        # Create a NEW ShiftFieldInfo instead of mutating the cached one
        updated_fields.append(ShiftFieldInfo(
            name=field.name,
            typ=field.typ,
            val=new_val,
            default=field.default
        ))
    return updated_fields

def get_val_fields(instance: Any, fields: list[ShiftFieldInfo]) -> list[ShiftFieldInfo]:
    val_fields = []
    for field in fields:
        if hasattr(instance, field.name):
            val_fields.append(ShiftFieldInfo(
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
            transform_errors=[],
            validation_errors=[],
            set_errors=[]
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
        transform_errors=[],
        validation_errors=[],
        set_errors=[]
    )

    # Register info and return it
    _shift_info_registry[cls] = info
    return info



## Classes
##########

class ShiftModel:
    """Base class for all shift models"""

    def __init__(self, **data):
        # Get shift info
        info = get_shift_info(self.__class__, self, data)

        # If cls has __pre_init__(), call
        if "__pre_init__" in self.__class__.__dict__:
            shift_init_function_wrapper(info, self.__class__.__dict__["__pre_init__"])

        # Run transform, validation, and set processes
        if info.shift_config.do_processing:
            self.transform(info)
            self.validate(info)
            self.set(info)

        # If cls has __post_init__(), call
        if "__post_init__" in self.__class__.__dict__:
            shift_init_function_wrapper(info, self.__class__.__dict__["__post_init__"])



    def transform(self, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, data)

        # Run transform process
        _transform(info)

        # Check for errors
        if len(info.transform_errors):
            raise ShiftModelError(self.__class__.__name__, 'transform', info.transform_errors)

    def validate(self, info: ShiftInfo=None, **data) -> bool:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, data)

        # Run validation, throw if fail
        if not _validate(info) or len(info.validation_errors):
            raise ShiftModelError(self.__class__.__name__, 'validation', info.validation_errors)
        return True

    def set(self, info: ShiftInfo=None, **data) -> None:
        # Get shift info if not provided
        if info is None:
            info = get_shift_info(self.__class__, self, data)

        # Run set process
        _set(info)

        # Check for errors
        if len(info.set_errors):
            raise ShiftModelError(self.__class__.__name__, 'set', info.set_errors)

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



# endregion
# region Utilities



## ShiftModel Types
##############

def get_shift_type_registry() -> dict[Type, ShiftType]:
    """Returns a copy of the shift type registry"""
    return _shift_types.copy()

def register_shift_type(typ: Type, shift_type: ShiftType) -> None:
    """Registers a shift type"""
    _shift_types[typ] = shift_type

def deregister_shift_type(typ: Type) -> None:
    """Deregisters a shift type"""
    if typ not in _shift_types:
        raise ShiftFieldError("<module>", f"Type `{typ}` is not registered")
    del _shift_types[typ]

def clear_shift_types() -> None:
    """Clears all registered shift types"""
    _shift_types.clear()



## Forward Refs
###############

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
        raise ShiftFieldError("<module>", f"Forward ref `{ref}` is not registered")
    del _resolved_forward_refs[ref]

def clear_forward_refs() -> None:
    """Clears all registered forward refs"""
    _resolved_forward_refs.clear()



## ShiftModel Infos
##############

def get_shift_info_registry() -> dict[Any, ShiftInfo]:
    """Returns a copy of the model info registry"""
    return _shift_info_registry.copy()

def clear_shift_info_registry() -> None:
    """Clears the shift info cache for a shift class"""
    _shift_info_registry.clear()



## ShiftModel Functions
##################

def get_shift_function_registry() -> dict[Callable[[AnyShiftDecorator], bool], bool]:
    """Returns a copy of the shift function registry"""
    return _shift_functions.copy()

def clear_shift_function_registry() -> None:
    """Clears the shift function cache"""
    _shift_functions.clear()



## ShiftModel init Functions
#######################

def get_shift_init_function_registry() -> dict[Callable[[Any | Any, ShiftInfo], bool], bool]:
    """Returns a copy of the shift init function registry"""
    return _shift_init_functions.copy()

def clear_shift_init_function_registry() -> None:
    """Clears the shift init function cache"""
    _shift_init_functions.clear()



## Misc
#######

missing_shift_type = ShiftType(shift_missing_type_transformer, shift_missing_type_validator, shift_missing_type_setter, shift_missing_type_repr, shift_missing_type_serializer)
base_shift_type = ShiftType(shift_base_type_transformer, shift_base_type_validator, shift_base_type_setter, shift_base_type_repr, shift_base_type_serializer)
none_shift_type = ShiftType(shift_none_type_transformer, shift_none_type_validator, shift_none_type_setter, shift_none_type_repr, shift_none_type_serializer)
any_shift_type = ShiftType(shift_any_type_transformer, shift_any_type_validator, shift_any_type_setter, shift_any_type_repr, shift_any_type_serializer)
one_of_val_shift_type = ShiftType(shift_one_of_val_type_transformer, shift_one_of_val_type_validator, shift_one_of_val_type_setter, shift_one_of_val_type_repr, shift_one_of_val_type_serializer)
one_of_shift_type = ShiftType(shift_one_of_type_transformer, shift_one_of_type_validator, shift_one_of_type_setter, shift_one_of_type_repr, shift_one_of_type_serializer)
all_of_single_shift_type = ShiftType(shift_all_of_single_type_transformer, shift_all_of_single_type_validator, shift_all_of_single_type_setter, shift_all_of_single_type_repr, shift_all_of_single_type_serializer)
all_of_many_shift_type = ShiftType(shift_all_of_many_type_transformer, shift_all_of_many_type_validator, shift_all_of_many_type_setter, shift_all_of_many_type_repr, shift_all_of_many_type_serializer)
all_of_pair_shift_type = ShiftType(shift_all_of_pair_type_transformer, shift_all_of_pair_type_validator, shift_all_of_pair_type_setter, shift_all_of_pair_type_repr, shift_all_of_pair_type_serializer)
shift_callable_shift_type = ShiftType(shift_callable_type_transformer, shift_callable_type_validator, shift_callable_type_setter, shift_callable_type_repr, shift_callable_type_serializer)
forward_ref_shift_type = ShiftType(shift_forward_ref_type_transformer, shift_forward_ref_type_validator, shift_forward_ref_type_setter, shift_forward_ref_type_repr, shift_forward_ref_type_serializer)
shift_shift_type = ShiftType(shift_shift_type_transformer, shift_shift_type_validator, shift_shift_type_setter, shift_shift_type_repr, shift_shift_type_serializer)
shift_field_shift_type = ShiftType(shift_shift_field_type_transformer, shift_shift_field_type_validator, shift_shift_field_type_setter, shift_shift_field_type_repr, shift_shift_field_type_serializer)

_shift_builtin_types: dict[Type, ShiftType] = {
    Missing: missing_shift_type,

    int: base_shift_type,
    bool: base_shift_type,
    float: base_shift_type,
    str: base_shift_type,
    bytes: base_shift_type,
    bytearray: base_shift_type,

    type(None): none_shift_type,

    Any: any_shift_type,

    list: all_of_single_shift_type,
    set: all_of_single_shift_type,
    frozenset: all_of_single_shift_type,

    tuple: all_of_many_shift_type,

    Callable: shift_callable_shift_type,

    dict: all_of_pair_shift_type,

    Union: one_of_shift_type,
    Optional: one_of_shift_type,

    Literal: one_of_val_shift_type,

    ShiftModel: shift_shift_type,

    ForwardRef: forward_ref_shift_type,

    ShiftField: shift_field_shift_type
}

def serialize(instance: Any, throw: bool = True) -> dict[str, Any] | None:
    """Try to call instance.serialize() if the instance has the attribute, else it conditionally throws an error"""
    if not hasattr(instance, "serialize") or not callable(instance.serialize):
        if throw:
            raise ShiftFieldError(instance.__class__.__name__, f".serialize() does not exist on the given instance, but serialize was called")
        return None
    return instance.serialize() # noqa

def reset_starshift_globals() -> None:
    """Reset all global registers and values"""
    _shift_types.clear()
    _shift_types.update(_shift_builtin_types)
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

def resolve_forward_ref(typ: str | ForwardRef, info: ShiftInfo) -> Type:
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
    raise ShiftFieldError(info.model_name, f"Could not resolve forward reference: {typ}")

# Setup starshift
reset_starshift_globals()



# endregion