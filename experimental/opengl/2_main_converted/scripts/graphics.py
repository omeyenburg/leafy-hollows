from platform import system
import scripts.util as util
import sys
import os

import numpy

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
#from OpenGL.GLU import *


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
import pygame


directory = os.path.dirname(os.path.realpath(__file__))
system = system()


class Window:
    def __init__(self, caption, resolution=1, keys=("w",)):
        # Callbacks
        self.callback_quit = None

        # Init pygame
        pygame.init()

        # Explicitly use OpenGL 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                        pygame.GL_CONTEXT_PROFILE_CORE)

        # MacOS support
        if system == "Darwin":
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

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
        
        # Caption & clock
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

        # OpenGL setup
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Set up vertex array object (VAO)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Create vertex buffer objects (VBOs)
        """
        # Vertices & texcoords
        vertices = numpy.array([
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            -1.0, 1.0, 0.0, 1.0,   # top-left
            1.0, 1.0, 1.0, 1.0,    # top-right
            1.0, -1.0, 1.0, 0.0    # bottom-right
        ], dtype=numpy.float32)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # 

        # Create element buffer object (EBO) for indices
        indices = numpy.array([0, 1, 2, 0, 2, 3], dtype=numpy.uint32)
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        #glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, (GLuint * len(indices))(*indices), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        glEnableVertexAttribArray(1)
        """

        #glBindBuffer(GL_ARRAY_BUFFER, 0)
        #glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        #glBindVertexArray(0)

        # vertex shader inputs
        """
        vec2 position
        vec2 texcoord
        instanced vec4 dest_rect
        instanced vec4 source_rect
        instanced vec4 color
        instanced int shape -> 0=image, 1=rect, 2=circle
        """

        # VBOs
        vertices_vbo, ebo, self.dest_vbo, self.source_vbo, self.color_vbo, self.shape_vbo = glGenBuffers(6)

        # Instanced shader inputs
        self.vbo_instances_length = 0
        self.vbo_instances_index = 0
        self.dest_vbo_data = numpy.zeros(0)
        self.source_vbo_data = numpy.zeros(0)
        self.color_vbo_data = numpy.zeros(0)
        self.shape_vbo_data = numpy.zeros(0, dtype=int)

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
        #glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, (GLuint * len(indices))(*indices), GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, vertices_vbo)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        
        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.dest_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(2, 1)

        glEnableVertexAttribArray(3)
        glBindBuffer(GL_ARRAY_BUFFER, self.source_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.source_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(3, 1)

        glEnableVertexAttribArray(4)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.color_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(4, 1)

        glEnableVertexAttribArray(5)
        glBindBuffer(GL_ARRAY_BUFFER, self.shape_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.shape_vbo_data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(5, 2, GL_INT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(5, 1)
        

        # Assigned by bind_atlas
        self.atlas = None
        self.atlas_rects = None

        # Assigned by bind_font
        self.fonts = []
        self.font_rects = []

        # Shaders
        vertPath = util.File.path("shaders/image.vert", __file__)
        fragPath = util.File.path("shaders/image.frag", __file__)
        self.image_shader = Shader(vertPath, fragPath, tex="int", dest_rect="vec4", source_rect="vec4")

        vertPath = util.File.path("shaders/text.vert", __file__)
        fragPath = util.File.path("shaders/text.frag", __file__)
        self.text_shader = Shader(vertPath, fragPath, tex="int", dest_rect="vec4", source="vec2")

        # Draw data
        self.image_draw_data = {}
        self.text_draw_data = {}

    def add_vbo_instance(self, dest, source, color, shape):
        if self.vbo_instances_length == vbo_instances_index: # Resize all instanced vbos
            if not self.vbo_instances_length:
                self.vbo_instances_length = 1
            else:
                self.vbo_instances_length *= 2

            new_dest_vbo_data = numpy.zeros(self.vbo_instances_length)
            new_source_vbo_data = numpy.zeros(self.vbo_instances_length)
            new_color_vbo_data = numpy.zeros(self.vbo_instances_length)
            new_shape_vbo_data = numpy.zeros(self.vbo_instances_length, dtype=int)

            new_dest_vbo_data[:len(self.dest_vbo_data)] = self.dest_vbo_data
            self.dest_vbo_data = new_dest_vbo_data
            new_source_vbo_data[:len(self.source_vbo_data)] = self.source_vbo_data
            self.dest_vbo_data = new_source_vbo_data
            new_color_vbo_data[:len(self.color_vbo_data)] = self.color_vbo_data
            self.dest_vbo_data = new_color_vbo_data
            new_shape_vbo_data[:len(self.shape_vbo_data)] = self.shape_vbo_data
            self.dest_vbo_data = new_shape_vbo_data

            glDeleteBuffers(4, (self.dest_vbo, self.source_vbo, self.color_vbo, self.shape_vbo))
            self.dest_vbo, self.source_vbo, self.color_vbo, self.shape_vbo = glGenBuffers(4)

            #glEnableVertexAttribArray(2)
            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            glBufferData(GL_ARRAY_BUFFER, 0, self.dest_vbo_data, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glVertexAttribDivisor(2, 1)

            #glEnableVertexAttribArray(3)
            glBindBuffer(GL_ARRAY_BUFFER, self.source_vbo)
            glBufferData(GL_ARRAY_BUFFER, 0, self.source_vbo_data, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glVertexAttribDivisor(3, 1)

            #glEnableVertexAttribArray(4)
            glBindBuffer(GL_ARRAY_BUFFER, self.color_vbo)
            glBufferData(GL_ARRAY_BUFFER, 0, self.color_vbo_data, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glVertexAttribDivisor(4, 1)

            #glEnableVertexAttribArray(5)
            glBindBuffer(GL_ARRAY_BUFFER, self.shape_vbo)
            glBufferData(GL_ARRAY_BUFFER, 0, self.shape_vbo_data, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(5, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glVertexAttribDivisor(5, 1)

        self.dest_vbo_data[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = dest
        self.source_vbo_data[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = source
        self.color_vbo_data[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = color
        self.shape_vbo_data[self.vbo_instances_index:self.vbo_instances_index + 1] = shape

        self.vbo_instances_index += 1


    def resize(self):
        if self.fullscreen:
            flags = FULLSCREEN
        else:
            flags = DOUBLEBUF | RESIZABLE

        # Called twice: OPENGL flag does something with the window size
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

    def toggle_wire_frame(self, state):
        if state:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def update(self):
        self.events()
        self.clock.tick(self.max_fps)

        glClear(GL_COLOR_BUFFER_BIT)

        self.image_shader.activate()

        for index, (loc, func, value) in Shader.active.variables.items():
            if value is None:
                continue
            func(loc, value)
            Shader.active.variables[index] = None

        # Efficiency:
        # https://learnopengl.com/Advanced-OpenGL/Instancing

        # Better look:
        # https://learnopengl.com/Advanced-OpenGL/Anti-Aliasing
        # https://learnopengl.com/Advanced-OpenGL/Framebuffers
    

        # Draw rectangles
        # ...

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.atlas)

        glUniform1i(Shader.active.variables["tex"][0], 0)
        #glBindVertexArray(self.vao)

        # Use atlas to draw images
        for image in self.image_draw_data:
            source_rect = self.atlas_rects[image]
            glUniform4fv(Shader.active.variables["source_rect"][0], 1, source_rect)
            for pos, size in self.image_draw_data[image]:
                dest_rect = (*pos, 0.3, 0.3)
                glUniform4fv(Shader.active.variables["dest_rect"][0], 1, dest_rect)
                #glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
                glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, 1)

        # Draw circles
        # ...

        # Use fonts to draw text
        self.text_shader.activate()

        text = str(self.clock.get_fps())
        pos = (-0.8, 0.8)
        size = 1

        for font in self.text_draw_data:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.fonts[font])

            glUniform1i(Shader.active.variables["tex"][0], 0)
            #glBindVertexArray(self.vao)

            for text, pos in self.text_draw_data[font]:
                offset = 0
                for letter in text:
                    if not letter in self.font_rects[font] and letter.isalpha():
                        if letter.upper() in self.font_rects[font]:
                            letter = letter.upper()
                        else:
                            letter = letter.lower()
                    if not letter in self.font_rects[font]:
                        letter = "?"
                    rect = self.font_rects[font][letter]
                    source = (rect[0], rect[1])
                    dest_rect = (pos[0] + offset + rect[1], pos[1], rect[1], rect[2] * 2)
                    offset += rect[1] * 2.5

                    glUniform4fv(Shader.active.variables["dest_rect"][0], 1, dest_rect)
                    glUniform2fv(Shader.active.variables["source"][0], 1, source)
                    #glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
                    glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, 1)

        pygame.display.flip()

        self.image_draw_data = {}
        self.text_draw_data = {}

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen

        self.resize_supress = True

        if self.fullscreen:
            self.pre_fullscreen = self.size
            self.width, self.height = self.size = self.screen_size
        else:
            self.width, self.height = self.size = self.pre_fullscreen

        self.resize()

    def callback(self, function):
        if not function is None:
            function()

    def quit(self):
        self.callback(self.callback_quit)
        pygame.quit()
        sys.exit()
    
    def bind_atlas(self, atlas, blur=0):
        data = pygame.image.tostring(atlas[1], "RGBA", 1)
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
        data = pygame.image.tostring(font[1], "RGBA", 1)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
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
        self.fonts.append(texture)
        self.font_rects.append(font[0])
        return len(self.fonts) - 1
    
    def draw(self, image, pos, size):
        if image in self.image_draw_data:
            self.image_draw_data[image].add((pos, size))
        else:
            self.image_draw_data[image] = {(pos, size)}

    def write(self, font, text, pos):
        if font in self.text_draw_data:
            self.text_draw_data[font].add((text, pos))
        else:
            self.text_draw_data[font] = {(text, pos)}


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
        image = pygame.image.load(path).convert()

        letter_width = image.get_width() // 64
        letter_height = image.get_height()
        letters = {chr(i + 32): (1 / 64 * i, 1 / 64, letter_height / image.get_width()) for i in range(64)}

        return (letters, image)

    def fromTTF(path, size=1):
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
        self.pos[1] = round(self.pos[1] + vel[1], 3)


class Shader:
    active = None

    def __init__(self, vertex, fragment, **variables):
        self.program = glCreateProgram()
        
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
