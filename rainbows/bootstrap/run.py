from .metadata import bootstrapping_metadata
from rainbows.helpers import import_folder
import os
import ntpath
import typing
import stat
import inspect


def partial_bootstrap(dirname: str) -> None:
    """Partially bootstraps the application but does not actually listen."""
    config_path = ntpath.join(dirname, "config")
    if not ntpath.isdir(config_path):
        raise FileNotFoundError("The config folder is not found")

    initializers_path = os.stat(ntpath.join(dirname, "initializers"))
    if not stat.S_ISDIR(initializers_path.st_mode):
        raise IOError("The initializers path was a file instead of a folder.")

    def order_filepaths(l: typing.List[str]) -> typing.List[str]:
        """
        Orders file paths in an order which will load initializers with "logger" in first, will load initializers with
        "loop" in after, and then just load the rest in alphabetical order.
        """
        logger_related = []
        loop_related = []
        remainder = []
        for item in l:
            if "logger" in item:
                logger_related.append(item)
            elif "loop" in item:
                loop_related.append(item)
            else:
                remainder.append(item)

        logger_related.sort()
        loop_related.sort()
        remainder.sort()

        return logger_related + loop_related + remainder

    remaining_initializers = import_folder(initializers_path, None, order_filepaths, lambda _: "initializer")
    async_inits = []
    for value in remaining_initializers.values():
        if inspect.iscoroutinefunction(value):
            async_inits.append(value)
        else:
            value()

    for initializer in async_inits:
        bootstrapping_metadata.loop.run_until_complete(initializer())

    bootstrapping_metadata._post_bootstrap()




def run(dirname: str) -> typing.NoReturn:
    """
    Used to bootstrap Rainbows and keep running it until CTRL+C is sent. This function expects Rainbows to be in the
    standard file/folder format of a regular install.
    """
    partial_bootstrap(dirname)
    loop = bootstrapping_metadata.loop
    # TODO
