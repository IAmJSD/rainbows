def driver_entrypoint(cls):
    """
    Defines this class as the entrypoint for the driver. Note you should only have one of these exported by the package.
    """
    cls._rainbows_driver_entrypoint = True
    return cls
