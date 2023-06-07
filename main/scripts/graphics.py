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
    def __init__(self, caption, keys=("w",)):
        # Constants
        self.max_fps = 1000
        self.vsync = 0

        # Events
        self.keys = dict.fromkeys(keys, 0) # 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.unicode = ""                  # Backspace = "\x08"
        self.mouse_buttons = [0, 0, 0]     # Left, Middle, Right | 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.mouse_pos = (0, 0, 0, 0)      # x, y, relx, rely
        self.mouse_wheel = [0, 0, 0, 0]    # x, y, relx, rely

        # Window
        info = pygame.display.Info()
        self.size = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.width, self.height = self.size
        
        if shader.OPENGL_SUPPORTED:
            flags = DOUBLEBUF | RESIZABLE | OPENGL
            self.window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.vsync)
            shader.init(self.width, self.height) # Shader connection
        else:
            flags = DOUBLEBUF | RESIZABLE | HWSURFACE
            self.window = pygame.display.set_mode((self.width, self.height), flags=flags)

        # Window caption & clock
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

    def resize(self, width, height):
        self.size = (width, height)
        self.width, self.height = self.size
        
        if shader.OPENGL_SUPPORTED:
            flags = DOUBLEBUF | RESIZABLE | OPENGL
            self.window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.vsync)
            shader.modify(self.width, self.height) # Shader connection
        else:
            flags = DOUBLEBUF | RESIZABLE | HWSURFACE
            self.window = pygame.display.set_mode((self.width, self.height), flags=flags)

    def events(self):
        events = pygame.event.get()

        self.keys = {key: (value if value != 1 else 2) for key, value in self.keys.items()}
        self.unicode = ""
        self.mouse_buttons = [2 if value == 1 else value for value in self.mouse_buttons]
        self.mouse_wheel[2], self.mouse_wheel[3] = 0, 0
        
        for event in events:
            if event.type == QUIT:
                quit()
            elif event.type == VIDEORESIZE:
                self.size = event.size
                self.width, self.height = event.w, event.h
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


class Font:
    """
    Create a font from a file.
    """
    def __init__(self, path):
        font = pygame.image.load(path).convert()
        self.letters = {}
    
        for i in range(0, 64):
            subsurf = font.subsurface((i * 3, 0, 3, 5))
            subsurf.set_colorkey((255, 255, 255))
            self.letters[chr(i + 32)] = subsurf

    def write(self, surf, text, color, size, coord):
        """
        Write text on a surface.
        """
        text = str(text)
        if color == (0, 0, 0):
            color = (1, 1, 1)
        for index, letter in enumerate(text):
            letter_surf = pygame.Surface((3, 5))
            letter_surf.set_colorkey((0, 0, 0))
            letter_surf.fill(color)
            letter_surf.blit(self.letters[letter.upper()], (0, 0))
            surf.blit(pygame.transform.scale(letter_surf, (3 * size, 5 * size)),
                      (index * 4 * size + coord[0], coord[1]))

    @staticmethod
    def width(text, size):
        """
        Return the height of the text.
        """
        return 4 * size * (len(text) - 0.5) + size

    @staticmethod
    def height(size):
        """
        Return the height of the text.
        """
        return 5 * size


class Camera:
    def __init__(self, window):
        self.pos = [0, 0]
        self.vel = [0, 0]
        self.dest = [0, 0]

    def set(self, pos):
        self.pos = pos
        self.vel = [0, 0]
        self.dest = pos

    def move(self, pos):
        self.dest = pos

    def update(self):
        self.vel[0] = round((self.pos[0] - self.dest[0]) / 5, 3)
        self.vel[1] = round((self.pos[1] - self.dest[1]) / 5, 3)
        self.pos[0] = round(self.pos[0] + vel[0], 3)
        self.pos[1] = round(self.pos[0] + vel[0], 3)
        

