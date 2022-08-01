import inspect
import typing
from .exceptions import ValidationError
from .builtin_validators import BUILT_IN_VALIDATORS
from rainbows.helpers import asyncify


VALIDATOR_CALLABLE = typing.Union[
    typing.Callable[[typing.Any, str], typing.Awaitable[typing.Any]],
    typing.Callable[[typing.Any], typing.Awaitable[typing.Any]],
    typing.Callable[[typing.Any, str], typing.Any],
    typing.Callable[[typing.Any], typing.Any]
]


def validates(key_name: typing.Union[str, typing.List[str], None] = None) -> typing.Callable[
    [VALIDATOR_CALLABLE], VALIDATOR_CALLABLE
]:
    """
    Used in models as a decorator to signify that a function is a validator.

    :param key_name: The keys this will affect. Can be a single string for one key, a list for many
                     keys, or None for all keys. Defaults to None.
    :return: The decorator to handle this specified above. This will go ahead and add an internal attribute
             to the function that will cause it to be called with self.add_validator. The (async) function
             should take either 1 parameter (value: any) or 2 parameters (value: any, key: str).
    """
    def deco(fn: VALIDATOR_CALLABLE) -> VALIDATOR_CALLABLE:
        fn._validates_keys = key_name
        return fn

    return deco


async def _validate_attr(type_: typing.Any, item: typing.Any, key: str) -> typing.Any:
    """Validates that an attribute matches the type specified."""
    typing_origin = typing.get_origin(type_)
    if typing_origin is None:
        # This isn't typing magic, this is a normal type.
        try:
            builtin_validator = BUILT_IN_VALIDATORS[type_]

            async def validator(value, key):
                return builtin_validator(key, value)
        except KeyError:
            # Check if there is a custom validator on the type.
            validator_attr = getattr(type_, "__validate__", None)
            if validator_attr is None:
                validator = None
            else:
                sig = inspect.signature(validator_attr)
                if len(sig.parameters) == 1:
                    if inspect.iscoroutinefunction(validator_attr):
                        async def two_params(a, _):
                            return await validator_attr(a)

                        validator = two_params
                    else:
                        def two_params(a, _):
                            return validator_attr(a)

                        validator = two_params
                else:
                    validator = validator_attr
                validator = asyncify(validator)

        # Call the validator function.
        if validator:
            return await validator(item, key)
        raise TypeError(f"The type parameter for {key} does not have "
                        "__validate__ and is not a recognised built-in type")

    # Handle any types.
    if typing_origin is typing.Any:
        return item

    # Handle unions.
    if typing_origin is typing.Union:
        types = typing.get_args(type_)
        if item is None and None in types:
            # Fast path!
            return None
        _undefined = {}
        last_throw = _undefined
        for type_ in types:
            if type_ is not None:
                try:
                    return await _validate_attr(type_, item, key)
                except (TypeError, ValidationError) as e:
                    last_throw = e
        if last_throw is not _undefined:
            raise last_throw from last_throw
        raise TypeError(f"Union for key {key} was empty")

    # Handle dicts.
    if typing_origin is typing.Dict:
        types = typing.get_args(type_)
        if len(types) != 2:
            raise TypeError(f"Unknown dict type count for {key}: {types}")
        dict_key_type = types[0]
        dict_value_type = types[1]
        if not isinstance(item, dict):
            raise ValidationError(f"The key {key} is not of a dict type", key)
        for dict_key, value in item.items():
            value = await _validate_attr(dict_value_type, value, f"{key}['{dict_key}']")
            new_key = await _validate_attr(dict_key_type, dict_key, f"{key}['{dict_key}']")
            if new_key is not dict_key:
                del item[dict_key]
            item[new_key] = value
        return item

    # Handle lists.
    if typing_origin is typing.List:
        type_ = typing.get_args(type_)[0]
        if not isinstance(item, list):
            if isinstance(item, set):
                # Close enough to safely convert.
                item = list(item)
            else:
                raise ValidationError(f"The key {key} is not of a list type", key)
        for index, list_obj in enumerate(item):
            item[index] = await _validate_attr(type_, list_obj, f"{key}[{index}]")
        return item

    # Handle sets.
    if typing_origin is typing.Set:
        type_ = typing.get_args(type_)[0]
        if not isinstance(item, (set, list)):
            raise ValidationError(f"The key {key} is not of a set or list type", key)
        s = set()
        for index, obj in enumerate(item):
            s.add(await _validate_attr(type_, obj, f"{key}[{index}]"))
        return s

    raise TypeError(f"Unsupported typing type used by key {key}: {typing_origin}")


class Model(object):
    """
    This is intended to represent a model object in an application. A model *can* be a database
    record type (and Record does use this), but it does not have to be. The Model type has many
    goals:

        1. Validation: This is arguably the most important part of the Model type. By default, making
           a type declaration on the root (for example, "a: str") will magically validate the type.
           You can set a default result with " = <default>". Note that Rainbows supports a "magic
           default" mode. If your default has "_rainbows_default", that sync function will be executed
           with "self" as the first argument. The result of that function will then be the actual default.
           Sometimes, though, you will want to make an external validator. The main ways to create an
           external validator are with the validates decorator in this package, or with self.add_validator.
           Follow the documentation for each of these to figure out how to use them.

        2. Extensibility: The Model type is designed to be highly extensible. Alongside the simple ways to
           extend with external validators listed above, you can go ahead and use self.attributes to figure out
           which typed attributes were setup. You can go ahead and use this dict to figure out the types and diff
           them externally. You can also use the magic defaults listed above to go ahead and inject things into
           the model. This is used by the Record type to handle indexes and foreign keys.

        3. Cleanliness: The end result should be VERY simple. You should be able to tell simply by the attributes of a
           class what the model handles.
    """

    def __init__(self, **kwargs):
        """
        Used to initialise the class and any attributes that you wish to set at the start via the kwargs. Note that
        this does NOT actually validate them, it just sets them ready to be validated.
        """
        self._defaults = {}

        for key in kwargs:
            if key.startswith("_"):
                del kwargs[key]
        self._items = kwargs

        _undefined = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            validates_keys = getattr(attr, "_validates_keys", _undefined)
            if validates_keys is not _undefined:
                self.add_validator(validates_keys, attr)

        self._attributes = getattr(self, "__annotations__", {})
        for attr_name in self._attributes:
            if attr_name.startswith("_"):
                del self._attributes[attr_name]
                continue

            found = False
            try:
                item = object.__getattribute__(self, attr_name)
                object.__delattr__(self, attr_name)
                found = True
            except AttributeError:
                pass

            if found:
                rainbows_default = getattr(item, "_rainbows_default", None)
                if rainbows_default is not None:
                    item = rainbows_default(self)
                self._defaults[attr_name] = item

    def attributes(self) -> typing.Dict[str, typing.Any]:
        """
        Gets a copy of all the keys and their expected types.

        :return: A dict with key -> type.
        """
        return self._attributes.copy()

    def is_default(self, key: str) -> bool:
        """
        Defines if a key will use its default value. This is false if there is no default or if the key is present.
        """
        if key in self._items:
            return False

        return key in self._defaults

    def __eq__(self, other) -> bool:
        """Check if 2 models are equal in type and content."""
        if type(self) != type(other):
            return False
        other_items = other._items
        for key, value in self._items.items():
            if key not in other_items or value != other_items[key]:
                return False
        return True

    def __ne__(self, other) -> bool:
        """Returns not __eq__."""
        return not self.__eq__(other)

    def __delattr__(self, item):
        """Allows you to delete an item by attribute."""
        try:
            object.__delattr__(self, item)
        except AttributeError as e:
            try:
                del self._items[item]
            except KeyError:
                raise e from e

    def __delitem__(self, key):
        """Allows you to delete an item by key."""
        del self._items[key]

    def __contains__(self, item):
        """Check if it is contained in our internal items."""
        return item in self._items

    def __getitem__(self, item):
        """Gets the item from the internal items dict."""
        try:
            return self._items[item]
        except KeyError as e:
            if item in self._defaults:
                return self._defaults[item]
            raise e from e

    def __setitem__(self, key, value):
        """Sets an item in the internal items dict."""
        if key.startswith("_"):
            raise ValueError("Key cannot start with an underscore")
        self._items[key] = value

    def __getattr__(self, name):
        """Gets the attribute if it isn't found in the main object."""
        try:
            return self._items[name]
        except KeyError as e:
            if name in self._defaults:
                return self._defaults[name]
            raise AttributeError(f"The attribute '{name}' is not present on this model object.") from e

    def __setattr__(self, key, value):
        """Sets the attribute to either the items dict or to the main object."""
        if key.startswith("_") or key in getattr(self, "_ignored_attrs", []):
            return object.__setattr__(self, key, value)

        self._items[key] = value

    def add_validator(self, key_name: typing.Union[str, typing.List[str], None], handler: VALIDATOR_CALLABLE) -> None:
        """
        This is used to add a custom validator to the model. This is used in situations where you wish to add
        custom logic to validate an item (for example: does a project ID actually exist as a record?).

        :param key_name: The keys this will affect. Can be a single string for one key, a list for many
                         keys, or None for all keys.
        :param handler:  The handler is a (async) function which takes in either 1 argument (the value) or
                         2 arguments (the value and the key).
        """
        validators = getattr(self, "_validators", None)
        if validators is None:
            validators = {}
            self._validators = validators

        sig = inspect.signature(handler)
        if len(sig.parameters) == 1:
            if inspect.iscoroutinefunction(handler):
                old_handler = handler

                async def two_params(a, _):
                    return await old_handler(a)

                handler = two_params
            else:
                old_handler = handler

                def two_params(a, _):
                    return old_handler(a)

                handler = two_params
        handler = asyncify(handler)

        if key_name is None:
            keys = [None]
        elif isinstance(key_name, str):
            keys = [key_name]
        else:
            keys = key_name

        for k in keys:
            try:
                validators[k].append(handler)
            except KeyError:
                validators[k] = [handler]

    def ignore_attribute(self, key: str) -> None:
        """
        Allows you to ignore an attribute. An ignored attribute will not show in items or count in validation.
        Note that keys that start with an underscore are automatically ignored.

        :param key: The attribute name you wish to ignore.
        """
        ignored = getattr(self, "_ignored_attrs", None)
        if ignored is None:
            ignored = []
            self._ignored_attrs = ignored

        if key in self._defaults:
            del self._defaults[key]

        if key in self._items:
            setattr(self, key, self._items[key])
            del self._items[key]

        ignored.append(key)

    async def validate(self) -> typing.Dict[str, typing.Any]:
        """
        Validates the specified data and returns a dict of it. Throws a ValidationError if it is invalid.

        :return: A dict with all the contents inside, using the default if it can when a value is not specified.
        """
        for key in self._items:
            if key not in self._attributes:
                raise ValidationError(f"Key {key} has been added to the model contents, but is not in the schema", key)

        all_items = self._items.copy()
        for key, value in self._attributes.items():
            # Handle if an attribute is present but not added.
            if key not in all_items:
                if key in self._defaults:
                    # Attempt to get from defaults.
                    value = self._defaults[key]
                    all_items[key] = value
                else:
                    # Check if it is typing.Optional.
                    is_optional = typing.get_origin(value) is typing.Union and type(None) in typing.get_args(value)
                    if is_optional:
                        all_items[key] = None
                        continue
                    raise ValidationError(f"Key {key} is not optional and was not found in the models contents", key)

            # Type check the specified param.
            item_value = await _validate_attr(value, all_items[key], key)
            all_items[key] = item_value
            self._items[key] = item_value

        custom_validators = getattr(self, "_validators", None)
        if custom_validators:
            async def call_validators(value, key):
                try:
                    handlers = custom_validators[key]
                except KeyError:
                    return
                for h in handlers:
                    value = await h(value, key)
                return value

            all_gobbler = []
            if None in custom_validators:
                all_gobbler = custom_validators[None]
            for key, value in all_items.items():
                for h in all_gobbler:
                    value = await h(value, key)
                value = await call_validators(value, key)
                all_items[key] = value
                self._items[key] = value

        return all_items
