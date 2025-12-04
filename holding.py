def _validate_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: Any, annotations: Any, validators: Any, setters: Any) -> None:
    _log_verbose(shift_config.verbosity, ["Validating fields"])

    """
    Validation flow:
        for field, typ in annotations
            if field in data
                if validator use
                if validator or _validate()
                    if setter use
                    else set
            elif default in fields
                if validator use
                if validator or _validate()
                    if setter use
                    else set
    """

    # Check each data.val against annotations.typ
    for field, typ in annotations.items():
        # If field in data, attempt validation
        if field in data:
            # Get val from data
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



def _validate_un_annotated(self: Any, shift_config: ShiftConfig, model_name: str, data: Any, annotations: Any, validators: Any, setters: Any) -> None:
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
                        raise TypeError(
                            f"`{model_name}`: `{self.__fields__.get(field)}` is not a valid type for `{field}`")

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