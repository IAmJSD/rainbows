from .logger import AbstractLogger, DefaultLogger
import asyncio


class _BootstrappingMetadata(object):
    """Defines any metadata relating to bootstrapping."""
    def __init__(self):
        self._bootstrapped = False
        self._model_path = None
        self._view_path = None
        self._controller_path = None
        self._config_path = None

    @property
    def bootstrapped(self) -> bool:
        """Defines if bootstrapping is complete."""
        return self._bootstrapped

    def _throw_if_bootstrapped(self):
        if self._bootstrapped:
            raise TypeError("Function ran after bootstrapping has ran. Functions here are only meant to be ran during "
                            "bootstrapping!")

    @property
    def logger(self) -> AbstractLogger:
        """Used to get the logger which used."""
        try:
            return self._logger
        except AttributeError:
            self._logger = DefaultLogger()
            return self._logger

    def set_logger(self, logger: AbstractLogger) -> None:
        """Used to set the logger within an initializer."""
        self._throw_if_bootstrapped()
        self._logger = logger

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Used to get the event loop which is used."""
        try:
            return self._loop
        except AttributeError:
            try:
                from uvloop import new_event_loop
                self._loop = new_event_loop()
            except ImportError:
                self.logger.warn("rainbows.bootstrap", "uvloop is not available. If this is not a Windows system, "
                                                       "install uvloop from pip for a free performance bump! The "
                                                       "default Dockerfile already contains uvloop.")
                self._loop = asyncio.get_event_loop()
            return self._loop

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Used to set the event loop within an initializer."""
        self._throw_if_bootstrapped()
        self._loop = loop

    def _post_bootstrap(self):
        """Does all post bootstrap handling."""
        self.logger.set_loop(self.loop)
        self._bootstrapped = True


bootstrapping_metadata = _BootstrappingMetadata()
