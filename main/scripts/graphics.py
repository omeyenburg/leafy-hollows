from platform import system
import scripts.util as util
import numpy
import math
import sys
import os

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
import pygame


class Window:
    def __init__(self, caption, keys=()):
        # Callbacks
        self.callback_quit = None

        # Init pygame
        pygame.init()

        # Explicitly use OpenGL 3.3 core (4.1 core also works)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                        pygame.GL_CONTEXT_PROFILE_CORE)
        #pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        #pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

        # MacOS support
        if system() == "Darwin":
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

        # Constants
        self.max_fps = 1000
        self.vsync = 0

        # Events
        self.keys = dict.fromkeys(keys, 0) # 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.unicode = ""                  # Backspace = "\x08"
        self.mouse_buttons = [0, 0, 0]     # Left, Middle, Right | 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.mouse_pos = (0, 0, 0, 0)      # x, y, relx, rely
        self.mouse_wheel = [0, 0, 0, 0]    # x, y, relx, rely
        self.fps = 0
        self.delta_time = 1

        # Window variables
        info = pygame.display.Info()
        self.screen_size = info.current_w, info.current_h
        self.width, self.height = self.size = self.pre_fullscreen = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.fullscreen = False
        self.resize_supress = False
        
        # Window
        flags = DOUBLEBUF | RESIZABLE | OPENGL
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.vsync)
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()
        self.camera = None

        # OpenGL setup
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        #glEnable(GL_MULTISAMPLE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Create vertex array object
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Create vertex buffer objects
        vertices_vbo, ebo, self.dest_vbo, self.source_or_color_vbo, self.shape_vbo = glGenBuffers(5)

        # Instanced shader inputs
        self.vbo_instances_length = 0
        self.vbo_instances_index = 0
        self.dest_vbo_data = numpy.zeros(0, dtype=numpy.float32)
        self.source_or_color_vbo_data = numpy.zeros(0, dtype=numpy.float32)
        self.shape_vbo_data = numpy.zeros(0, dtype=numpy.float32)

        # Vertices & texcoords
        vertices = numpy.array([
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            -1.0, 1.0, 0.0, 1.0,   # top-left
            1.0, 1.0, 1.0, 1.0,    # top-right
            1.0, -1.0, 1.0, 0.0    # bottom-right
        ], dtype=numpy.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vertices_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Create element buffer object (EBO) for indices
        indices = numpy.array([0, 1, 2, 0, 2, 3], dtype=numpy.uint32)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, (GLuint * len(indices))(*indices), GL_STATIC_DRAW)

        # Create vertex buffer object (VBO) for vertices
        glBindBuffer(GL_ARRAY_BUFFER, vertices_vbo)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        
        # Create vertex buffer objects (VBOs) for draw data
        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.dest_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(2, 1)

        glEnableVertexAttribArray(3)
        glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.source_or_color_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(3, 1)

        glEnableVertexAttribArray(4)
        glBindBuffer(GL_ARRAY_BUFFER, self.shape_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.shape_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(4, 1, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(4, 1)
        
        # Assigned by bind_atlas
        self.atlas = None
        self.atlas_rects = None

        # Assigned by bind_font
        self.font = None
        self.font_rects = None

    def add_vbo_instance(self, dest, source_or_color, shape):
        """
        Queue a object to be drawn on the screen and resize buffers as necessary.
        """
        if self.vbo_instances_length == self.vbo_instances_index: # Resize all instanced vbos
            if not self.vbo_instances_length:
                self.vbo_instances_length = 1
            else:
                self.vbo_instances_length *= 2

            new_dest_vbo_data = numpy.zeros(self.vbo_instances_length * 4, dtype=numpy.float32)
            new_source_or_color_vbo_data = numpy.zeros(self.vbo_instances_length * 4, dtype=numpy.float32)
            new_shape_vbo_data = numpy.zeros(self.vbo_instances_length, dtype=numpy.float32)

            new_dest_vbo_data[:len(self.dest_vbo_data)] = self.dest_vbo_data
            self.dest_vbo_data = new_dest_vbo_data
            new_source_or_color_vbo_data[:len(self.source_or_color_vbo_data)] = self.source_or_color_vbo_data
            self.source_or_color_vbo_data = new_source_or_color_vbo_data
            new_shape_vbo_data[:len(self.shape_vbo_data)] = self.shape_vbo_data
            self.shape_vbo_data = new_shape_vbo_data

            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.dest_vbo_data.nbytes, self.dest_vbo_data, GL_DYNAMIC_DRAW)
 
            glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.source_or_color_vbo_data.nbytes, self.source_or_color_vbo_data, GL_DYNAMIC_DRAW)

            glBindBuffer(GL_ARRAY_BUFFER, self.shape_vbo)
            glBufferData(GL_ARRAY_BUFFER, self.shape_vbo_data.nbytes, self.shape_vbo_data, GL_DYNAMIC_DRAW)
            
        self.dest_vbo_data[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = dest
        self.source_or_color_vbo_data[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = source_or_color
        self.shape_vbo_data[self.vbo_instances_index:self.vbo_instances_index + 1] = shape

        self.vbo_instances_index += 1

    def resize(self):
        if self.fullscreen:
            flags = FULLSCREEN
        else:
            flags = DOUBLEBUF | RESIZABLE

        # Called twice, because of VSYNC...
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL, vsync=self.vsync)
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL, vsync=self.vsync)
        glViewport(0, 0, self.width, self.height)

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
                if self.resize_supress:
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
                self.mouse_pos = (event.pos[0] - self.width / 2, self.height / 2 - event.pos[1], event.rel[0], -event.rel[1])
            elif event.type == MOUSEBUTTONDOWN:
                if event.button < 4:
                    self.mouse_buttons[event.button - 1] = 1
            elif event.type == MOUSEBUTTONUP:
                if event.button < 4:
                    self.mouse_buttons[event.button - 1] = 0
            elif event.type == MOUSEWHEEL:
                self.mouse_wheel = [self.mouse_wheel[0] + event.x, self.mouse_wheel[1] + event.y, event.x, event.y]

    def update(self):
        # Update pygame
        self.events()
        self.clock.tick(self.max_fps)
        self.fps = self.clock.get_fps()
        self.delta_time = (1 / self.fps) if self.fps > 0 else self.delta_time

        # Reset
        glClear(GL_COLOR_BUFFER_BIT)

        # Use VAO
        glBindVertexArray(self.vao)

        # Send variables to shader
        for index, (loc, func, value) in Shader.active.variables.items():
            if value is None:
                continue
            func(loc, value)
            Shader.active.variables[index][2] = None

        # Bind texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.atlas)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.font)

        # Send instance data to shader
        glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.dest_vbo_data.nbytes, self.dest_vbo_data)
        glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.source_or_color_vbo_data.nbytes, self.source_or_color_vbo_data)
        glBindBuffer(GL_ARRAY_BUFFER, self.shape_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.shape_vbo_data.nbytes, self.shape_vbo_data)

        glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, self.vbo_instances_index)
        pygame.display.flip()

        self.vbo_instances_index = 0

    def toggle_fullscreen(self):
        """
        Toggle between fullscreen and normal mode.
        """
        self.fullscreen = not self.fullscreen

        self.resize_supress = True

        if self.fullscreen:
            self.pre_fullscreen = self.size
            self.width, self.height = self.size = self.screen_size
        else:
            self.width, self.height = self.size = self.pre_fullscreen

        self.resize()

    def toggle_wire_frame(self, state):
        """
        Toggle between drawing only outlines and filled shapes.
        """
        if state:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def callback(self, function):
        if not function is None:
            function()

    def quit(self):
        self.callback(self.callback_quit)
        pygame.quit()
        sys.exit()
    
    def bind_atlas(self, atlas, blur=0):
        """
        Set the currently used texture atlas.
        """
        data = pygame.image.tostring(atlas[1], "RGBA", 1)
        if not self.atlas is None:
            glDeleteTextures(1, (self.atlas,))
        self.atlas = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.atlas)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *atlas[1].get_size(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        if blur:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.atlas_rects = atlas[0]

    def bind_font(self, font, blur=0):
        """
        Set the currently used font.
        """
        data = pygame.image.tostring(font[1], "RGBA", 1)
        if not self.font is None:
            glDeleteTextures(1, (self.font,))
        self.font = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.font)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *font[1].get_size(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        if blur:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.font_rects = font[0]
    
    def draw_image(self, image, position, size):
        """
        Draw an image on the window.
        """
        rect = (position[0] + size[0], position[1] + size[1], size[0] / 2, size[1] / 2)
        self.add_vbo_instance(rect, self.atlas_rects[image], 0)

    def draw_rect(self, position, size, color):
        """
        Draw a rectangle on the window.
        """
        rect = (position[0] + size[0] / 2, position[1] + size[1] / 2, size[0] / 2, size[1] / 2)
        self.add_vbo_instance(rect, self.camera.map_color(color), 1)

    def draw_circle(self, position, radius, color):
        """
        Draw a circle on the window.
        """
        self.add_vbo_instance((*position, radius, radius), self.camera.map_color(color), 2)

    def draw_text(self, position, text, color):
        """
        Draw text on the window.
        """
        offset = 0

        if len(color) == 3:
            color = (*color, 255)

        for letter in text:
            if not letter in self.font_rects and letter.isalpha():
                if letter.upper() in self.font_rects:
                    letter = letter.upper()
                else:
                    letter = letter.lower()
            if not letter in self.font_rects:
                letter = "?"
            rect = self.font_rects[letter]
            source_and_color = (color[0] + rect[0], color[1] + rect[1], color[2], color[3])
            dest_rect = (position[0] + offset + rect[1], position[1], rect[1], rect[2] * 2)
            offset += rect[1] * 2.5
            self.add_vbo_instance(dest_rect, source_and_color, 3)


class TextureAtlas:
    def __init__(self, **images):
        self.max_atlas_size = glGetIntegerv(GL_MAX_TEXTURE_SIZE)

        # Sort images with decreasing size
        self.sorted_images = sorted(images.keys(), key=lambda index: sum(images[index].get_size()), reverse=True)

        # Gather image size
        self.image_rects = [[0, 0, *images[index].get_size()] for index in self.sorted_images]
        if self.image_rects:
            self.atlas_size = list(self.image_rects[0][2:])
        else:
            self.atlas_size = [0, 0]

        # Create image coords on the texture atlas
        self.space = numpy.ones(self.atlas_size[::-1], dtype=numpy.int8)
        for index, key in enumerate(self.sorted_images):
            image = images[key]
            self.image_rects[index][:2] = self.find_empty_position(*self.image_rects[index][2:])
            for dx, dy in numpy.ndindex(*self.image_rects[index][2:]):
                x = dx + self.image_rects[index][0]
                y = dy + self.image_rects[index][1]
                self.space[y, x] = 0

        self.texture_atlas = pygame.Surface(self.atlas_size, flags=pygame.SRCALPHA)
        for index, key in enumerate(self.sorted_images):
            image = images[key]
            coord = self.image_rects[index][:2]
            self.texture_atlas.blit(image, coord)
            self.image_rects[index] = (self.image_rects[index][0] / self.atlas_size[0],
                                       self.image_rects[index][1] / self.atlas_size[1],
                                       self.image_rects[index][2] / self.atlas_size[0],
                                       self.image_rects[index][3] / self.atlas_size[1])

        self.data = pygame.image.tostring(self.texture_atlas, "RGBA", 1)

    def find_empty_position(self, width, height):
        while True:
            # Find empty space
            for x in range(self.atlas_size[0] - width + 1):
                for y in range(self.atlas_size[1] - height + 1):
                    if numpy.all(self.space[y:y+height, x:x+width] == 1):
                        return (x, y)

            # Resize space
            if self.atlas_size[0] > 2048 or self.atlas_size[1] > 2048:
                print("Warning: Atlas has a size of (2048, 2048) or higher")
            if self.atlas_size[1] > self.atlas_size[0]:
                self.space = numpy.concatenate((self.space, numpy.ones((self.space.shape[0], 1), dtype=numpy.int8)), axis=1)
                self.atlas_size[0] += 1
            else:
                self.space = numpy.concatenate((self.space, numpy.ones((1, self.space.shape[1]), dtype=numpy.int8)), axis=0)
                self.atlas_size[1] += 1

        raise Exception("Ran out of space to create texture atlas with maximum size of %d" % self.max_atlas_size)

    def load(folder):
        """
        Load texture atlas data from files in a folder.
        """
        with open(folder + "/data.txt", "r") as f:
            data_str = f.readlines()
        image = pygame.image.load(folder + "/atlas.png")
        rects = {}
        for line in data_str:
            if line:
                line = line.replace(" ", "")
                var, rect_str = line.split(":")
                rect = tuple([float(val) if val.replace(".", "").isdecimal()
                              and not val.replace("/", "", 1).replace(".", "").isdecimal()
                              else eval(val) for val in rect_str.split(",")]) # eval() for "1/3", otherwise float("23.2")
                rects[var] = rect
        return rects, image
                

class Font:
    def fromPNG(path):
        """
        Load a monospaced font from a PNG file with all letters from chr(32) to chr(96).
        """
        image = pygame.image.load(path).convert()

        letter_width = image.get_width() // 64
        letter_height = image.get_height()
        letters = {chr(i + 32): (1 / 64 * i, 1 / 64, letter_height / image.get_width()) for i in range(64)}

        return (letters, image)

    def fromTTF(path, size=1):
        """
        Load a font from a TrueTypeFont file.
        """
        font = pygame.font.Font(path, size)
        images = []
        letters = {}

        font_height = font.render("".join([chr(i) for i in range(32, 96)]), 0, (0, 0, 0)).get_height()
        font_width = 0

        space = font.render("A", 0, (0, 0, 0))

        for i in range(32, 96):
            letter = chr(i)
            if letter != " ":
                image = font.render(letter, 0, (255, 255, 255))
            else:
                image = space
            letter_width = image.get_width()
            letters[chr(i)] = (font_width, letter_width, font_height)

            font_width += letter_width
            images.append(image)

        image = pygame.Surface((font_width, font_height))

        for letter in letters:
            image.blit(images[ord(letter) - 32], (0, letters[letter][0]))
            letters[letter] = (letters[letter][0] / font_width, letters[letter][1] / font_width, font_height / font_width)

        return (letters, image)

    def fromSYS(name, size=1):
        """
        Load a font from the system.
        """
        font = pygame.font.SysFont(name, size)
        images = []
        letters = {}

        font_height = font.render("".join([chr(i) for i in range(32, 96)]), 0, (0, 0, 0)).get_height()
        font_width = 0

        space = font.render("A", 0, (0, 0, 0))

        for i in range(32, 96):
            letter = chr(i)
            if letter != " ":
                image = font.render(letter, 0, (255, 255, 255))
            else:
                image = space
            letter_width = image.get_width()
            letters[chr(i)] = (font_width, letter_width, font_height)

            font_width += letter_width
            images.append(image)

        image = pygame.Surface((font_width, font_height))

        for letter in letters:
            image.blit(images[ord(letter) - 32], (letters[letter][0], 0))
            letters[letter] = (letters[letter][0] / font_width, letters[letter][1] / font_width, font_height / font_width)

        return (letters, image)


class Camera:
    def __init__(self, window):
        self.pos = [0, 0]
        self.vel = [0, 0]
        self.dest = [0, 0]
        self.window = window
        window.camera = self

    def set(self, pos):
        """
        Set the camera position.
        Use move() for slow movement.
        """
        self.pos = pos
        self.vel = [0, 0]
        self.dest = pos

    def move(self, pos):
        """
        Move the camera slowly to a position.
        Use set() for instant movement.
        """
        self.dest = pos

    def update(self):
        """
        Update the camera.
        """
        self.vel[0] = round((self.pos[0] - self.dest[0]) / 5, 3)
        self.vel[1] = round((self.pos[1] - self.dest[1]) / 5, 3)
        self.pos[0] = round(self.pos[0] + vel[0], 3)
        self.pos[1] = round(self.pos[1] + vel[1], 3)

    def map_coord(self, coord, fpixel=True, fcentered=True, fworld=False, pixel=False, centered=True, world=False):
        """
        Convert a coordinate to a different format.
        Current format specified by fpixel, fcentered, fworld.
        Output format specified by pixel, centered, world.
        """
        if fworld:
            fpixel = True
        if world:
            pixel = True
        coord = list(coord)
        if fpixel and not pixel:
            for i in range(len(coord)):
                coord[i] /= (self.window.width, self.window.height)[i%2] / 2
        elif not fpixel and fpixel:
            for i in range(len(coord)):
                coord[i] /= (self.window.width, self.window.height)[i%2] / 2
        if not fcentered and centered:
            for i in range(2):
                coord[i] -= 1
        elif fcentered and not centered:
            for i in range(2):
                coord[i] += 1

        return coord

    def map_color(self, color):
        if not float in color:
            color = [i / 255 for i in color]
        if len(color) == 3:
            color = (*color, 1)
        return color


class Shader:
    active = None

    def __init__(self, vertex, fragment, textures, **variables):
        self.program = glCreateProgram()
        self.texAtlas, self.texFont = textures
        variables[self.texAtlas] = "int"
        variables[self.texFont] = "int"
        
        with open(vertex, "r") as file:
            vertex_shader = compileShader(file.read(), GL_VERTEX_SHADER)
        with open(fragment, "r") as file:
            fragment_shader = compileShader(file.read(), GL_FRAGMENT_SHADER)
        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)
        glLinkProgram(self.program)
        glValidateProgram(self.program)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        # Dict containing all variables which should be send to the fragment shader {variable1: (uniformLoc, glUniformFunc, value)}
        self.variables = {variable: Shader.get_uniform_loc(self.program, variable, variables[variable]) for variable in variables}

        self.setvar(self.texAtlas, 0)
        self.setvar(self.texFont, 1)

    def setvar(self, variable, value):
        self.variables[variable][2] = value

    def activate(self):
        glUseProgram(self.program)
        Shader.active = self

    def delete(self):
        glDeleteProgram(self.program)

    def get_uniform_loc(program, variable, data_type): # Get location and convert glsl data type to valid function
        loc = glGetUniformLocation(program, variable)
        func = data_type_map = {'int': glUniform1i,
                                'uint': glUniform1ui,
                                'float': glUniform1f,
                                'vec2': glUniform2f,
                                'vec3': glUniform3f,
                                'vec4': glUniform4f,
                                'bvec2': glUniform2i,
                                'bvec3': glUniform3i,
                                'bvec4': glUniform4i,
                                'ivec2': glUniform2i,
                                'ivec3': glUniform3i,
                                'ivec4': glUniform4i,
                                'uvec2': glUniform2ui,
                                'uvec3': glUniform3ui,
                                'uvec4': glUniform4ui,
                                'mat2': glUniformMatrix2fv,
                                'mat3': glUniformMatrix3fv,
                                'mat4': glUniformMatrix4fv}[data_type]
        return [loc, func, None]
