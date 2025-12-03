


class Shift:
    def __init_subclass__(cls):
        cls.__fields__ = getattr(cls, "__annotations__", {}).copy()

    def __init__(self, **data):
        model_name = self.__class__.__name__

        for field, typ in self.__fields__.items():
            if field not in data:
                raise TypeError(f"{model_name} missing field: {field}")
            val = data[field]
            if not isinstance(val, typ):
                raise TypeError(f"{model_name} invalid type for {field}")
            setattr(self, field, val)
