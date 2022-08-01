import asyncio
import typing


class Context(object):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._autoclose_records = []
        self.loop = loop

    def new_task(self, fn: typing.Coroutine):
        """Used to add a new task to the event loop."""
        self.loop.create_task(fn)

    def dont_autokill_iterators(self):
        """
        This is used to prevent the killing of iterators after a request is done. This is useful if you intend to give
        the results to a task. Note that this means you MUST manually call the close function on iterators. If you do
        not, they will stay alive and cause a connection leak.
        """
        self._autoclose_records = None

    def _autoclose_record(self, fn):
        """This is a magic function used by record iterators to auto-close record iterators at the end of a request."""
        if self._autoclose_records is None:
            return
        self._autoclose_records.append(fn)
