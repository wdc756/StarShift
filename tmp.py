"""
StarShift - Better Dataclasses (Revised)

Goals:
1. Feels like native Python
2. Simple cases stay simple (field constraints)
3. Complex cases are possible (custom type handlers, per-field overrides)
4. Zero dependencies
"""

from __future__ import annotations
from typing import (
    Any, Callable, ClassVar, Generic, TypeVar, Union, Literal,
    get_origin, get_args, get_type_hints, ForwardRef, Protocol,
    runtime_checkable,
)
from dataclasses import dataclass
import inspect
import sys
import json

T = TypeVar("T")


# ============================================================
# PART 1: Sentinels and Core Types
# ============================================================

class _MissingType:
    """Sentinel for missing values"""
    __slots__ = ()

    def __repr__(self) -> str: return "MISSING"

    def __bool__(self) -> bool: return False

    def __copy__(self) -> _MissingType: return self

    def __deepcopy__(self, memo: dict) -> _MissingType: return self


MISSING: Any = _MissingType()


# ============================================================
# PART 2: Type Handlers (Extensibility)
# ============================================================

@dataclass(slots=True)
class TypeHandler:
    """
    Handles transform/validate/serialize for a type category.

    Users can register custom handlers for their own types:

        handler = TypeHandler(
            match=lambda hint: hint is np.ndarray,
            transform=lambda v, h, ctx: np.asarray(v) if ctx.coerce else v,
            validate=lambda v, h, ctx: isinstance(v, np.ndarray),
            serialize=lambda v, h, ctx: v.tolist(),
        )
        register_type_handler(handler)
    """
    match: Callable[[Any], bool]
    transform: Callable[[Any, Any, "TypeContext"], Any] | None = None
    validate: Callable[[Any, Any, "TypeContext"], bool] | None = None
    serialize: Callable[[Any, Any, "TypeContext"], Any] | None = None
    repr: Callable[[Any, Any, "TypeContext"], str] | None = None


@dataclass(slots=True, frozen=True)
class TypeContext:
    """Context passed to type handler functions"""
    coerce: bool
    field_name: str
    model_name: str


# Type handler registry
_type_handlers: list[TypeHandler] = []


def register_type_handler(handler: TypeHandler, priority: bool = False) -> None:
    """
    Register a custom type handler.

    Args:
        handler: The TypeHandler to register
        priority: If True, insert at front (checked first)
    """
    if priority:
        _type_handlers.insert(0, handler)
    else:
        _type_handlers.append(handler)


def deregister_type_handler(handler: TypeHandler) -> None:
    """Remove a type handler"""
    _type_handlers.remove(handler)


def get_type_handler(hint: Any) -> TypeHandler | None:
    """Find a handler that matches this type hint"""
    for handler in _type_handlers:
        if handler.match(hint):
            return handler
    return None


def clear_type_handlers() -> None:
    """Clear all custom type handlers (keeps builtins)"""
    _type_handlers.clear()
    _register_builtin_handlers()


# ============================================================
# PART 3: Forward Reference Resolution
# ============================================================

# Cache for resolved forward references
_forward_ref_cache: dict[str, type] = {}


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


def register_forward_ref(name: str, cls: type) -> None:
    """Manually register a forward reference"""
    _forward_ref_cache[name] = cls


def clear_forward_refs() -> None:
    """Clear the forward reference cache"""
    _forward_ref_cache.clear()


# ============================================================
# PART 4: Field Definition
# ============================================================

@dataclass(slots=True)
class Field(Generic[T]):
    """
    Field configuration with validation, transformation, and serialization.

    Usage:
        class User(Shift):
            name: str
            age: int = field(default=0, ge=0)
            email: str = field(transform=str.lower, check=lambda x: "@" in x)
            password: str = field(repr=lambda v: "***", serialize=lambda v: hash(v))
    """
    # Defaults
    default: T | _MissingType = MISSING
    default_factory: Callable[[], T] | None = None

    # Transformation (runs before validation)
    transform: Callable[[Any], T] | None = None

    # Validation
    check: Callable[[T], bool] | None = None

    # Numeric constraints
    ge: float | None = None
    le: float | None = None
    gt: float | None = None
    lt: float | None = None

    # Length constraints (strings, collections)
    min_length: int | None = None
    max_length: int | None = None

    # String pattern
    pattern: str | None = None

    # Serialization
    serialize: Callable[[T], Any] | None = None
    serialize_as: str | None = None  # Rename in output
    exclude: bool = False

    # Repr
    repr: Callable[[T], str] | None = None
    repr_exclude: bool = False

    def get_default(self) -> T:
        """Get default value, calling factory if needed"""
        if self.default_factory is not None:
            return self.default_factory()
        if self.default is not MISSING:
            return self.default
        raise ValueError("No default value")

    def has_default(self) -> bool:
        return self.default is not MISSING or self.default_factory is not None

    def validate_constraints(self, value: Any) -> list[str]:
        """Check all constraints, return list of error messages"""
        errors = []

        # Numeric constraints
        if self.ge is not None:
            try:
                if value < self.ge:
                    errors.append(f"must be >= {self.ge}")
            except TypeError:
                pass

        if self.le is not None:
            try:
                if value > self.le:
                    errors.append(f"must be <= {self.le}")
            except TypeError:
                pass

        if self.gt is not None:
            try:
                if value <= self.gt:
                    errors.append(f"must be > {self.gt}")
            except TypeError:
                pass

        if self.lt is not None:
            try:
                if value >= self.lt:
                    errors.append(f"must be < {self.lt}")
            except TypeError:
                pass

        # Length constraints
        if self.min_length is not None:
            try:
                if len(value) < self.min_length:
                    errors.append(f"length must be >= {self.min_length}")
            except TypeError:
                pass

        if self.max_length is not None:
            try:
                if len(value) > self.max_length:
                    errors.append(f"length must be <= {self.max_length}")
            except TypeError:
                pass

        # Pattern constraint
        if self.pattern is not None:
            import re
            try:
                if not re.match(self.pattern, str(value)):
                    errors.append(f"must match pattern {self.pattern!r}")
            except (TypeError, re.error):
                pass

        # Custom check
        if self.check is not None:
            try:
                if not self.check(value):
                    errors.append("failed validation check")
            except Exception as e:
                errors.append(f"check raised {type(e).__name__}: {e}")

        return errors


def field(
        default: T | _MissingType = MISSING,
        *,
        default_factory: Callable[[], T] | None = None,
        transform: Callable[[Any], T] | None = None,
        check: Callable[[T], bool] | None = None,
        ge: float | None = None,
        le: float | None = None,
        gt: float | None = None,
        lt: float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        serialize: Callable[[T], Any] | None = None,
        serialize_as: str | None = None,
        exclude: bool = False,
        repr: Callable[[T], str] | None = None,
        repr_exclude: bool = False,
) -> Any:
    """Create a Field configuration"""
    return Field(
        default=default,
        default_factory=default_factory,
        transform=transform,
        check=check,
        ge=ge, le=le, gt=gt, lt=lt,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        serialize=serialize,
        serialize_as=serialize_as,
        exclude=exclude,
        repr=repr,
        repr_exclude=repr_exclude,
    )


# ============================================================
# PART 5: Errors
# ============================================================

@dataclass(slots=True)
class FieldError:
    """Single field validation error"""
    field: str
    message: str
    value: Any = MISSING

    def __str__(self) -> str:
        if self.value is MISSING:
            return f"{self.field}: {self.message}"

        val_repr = _safe_repr(self.value, max_length=50)
        return f"{self.field}: {self.message} (got {val_repr})"


def _safe_repr(value: Any, max_length: int = 50) -> str:
    """Safe repr with truncation"""
    try:
        r = builtins_repr(value)
        if len(r) > max_length:
            return r[:max_length - 3] + "..."
        return r
    except Exception:
        return f"<{type(value).__name__}>"


# Store reference to builtin repr before we potentially shadow it
builtins_repr = repr


class ValidationError(Exception):
    """Raised when validation fails"""

    def __init__(self, model: str, errors: list[FieldError]):
        self.model = model
        self.errors = errors
        super().__init__(self._format())

    def _format(self) -> str:
        if len(self.errors) == 1:
            return f"{self.model}: {self.errors[0]}"

        lines = [f"{self.model}: {len(self.errors)} validation error(s)"]
        for err in self.errors:
            lines.append(f"  {err}")
        return "\n".join(lines)


# ============================================================
# PART 6: Schema (Cached Class Metadata)
# ============================================================

@dataclass(slots=True)
class FieldInfo:
    """Resolved field information (cached per class)"""
    name: str
    type_hint: Any
    resolved_hint: Any  # Type hint with forward refs resolved
    field_config: Field
    required: bool
    type_handler: TypeHandler | None

    @property
    def serialize_name(self) -> str:
        return self.field_config.serialize_as or self.name


class Schema:
    """Cached metadata for a Shift class"""
    __slots__ = (
        "name", "cls", "fields", "field_map",
        "has_pre_init", "has_post_init",
        "has_pre_init_advanced", "has_post_init_advanced",
    )

    name: str
    cls: type
    fields: tuple[FieldInfo, ...]
    field_map: dict[str, FieldInfo]
    has_pre_init: bool
    has_post_init: bool
    has_pre_init_advanced: bool
    has_post_init_advanced: bool

    def __init__(self, cls: type):
        self.name = cls.__name__
        self.cls = cls

        # Check for hooks
        self.has_pre_init = "__pre_init__" in cls.__dict__
        self.has_post_init = "__post_init__" in cls.__dict__
        self.has_pre_init_advanced = "__pre_init_advanced__" in cls.__dict__
        self.has_post_init_advanced = "__post_init_advanced__" in cls.__dict__

        fields = []

        # Get type hints, handling forward refs gracefully
        try:
            hints = get_type_hints(cls)
        except NameError:
            # Forward refs couldn't be resolved, use raw annotations
            hints = getattr(cls, "__annotations__", {}).copy()

        for name, hint in hints.items():
            # Skip private and dunder
            if name.startswith("_"):
                continue

            # Get field config
            class_val = getattr(cls, name, MISSING)

            if isinstance(class_val, Field):
                field_config = class_val
            elif class_val is not MISSING:
                field_config = Field(default=class_val)
            else:
                field_config = Field()

            # Resolve forward references in type hint
            resolved_hint = _resolve_hint(hint, cls)

            # Find type handler
            type_handler = get_type_handler(resolved_hint)

            fields.append(FieldInfo(
                name=name,
                type_hint=hint,
                resolved_hint=resolved_hint,
                field_config=field_config,
                required=not field_config.has_default(),
                type_handler=type_handler,
            ))

        self.fields = tuple(fields)
        self.field_map = {f.name: f for f in fields}


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


# Schema cache
_schemas: dict[type, Schema] = {}


def get_schema(cls: type) -> Schema:
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


# ============================================================
# PART 7: Type Validation & Coercion
# ============================================================

def validate_type(
        value: Any,
        hint: Any,
        ctx: TypeContext,
) -> tuple[Any, bool]:
    """
    Validate and optionally coerce a value against a type hint.

    Returns:
        (possibly_transformed_value, is_valid)
    """
    # Check for custom handler first
    handler = get_type_handler(hint)
    if handler:
        # Transform
        if handler.transform and ctx.coerce:
            try:
                value = handler.transform(value, hint, ctx)
            except Exception:
                pass

        # Validate
        if handler.validate:
            return value, handler.validate(value, hint, ctx)

        # No validate means accept anything
        return value, True

    # Built-in handling follows...
    return _validate_builtin(value, hint, ctx)


def _validate_builtin(
        value: Any,
        hint: Any,
        ctx: TypeContext,
) -> tuple[Any, bool]:
    """Handle built-in types"""

    # None
    if hint is type(None):
        return value, value is None

    # Any
    if hint is Any:
        return value, True

    origin = get_origin(hint)
    args = get_args(hint)

    # Union / Optional
    if origin is Union:
        for arg in args:
            coerced, valid = validate_type(value, arg, ctx)
            if valid:
                return coerced, True
        return value, False

    # Literal
    if origin is Literal:
        return value, value in args

    # list[T]
    if origin is list:
        if not isinstance(value, list):
            if ctx.coerce:
                try:
                    value = list(value)
                except (TypeError, ValueError):
                    return value, False
            else:
                return value, False

        if not args:
            return value, True

        elem_type = args[0]
        result = []
        for item in value:
            coerced, valid = validate_type(item, elem_type, ctx)
            if not valid:
                return value, False
            result.append(coerced)
        return result, True

    # set[T] / frozenset[T]
    if origin in (set, frozenset):
        target = origin
        if not isinstance(value, (set, frozenset)):
            if ctx.coerce:
                try:
                    value = target(value)
                except (TypeError, ValueError):
                    return value, False
            else:
                return value, False

        if not args:
            return value, True

        elem_type = args[0]
        result = []
        for item in value:
            coerced, valid = validate_type(item, elem_type, ctx)
            if not valid:
                return value, False
            result.append(coerced)
        return target(result), True

    # dict[K, V]
    if origin is dict:
        if not isinstance(value, dict):
            return value, False

        if not args:
            return value, True

        key_type = args[0]
        val_type = args[1] if len(args) > 1 else Any
        result = {}
        for k, v in value.items():
            coerced_k, valid_k = validate_type(k, key_type, ctx)
            coerced_v, valid_v = validate_type(v, val_type, ctx)
            if not valid_k or not valid_v:
                return value, False
            result[coerced_k] = coerced_v
        return result, True

    # tuple[T, ...] or tuple[T1, T2, ...]
    if origin is tuple:
        if not isinstance(value, tuple):
            if ctx.coerce:
                try:
                    value = tuple(value)
                except (TypeError, ValueError):
                    return value, False
            else:
                return value, False

        if not args:
            return value, True

        # Homogeneous: tuple[int, ...]
        if len(args) == 2 and args[1] is Ellipsis:
            elem_type = args[0]
            result = []
            for item in value:
                coerced, valid = validate_type(item, elem_type, ctx)
                if not valid:
                    return value, False
                result.append(coerced)
            return tuple(result), True

        # Fixed length
        if len(value) != len(args):
            return value, False

        result = []
        for item, arg_type in zip(value, args):
            coerced, valid = validate_type(item, arg_type, ctx)
            if not valid:
                return value, False
            result.append(coerced)
        return tuple(result), True

    # Callable
    if origin is Callable or hint is Callable:
        return value, callable(value)

    # Check if it's a Shift subclass
    if isinstance(hint, type) and issubclass(hint, Shift):
        if isinstance(value, hint):
            return value, True
        if isinstance(value, dict):
            try:
                return hint(**value), True
            except ValidationError:
                return value, False
        return value, False

    # Base types
    if isinstance(hint, type):
        if isinstance(value, hint):
            return value, True
        if ctx.coerce:
            try:
                return _coerce_to_type(value, hint), True
            except (ValueError, TypeError):
                return value, False
        return value, False

    # Unknown type, be permissive
    return value, True


def _coerce_to_type(value: Any, target: type) -> Any:
    """Coerce value to target type"""
    if target is bool:
        if isinstance(value, str):
            lower = value.lower().strip()
            if lower in ("true", "1", "yes", "on"):
                return True
            if lower in ("false", "0", "no", "off", ""):
                return False
            raise ValueError(f"Cannot coerce {value!r} to bool")
        return bool(value)

    return target(value)


# ============================================================
# PART 8: Serialization Helpers
# ============================================================

def _serialize_value(value: Any, hint: Any, ctx: TypeContext) -> Any:
    """Recursively serialize a value"""
    # Check for custom handler
    handler = get_type_handler(hint)
    if handler and handler.serialize:
        return handler.serialize(value, hint, ctx)

    # Shift instances
    if isinstance(value, Shift):
        return value.to_dict()

    # Collections
    if isinstance(value, dict):
        return {k: _serialize_value(v, Any, ctx) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        result = [_serialize_value(item, Any, ctx) for item in value]
        # Convert to list for JSON compatibility
        return result

    return value


def _repr_value(value: Any, hint: Any, ctx: TypeContext) -> str:
    """Get repr for a value, respecting custom handlers"""
    # Check for custom handler
    handler = get_type_handler(hint)
    if handler and handler.repr:
        return handler.repr(value, hint, ctx)

    return builtins_repr(value)


# ============================================================
# PART 9: Processing Context (for advanced hooks)
# ============================================================

@dataclass
class ProcessingContext:
    """
    Full context for advanced pre/post init hooks.

    Provides access to everything about the current initialization.
    """
    instance: Shift
    schema: Schema
    values: dict[str, Any]
    errors: list[FieldError]
    coerce: bool
    strict: bool

    def add_error(self, field: str, message: str, value: Any = MISSING) -> None:
        """Add a validation error"""
        self.errors.append(FieldError(field, message, value))

    def get_field_info(self, name: str) -> FieldInfo | None:
        """Get field info by name"""
        return self.schema.field_map.get(name)


# ============================================================
# PART 10: The Shift Base Class
# ============================================================

class ShiftMeta(type):
    """Metaclass for Shift classes"""

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)

        # Skip base Shift class
        if name != "Shift" and any(isinstance(b, ShiftMeta) for b in bases):
            # Build schema early to catch definition errors
            get_schema(cls)

        return cls


class Shift(metaclass=ShiftMeta):
    """
    Base class for validated models.

    Usage:
        class User(Shift):
            name: str
            age: int = 0
            email: str = field(transform=str.lower, check=lambda x: "@" in x)

        user = User(name="Alice", age=30, email="ALICE@EXAMPLE.COM")

    Class options:
        __coerce__: bool = False  - Enable automatic type coercion
        __strict__: bool = True   - Fail on unknown fields
        __frozen__: bool = False  - Make instances immutable after init
    """

    __coerce__: ClassVar[bool] = False
    __strict__: ClassVar[bool] = True
    __frozen__: ClassVar[bool] = False

    def __init__(self, **data: Any) -> None:
        schema = get_schema(self.__class__)
        errors: list[FieldError] = []
        values: dict[str, Any] = {}
        coerce = self.__coerce__
        strict = self.__strict__

        # Check for unknown fields
        if strict:
            known = {f.name for f in schema.fields}
            for key in data:
                if key not in known:
                    errors.append(FieldError(key, "unknown field"))

        # Process each field
        for field_info in schema.fields:
            name = field_info.name
            hint = field_info.resolved_hint
            config = field_info.field_config

            # Get raw value
            if name in data:
                raw = data[name]
            elif config.has_default():
                raw = config.get_default()
            else:
                errors.append(FieldError(name, "required field missing"))
                continue

            # Field-level transform
            if config.transform is not None:
                try:
                    raw = config.transform(raw)
                except Exception as e:
                    errors.append(FieldError(name, f"transform failed: {e}", raw))
                    continue

            # Type validation (with handler transform if coercing)
            type_ctx = TypeContext(coerce=coerce, field_name=name, model_name=schema.name)
            coerced, valid = validate_type(raw, hint, type_ctx)

            if not valid:
                errors.append(FieldError(name, f"expected {_format_type(hint)}", raw))
                continue

            # Field constraint validation
            constraint_errors = config.validate_constraints(coerced)
            if constraint_errors:
                for msg in constraint_errors:
                    errors.append(FieldError(name, msg, coerced))
                continue

            values[name] = coerced

        # Raise if errors (before any hooks)
        if errors:
            raise ValidationError(schema.name, errors)

        # Pre-init hooks
        if schema.has_pre_init:
            self.__pre_init__(values)

        if schema.has_pre_init_advanced:
            ctx = ProcessingContext(
                instance=self,
                schema=schema,
                values=values,
                errors=errors,
                coerce=coerce,
                strict=strict,
            )
            self.__pre_init_advanced__(ctx)
            if ctx.errors:
                raise ValidationError(schema.name, ctx.errors)

        # Set attributes
        for name, value in values.items():
            object.__setattr__(self, name, value)

        # Post-init hooks
        if schema.has_post_init:
            self.__post_init__()

        if schema.has_post_init_advanced:
            ctx = ProcessingContext(
                instance=self,
                schema=schema,
                values=values,
                errors=[],
                coerce=coerce,
                strict=strict,
            )
            self.__post_init_advanced__(ctx)

    def __pre_init__(self, values: dict[str, Any]) -> None:
        """Called before attributes are set. Modify values dict as needed."""
        pass

    def __post_init__(self) -> None:
        """Called after attributes are set."""
        pass

    def __pre_init_advanced__(self, ctx: ProcessingContext) -> None:
        """Advanced pre-init with full context."""
        pass

    def __post_init_advanced__(self, ctx: ProcessingContext) -> None:
        """Advanced post-init with full context."""
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__frozen__:
            raise AttributeError(f"{self.__class__.__name__} is frozen")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if self.__frozen__:
            raise AttributeError(f"{self.__class__.__name__} is frozen")
        object.__delattr__(self, name)

    def __repr__(self) -> str:
        schema = get_schema(self.__class__)
        parts = []

        for field_info in schema.fields:
            config = field_info.field_config

            # Skip excluded fields
            if config.repr_exclude:
                continue

            value = getattr(self, field_info.name, MISSING)
            if value is MISSING:
                continue

            # Custom repr?
            if config.repr is not None:
                try:
                    val_repr = config.repr(value)
                except Exception:
                    val_repr = builtins_repr(value)
            else:
                # Check type handler
                type_ctx = TypeContext(
                    coerce=False,
                    field_name=field_info.name,
                    model_name=schema.name,
                )
                val_repr = _repr_value(value, field_info.resolved_hint, type_ctx)

            parts.append(f"{field_info.name}={val_repr}")

        return f"{schema.name}({', '.join(parts)})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(json.dumps(self.to_dict(), sort_keys=True, default=str))

    def __copy__(self) -> Shift:
        return self.__class__(**self.to_dict())

    def __deepcopy__(self, memo: dict) -> Shift:
        return self.__class__(**self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary"""
        schema = get_schema(self.__class__)
        result = {}

        for field_info in schema.fields:
            config = field_info.field_config

            if config.exclude:
                continue

            value = getattr(self, field_info.name, MISSING)
            if value is MISSING:
                continue

            # Custom serializer?
            if config.serialize is not None:
                try:
                    value = config.serialize(value)
                except Exception:
                    pass  # Fall through to default
            else:
                # Type handler serializer
                type_ctx = TypeContext(
                    coerce=False,
                    field_name=field_info.name,
                    model_name=schema.name,
                )
                value = _serialize_value(value, field_info.resolved_hint, type_ctx)

            key = field_info.serialize_name
            result[key] = value

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Shift:
        """Construct from dictionary"""
        return cls(**data)

    def to_json(self, **kwargs) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_json(cls, s: str) -> Shift:
        """Construct from JSON"""
        return cls(**json.loads(s))

    def copy(self, **overrides: Any) -> Shift:
        """Create copy with optional overrides"""
        data = self.to_dict()
        data.update(overrides)
        return self.__class__(**data)

    def validate(self) -> bool:
        """
        Re-validate current field values.

        Raises ValidationError if invalid.
        """
        schema = get_schema(self.__class__)
        errors: list[FieldError] = []

        for field_info in schema.fields:
            value = getattr(self, field_info.name, MISSING)

            if value is MISSING:
                if field_info.required:
                    errors.append(FieldError(field_info.name, "required field missing"))
                continue

            # Type validation
            type_ctx = TypeContext(
                coerce=False,
                field_name=field_info.name,
                model_name=schema.name,
            )
            _, valid = validate_type(value, field_info.resolved_hint, type_ctx)

            if not valid:
                errors.append(FieldError(
                    field_info.name,
                    f"expected {_format_type(field_info.resolved_hint)}",
                    value
                ))
                continue

            # Constraint validation
            constraint_errors = field_info.field_config.validate_constraints(value)
            for msg in constraint_errors:
                errors.append(FieldError(field_info.name, msg, value))

        if errors:
            raise ValidationError(schema.name, errors)

        return True


def _format_type(hint: Any) -> str:
    """Format a type hint for error messages"""
    if hint is type(None):
        return "None"
    if isinstance(hint, type):
        return hint.__name__
    return str(hint)


# ============================================================
# PART 11: Builtin Type Handlers
# ============================================================

def _register_builtin_handlers() -> None:
    """Register handlers for built-in types"""
    # Currently all built-in handling is in _validate_builtin
    # This function exists for extension patterns and future use
    pass


# Initialize on module load
_register_builtin_handlers()


# ============================================================
# PART 12: Utility Functions
# ============================================================

def is_shift(obj: Any) -> bool:
    """Check if an object is a Shift instance"""
    return isinstance(obj, Shift)


def is_shift_class(cls: Any) -> bool:
    """Check if a class is a Shift subclass"""
    return isinstance(cls, type) and issubclass(cls, Shift)


def fields(cls: type) -> tuple[FieldInfo, ...]:
    """Get field information for a Shift class"""
    return get_schema(cls).fields


def validate_data(cls: type, data: dict[str, Any]) -> list[FieldError]:
    """
    Validate data against a Shift class without instantiating.

    Returns list of errors (empty if valid).
    """
    try:
        cls(**data)
        return []
    except ValidationError as e:
        return e.errors


def reset() -> None:
    """Reset all caches and registries"""
    _schemas.clear()
    _forward_ref_cache.clear()
    _type_handlers.clear()
    _register_builtin_handlers()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Core
    "Shift",
    "field",
    "Field",
    "MISSING",

    # Errors
    "ValidationError",
    "FieldError",

    # Type extensibility
    "TypeHandler",
    "TypeContext",
    "register_type_handler",
    "deregister_type_handler",
    "get_type_handler",
    "clear_type_handlers",

    # Forward refs
    "resolve_forward_ref",
    "register_forward_ref",
    "clear_forward_refs",

    # Schema access
    "get_schema",
    "clear_schema",
    "FieldInfo",
    "Schema",

    # Advanced hooks
    "ProcessingContext",

    # Utilities
    "is_shift",
    "is_shift_class",
    "fields",
    "validate_data",
    "reset",
]