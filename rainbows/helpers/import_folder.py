import importlib
import os
import ntpath
import typing


class ImportDisallowedError(Exception):
    """Thrown by the validate_filepath function if a filepath is disallowed."""


def import_folder(
        fp: str, validate_filepath: typing.Union[typing.Callable[[str], typing.Union[str, None]], None],
        order_filepaths: typing.Union[typing.Callable[[typing.List[str]], typing.List[str]], None],
        look_for_imports: typing.Callable[[typing.Union[str, None]], typing.Union[None, typing.List[str], str]],
) -> typing.Dict[str, typing.Any]:
    """
    Used to import a folder that uses the ordered import structure instead of the __init__.py one. Whilst not awfully
    Pythonic, this structure has a number of advantages for rapid application development. This import function is
    recursive and will return/load imports for nested children of the folder.

    :param fp:                The folder which this import starts from.
    :param validate_filepath: A function which takes the filepath and returns a string which is used in
                              look_for_imports, None to give said function a None as the argument, or raises a
                              ImportDisallowedError if this filepath should not be imported. If none, only the standard
                              validation is performed (ends in .py and does not start with an underscore).
    :param order_filepaths:   A function which takes in a list of strings and returns a list which is in the order we
                              want. If set to None, imports are loaded in the order Python returns them.
    :param look_for_imports:  Defines a function to look for things to import from the specified file. The argument is
                              the result from validate_filepath (useful if you are looking for
                              <part of filename>Controller) and the result of this function should either be a string to
                              import, a string array to import, or None.
    :return:                  A dict containing the filepath mapped to either a list of imports or a single import
                              depending on if the result of look_for_imports is a string or string array. If none of the
                              imports are found or None is specified, the key will not be in the dict.
    """
    allowed_paths = []
    sub_part = {}
    file_result = {}

    def _process_folder(files):
        for file in files:
            if ntpath.isdir(file):
                # This is a folder, give it to the processor.
                fps = os.listdir(file)
                for index, filename in enumerate(fps):
                    fps[index] = ntpath.join(file, filename)
                _process_folder(fps)
            else:
                # This is a file, process it.
                try:
                    # Do the default handling.
                    filename = ntpath.basename(file)
                    if not filename.endswith(".py") or filename.startswith("_"):
                        raise ImportDisallowedError

                    # Call the validate function.
                    if validate_filepath is None:
                        sub_part[file] = None
                    else:
                        sub_part[file] = validate_filepath(file)
                except ImportDisallowedError:
                    continue
                allowed_paths.append(file)

    fps = os.listdir(fp)
    for index, filename in enumerate(fps):
        fps[index] = ntpath.join(fp, filename)
    _process_folder(fps)

    if order_filepaths is not None:
        allowed_paths = order_filepaths(allowed_paths)

    undefined = {}
    for fp in allowed_paths:
        imports = look_for_imports(sub_part[fp])
        module = importlib.import_module(fp)
        if type(imports) is str:
            a = getattr(module, imports, undefined)
            if a is not undefined:
                file_result[fp] = a
        elif imports is not None:
            results = []
            for i in imports:
                a = getattr(module, i, undefined)
                if a is not undefined:
                    results.append(a)
            if len(results) != 0:
                file_result[fp] = results

    return file_result
