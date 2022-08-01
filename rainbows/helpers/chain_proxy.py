class ChainProxy(object):
    """
    This class is a special dirty hack to call different sync methods in a clean way and not care about the result.
    Instead, you will get back this chain proxy class that will handle calling the next method.
    """
    def __init__(self, obj):
        self._obj = obj

    def __getattribute__(self, item):
        root = object.__getattribute__(self, "_obj")
        _undefined = {}
        res = getattr(root, item, _undefined)
        if res is _undefined:
            raise AttributeError(f"{type(root)} does not contain {item}")

        def self_returning_caller(*args, **kwargs):
            res(*args, **kwargs)
            return self

        return self_returning_caller
