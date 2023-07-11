# -*- coding: utf-8 -*-
import platform
import sys
import os


# Global variables
realistic = True # only for testing purposes


class File:
    @staticmethod
    def read(path: str):
        with open(path, "r") as f:
            lines = f.read()
        return lines
    
    @staticmethod
    def write(path: str, content: str):
        with open(path, "w") as f:
            lines = f.write(content)
        return lines

    @staticmethod
    def path(relative_path: str):
        return os.path.abspath(os.path.join(__file__, "../..", relative_path))