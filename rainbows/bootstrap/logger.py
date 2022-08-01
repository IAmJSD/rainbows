import abc
import asyncio
import multiprocessing
import os
import threading


class AbstractLogger(abc.ABC):
    """
    Defines an abstract logger. The logger should not do any async functions. Note that due to stop any circular
    imports, the loop is set in the logger after the loop is made. If anything is logged during initialisation,
    it should be stored until set_loop when it can then be added to the loop.
    """
    @abc.abstractmethod
    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        pass

    @abc.abstractmethod
    def info(self, handler: str, message: str) -> None:
        pass

    @abc.abstractmethod
    def warn(self, handler: str, message: str) -> None:
        pass

    @abc.abstractmethod
    def error(self, handler: str, message: str) -> None:
        pass

    @abc.abstractmethod
    def fatal(self, handler: str, message: str) -> None:
        pass


class DefaultLogger(AbstractLogger):
    """The class used for the default logging class."""
    def __init__(self):
        self._thread_pool = multiprocessing.Pool(os.cpu_count())
        self._lock = threading.Lock()

    def _do_log(self, msg: str):
        def do():
            self._lock.acquire()
            print(msg)
            self._lock.release()

        self._thread_pool.apply_async(do)

    def info(self, handler: str, message: str) -> None:
        self._do_log(f"ⓘ [{handler}] {message}")

    def warn(self, handler: str, message: str) -> None:
        self._do_log(f"⚠️️ [{handler}] {message}")

    def error(self, handler: str, message: str) -> None:
        self._do_log(f"❌️️ [{handler}] {message}")

    def fatal(self, handler: str, message: str) -> None:
        self._do_log(f"⛔ [{handler}] {message}")
        exit(1)

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        # Unneeded for this logger.
        pass
