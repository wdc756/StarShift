from dataclasses import dataclass
from typing import get_origin, get_args, Any, Union



@dataclass
class ShiftConfig:
    verbosity: int = 0
    allow_any: bool = True
    allow_defaults: bool = True
    allow_non_annotated: bool = True


DEFAULT_SHIFT_CONFIG = ShiftConfig(verbosity=0, allow_any=True, allow_defaults=True, allow_non_annotated=True)




def _validate_union_optional(typ: Any, val: Any, shift_config: ShiftConfig) -> bool:
    # If typ not a Union (Optional = Union[type, None]), invalidate
    if not get_origin(typ) is Union:
        return False

    # If val is any arg(assume arg is not empty), validate
    args = get_args(typ)
    for arg in args:
        if not _validate_value(arg, val, shift_config):
            return True

    # val is any typ, validate
    return False

def _validate_list(typ: Any, lis: Any, shift_config: ShiftConfig) -> bool:
    # If typ or lis are not a list, return false
    if not get_origin(typ) is list or not isinstance(lis, list):
        return False

    # If typ is un-annotated or lis is empty, validate
    args = get_args(typ)
    if not args or not lis:
        return True

    # If any li in lis is not an arg, return false
    for li in lis:
        if not _validate_value(args[0], li, shift_config):
            return False

    # All li in lis are typ, validate
    return True

def _validate_dict(typ: Any, dct: Any, shift_config: ShiftConfig) -> bool:
    # If typ or dct are not a dict, invalidate
    if not get_origin(typ) is dict or not isinstance(dct, dict):
        return False

    # If typ is un-annotated or dct is empty, validate
    args = get_args(typ)
    if not args or not dct:
        return True

    # If any key is not arg[0], invalidate
    for key in dct.keys():
        if not _validate_value(args[0], key, shift_config):
            return False

    # If args[1] is defined and any val in dct.values is not instance, invalidate
    if len(args) > 1:
        for key in dct.keys():
            if not _validate_value(args[1], dct.get(key), shift_config):
                return False

    # All key-val in dct match typ, validate
    return True

def _validate_value(typ: Any, val: Any, shift_config: ShiftConfig) -> bool:
    if shift_config.verbosity > 2:
        print(f"Attempting `{val}` validation against `{typ}`")

    # If complex type validates, return validation
    if shift_config.allow_any and typ is Any:
        return True
    elif _validate_union_optional(typ, val, shift_config):
        return True
    elif _validate_list(typ, val, shift_config):
        return True
    elif _validate_dict(typ, val, shift_config):
        return True

    # If no complex type validated but simple validation works, validate
    # Use try block here to gracefully handle invalid types
    try:
        if isinstance(val, typ):
            return True
    except TypeError:
        pass

    # If no type validated, invalidate
    return False



def shift_validator(field: str):
    def decorator(func):
        func.__validator_for__ = field
        return func
    return decorator

def shift_setter(field: str):
    def decorator(func):
        func.__validator_for__ = field
        return func
    return decorator



class Shift:
    def __init_subclass__(cls):
        cls.__fields__ = getattr(cls, "__dict__", {}).copy()

        # Find all validators and setters
        cls.__validators__ = {}
        cls.__setters__ = {}
        for name, value in cls.__dict__.items():
            # If value is callable test if it has a shift marker
            if callable(value):
                # If shift_validator, add to validators
                if hasattr(value, '__validator_for__'):
                    field = value.__validator_for__
                    cls.__validators__[field] = value
                    continue

                # If shift_setter, add to setters
                elif hasattr(value, '__setter_for__'):
                    field = value.__setter_for__
                    cls.__setters__[field] = value
                    continue

    def __init__(self, **data):
        # Get model name to print useful error messages
        model_name = self.__class__.__name__


        # Configure validation standards
        ################################


        # Get ShiftConfig (should always be `__shift_config__`) and check type
        shift_config = self.__fields__.get("__shift_config__")
        if shift_config and not isinstance(shift_config, ShiftConfig):
            raise TypeError(f"`{model_name}`: __shift_config__ must be a ShiftConfig instance")

        # If no shift config provided, use global default
        if shift_config and shift_config.verbosity > 0:
            print(f"__shift_config__ set")
        else:
            shift_config = DEFAULT_SHIFT_CONFIG

        if shift_config.verbosity > 2:
            print(f"__shift_config__: {shift_config}")

        # Get validators and setters
        validators = self.__validators__
        if shift_config.verbosity > 2:
            print(f"validators: {validators}")
        setters = self.__setters__
        if shift_config.verbosity > 2:
            print(f"setters: {setters}")


        # Validate annotated vars (type hints)
        ######################################


        if shift_config.verbosity > 0:
            print(f"Validating `{model_name}`")
            print("Validating fields")

        # Get annotation vars (dict[field, typ])
        annotations = getattr(self.__class__, "__annotations__", {})
        if shift_config.verbosity > 2:
            print(f"annotated fields: {annotations}")

        # Check each data.field against typ
        for field, typ in annotations.items():
            if shift_config.verbosity > 2:
                print(f"Attempting `{field}` validation against `{typ}`")

            # If field in data, attempt validation
            if field in data:
                # Get value from data
                val = data[field]

                # If custom validator, validate against it
                c_valid = False
                if field in validators:
                    if shift_config.verbosity > 2:
                        print(f"`{field}` is being validated by `{validators[field]}`")

                    c_valid = validators[field](self, val)

                # If valid, set
                if c_valid or _validate_value(typ, val, shift_config):
                    # If val validated, set field
                    if shift_config.verbosity > 2:
                        print(f"`{val}` validated as `{typ}`, setting field")
                    elif shift_config.verbosity > 1:
                        print(f"Validated `{field}`")

                    # If custom setter, use
                    if field in setters:
                        if shift_config.verbosity > 2:
                            print(f"`{field}` is being set by `{setters[field]}`")
                        setters[field](self, val)
                        continue

                    setattr(self, field, val)
                    continue

                # If val not validated, throw
                raise TypeError(f"`{model_name}`: `{val}` is not a valid type for `{field}`")

            if shift_config.verbosity > 2:
                print(f"`{field}` not in `**data`")

            # If no field in data but default exists, attempt validation
            # Default values for annotated items are found in the global fields
            default = self.__fields__.get(field)
            if shift_config.allow_defaults and default is not None:
                # If custom validator, validate against it
                c_valid = False
                if field in validators:
                    if shift_config.verbosity > 2:
                        print(f"`{field}` is being validated by `{validators[field]}`")

                    c_valid = validators[field](self, default)

                # If valid, set
                if c_valid or _validate_value(typ, default, shift_config):
                    # If default validated, set field
                    if shift_config.verbosity > 2:
                        print(f"`{default}` validated as `{typ}`, setting field")
                    elif shift_config.verbosity > 1:
                        print(f"Validated `{field}`")

                    # If custom setter, use
                    if field in setters:
                        if shift_config.verbosity > 2:
                            print(f"`{field}` is being set by `{setters[field]}`")
                        setters[field](self, default)
                        continue

                    setattr(self, field, default)
                    continue

                # If default not validated, throw
                raise TypeError(f"`{model_name}`: `{default}` is not a valid type for `{field}`")

            if shift_config.verbosity > 2:
                if shift_config.allow_defaults:
                    print(f"`default` for `{field}` not set")
                else:
                    print(f"Skipping `default` (if set) for `{field}`")

            # If val not in data and default does not exist, throw
            raise ValueError(f"`{model_name}`: missing `{field}` field and no default was set")


        # Validate non-annotated vars (no type hints)
        #############################################


        if shift_config.allow_non_annotated and shift_config.verbosity > 0:
            print("Setting non-annotated fields")

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

        if shift_config.verbosity > 2:
            print(f"non-annotated fields: {fields}")

        # Set fields (assume user/interpreter validation)
        if shift_config.allow_non_annotated:
            for field in fields.keys():

                # If data override, set with data
                if field in data:
                    # If custom validador, validate against it
                    if field in validators:
                        if shift_config.verbosity > 2:
                            print(f"`{field}` is being validated by `{validators[field]}`")

                        if not validators[field](self, data[field]):
                            raise TypeError(f"`{model_name}`: `{data[field]}` is not a valid type for `{field}`")

                    if shift_config.verbosity > 2:
                        print(f"Setting `{field}` to `data[field]`")
                    elif shift_config.verbosity > 1:
                        print(f"Setting `{field}`")

                    # If custom setter, use
                    if field in setters:
                        if shift_config.verbosity > 2:
                            print(f"`{field}` is being set by `{setters[field]}`")
                        setters[field](self, data[field])
                        continue

                    setattr(self, field, data[field])

                # If no data override, use default
                else:
                    # If custom validador, validate against it
                    if field in validators:
                        if shift_config.verbosity > 2:
                            print(f"`{field}` is being validated by `{validators[field]}`")

                        if not validators[field](self, self.__fields__.get(field)):
                            raise TypeError(f"`{model_name}`: `{self.__fields__.get(field)}` is not a valid type for `{field}`")

                    if shift_config.verbosity > 2:
                        print(f"Setting `{field}` to default")
                    elif shift_config.verbosity > 1:
                        print(f"Setting `{field}`")

                    # If custom setter, use
                    if field in setters:
                        if shift_config.verbosity > 2:
                            print(f"`{field}` is being set by `{setters[field]}`")
                        setters[field](self, self.__fields__.get(field))
                        continue

                    setattr(self, field, self.__fields__.get(field))

        elif fields.keys():
            raise ValueError(f"`{model_name}`: has un-annotated fields but `__shift_config__.allow_non_annotated` is False")


        # Misc
        ######


        if shift_config.verbosity > 0:
            print(f"Validated class `{model_name}`")

        # If cls has __post_init__(), call
        if "__post_init__" in self.__fields__:
            if shift_config.verbosity > 1:
                print(f"Calling __post_init__")

                self.__fields__["__post_init__"](self)

