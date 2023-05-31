import sys, os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
import pygame

import shader


def quit():
    shader.quit()
    pygame.quit()
    sys.exit()

class Window:

    def __init__(self):
        info = pygame.display.Info()
        self.size = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.width, self.height = 300, 300#self.size
        self.window = shader.init(self.width, self.height, 0)
        self.clock = pygame.time.Clock()

    def resize(self, width, height):
        self.size = (width, height)
        self.width, self.height = self.size
        self.window = shader.modify_window(self.width, self.height, 0)

    def update(self, world_surface, ui_surface):
        shader.update(world_surface, ui_surface)
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.VIDEORESIZE:
                self.resize(event.w, event.h)



class File:

    def read(path):
        with open(path, "r") as f:
            lines = f.readlines()
        return lines

    def path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
