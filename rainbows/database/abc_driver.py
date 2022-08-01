import abc
import asyncio
import typing
from rainbows.model.model import Model


class AbstractRecordIterator(abc.ABC):
    """This should be inherited by the database driver to create a new iterator."""
    def _rainbows_autoclose(self, ctx):
        """Internal - do not edit. Handles Rainbows magic like auto-closing record iterators."""
        ctx._autoclose_record(self.close)

    @abc.abstractmethod
    async def close(self) -> None:
        """Used to close an iterator. Note this should no-op if it was already closed."""
        raise NotImplementedError("The close function is not implemented by your driver")

    @abc.abstractmethod
    async def __anext__(self) -> typing.Any:
        """
        The __anext__ function should be used to iterate through the records.
        Each item should be a validated record.
        """
        raise NotImplementedError("The __anext__ function is not implemented by your driver")

    @abc.abstractmethod
    async def remaining(self) -> typing.List[typing.Any]:
        """Get a list of all the remaining records."""
        raise NotImplementedError("The remaining function is not implemented by your driver")


class AbstractDatabaseDriver(abc.ABC):
    """
    This class is the abstract class which is used to define how databases should be managed. The intention is that this
    class is inherited by your database driver which is then loaded in by being called <database name>Driver, having
    the @driver_entrypoint decorator, and being imported by the drivers __init__.

    When the database driver is found, the bootstrap async static method is called on it. The returned data is seen by
    Rainbows as the bootstrapper context, and is passed as the first argument in this classes __init__. This can be used
    by the driver as it wishes, but it is suggested that this is used to hold the connection information.

    All record construction methods are sync and return None. Exceptions such as RecordNotFound should NOT be raised by
    the construction methods and should instead be raised by the execute async function. All exceptions which can be
    thrown in this function are found in driver_exceptions.py. A special exception is RerunBootstrap. If this is thrown,
    the connection will be locked, the bootstrapping function will be re-ran, and the context will be stored. If any
    exceptions are thrown in this process, the connection context will not be changed.

    As a general rule, a driver should always try and avoid storing things in the global scope. Since many connections
    can be established, this has the potential to cause problems.
    """

    @abc.abstractmethod
    def __init__(self, bootstrap_ctx):
        """Initialises the class with the context from the bootstrap function."""
        pass

    @staticmethod
    @abc.abstractmethod
    async def bootstrap(config: typing.Dict[str, typing.Any], loop: asyncio.AbstractEventLoop) -> typing.Any:
        """
        Bootstraps the driver. Can return any exceptions the driver thinks is appropriate, but if this is at boot,
        throwing here will result in the application crashing. The config parameter is fetched by taking the config
        supplied to Rainbows for this specific connection and removing the driver key (this is just used for finding
        the package to import). THe returned result is passed on initialisation if this is deemed to be the right driver.
        """
        pass

    @staticmethod
    @abc.abstractmethod
    async def shutdown(bootstrap_ctx) -> None:
        """
        Used to gracefully shutdown the database driver. This is used if the connection configuration changes, if there
        is a forced reload, or if the application is closing.
        """
        pass

    @abc.abstractmethod
    def get(self, record_type: Model, id_: typing.Any, pk: typing.Optional[str]) -> None:
        """
        Used to get a record by a primary key using the ID and table name. If the primary key is set to None, then the
        primary key will be fetched from the database table and then cached for 10 minutes. The result is then
        initialised from the record type. Note that the Record type is not used here to avoid a circular import, so
        the Model type is deemed close enough and is not incompatible.

        The model should be used to determine the attributes. If an attribute is not in the model, it should not be got.

        You must handle joins within this. You can use the get_joins function within the record_type to go ahead and
        figure out how to get this from the table. Consult the documentation get_joins in the Record type for more
        information on how to do this.

        If all is okay when execute is ran, the validated record type should be at the index it was called at in the
        results list. If the record doesn't exist, a RecordNotFound error should be thrown.
        """
        pass

    @abc.abstractmethod
    def select_one(self, record_type: Model, query: typing.Dict[str, typing.Any]) -> None:
        """
        Used to get a record by the query specified. Note that the Record type is not used here to avoid a circular
        import, so the Model type is deemed close enough and is not incompatible.

        The model should be used to determine the attributes. If an attribute is not in the model, it should not be got.

        You must handle joins within this. You can use the get_joins function within the record_type to go ahead and
        figure out how to get this from the table. Consult the documentation get_joins in the Record type for more
        information on how to do this.

        If all is okay when execute is ran, the validated record type should be at the index it was called at in the
        results list. If the record doesn't exist, a RecordNotFound error should be thrown.
        """
        pass

    @abc.abstractmethod
    def select(self, record_type: Model, query: typing.Dict[str, typing.Any], iterator: bool) -> None:
        """
        Used to get a record by the query specified. Note that the Record type is not used here to avoid a circular
        import, so the Model type is deemed close enough and is not incompatible.

        The model should be used to determine the attributes. If an attribute is not in the model, it should not be got.

        You must handle joins within this. You can use the get_joins function within the record_type to go ahead and
        figure out how to get this from the table. Consult the documentation get_joins in the Record type for more
        information on how to do this.

        The result at the index it was called at in the results list will be different depending on the iterator param.
        If iterator is true and execute does not throw an exception, the result at this index MUST inherit
        BaseRecordIterator. If this iterator is false, a list of validated records should be returned.
        """
        pass

    @abc.abstractmethod
    def delete_by_id(self, record_type: Model, id_: typing.Any, pk: typing.Optional[str]) -> None:
        """
        Used to delete a record by its ID. If the primary key is set to None, then the primary key will be fetched from
        the database table and then cached for 10 minutes.

        If all is okay when execute is ran, a boolean specifying if it was deleted should be at the index it was called
        at in the results list.
        """
        pass

    @abc.abstractmethod
    def delete_by(self, record_type: Model, query: typing.Dict[str, typing.Any]) -> None:
        """
        Used to delete a record by the query specified. Note that the Record type is not used here to avoid a circular
        import, so the Model type is deemed close enough and is not incompatible.

        If all is okay when execute is ran, a number specifying the delete count should be at the index it was called
        at in the results list.
        """
        pass

    @abc.abstractmethod
    async def execute(self) -> typing.List[typing.Any]:
        """
        Used to execute the queries specified. The driver should do its best to batch together as many of the queries as
        possible and the result here should be all the results in a list. Any exceptions from the above functions should
        also been thrown by this function.
        """
        pass
