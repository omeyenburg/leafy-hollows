import numpy
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *
if not pygame.display.get_init():
    pygame.init()


def init(width, height, vsync):
    # Create pygame window
    flags = DOUBLEBUF | RESIZABLE
    return pygame.display.set_mode((width, height), flags=flags)


def quit():
    return


def modify_window(width, height, vsync):
    flags = DOUBLEBUF | RESIZABLE
    return pygame.display.set_mode((width, height), flags=flags)


class Shader:
    def __init__(self, vertex, fragment, **variables):
        return

    def setvar(self, variable, value):
        return

    def activate(self):
        return

    def delete(self):
        return


def load_vertex(path):
    return


def load_fragment(path):
    return
   

def update(world_surface, ui_surface):
    pygame.display.flip()
