import ctypes
import platform
import subprocess
import os
import sys
import numpy

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *


directory = os.path.dirname(os.path.realpath(__file__))

os_name = platform.system()
graphics_library_name = directory + "/graphics-" + os_name.lower()
if os_name == 'Windows':
    graphics_library_name += platform.architecture()[0] + ".dll"
else:
    graphics_library_name += ".so"


# The shared library file doesn't exist, run setup.py to build it
if not os.path.exists(graphics_library_name):
    subprocess.check_call(['python', f'{directory}/setup.py', 'build_ext', '--inplace'], stdout=subprocess.DEVNULL)


# Load the shared library
graphics = ctypes.CDLL(graphics_library_name)

# Function prototypes
graphics.c_init.argtypes = [ctypes.c_int, ctypes.c_int]
graphics.c_init.restype = ctypes.c_int

graphics.c_update.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
graphics.c_update.restype = ctypes.POINTER(ctypes.c_uint8)

graphics.c_quit.argtypes = []
graphics.c_quit.restype = None

graphics.c_info_max_tex_size = []
graphics.c_info_max_tex_size = ctypes.c_int

graphics.c_load_shader.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
graphics.c_load_shader.restype = ctypes.c_int
graphics.load_shader = lambda vertex, fragment, **variables: graphics.c_load_shader(
    vertex.encode("utf-8"), fragment.encode("utf-8"),
    (ctypes.c_char_p * len(variables))(*map(lambda v: v.encode("utf-8"), variables.keys())),
    (ctypes.c_char_p * len(variables))(*map(lambda v: v.encode("utf-8"), variables.values())),
    len(variables))

graphics.c_update_shader_value.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
graphics.c_update_shader_value.restype = None
def p_update_shader_value(shader, index, value):
    if isinstance(value, int):
        c_value = ctypes.c_int(value)
    elif isinstance(value, float):
        c_value = ctypes.c_float(value)
    elif isinstance(value, (list, tuple)):
        if isinstance(value[0], int):
            c_value = (ctypes.c_int * len(value))(*value)
        elif isinstance(value[0], float):
            c_value = (ctypes.c_float * len(value))(*value)
    else:
        raise ValueError("Invalid value %r" % value)
    graphics.c_update_shader_value(shader, index, ctypes.byref(c_value))
graphics.update_shader_value = p_update_shader_value

graphics.activate_shader.argtypes = [ctypes.c_int]
graphics.activate_shader.restype = None


class Window:
    def __init__(self, caption, resolution=1, keys=("w",)):
        # Callbacks
        callback_quit = None

        # Init pygame
        pygame.init()

        print("01")

        # Explicitly use OpenGL 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                        pygame.GL_CONTEXT_PROFILE_CORE)

        # MacOS support
        if os_name == "Darwin":
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

        print("02")

        # Constants
        self.max_fps = 1000
        self.vsync = 0 # vertical sync = wait for buffer -> max. 60/120 fps

        # Events
        self.keys = dict.fromkeys(keys, 0) # 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.unicode = ""                  # Backspace = "\x08"
        self.mouse_buttons = [0, 0, 0]     # Left, Middle, Right | 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.mouse_pos = (0, 0, 0, 0)      # x, y, relx, rely
        self.mouse_wheel = [0, 0, 0, 0]    # x, y, relx, rely

        # Window variables
        info = pygame.display.Info()
        self.screen_size = info.current_w, info.current_h
        self.width, self.height = self.size = self.pre_fullscreen = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.fullscreen = False
        self.resize_supress = False
        
        # Window
        flags = DOUBLEBUF | RESIZABLE | OPENGL
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.vsync)

        print("03")
        
        # Caption & clock
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

        # Init OpenGL
        graphics.c_init(self.width, self.height)

        print("04")

    def resize(self):
        if self.fullscreen:
            flags = FULLSCREEN
        else:
            flags = DOUBLEBUF | RESIZABLE

        # Called twice: OPENGL flag does something with the window size
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL, vsync=self.vsync)
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL, vsync=self.vsync)
        graphics.resize(self.width, self.height)

    def events(self):
        events = pygame.event.get()

        self.keys = {key: (value if value != 1 else 2) for key, value in self.keys.items()}
        self.unicode = ""
        self.mouse_buttons = [2 if value == 1 else value for value in self.mouse_buttons]
        self.mouse_wheel[2], self.mouse_wheel[3] = 0, 0
        
        for event in events:
            if event.type == QUIT:
                self.quit()
            elif event.type == VIDEORESIZE:
                if self.resize_supress or 1:
                    resize_supress = False
                    continue
                self.size = event.size
                self.width, self.height = event.w, event.h
                self.resize()
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

    def update(self):
        graphics.c_update()
        self.events()
        self.clock.tick(self.max_fps)
        pygame.display.flip()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

        self.resize_supress = True

        if self.fullscreen:
            self.pre_fullscreen = self.size
            self.width, self.height = self.size = self.screen_size
        else:
            self.width, self.height = self.size = self.pre_fullscreen

        self.resize()

    def callback(function):
        if not function is None:
            function()

    def quit(self):
        self.callback(self.callback_quit)
        graphics.c_quit()
        pygame.quit()
        sys.exit()


class TextureAtlas:
    def __init__(self, **images):
        self.max_atlas_size = graphics.c_info_max_tex_size()

        # Sort images with decreasing size
        self.sorted_images = sorted(images.keys(), key=lambda index: sum(images[index].get_size()), reverse=True)

        # Gather image size
        self.image_rects = [pygame.Rect(0, 0, *images[index].get_size()) for index in self.sorted_images]
        if self.image_rects:
            self.atlas_size = list(self.image_rects[0].size)
        else:
            self.atlas_size = [0, 0]

        # Create image coords on the texture atlas
        self.space = numpy.ones(self.atlas_size[::-1], dtype=numpy.int8)
        for index, key in enumerate(self.sorted_images):
            image = images[key]
            self.image_rects[index].topleft = self.find_empty_position(*self.image_rects[index].size)
            for dx, dy in numpy.ndindex(*self.image_rects[index].size):
                x = dx + self.image_rects[index].x
                y = dy + self.image_rects[index].y
                self.space[y, x] = 0

        self.texture_atlas = pygame.Surface(self.atlas_size, flags=pygame.SRCALPHA)
        for index, key in enumerate(self.sorted_images):
            image = images[key]
            coord = self.image_rects[index].topleft
            self.texture_atlas.blit(image, coord)

        pygame.image.tostring(self.texture_atlas, "RGBA", 1)


    def find_empty_position(self, width, height):
        while True:
            # Find empty space
            for x in range(self.atlas_size[0] - width):
                for y in range(self.atlas_size[1] - height):
                    if numpy.all(self.space[y:y+height, x:x+width] == 1):
                        return (x, y)
            
            # Resize space
            if self.atlas_size == self.max_atlas_size:
                break
            if self.atlas_size[0] > 2048 or self.atlas_size[1] > 2048:
                print("Warning: Atlas has a size of (2048, 2048) or higher")
            if self.atlas_size[1] > self.atlas_size[0]:
                self.space = numpy.concatenate((self.space, numpy.ones((self.space.shape[0], 1), dtype=numpy.int8)), axis=1)
                self.atlas_size[0] += 1
            else:
                self.space = numpy.concatenate((self.space, numpy.ones((1, self.space.shape[1]), dtype=numpy.int8)), axis=0)
                self.atlas_size[1] += 1

        raise Exception("Ran out of space to create texture atlas with maximum size of %d" % self.max_atlas_size)
