# Core
########################################################################################################################



class Shift:
    """Base class for validated models"""

    # Class options (set as class variables)
    __coerce__: ClassVar[bool] = False  # Enable automatic type coercion
    __strict__: ClassVar[bool] = True  # Fail on unknown fields
    __frozen__: ClassVar[bool] = False  # Make instances immutable

    # Hooks (override in subclass)
    def __pre_init__(self, values: dict[str, Any]) -> None
        """Called before attributes are set. Modify values dict as needed."""

    def __post_init__(self) -> None
        """Called after attributes are set."""

    def __pre_init_advanced__(self, ctx: ProcessingContext) -> None
        """Advanced pre-init with full context access."""

    def __post_init_advanced__(self, ctx: ProcessingContext) -> None
        """Advanced post-init with full context access."""

    # Instance methods
    def to_dict(self) -> dict[str, Any]
        def to_json(self, **kwargs) -> str

            def copy(self, **overrides) -> Self

            def validate(self) -> bool  # Re-validate current values, raises on failure

    # Class methods
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self
        @classmethod
        def from_json(cls, s: str) -> Self


def field(
        default=MISSING,
        *,
        # Default
        default_factory: Callable[[], T] | None = None,

        # Transformation (runs before validation)
        transform: Callable[[Any], T] | None = None,

        # Validation
        check: Callable[[T], bool] | None = None,
        ge: float | None = None,  # >= value
        le: float | None = None,  # <= value
        gt: float | None = None,  # > value
        lt: float | None = None,  # < value
        min_length: int | None = None,  # len(x) >= value
        max_length: int | None = None,  # len(x) <= value
        pattern: str | None = None,  # regex match

        # Serialization
        serialize: Callable[[T], Any] | None = None,
        serialize_as: str | None = None,  # Rename field in output
        exclude: bool = False,  # Exclude from to_dict()

        # Repr
        repr: Callable[[T], str] | None = None,
        repr_exclude: bool = False,  # Exclude from __repr__()
) -> T


MISSING  # Sentinel for missing values



# Errors
########################################################################################################################



class ValidationError(Exception):
    """Raised when validation fails"""
    model: str
    errors: list[FieldError]


class FieldError:
    """Single field validation error"""
    field: str
    message: str
    value: Any  # MISSING if not captured



# Type Extensibility
########################################################################################################################



class TypeHandler:
    """Custom type handling for transform/validate/serialize/repr"""
    match: Callable[[Any], bool]  # Returns True if this handler handles the type
    transform: Callable[[Any, Any, TypeContext], Any] | None  # (value, hint, ctx) -> transformed
    validate: Callable[[Any, Any, TypeContext], bool] | None  # (value, hint, ctx) -> is_valid
    serialize: Callable[[Any, Any, TypeContext], Any] | None  # (value, hint, ctx) -> serialized
    repr: Callable[[Any, Any, TypeContext], str] | None  # (value, hint, ctx) -> repr_string


class TypeContext:
    """Context passed to type handler functions"""
    coerce: bool  # Whether coercion is enabled
    field_name: str  # Name of the field being processed
    model_name: str  # Name of the model class


def register_type_handler(handler: TypeHandler, priority: bool = False) -> None
    """Register a custom type handler. If priority=True, check first."""


def deregister_type_handler(handler: TypeHandler) -> None
    """Remove a type handler."""


def get_type_handler(hint: Any) -> TypeHandler | None
    """Find handler that matches a type hint."""


def clear_type_handlers() -> None
    """Clear all custom handlers, restore builtins."""



# Forward References
########################################################################################################################



def resolve_forward_ref(ref: str | ForwardRef, context_cls: type) -> type
    """Resolve a forward reference to its actual type."""


def register_forward_ref(name: str, cls: type) -> None
    """Manually register a forward reference mapping."""


def clear_forward_refs() -> None
    """Clear the forward reference cache."""



# Schemas
########################################################################################################################



class Schema:
    """Cached class metadata"""
    name: str
    cls: type
    fields: tuple[FieldInfo, ...]
    field_map: dict[str, FieldInfo]
    has_pre_init: bool
    has_post_init: bool
    has_pre_init_advanced: bool
    has_post_init_advanced: bool


class FieldInfo:
    """Resolved field information"""
    name: str
    type_hint: Any  # Original type hint
    resolved_hint: Any  # With forward refs resolved
    field_config: Field  # The field() configuration
    required: bool  # True if no default
    type_handler: TypeHandler | None
    serialize_name: str  # Property: name used in serialization


def get_schema(cls: type) -> Schema
    """Get or build schema for a Shift class."""


def clear_schema(cls: type | None = None) -> None
    """Clear schema cache. If cls=None, clear all."""



# Advanced Hooks
########################################################################################################################



class ProcessingContext:
    """Full context for advanced pre/post init hooks"""
    instance: Shift
    schema: Schema
    values: dict[str, Any]
    errors: list[FieldError]
    coerce: bool
    strict: bool

    def add_error(self, field: str, message: str, value: Any = MISSING) -> None
        def get_field_info(self, name: str) -> FieldInfo | None



# Utilities
########################################################################################################################



def is_shift(obj: Any) -> bool
    """Check if an object is a Shift instance."""


def is_shift_class(cls: Any) -> bool
    """Check if a class is a Shift subclass."""


def fields(cls: type) -> tuple[FieldInfo, ...]
    """Get field information for a Shift class."""


def validate_data(cls: type, data: dict[str, Any]) -> list[FieldError]
    """Validate data without instantiating. Returns errors (empty if valid)."""


def reset() -> None
    """Reset all caches and registries."""