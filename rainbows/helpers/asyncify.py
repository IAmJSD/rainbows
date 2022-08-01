import inspect


def asyncify(fn):
    """This function exists to take a function that may or may not be async and ensure that the function is."""
    if inspect.iscoroutinefunction(fn):
        return fn

    async def wrap(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrap
