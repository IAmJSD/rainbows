"""
This file is dedicated to the built-in Python types and the converters for them.
We try and validate in a "type-like" way. We need to be careful here because we do
not want to cause a situation where garbage is allowed in, but at the same time, we
do want to allow items that are very likely to be correct and then make minor changes
to them (for example "true" instead of true or "1" for a int).

We do not, however, make a best guess when the best guess has the risk of corrupting data.
We aren't trying to force something to be something, we just are trying to not be pedantic
over small validation issues.
"""
import datetime
import typing
from .exceptions import ValidationError

# Defines the built-in validator types.
_BUILT_IN_VALIDATOR_TYPE = typing.Callable[[str, typing.Any], typing.Any]
BUILT_IN_VALIDATORS: typing.Dict[typing.Any, _BUILT_IN_VALIDATOR_TYPE] = {}


def _validator(_type):
    def deco(fn: _BUILT_IN_VALIDATOR_TYPE):
        BUILT_IN_VALIDATORS[_type] = fn
    return deco


@_validator(bool)
def _validate_bool(key: str, x: typing.Any) -> bool:
    if isinstance(x, bool):
        return x

    if isinstance(x, str):
        l = key.lower()
        if l in ["yes", "true", "y", "t"]:
            return True
        if l in ["no", "false", "n", "f"]:
            return False

    raise ValidationError(f"The value of key {key} is of type {type(x)}, expected bool compatible", key)


@_validator(str)
def _validate_str(key: str, x: typing.Any) -> str:
    if isinstance(x, str):
        return x

    if isinstance(x, bool):
        return "true" if x else "false"

    if isinstance(x, (int, float)):
        return str(x)

    raise ValidationError(f"The value of key {key} is of type {type(x)}, expected str compatible", key)


@_validator(int)
def _validate_int(key: str, x: typing.Any) -> int:
    if isinstance(x, int):
        return x

    if isinstance(x, str):
        try:
            return int(x)
        except ValueError:
            pass

    raise ValidationError(f"The value of key {key} is of type {type(x)}, expected int compatible", key)


@_validator(float)
def _validate_float(key: str, x: typing.Any) -> float:
    if isinstance(x, float):
        return x

    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            pass

    raise ValidationError(f"The value of key {key} is of type {type(x)}, expected float compatible", key)


@_validator(datetime.datetime)
def _validate_datetime(key: str, x: typing.Any) -> datetime.datetime:
    if isinstance(x, datetime.datetime):
        return x

    if isinstance(x, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(x)
        except:
            pass

    elif isinstance(x, str):
        try:
            return datetime.datetime.fromtimestamp(int(x))
        except ValueError:
            return datetime.datetime.fromisoformat(x)

    raise ValidationError(f"The value of key {key} is of type {type(x)}, expected datetime compatible", key)
