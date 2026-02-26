import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from abc import ABC, abstractmethod



InvalidType = object()

@pytest.fixture(autouse=True)
def reset_starshift():
    reset_starshift_globals()
    yield
    reset_starshift_globals()



def test_changing_vals():
    class Test(Shift):
        val: int

    test = Test(val=42)
    assert test.val == 42
    test = Test(val=81)
    assert test.val == 81

def test_static_vals():
    class Test(Shift):
        val: int

    test_1 = Test(val=42)
    assert test_1.val == 42
    test_2 = Test(val=81)
    assert test_1.val == 42
    assert test_2.val == 81

def test_shift_has_methods():
    class Test(Shift):
        val: int

    test = Test(val=42)
    assert hasattr(test, "__init__")
    assert hasattr(test, "transform")
    assert hasattr(test, "validate")
    assert hasattr(test, "set")
    assert hasattr(test, "__repr__")
    assert hasattr(test, "serialize")
    assert hasattr(test, "__eq__")
    assert hasattr(test, "__ne__")
    assert hasattr(test, "__hash__")
    assert hasattr(test, "__copy__")

# We don't need to test __init__ because those are validated when everything else works

# We don't need to test transform() because it's only relevant in validate(), which is already tested

def test_shift_validate():
    class Test(Shift):
        val: int = 42

    test = Test()
    with pytest.raises(ShiftModelError):
        test.validate(**{"val": InvalidType})
    assert test.val == 42

def test_shift_set():
    class Test(Shift):
        val: int = 42

    test = Test()
    test.set(val=81)
    assert test.val == 81

def test_shift_repr():
    class Test(Shift):
        val: int = 42

    test = Test(val=81)
    assert repr(test) == "Test(val=81)"
    test = Test()
    assert repr(test) == "Test()"

def test_shift_serialize():
    class Test(Shift):
        val: int = 42

    test = Test(val=81)
    assert test.serialize() == {"val": 81}
    test = Test()
    assert test.serialize() == {}

def test_pre_init():
    class Test(Shift):
        val: int = 42

        def __pre_init__(self, info: ShiftInfo):
            info.data["val"] = 81
            info.fields = get_updated_fields(self, info.fields, info.data, info.shift_config)

    test = Test()
    assert test.val == 81

    class Test(Shift):
        val: int = 42

        def __pre_init__(self):
            pass # There's no way to test, other than making sure this doesn't throw

    test = Test()
    assert test.val == 42

def test_post_init():
    class Test(Shift):
        val: int = 42

        def __post_init__(self, info: ShiftInfo):
            self.val = 81

    test = Test()
    assert test.val == 81

    class Test(Shift):
        val: int = 42

        def __post_init__(self):
            self.val = 81

    test = Test()
    assert test.val == 81

def test_override_shift_methods():
    class Test(Shift):
        val: int

        def __eq__(self, other):
            return self.val != other.val

    test_1 = Test(val=42)
    test_2 = Test(val=81)
    assert test_1 == test_2

def test_new_shift_method():
    class Test(Shift):
        val: int

        def __str__(self):
            return str(self.val)

    test = Test(val=42)
    assert str(test) == "42"

def test_abstract_base_class():
    class Device(Shift, ABC):
        type: str

        @abstractmethod
        def __post_init__(self, info) -> None:
            pass

        @abstractmethod
        def get(self) -> Any:
            pass

    class _EPICSDevice(Device):
        type: str = ShiftField(eq='EPICS')
        var: str = ShiftField(min_len=0, max_len=64)
        _pv: Any = None

        def __post_init__(self, info) -> None:
            try:
                _ = self.get()
            except Exception as e:
                raise ValueError(f"ProcessVar: could not read {self.var} : {e}")

        def get(self) -> Any:
            return self._pv is None

    class _IPDevice(Device):
        type: str = ShiftField(eq='IP')
        ip: str = ShiftField(
            pattern=r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        port: int = ShiftField(default=None, ge=0, le=65535, default_skips=True)

        def __post_init__(self, info) -> None:
            try:
                _ = self.get()
            except Exception as e:
                if self.port is None:
                    raise ValueError(f"IPDevice: could not read {self.ip} : {e}")
                else:
                    raise ValueError(f"IPDevice: could not read {self.ip}:{self.port} : {e}")

        def get(self) -> Any:
            return self.port is None

    _device_registry = {
        'EPICS': _EPICSDevice,
        'IP': _IPDevice,
    }

    def build_device(**data):
        t = data.get('type')
        if t not in _device_registry:
            raise ValueError(f"Unknown device type: {t}")
        return _device_registry[t](**data)



    valid = {
        'devices': [
            {
                'type': 'EPICS',
                'var': 'AUTO_ALARM:SCALE'
            },
            {
                'type': 'IP',
                'ip': '192.168.1.253',
                'port': 8080
            }
        ]
    }
    devices: list[Device] = []
    for device in valid['devices']:
        devices.append(build_device(**device))
    for device in devices:
        assert isinstance(device, Device)