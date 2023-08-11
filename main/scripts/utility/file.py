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
    In 'name', "*" can be used as a placeholder for any of symbols.
    """
    if not os.path.isabs(folder):
        folder = os.path.join(__file__, "..", "..", "..", *folder.split("/"))
    if sub_folder:
        return glob.glob(os.path.abspath("/" + os.path.join(*folder.split("/"), "**", name)), recursive=True)
    return glob.glob(os.path.abspath("/" + os.path.join(*folder.split("/"), name)))
    '''
    #print(os.path.abspath(os.path.join(__file__, "..", "..", "..", *folder.split("/"), "**", name)))
    #print(os.path.join(*os.path.join(__file__, "..", "..", "..", *folder.split("/")).split("/"), "**", name))
    if sub_folder:
        return glob.glob(os.path.abspath(os.path.join(__file__, "..", "..", "..", *folder.split("/"), "**", name)), recursive=True)
    return glob.glob(os.path.abspath(os.path.join(__file__, "..", "..", "..", *folder.split("/"), name)))
    '''


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


def read(path: str, default=None, split=False):
    """
    Reads the content of a file.
    """
    if not os.path.isabs(path):
        path = abspath(path)
    try:
        with open(path, "r") as f:
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
    """
    if not os.path.isabs(path):
        path = abspath(path)
    with open(path, "w") as f:
        lines = f.write(content)
    return lines


def read_json(path: str):
    """
    Reads the content of a json file.
    """
    if not os.path.isabs(path):
        path = abspath(path)
    with open(path, "r") as f:
        data = json.load(f)
    return data


def write_json(path: str, content: str):
    """
    Writes into a json file.
    """
    if not os.path.isabs(path):
        path = abspath(path)
    with open(path, "w") as f:
        lines = json.dump(content, f, indent=4)
    return lines