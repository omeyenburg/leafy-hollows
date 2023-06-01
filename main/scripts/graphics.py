import sys, os
import scripts.shader as shader
if not shader.OPENGL_SUPPORTED:
    import scripts.shader_fallback as shader

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
import pygame


def quit():
    shader.quit() # Shader connection
    pygame.quit()
    sys.exit()


class Window:
    def __init__(self):
        self.max_fps = 60
        self.vsync = 0
        self.events = None
        
        info = pygame.display.Info()
        self.size = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.width, self.height = self.size
        self.window = shader.init(self.width, self.height, self.vsync) # Shader connection
        self.clock = pygame.time.Clock()

    def resize(self, width, height):
        self.size = (width, height)
        self.width, self.height = self.size
        self.window = shader.modify_window(self.width, self.height, self.vsync) # Shader connection

    def update(self, world_surface, ui_surface):
        shader.update(world_surface, ui_surface) # Shader connection
        
        self.clock.tick(self.max_fps)
        self.events = pygame.event.get()
        
        for event in self.events:
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.VIDEORESIZE:
                self.resize(event.w, event.h)
