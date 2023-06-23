import sys
import os

class File:
    @staticmethod
    def read(path):
        with open(path, "r") as f:
            lines = f.read()
        return lines
    
    @staticmethod
    def write(path, content):
        with open(path, "w") as f:
            lines = f.write(content)
        return lines
    
    @staticmethod
    def path(relative_path, script=None):
        if script is None:
            try:
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        else:
            return os.path.dirname(os.path.realpath(script)) + "/" + relative_path
