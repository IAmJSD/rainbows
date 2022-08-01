import re
from .model import Model


# Credit: https://stackoverflow.com/a/1176023
SNAKE_REGEX = re.compile("(?<!^)(?=[A-Z])")


class Record(Model):
    """
    Record is based off Model and handles all the database logic for your application.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ignore_attribute("table_name")
        self.ignore_attribute("connection_name")

    def get_table_name(self) -> str:
        """
        Gets the table name for this class. If table_name is set, this will be used. If not, this will be a normalised
        version of the class name.

        :return: The table name for the class.
        """
        _undefined = {}
        self_table_name = getattr(self, "table_name", _undefined)
        if self_table_name is not _undefined:
            return str(self_table_name)

        table_name = SNAKE_REGEX.sub("_", self.__name__).lower()
        if table_name.endswith("s"):
            table_name += "es"
        else:
            table_name += "s"

        return table_name
