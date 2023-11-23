# -*- coding: utf-8 -*-
from scripts.utility.const import *
import pickle
import json
import glob
import sys
import os


try:
    import numpy
except:
    pass


dirpath = os.path.dirname
basename = os.path.basename
isabs = os.path.isabs


def find(folder: str, name: str, sub_folder=False, first=False):
    """
    Finds a filename in a folder. If sub_folder is enabled, folders within it are searched recursively. If first is enabled, only the first file is returned.
    In 'name', "*" can be used as a placeholder for any of symbols.
    """
    if not os.path.isabs(folder):
        folder = os.path.join(__file__, "..", "..", "..", *folder.split("/"))
    
    # Darwin fix
    prefix = ""
    if PLATFORM == "Darwin":
        prefix = "/"

    if sub_folder:
        files = glob.glob(os.path.abspath(prefix + os.path.join(*folder.split("/"), "**", name)), recursive=True)
    else:
        files = glob.glob(os.path.abspath(prefix + os.path.join(*folder.split("/"), name)))

    if first and len(files):
        return files[0]
    return files


def abspath(path: str):
    """
    Converts a relative file path to a absolute file path at runtime.
    """
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(__file__, "..", "..", "..", *path.split("/")))


def relpath(path: str):
    """
    Converts a absolute file path to a relative file path at runtime.
    """
    if not os.path.isabs(path):
        return path
    index = len(path) - path[::-1].find("niam") + 1
    return path[index:]


def load(path: str, default=None, file_format="text", split=False):
    """
    Reads the content of a file.
    """
    if not os.path.isabs(path):
        path = abspath(path)

    try:
        if file_format == "text":
            with open(path, "r") as f:
                if split:
                    data = f.readlines()
                else:
                    data = f.read()

        elif file_format == "json":
            with open(path, "r") as f:
                data = json.load(f)

        elif file_format == "pickle":
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
            except EOFError:
                return None

        elif file_format == "numpy":
            data = numpy.load(path)

    except (ValueError if default is None else FileNotFoundError):
            data = default

    return data


def save(path: str, data, file_format="text"):
    """
    Writes into a file.
    """
    if not os.path.isabs(path):
        path = abspath(path)

    # Create folders
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if file_format == "text":
        with open(path, "w") as f:
             f.write(data)

    elif file_format == "json":
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    elif file_format == "pickle":
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    elif file_format == "numpy":
        numpy.save(path, data)

    
def exists(path: str):
    if not os.path.isabs(path):
        path = abspath(path)
    return os.path.exists(path)


def delete(path: str):
    if not os.path.isabs(path):
        path = abspath(path)

    if os.path.exists(path):
        os.remove(path) 
