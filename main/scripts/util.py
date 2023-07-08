import sys
import os


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

    """
    @staticmethod
    def path(relative_path: str):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.abspath(os.path.join(base_path, relative_path))
    """

    @staticmethod
    def path(relative_path: str):
        return os.path.abspath(os.path.join(__file__, "../..", relative_path))