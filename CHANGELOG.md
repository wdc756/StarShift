# StarShift Changelog



## 0.4.x

### 0.6.7
- Added `defer_transform`, `defer_validation`, `defer_set`, `defer_repr`, & `defer_serialize` fields to `ShiftField`
- Added `shift_none_type_validator` and `shift_none_type_setter` to handle when type is `None` and val is missing
- Reworked internal transform and repr processes to work the same as validate and serialize

### 0.4.6
- Added defer key to ShiftField to make StarShift completely ignore fields
- Updated get_fields to respect ShiftField.defer

### 0.4.5
- Removed duplicate transform call
- Fixed private field behavior to ignore validation by default, but use shift functions

### 0.4.4
- Made simple and advanced pre/post init function signature checks
- Removed type checks in signature inspection for shift functions
- Made all builtin type shift functions public
- Renamed `shift_literal_type_validator` to `shift_one_of_val_type_validator`

### 0.4.3
- Made `default_skip` attribute in `ShiftField`
- Fixed bug with `ShiftField` mutation in `_get_updated_fields()`

### 0.4.2
- Made simple validation comparisons in `ShiftField` `Any` type

### 0.4.1
- Added `check` to `ShiftField` for another simple validation option that just passes the value instead of using the 
normal starshift validator signatures
- Added new tests for `check`
- Renamed `ShiftField`'s `validate_constaints` def to `validate`

### 0.4.0
- Renamed `ShiftField` to `ShiftFieldInfo`
- Introduced `ShiftField` class for simple checks
- Added single config option kwarg detection
- Changed repr and serialize functions to include the field name in return values



## 0.3.x

Beta versions, stable API, comprehensive unit tests, could be used



## 0.2.x

Alpha versions, stable API, semi-comprehensive unit tests, not recommended for use.



## 0.0.x - 0.1.x

Early development, unstable API, not recommended for use.
