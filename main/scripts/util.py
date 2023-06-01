from pygame import Rect, Vector2 as Vector # pygame.org/docs/
import sys
import os

class File:
    @staticmethod
    def read(path):
        with open(path, "r") as f:
            lines = f.read()
        return lines

    def write(path, content):
        with open(path, "w") as f:
            lines = f.write(content)
        return lines
    
    @staticmethod
    def path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
