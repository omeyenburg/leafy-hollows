import sys, os
import scripts.shader as shader

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
import pygame


def quit():
    shader.quit() # Shader connection
    pygame.quit()
    sys.exit()


class Window:
    def __init__(self, keys=("w",)):
        # Constants
        self.max_fps = 1000
        self.vsync = 0

        # Events
        self.keys = dict.fromkeys(keys, 0) # 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.unicode = "" # Backspace = "\x08"
        self.mouse_buttons = [0, 0, 0] # Left, Middle, Right | 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.mouse_pos = (0, 0, 0, 0) # x, y, relx, rely
        self.mouse_wheel = [0, 0, 0, 0] # x, y, relx, rely

        # Window & clock
        info = pygame.display.Info()
        self.size = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.width, self.height = self.size
        
        try:
            self.window = pygame.display.set_mode((self.width, self.height), flags=DOUBLEBUF | RESIZABLE | OPENGL, vsync=self.vsync)
            shader.init(self.width, self.height) # Shader connection
        except:
            self.window = pygame.display.set_mode((self.width, self.height), flags=DOUBLEBUF | RESIZABLE)
        self.clock = pygame.time.Clock()

    def resize(self, width, height):
        self.size = (width, height)
        self.width, self.height = self.size
        
        if shader.OPENGL_SUPPORTED:
            self.window = pygame.display.set_mode((self.width, self.height), flags=DOUBLEBUF | RESIZABLE | OPENGL, vsync=self.vsync)
            shader.modify(self.width, self.height) # Shader connection
        else:
            self.window = pygame.display.set_mode((self.width, self.height), flags=DOUBLEBUF | RESIZABLE)

    def events(self):
        events = pygame.event.get()

        self.keys = {k: (v if v != 1 else 2) for k, v in self.keys.items()}
        self.unicode = ""
        self.mouse_buttons = [2 if v == 1 else v for v in self.mouse_buttons]
        self.mouse_wheel[2], self.mouse_wheel[3] = 0, 0
        
        for event in events:
            if event.type == QUIT:
                quit()
            elif event.type == VIDEORESIZE:
                self.size = event.size
                self.width, self,height = event.w, event.h
                self.resize(event.w, event.h)
            elif event.type == KEYDOWN:
                if event.unicode != "":
                    self.unicode = event.unicode
                key = pygame.key.name(event.key)
                if key in self.keys:
                    self.keys[key] = 1
            elif event.type == KEYUP:
                key = pygame.key.name(event.key)
                if key in self.keys:
                    self.keys[key] = 0
            elif event.type == MOUSEMOTION:
                self.mouse_pos = (*event.pos, *event.rel)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button < 4:
                    self.mouse_buttons[event.button - 1] = 1
            elif event.type == MOUSEBUTTONUP:
                if event.button < 4:
                    self.mouse_buttons[event.button - 1] = 0
            elif event.type == MOUSEWHEEL:
                self.mouse_wheel = [self.mouse_wheel[0] + event.x, self.mouse_wheel[1] + event.y, event.x, event.y]

    def update(self, world_surface, ui_surface):
        shader.update(world_surface, ui_surface) # Shader connection
        self.events()
        self.clock.tick(self.max_fps)
