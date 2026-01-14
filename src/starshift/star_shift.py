# Imports
########################################################################################################################



# Make all type hints str
from __future__ import annotations

# Import type hints
from typing import (
    Any, Callable, ClassVar, Generic, TypeVar, Union, Literal, ForwardRef, Protocol,
    get_origin, get_args, get_type_hints,
    runtime_checkable
)

# Dataclasses for ShiftTypes
from dataclasses import dataclass
from types import MappingProxyType

# Used to manage types, functions, and forward refs
import inspect
import sys

# Used to validate regex
import re



# Globals
########################################################################################################################

# Generic type for templatized classes and functions
T = TypeVar('T')

class Missing:
    """Sentinel class for non-set values"""
    def __repr__(self) -> str:
        return 'Missing'
    def __bool__(self) -> bool:
        return False
MISSING = Missing()

# Cache for resolved forward references
_forward_ref_cache: dict[str, type] = {}

# Type handler registry
_type_handlers: list[TypeHandler] = []



# Types
########################################################################################################################



## Errors
############################################################

class ShiftError(Exception):
    """Raised when validation fails

    Attributes:
        model (str): The model name which failed validation
        errors (list[_ShiftFieldError]): The per-field errors
    """
    model: str
    errors: list[_ShiftFieldError]

@dataclass(slots=True, frozen=True)
class _ShiftFieldError:
    """Container to hold field errors

    Attributes:
        field (str): The field name that encountered an error
        msg (str): The error message
        val (Any): The value that caused the error (when applicable); Default: MISSING
    """
    field: str
    msg: str
    val: Any = MISSING



## Fields
############################################################

@dataclass(slots=True, frozen=True)
class _ShiftFieldConfig(Generic[T]):
    """Field configuration with transformation, validation, and serialization

    Attributes:

    """

    # Defaults
    default: T | Missing = MISSING
    default_factory: Callable[[], T] | None = None

    # Transform
    transform: Callable[[Any], T] | None = None

    # Validation
    check: Callable[[T], bool] | None = None
    ge: float | None = None,
    le: float | None = None,
    gt: float | None = None,
    lt: float | None = None,
    min_len: int | None = None,
    max_len: int | None = None,
    pattern: str | None = None,

    # Repr
    repr: Callable[[T], str] | None = None,
    repr_as: str | None = None,
    repr_exclude: bool = False,

    # Serialize
    serializer: Callable[[T], Any] | None = None,
    serialize_as: str | None = None,
    serializer_exclude: bool = False,



    def get_default(self) -> T:
        """Get the default value, calling factory if needed"""
        if self.default is not MISSING:
            return self.default
        elif self.default_factory is not None:
            return self.default_factory()
        raise ValueError('Default value was requested, but no default or factory was provided')

    def has_default(self) -> bool:
        """Returns whether the field has a default value"""
        return self.default is not MISSING or self.default_factory is not None

    def validate_constraints(self, val: Any) -> list[str]:
        """"Check the value against the constraints when set"""
        errors = []

        # Simple checks
        if self.ge is not None:
            try:
                if val < self.ge:
                    errors.append(f"Must be >= {self.ge}")
            except (TypeError, NotImplementedError):
                errors.append(f"ge was set, but val could not be compared to ge")
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
        if self.lt is not None:
            try:
                if val <= self.lt:
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

        return errors

def field(
    # Default
    default=MISSING, # Default value from def
    *,
    default_factory: Callable[[], T] | None = None, # Custom default instantiation

    # Transform
    transform: Callable[[Any], T] | None = None, # Custom transform logic

    # Validation
    check: Callable[[T], bool] | None = None, # Custom validation logic
    ge: float | None = None, # >= val
    le: float | None = None, # <= val
    gt: float | None = None, # > val
    lt: float | None = None, # < val
    min_len: int | None = None, # len(val) >= x
    max_len: int | None = None, # len(val) <= x
    pattern: str | None = None, # regex match

    # Repr
    repr: Callable[[T], str] | None = None, # Custom repr logic
    repr_as: str | None = None, # Rename field in repr output
    repr_exclude: bool = False, # Exclude from repr

    # Serialization
    serializer: Callable[[T], Any] | None = None, # Custom serialize logic
    serialize_as: str | None = None, # Rename field in serialization output
    serialize_exclude: bool = False, # Exclude in serialize
) -> T:
    """Creates a field configuration"""
    return _ShiftFieldConfig(
        default=default,
        default_factory=default_factory,
        transform=transform,
        check=check,
        ge=ge,
        le=le,
        gt=gt,
        lt=lt,
        min_len=min_len,
        max_len=max_len,
        pattern=pattern,
        repr=repr,
        repr_as=repr_as,
        repr_exclude=repr_exclude,
        serializer=serializer,
        serialize_as=serialize_as,
        serializer_exclude=serialize_exclude
    )

@dataclass(slots=True)
class ShiftFieldInfo:
    """Resolved field information (cached per class)

    Attributes
        name (str): field name
        field_config (Field): field configuration
        type_hint (Any): field type hint; Default MISSING
        resolved_hint (Any): resolved type hint for forward refs; Default MISSING
        required (bool): whether to require this field be set; Default True
        type_handler (TypeHandler | None): field's type handler; Default None
    """
    name: str
    field_config: _ShiftFieldConfig
    type_hint: Any = MISSING
    resolved_hint: Any = MISSING
    required: bool = True
    type_handler: TypeHandler | None = None

    @property
    def repr_name(self) -> str:
        return self.field_config.repr_as or self.name
    @property
    def serialized_name(self) -> str:
        return self.field_config.serialize_as or self.name



## Class
############################################################

class ShiftSchema:
    """Cached metadata for a Shift class"""
    __slots__ = (
        "name", "cls", "fields", "field_map",
        "has_pre_init", "has_post_init",
        "has_pre_init_advanced", "has_post_init_advanced",
    )

    name: str
    cls: type
    fields: tuple[ShiftFieldInfo, ...]
    field_map: MappingProxyType[str, ShiftFieldInfo]
    has_pre_init: bool
    has_pre_init_advanced: bool
    has_post_init: bool
    has_post_init_advanced: bool



    def __init__(self, cls: type):
        self.name = cls.__name__
        self.cls = cls

        self.has_pre_init = '__pre_init__' in cls.__dict__
        self.has_pre_init_advanced = '__pre_init_advanced__' in cls.__dict__
        self.has_post_init = '__post_init__' in cls.__dict__
        self.has_post_init_advanced = '__post_init_advanced__' in cls.__dict__

        fields = []
        # Get type hints
        try:
            hints = get_type_hints(cls)
        except NameError:
            # Forward refs weren't resolved, use raw
            hints = getattr(cls, '__annotations__', {}).copy()
        for name, hint in hints.items():
            # Skip private and dunder
            if name.startswith('_'):
                continue

            # Get field config
            class_val = getattr(cls, name, MISSING)
            if isinstance(class_val, _ShiftFieldConfig):
                field_config = class_val
            elif class_val is not MISSING:
                field_config = _ShiftFieldConfig(default=class_val)
            else:
                field_config = _ShiftFieldConfig()

            # Resolve forward refs
            resolved_hint = _resolve_hint(hint, cls)
            # Get type handler
            type_handler = _get_type_handler(resolved_hint)

            fields.append(ShiftFieldInfo(
                name=name,
                field_config=field_config,
                type_hint=hint,
                resolved_hint=resolved_hint,
                required=not field_config.has_default(),
                type_handler=type_handler,
            ))
        self.fields = tuple(fields)
        self.field_map = MappingProxyType({f.name: f for f in fields})



# Functions
########################################################################################################################



## Utilities
############################################################

def _resolve_hint(hint: Any, context_cls: type) -> Any:
    """Recursively resolve forward references in a type hint"""
    # Handle ForwardRef
    if isinstance(hint, ForwardRef):
        return resolve_forward_ref(hint, context_cls)

    # Handle string annotations
    if isinstance(hint, str):
        return resolve_forward_ref(hint, context_cls)

    # Handle generic types
    origin = get_origin(hint)
    if origin is not None:
        args = get_args(hint)
        resolved_args = tuple(_resolve_hint(arg, context_cls) for arg in args)

        # Reconstruct the generic type
        if resolved_args:
            try:
                return origin[resolved_args]
            except TypeError:
                # Some origins don't support subscripting
                return hint

    return hint

def resolve_forward_ref(ref: str | ForwardRef, context_cls: type) -> type:
    """
    Resolve a forward reference to its actual type.

    Resolution order:
    1. Check cache
    2. Check if it's the current class name (self-reference)
    3. Check the module where context_cls is defined
    4. Check registered Shift classes
    5. Check builtins
    """
    # Normalize to string
    if isinstance(ref, ForwardRef):
        ref_str = ref.__forward_arg__
    else:
        ref_str = ref

    # Check cache
    if ref_str in _forward_ref_cache:
        return _forward_ref_cache[ref_str]

    # Self-reference
    if ref_str == context_cls.__name__:
        _forward_ref_cache[ref_str] = context_cls
        return context_cls

    # Check module where class is defined
    module = sys.modules.get(context_cls.__module__)
    if module and hasattr(module, ref_str):
        resolved = getattr(module, ref_str)
        _forward_ref_cache[ref_str] = resolved
        return resolved

    # Check registered Shift schemas (for cross-module refs)
    for cls in _schemas:
        if cls.__name__ == ref_str:
            _forward_ref_cache[ref_str] = cls
            return cls

    # Check builtins
    import builtins
    if hasattr(builtins, ref_str):
        resolved = getattr(builtins, ref_str)
        _forward_ref_cache[ref_str] = resolved
        return resolved

    raise TypeError(f"Cannot resolve forward reference: {ref_str!r}")


def get_schema(cls: type) -> ShiftSchema:
    """Get or create schema for a class"""
    if cls not in _schemas:
        _schemas[cls] = Schema(cls)
    return _schemas[cls]


def clear_schema(cls: type | None = None) -> None:
    """Clear schema cache (all or specific class)"""
    if cls is None:
        _schemas.clear()
    else:
        _schemas.pop(cls, None)