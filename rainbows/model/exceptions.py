class ValidationError(Exception):
    """
    A validation error is thrown in the event that the model could not be validated.
    It contains the "key_name" attribute to allow you to find the key responsible.
    """
    def __init__(self, message, key_name: str):
        super().__init__(message)
        self._key_name = key_name

    @property
    def key_name(self):
        return self._key_name
