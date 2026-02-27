## How to read this API:

This API comprises multiple files split by use case and level of detail.
In this document you can expect to find a 1-2 sentence summary for all
elements of StarShift, a short example of its use case, and a link to 
an in depth guide when needed.



# StarShift API



## `ShiftModel`

The main class that pulls StarShift together. To use just make any class
inherit `ShiftModel` to automatically validate and provide repr and serialization.

```python
from starshift import ShiftModel


class Class(ShiftModel):
    val: int


# Works
_ = Class(val=42)

# Fails
_ = Class(val='Hello There!')
```

Full `ShiftModel` API: [here](https://github.com/wdc756/StarShift/blob/main/docs/api/Shift.md)



## `ShiftField`

The main class used for basic value checks. To use make a class that inherits 
`ShiftModel` and set a field equal to an instance of `ShiftField`.

```python
from starshift import ShiftModel, ShiftField


class Class(ShiftModel):
    val: int = ShiftField(ge=0)


# Works
_ = Class(val=42)

# Fails
_ = Class(val=-42)
```

Full `ShiftField` API [here](https://github.com/wdc756/StarShift/blob/main/docs/api/ShiftField.md)



## `ShiftFieldInfo` and `ShiftInfo`

### `ShiftFieldInfo`

A class used to hold intermediate data for a class attribute. Used in
internal function signatures and advanced mode decorators.

### `ShiftInfo`

A class used to hold intermediate data about a class instance being created.
Used in internal function signatures, advanced mode decorators, and in 
advanced pre/post init functions.

### Usage

```python
from starshift import ShiftModel, ShiftFieldInfo, ShiftInfo, shift_validator


class Class(ShiftModel):
    val1: int
    val2: int = 88

    @shift_validator('val1')
    def _validate_val1(self, field: ShiftFieldInfo, info: ShiftInfo):
        # Makes sure val1 is less than val2 when it exists
        return field.val < info.data.get('val2', field.val + 1)

    def __post_init__(self, info: ShiftInfo):
        # If no val2 provided, set it to val1 * 2
        if 'val2' not in info.data:
            self.val2 = self.val1 * 2
```

Full `ShiftFieldInfo` and `ShiftInfo` API [here](https://github.com/wdc756/StarShift/blob/main/docs/api/ShiftFieldInfo_ShiftInfo.md)



## `ShiftType`

A class used to hold processing logic defining how to manage a type. Used 
by internal functions.

```python
from starshift import ShiftModel, ShiftType, register_shift_type


def validate_int(instance, val) -> bool:
    return val % 2 == 0


int_shift_type = ShiftType(
    validator=validate_int
)
register_shift_type(int, int_shift_type)


class Class(ShiftModel):
    val: int


# This works
_ = Class(val=42)

# This doesn't because of the type-level validator
_ = Class(val=1)
```

Full `ShiftType` API [here](https://github.com/wdc756/StarShift/blob/main/docs/api/ShiftType.md)



## ShiftModel Functions

These are functions used during shift processes. All of these functions accept
`(instance: Any, field: ShiftFieldInfo, info: ShiftInfo)` arguments.

### Transformers

#### `shift_type_transformer`
A function that handles the default transformation behavior (if val is Missing
but default exists, `val = default`).

#### `shift_forward_ref_type_transformer`
A function that handles transformation for forward references by attempting 
resolution via cache, falling back to `resolve_forward_ref` when needed.

#### `shift_shift_field_type_transformer`
A function that handles transformation of `ShiftField`s.

### Validators

#### `shift_type_validator`
A function that handles the default validation behavior (if type is registered
`ShiftType` use it's validator, else perform a simple `isinstance` check).

#### `shift_missing_type_validator`
A function that handles validation for `Missing`s.

#### `shift_base_type_validator`
A function that handles validation for most simple (`int`, `str`) types
(by doing `isintance` checks).

#### `shift_any_type_validator`
A function that handles validation for `Any` types (validates everything).

#### `shift_one_of_val_type_validator`
A function that handles validation for any-of-val (`Literal`) types 
(if val is any arg-val).

#### `shift_one_of_type_validator`
A function that handles validation for one-of-arg (`Union`) types
(if val is any arg-type).

#### `shift_all_of_single_validator`
A function that handles validation for all vals are type (`list`) types
(if all vals are arg-type).

#### `shift_all_of_many_validator`
A function that handles validation for all vals are ordered type (`tuple`) types
(if all vals are arg - ordered).

#### `shift_all_of_pair_validator`
A function that handles validation for all val pairs match arg pairs (`dict`) types
(if all val-keys match arg-key and all val-val match arg-val).

#### `shift_callable_validator`
A function that handles validation for `Callable`s.

#### `shift_shift_type_validator`
A function that handles validation for `ShiftModel` types.

#### `shift_forward_ref_type_validator`
A function that handles validation for `ForwardRef`s.

#### `shift_shift_field_type_validator`
A function that handles validation for `ShiftField`s.

### Setters

#### `shift_type_setter`
A function that handles default set behavior (`instance.field = val`).

#### `shift_shift_field_type_setter`
A function that handles set logic for `ShiftField`s.

### Reprs

#### `shift_type_repr`
A function that handles the default representation behavior (`field=repr(val)`).

#### `shift_shift_field_type_repr`
A function that handles representation for `ShiftFields`s.

### Serializers

#### `shift_type_serializer`
A function that handles the default serialization behavior (if type is a
registered `ShiftType` call it's serializer, else `{field: val}`).

#### `shift_missing_type_serializer`
A function that handles serialization for `Missing`s.

#### `shift_base_type_serializer`
A function that handles serialization for most simple (`int`, `str`) types
(`{field: val}`).

#### `shift_all_of_serializer`
A function that handles serialization for all vals (`list`) types 
(`{field: [vals]}`).

#### `shift_all_of_pair_serializer`
A function that handles serialization for all val pairs (`dict`) types 
(`{field: {vals}}`).

#### `shift_shift_type_serializer`
A function that handles serialization for `ShiftModel`s.

#### `shift_forward_ref_type_serializer`
A function that handles serialization for `ForwardRef`s.

#### `shift_shift_field_type_serializer`
A function that handles serialization for `ShiftField`s.

### Usage

Say you define a custom class that needs to validate all it's values are the right 
type (`list`-like). Then you can create a `ShiftType` instance using the `all_of`
shift functions:

```python
from starshift import ShiftModel, ShiftFieldInfo, ShiftInfo, ShiftType
from starshift import shift_all_of_single_type_validator, shift_all_of_serializer
from starshift import register_shift_type
from typing import TypeVar, Generic

T = TypeVar('T')


class SimpleList(Generic[T]):
    def __init__(self, items=None):
        self._items = items if items is not None else []

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        return self._items[index]

    def __setitem__(self, index: int, value: T) -> None:
        self._items[index] = value

    def __iter__(self):
        return iter(self._items)


simple_list_shift_type = ShiftType(
    validator=shift_all_of_single_type_validator,
    serializer=shift_all_of_serializer
)
register_shift_type(SimpleList, simple_list_shift_type)


class Class(ShiftModel):
    val: SimpleList[int]


# This works
_ = Class(val=SimpleList([4, 5, 6, 1, 2, 3]))

# This fails because the hint is a int, not float
_ = Class(val=SimpleList([4, 5, 6.0]))
```



## Utilities

### `Missing`

A class that is used for sentinel values internally. (Allows StarShift to
distinguish between `None` and a value the user didn't set)

### `ShiftFieldError`

An exception class used for all internal errors, that accepts 
`(model_name: str, msg: str)`

### `log_verbose` 

A method that accepts `(verbosity: int, msgs: list[str])` and prints the most
verbose message the verbosity key will allow, where verbosity=0 prints nothing, 
and verbosity > len(msgs) will print the first message counting down.

### `get_shift_type`

A method that accepts `(type: Any)` and returns the corresponding `ShiftType`
if the type is registered.

### `get_shift_config`

A method that accepts `(cls: Any, fields: dict)` and returns the `ShiftConfig`
for that class, if one is set. Otherwise it will return `DEFAULT_SHIFT_CONFIG`.

### `get_field_decorators`

A method that accepts `(cls: Any, fields: dict)` and returns a `dict` following 
this structure:

```python
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
```

### `get_fields`

A method that accepts 
`(cls: Any, fields: dict, data: dict, shift_config: ShiftConfig = DEFAULT_SHIFT_CONFIG)`
and returns a list of `ShiftFieldInfo`s.

### `get_updated_fields`

A method that accepts
`(instance: Any, fields: list[ShiftFieldInfo], data: dict, shift_config: ShiftConfig = DEFAULT_SHIFT_CONFIG)`
and returns a list of `ShiftFieldInfo`s based on fields and using new values from data.

### `get_val_fields`

A method that accepts `(instance: Any, fields: list[ShiftFieldInfo])` and returns 
a list of `ShiftFieldInfo`s based on fields and updated with the current values of
instance.

### `get_shift_info`

A method that accepts `(cls: Any, instance: Any, data: dict)` and returns the updated
`ShiftInfo` from cache or constructs a new one.

### `resolve_forward_ref`

A method that accepts `(typ: str | ForwardRef, info: ShiftInfo)` and returns the 
resolved forward ref from cache or attempts to resolve the forward ref automatically.

### `serialize`

A method that accepts `(instance: Any, throw: bool = True)` and attempts to call
instance.serialize() if it exists, and if it doesn't and throws is true a `ShiftFieldError`
is raised.

### `reset_starshift_globals`

A method that accepts `()` and resets all shift registers and cache to their default
states.



## Registers

### `ShiftType` Registers

#### `get_shift_type_registry`
A function that returns a copy of the current shift type registry.

#### `register_shift_type`
A function that registers a `ShiftType` to a given type by adding it to the registry.

#### `deregister_shift_type`
A function that removes a `ShiftType`-type pair registry entry.

#### `clear_shift_types`
A function that removes all `ShiftType`-type pairs from the registry.

### `ForwardRef` Registers

#### `get_forward_ref_registry`
A function that returns a copy of the current forward ref registry.

#### `register_forward_ref`
A function that registers a `ForwardRef` to a given type by adding it to the registry.

#### `deregister_forward_ref`
A function that removes a `ForwardRef`-type pair registry entry.

#### `clear_forward_refs`
A function that removes all `ForwardRef`-type pairs from the registry.

### `ShiftInfo` Registers

#### `get_shift_info_registry`
A function that returns a copy of the current `ShiftInfo` registry.

#### `clear_shift_info_registry`
A function that removes all `ShiftInfo`-type pairs from the registry.

### ShiftModel Function Registers

#### `get_shift_function_registry`
A function that returns a copy of the current shift function registry.

#### `clear_shift_function_registry`
A function that removes all shift functions from the registry.

### ShiftModel Init Function Registers

#### `get_shift_init_function_registry`
A function that returns a copy of the current shift init function registry.

#### `clear_shift_init_function_registry`
A function that removes all shift init functions from the registry.