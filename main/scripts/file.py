# -*- coding: utf-8 -*-
import json
import glob
import sys
import os


dirpath = os.path.dirname
basename = os.path.basename


def find(folder: str, name: str, sub_folder=False):
    """
    Finds a filename in a folder. If sub_folder is enabled, folders within it are searched recursively.
    'folder' should be a relative path. In 'name', "*" can be used as a placeholder for any of symbols.
    """
    if sub_folder:
        return glob.glob(os.path.abspath(os.path.join(__file__, "..", "..", *folder.split("/"), "**", name)), recursive=True)
    return glob.glob(os.path.abspath(os.path.join(__file__, "..", "..", *folder.split("/"), name)))


def abspath(path: str):
    """
    Converts a relative file path to a absolute file path at runtime.
    """
    return os.path.abspath(os.path.join(__file__, "..", "..", *path.split("/")))


def relpath(path: str):
    """
    Converts a absolute file path to a relative file path at runtime.
    """
    index = len(path) - path[::-1].find("niam")
    return path[index:]


def read(path: str, default=None, split=False):
    """
    Reads the content of a file.
    'path' should be a relative file path.
    """
    try:
        with open(abspath(path), "r") as f:
            if split:
                lines = f.readlines()
            else:
                lines = f.read()
    except (ValueError if default is None else FileNotFoundError):
        lines = default
    return lines


def write(path: str, content: str):
    """
    Writes into a file.
    'path' should be a relative file path.
    """
    with open(abspath(path), "w") as f:
        lines = f.write(content)
    return lines


def read_json(path: str):
    """
    Reads the content of a json file.
    'path' should be a relative file path.
    """
    with open(abspath(path), "r") as f:
        data = json.load(f)
    return data