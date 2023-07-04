import sys
import os


realistic = False # only for testing purposes


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
    def path(relative_path: str, script: str=None):
        if script is None:
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        else:
            return os.path.dirname(os.path.realpath(script)) + "/" + relative_path
