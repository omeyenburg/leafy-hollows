# -*- coding: utf-8 -*-
import platform
import glob
import sys
import os


# Global variables
realistic = True # only for testing purposes


class file:
    @staticmethod
    def find(folder: str, name: str, sub_folder=False):
        if sub_folder:
            return glob.glob(os.path.abspath(os.path.join(__file__, "..", "..", *folder.split("/"), "**", name)), recursive=True)
        return glob.glob(os.path.abspath(os.path.join(__file__, "..", "..", *folder.split("/"), name)))

    @staticmethod
    def path(path: str):
        return os.path.abspath(os.path.join(__file__, "..", "..", *path.split("/")))

    @staticmethod
    def read(path: str, default=None, split=False):
        try:
            with open(file.path(path), "r") as f:
                if split:
                    lines = f.readlines()
                else:
                    lines = f.read()
        except (ValueError if default is None else FileNotFoundError):
            lines = default
        return lines
    
    @staticmethod
    def write(path: str, content: str):
        with open(file.path(path), "w") as f:
            lines = f.write(content)
        return lines