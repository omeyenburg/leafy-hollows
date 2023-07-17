# -*- coding: utf-8 -*-
from platform import system
import numpy
import math
import glob
import sys
import os

import scripts.world as world
import scripts.util as util

from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

operating_system = system()
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import *
import pygame


class Window:
    def __init__(self, caption):
        # Load options
        self.options_default: dict = {
            "enableVsync": True,
            "maxFps": 1000,
            "particles": 1,
            "map buffers": True,
            "antialiasing": 16,
            "resolution": 2,
            "post processing": True,
            "show fps": False,
            "show debug": False,
            "key.left": "a",
            "key.right": "d",
            "key.jump": "space",
            "key.sprint": "left shift",
            "key.return": "escape",
        }
        self.options: dict = self.load_options()

        # Callbacks
        self.callback_quit = None

        # Init pygame
        pygame.init()

        # Explicitly use OpenGL 3.3 core (4.1 core also works)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                        pygame.GL_CONTEXT_PROFILE_CORE)

        # MacOS support
        if operating_system == "Darwin":
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

        # antialiasing
        if self.options["antialiasing"]:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, self.options["antialiasing"])
        else:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)

        # Events
        self.keys: dict = dict.fromkeys([value for key, value in self.options.items() if key.startswith("key.")], 0) # 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.unicode: str = ""                    # Backspace = "\x08"
        self.mouse_buttons: [int] = [0, 0, 0]     # Left, Middle, Right | 0 = Not pressed | 1 = Got pressed | 2 = Is pressed
        self.mouse_pos: [int] = (0, 0, 0, 0)      # x, y, relx, rely
        self.mouse_wheel: [int] = [0, 0, 0, 0]    # x, y, relx, rely
        self.fps: int = 0
        self.delta_time: float = 1.0
        self.time: float = 0.0
        self.animation_speed = 0.3

        # Key press states
        if operating_system == "Darwin":
            self.mod_names = {
                pygame.__dict__[identifier]: identifier[4:].replace("_R", "Right ").replace("_L", "Left ").replace("_", "").replace("META", "Cmd").title()
                for index, identifier in enumerate(pygame.__dict__.keys())
                if identifier.startswith("KMOD_") and not identifier[5:] in ("NONE", "CTRL", "SHIFT", "ALT", "GUI", "META")
            }
        else:
            self.mod_names = {
                pygame.__dict__[identifier]: identifier[4:].replace("_R", "Right ").replace("_L", "Left ").replace("_", "").title()
                for index, identifier in enumerate(pygame.__dict__.keys())
                if identifier.startswith("KMOD_") and not identifier[5:] in ("NONE", "CTRL", "SHIFT", "ALT", "GUI", "META")
            }
        self.key_names = [pygame.__dict__[identifier] for identifier in pygame.__dict__.keys() if identifier.startswith("K_")]
        self.get_keys_all = pygame.key.get_pressed
        self.get_keys_all = pygame.key.get_mods
        self.get_key_name = pygame.key.name
        self.get_mod_name = lambda mod: self.mod_names[mod]

        # Window variables
        info = pygame.display.Info()
        self.screen_size = info.current_w, info.current_h
        self.width, self.height = self.size = self.pre_fullscreen = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.fullscreen = False
        self.wireframe = False
        self.resize_supress = False
        self.stencil_rect = None
        self.refresh = False

        # Window
        flags = DOUBLEBUF | RESIZABLE | OPENGL
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.options["enableVsync"])
        self.clock = pygame.time.Clock()
        self.camera: Camera = Camera(self)
        self.world_view = numpy.zeros((0, 0))
        pygame.display.set_caption(caption)
        pygame.key.set_repeat(1000, 10)
        
        # OpenGL setup
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        if self.options["antialiasing"]:
            glEnable(GL_MULTISAMPLE)
        else:
            glDisable(GL_MULTISAMPLE)

        # Create vertex array object
        self.instance_vao = glGenVertexArrays(1)
        glBindVertexArray(self.instance_vao)

        # Create vertex buffer objects
        self.vertices_vbo, self.ebo, self.dest_vbo, self.source_or_color_vbo, self.shape_transform_vbo = glGenBuffers(5)

        # Instanced shader inputs
        self.vbo_instances_length = 0
        self.vbo_instances_index = 0
  
        self.dest_vbo_array = numpy.zeros(0, dtype=numpy.float32)
        self.source_or_color_vbo_array = numpy.zeros(0, dtype=numpy.float32)
        self.shape_transform_vbo_array = numpy.zeros(0, dtype=numpy.float32)
        self.render_buffers_mapped = False

        # Vertices & texcoords
        vertices = numpy.array([
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            -1.0, 1.0, 0.0, 1.0,   # top-left
            1.0, 1.0, 1.0, 1.0,    # top-right
            1.0, -1.0, 1.0, 0.0    # bottom-right
        ], dtype=numpy.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertices_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        
        # Create element buffer object (EBO) for indices
        indices = numpy.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=numpy.uint32)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, (GLuint * len(indices))(*indices), GL_STATIC_DRAW)

        # Create vertex buffer objects (VBOs) for draw data
        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.dest_vbo_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(2, 1)

        glEnableVertexAttribArray(3)
        glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.source_or_color_vbo_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(3, 1)

        glEnableVertexAttribArray(4)
        glBindBuffer(GL_ARRAY_BUFFER, self.shape_transform_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self.shape_transform_vbo_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(4, 1)

        # Atlas texture (contains images)
        self.atlas_rects, self.atlas_images, image = TextureAtlas.loadImages()
        self.texAtlas = self.texture(image)

        # Font texture (contains letter images)
        #self.font_rects, image = Font.fromPNG(util.File.path("data/fonts/font.png"))
        self.font_rects, image = Font.fromSYS(None, size=30, bold=True, antialias=True, lower=True)
        self.texFont = self.texture(image)

        # Block texture (contains block images)
        self.block_indices, image = TextureAtlas.loadBlocks()
        self.texBlocks = self.texture(image)

        # World texture (contains map data)
        self.world_size = (0, 0)
        self.texWorld = None
        
        # Instance shader
        vertPath: str = util.File.path("scripts/shaders/instance.vert")
        fragPath: str = util.File.path("scripts/shaders/instance.frag")
        self.instance_shader = Shader(
            vertPath, fragPath, replace={"block." + key: value for key, value in self.block_indices.items()},
            texAtlas="int", texFont="int", texBlocks="int", texWorld="int", offset="vec2", resolution="int", time="float")
        self.instance_shader.setvar("texAtlas", 0)
        self.instance_shader.setvar("texFont", 1)
        self.instance_shader.setvar("texBlocks", 2)
        self.instance_shader.setvar("texWorld", 3)
        self.instance_shader.setvar("resolution", self.camera.resolution)

    def add_vbo_instance(self, dest, source_or_color, shape_transform):
        """
        Queue a object to be drawn on the screen and resize buffers as necessary.
        """
        if (not self.render_buffers_mapped) and self.options["map buffers"]:
            return

        if self.vbo_instances_length == self.vbo_instances_index: # Resize all instanced vbos
            self.vbo_instances_length = int(1 + self.vbo_instances_length * 1.5)

            new_dest_vbo_array = numpy.zeros(self.vbo_instances_length * 4, dtype=numpy.float32)
            new_dest_vbo_array[:len(self.dest_vbo_array)] = self.dest_vbo_array
            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            if self.options["map buffers"]:
                glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            glBufferData(GL_ARRAY_BUFFER, new_dest_vbo_array.nbytes, new_dest_vbo_array, GL_DYNAMIC_DRAW)
            if self.options["map buffers"]:
                address = glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
                self.dest_vbo_array = (GLfloat * len(new_dest_vbo_array)).from_address(address)
            else:
                self.dest_vbo_array = new_dest_vbo_array
 
            new_source_or_color_vbo_array = numpy.zeros(self.vbo_instances_length * 4, dtype=numpy.float32)
            new_source_or_color_vbo_array[:len(self.source_or_color_vbo_array)] = self.source_or_color_vbo_array
            glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
            if self.options["map buffers"]:
                glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            glBufferData(GL_ARRAY_BUFFER, new_source_or_color_vbo_array.nbytes, new_source_or_color_vbo_array, GL_DYNAMIC_DRAW)
            if self.options["map buffers"]:
                address = glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
                self.source_or_color_vbo_array = (GLfloat * len(new_source_or_color_vbo_array)).from_address(address)
            else:
                self.source_or_color_vbo_array = new_source_or_color_vbo_array

            new_shape_transform_vbo_array = numpy.zeros(self.vbo_instances_length * 4, dtype=numpy.float32)
            new_shape_transform_vbo_array[:len(self.shape_transform_vbo_array)] = self.shape_transform_vbo_array
            glBindBuffer(GL_ARRAY_BUFFER, self.shape_transform_vbo)
            if self.options["map buffers"]:
                glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            glBufferData(GL_ARRAY_BUFFER, new_shape_transform_vbo_array.nbytes, new_shape_transform_vbo_array, GL_DYNAMIC_DRAW)
            if self.options["map buffers"]:
                address = glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
                self.shape_transform_vbo_array = (GLfloat * len(new_shape_transform_vbo_array)).from_address(address)
            else:
                self.shape_transform_vbo_array = new_shape_transform_vbo_array

        self.dest_vbo_array[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = dest
        self.source_or_color_vbo_array[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = source_or_color
        self.shape_transform_vbo_array[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4] = numpy.array(shape_transform, dtype=numpy.float32)
        #print(self.shape_transform_vbo_array[4 * self.vbo_instances_index:4 * self.vbo_instances_index + 4])
        
        self.vbo_instances_index += 1

    def get_pressed_keys(self):
        keys = pygame.key.get_pressed()
        return [pygame.key.name(i).title() for i in self.key_names if keys[i]]

    def get_pressed_mods(self):
        mods = pygame.key.get_mods()
        return [self.mod_names[mod] for mod in self.mod_names if mods & mod]

    def resize(self):
        if self.fullscreen:
            flags = FULLSCREEN
        else:
            flags = DOUBLEBUF | RESIZABLE

        # Called twice, because of VSYNC...
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL)
        self.window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL, vsync=self.options["enableVsync"])
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
        """
        Update the window and inputs.
        """
        # Update pygame
        self.events()
        self.clock.tick(self.options["maxFps"])
        self.fps = self.clock.get_fps()
        self.delta_time = (1 / self.fps) if self.fps > 0 else self.delta_time
        self.time += self.delta_time

        # Reset
        glClear(GL_COLOR_BUFFER_BIT)

        # Use VAO
        glBindVertexArray(self.instance_vao)

        # Use instance shader
        self.instance_shader.activate()

        # Send variables to shader
        self.update_world()
        self.instance_shader.update()

        # Bind textures
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texAtlas)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.texFont)

        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.texBlocks)

        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, self.texWorld)

        # Send instance data to shader
        if not self.options["map buffers"]:
            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.dest_vbo_array.nbytes, self.dest_vbo_array)
            glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.source_or_color_vbo_array.nbytes, self.source_or_color_vbo_array)
            glBindBuffer(GL_ARRAY_BUFFER, self.shape_transform_vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.shape_transform_vbo_array.nbytes, self.shape_transform_vbo_array)
        elif self.render_buffers_mapped:
            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            dest_vbo_size = len(self.dest_vbo_array)
            glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)

            glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
            source_or_color_vbo_size = len(self.source_or_color_vbo_array)
            glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)

            glBindBuffer(GL_ARRAY_BUFFER, self.shape_transform_vbo)
            shape_transform_vbo_size = len(self.shape_transform_vbo_array)
            glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            self.render_buffers_mapped = True
        else:
            dest_vbo_size = source_or_color_vbo_size = shape_transform_vbo_size = 0
            self.render_buffers_mapped = True

        # Draw
        glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, self.vbo_instances_index)
        if self.refresh:
            pygame.display.flip()
        else:
            self.refresh = True

        # Reset buffers
        if self.options["map buffers"]:
            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            address = glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            if dest_vbo_size:
                self.dest_vbo_array = (GLfloat * dest_vbo_size).from_address(address)
            else:
                self.dest_vbo_array = numpy.zeros(0, dtype=numpy.float32)

            glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
            address = glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            if source_or_color_vbo_size:
                self.source_or_color_vbo_array = (GLfloat * source_or_color_vbo_size).from_address(address)
            else:
                self.source_or_color_vbo_array = numpy.zeros(0, dtype=numpy.float32)

            glBindBuffer(GL_ARRAY_BUFFER, self.shape_transform_vbo)
            address = glMapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            if shape_transform_vbo_size:
                self.shape_transform_vbo_array = (GLfloat * shape_transform_vbo_size).from_address(address)
            else:
                self.shape_transform_vbo_array = numpy.zeros(0, dtype=numpy.float32)

        # Reset instance index
        self.vbo_instances_index = 0

        # Move camera
        self.camera.update() # Better at the start, but currently at the end for sync of world and instanced rendering

        # Draw background and world
        self.instance_shader.setvar("time", self.time / self.animation_speed)
        self.add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (4, 0, 0, 0))

    def toggle_fullscreen(self):
        """
        Toggle between fullscreen and normal mode.
        """
        self.fullscreen = not self.fullscreen
        self.resize_supress = True
        self.refresh = False

        if self.fullscreen:
            self.pre_fullscreen = self.size
            self.width, self.height = self.size = self.screen_size
        else:
            self.width, self.height = self.size = self.pre_fullscreen

        self.resize()

    def toggle_wire_frame(self):
        """
        Toggle between drawing only outlines and filled shapes.
        """
        self.wireframe = not self.wireframe
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def toggle_map_buffers(self):
        """
        Toggle mapping buffers for drawing.
        """
        if self.options["map buffers"]:
            glBindBuffer(GL_ARRAY_BUFFER, self.dest_vbo)
            glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            glBindBuffer(GL_ARRAY_BUFFER, self.source_or_color_vbo)
            glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
            glBindBuffer(GL_ARRAY_BUFFER, self.shape_transform_vbo)
            glUnmapBuffer(GL_ARRAY_BUFFER, GL_WRITE_ONLY)
    
        self.options["map buffers"] = not self.options["map buffers"]
        self.render_buffers_mapped = False
        self.dest_vbo_array = numpy.array([], dtype=numpy.float32)
        self.source_or_color_vbo_array = numpy.array([], dtype=numpy.float32)
        self.shape_transform_vbo_array = numpy.array([], dtype=numpy.float32)
        self.vbo_instances_length = 0
        self.vbo_instances_index = 0
        self.refresh = False

    def set_antialiasing(self, level):
        """
        Toggle antialiasing.
        """
        self.options["antialiasing"] = level
        if self.options["antialiasing"]:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, self.options["antialiasing"])
            glEnable(GL_MULTISAMPLE)
        else:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
            glDisable(GL_MULTISAMPLE)
        self.resize()

    def set_resolution(self, resolution):
        self.options["resolution"] = resolution
        self.camera.resultion = resolution
        self.camera.pixels_per_meter = resolution * 16
        self.instance_shader.setvar("resolution", resolution)
        
    def load_options(self):
        """
        Loads the options from the options.txt file.
        """
        options = self.options_default.copy()

        try:
            with open(util.File.path("data/user/options.txt"), "r") as file:
                options_string = file.read()
        except:
            options_string = ""

        for line in options_string.split("\n"):
            keyword = line.split(":")[0].strip()
            if not keyword in options or len(line.split(":")) != 2:
                continue
            value = line.split(":")[1].strip()
            if value.isdecimal():
                value = int(value)
            elif value.replace(".", "", 1).isdecimal():
                value = float(value)
            elif (value in ("True", "False") or
                  value.count("\"") == 2 and value[0] == value[-1] == "\"" or
                  value.count("'") == 2 and value[0] == value[-1] == "'"):
                value = eval(value)
            else:
                raise ValueError("Invalid value (\"" + str(value) + "\") for " + keyword)
            if ((isinstance(options[keyword], (int, bool)) and not isinstance(value, (int, bool))) or
                (isinstance(options[keyword], float) and not isinstance(value, (float, int, bool))) or
                (isinstance(options[keyword], str) and not isinstance(value, str))):
                raise ValueError("Invalid value type (\"" + str(value) + "\") for " + keyword)
            options[keyword] = value
                  
        return options

    def save_options(self):
        """
        Save the options in the options.txt file.
        """
        options_string = ""
        for key, value in self.options.items():
            if isinstance(value, str):
                options_string += str(key) + ": \"" + str(value) + "\"\n"
            else:
                options_string += str(key) + ": " + str(value) + "\n"

        with open(util.File.path("data/user/options.txt"), "w") as file:
            file.write(options_string)

    def keybind(self, key):
        """
        Returns the state of an action key.
        """
        return self.keys[self.options["key." + key]]

    def callback(self, function):
        if not function is None:
            function()

    def quit(self):
        """
        Quit the program
        """
        # Quit callback
        self.callback(self.callback_quit)

        # OpenGL cleanup
        glDeleteBuffers(5, (self.vertices_vbo, self.ebo, self.dest_vbo, self.source_or_color_vbo, self.shape_transform_vbo))
        glDeleteVertexArrays(1, (self.instance_vao,))
        glDeleteTextures(4, (self.texAtlas, self.texFont, self.texBlocks, self.texWorld))
        self.instance_shader.delete()

        # Save options
        self.save_options()

        # Quit
        pygame.quit()
        sys.exit()
    
    def texture(self, image, blur=False):
        """
        Create a texture from an image.
        """
        data = pygame.image.tostring(image, "RGBA", 1)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *image.get_size(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        if blur:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        glBindTexture(GL_TEXTURE_2D, 0)
        return texture

    def update_world(self, blur=0):
        """
        Update the world texture.
        """
        start = (int(self.camera.pos[0]) - math.floor(self.width / 2 / self.camera.pixels_per_meter) - 2,  # ideal start to render
                 int(self.camera.pos[1]) - math.floor(self.height / 2 / self.camera.pixels_per_meter) - 2)

        chunk_start = (start[0] // world.CHUNK_SIZE * world.CHUNK_SIZE, # round down to chunk corner
                       start[1] // world.CHUNK_SIZE * world.CHUNK_SIZE)

        offset = (self.camera.pos[0] % 1 + (start[0] - chunk_start[0]) % world.CHUNK_SIZE # final offset of world in blocks
                    - (self.width / 2) % self.camera.pixels_per_meter / self.camera.pixels_per_meter + 2 - int(self.camera.pos[0] < 0),
                  self.camera.pos[1] % 1 + (start[1] - chunk_start[1]) % world.CHUNK_SIZE
                    - (self.height / 2) % self.camera.pixels_per_meter / self.camera.pixels_per_meter + 2 - int(self.camera.pos[1] < 0))
        self.instance_shader.setvar("offset", *offset) 

        # View size
        size = self.world_view.shape
        data = numpy.transpose(self.world_view) # flip axis
        self.world_view = numpy.zeros((0, 0))
        if self.world_size != size:
            if not self.texWorld is None:
                glDeleteTextures(1, (self.texWorld,))
                self.texWorld = None
            self.world_size = size
        
        if self.texWorld is None: # Generate texture if necessary
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_R32I, *self.world_size, 0, GL_RED_INTEGER, GL_INT, data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glBindTexture(GL_TEXTURE_2D, 0)
            self.texWorld = texture
        else: # Write world data into texture
            glBindTexture(GL_TEXTURE_2D, self.texWorld)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_R32I, *self.world_size, 0, GL_RED_INTEGER, GL_INT, data)
    
    def draw_image(self, image, position, size, angle=0, flip=(0, 0)):
        """
        Draw an image on the window.
        """
        animation_frames, rect_index = self.atlas_images[image]
        frame = int((self.time / self.animation_speed) % animation_frames)
        rect = self.atlas_rects[rect_index + frame]

        dest_rect = (position[0] + size[0] / 2, position[1] + size[1] / 2, size[0] / 2, size[1] / 2)
        if not self.stencil_rect is None:
            org = dest_rect[:]

            left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
            right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
            top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
            bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

            width = (right - left) / 2
            height = (bottom - top) / 2

            if width > 0 and height > 0:
                dest_rect = [left + width, top + height, width, height]
                self.add_vbo_instance(dest_rect, rect, (0, *flip, angle / 180 * math.pi))
        else:
            self.add_vbo_instance(dest_rect, rect, (0, *flip, angle / 180 * math.pi))

    def draw_rect(self, position, size, color):
        """
        Draw a rectangle on the window.
        """
        dest_rect = (position[0] + size[0] / 2, position[1] + size[1] / 2, size[0] / 2, size[1] / 2)
        if not self.stencil_rect is None:
            org = dest_rect[:]

            left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
            right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
            top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
            bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

            width = (right - left) / 2
            height = (bottom - top) / 2

            if width > 0 and height > 0:
                dest_rect = [left + width, top + height, width, height]
                self.add_vbo_instance(dest_rect, self.camera.map_color(color), (1, 0, 0, 0))
        else:
            self.add_vbo_instance(dest_rect, self.camera.map_color(color), (1, 0, 0, 0))

    def draw_circle(self, position, radius, color):
        """
        Draw a circle on the window.
        """
        self.add_vbo_instance((*position, radius / self.width * self.screen_size[1], radius / self.height * self.screen_size[1]), self.camera.map_color(color), (2, 0, 0, 0))

    def draw_text(self, position, text, color, size=1, centered=False, spacing=1.25, fixed_size=1):
        """
        Draw text on the window.
        fixed_size: 0 = stretch, 1 = relational size on both axis, 2 = fixed size
        """
        offset = 0
        x_factor_fixed = 1 / self.width * self.screen_size[0]
        y_factor_fixed = 1 / self.height * self.screen_size[1]
        y_factor_relational = 1 / self.height * self.screen_size[1] * self.width / self.screen_size[0]
        if len(color) == 3:
            color = (*color, 255)

        if centered:
            for letter in text:
                if not letter in self.font_rects and letter.isalpha():
                    if letter.upper() in self.font_rects:
                        letter = letter.upper()
                    else:
                        letter = letter.lower()
                if not letter in self.font_rects:
                    letter = "?"
                if fixed_size < 2:
                    offset -= self.font_rects[letter][1] * spacing * size
                else:
                    offset -= self.font_rects[letter][1] * spacing * size * x_factor_fixed

            for letter in text:
                if not letter in self.font_rects and letter.isalpha():
                    if letter.upper() in self.font_rects:
                        letter = letter.upper()
                    else:
                        letter = letter.lower()
                if not letter in self.font_rects:
                    letter = "?"

                rect = self.font_rects[letter]
                if fixed_size == 0:
                    offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + offset + rect[1], position[1], rect[1] * size, rect[2] * 2 * size]
                    offset += rect[1] * spacing * size * 1.5
                elif fixed_size == 1:
                    offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + offset + rect[1], position[1], rect[1] * size, rect[2] * 2 * size * y_factor_relational]
                    offset += rect[1] * spacing * size * 1.5
                else:
                    offset += rect[1] * spacing * size * x_factor_fixed * 0.5
                    dest_rect = [position[0] + offset + rect[1], position[1], rect[1] * size * x_factor_fixed, rect[2] * 2 * size * y_factor_fixed]
                    offset += rect[1] * spacing * size * x_factor_fixed * 1.5
                
                if not self.stencil_rect is None:
                    org = dest_rect[:]

                    left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
                    right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
                    top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
                    bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

                    width = (right - left) / 2
                    height = (bottom - top) / 2

                    if width > 0 and height > 0:
                        dest_rect = [left + width, top + height, width, height]
                        source_and_color = (color[0] + rect[0] + rect[1] * ((1 - dest_rect[2] / org[2]) if dest_rect[0] > org[0] else 0),
                                            color[1] + (round(1 - dest_rect[3] / org[3], 6) if dest_rect[1] > org[1] else 0),
                                            color[2] + rect[1] * (width / org[2]) - 0.00001,
                                            color[3] + ((height / org[3]) if (height / org[3]) < 1 else 0))
                        self.add_vbo_instance(dest_rect, source_and_color, (3, 0, 0, 0))
                        
                else:
                    source_and_color = (color[0] + rect[0], color[1], color[2] + rect[1] - 0.00001, color[3])
                    self.add_vbo_instance(dest_rect, source_and_color, (3, 0, 0, 0))
        else:
            for letter in text:
                if not letter in self.font_rects and letter.isalpha():
                    if letter.upper() in self.font_rects:
                        letter = letter.upper()
                    else:
                        letter = letter.lower()
                if not letter in self.font_rects:
                    letter = "?"

                rect = self.font_rects[letter]
                source_and_color = (color[0] + rect[0], color[1], color[2] + rect[1] - 0.00001, color[3])
                if fixed_size == 0:
                    offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + offset + rect[1], position[1] - rect[2] * 2, rect[1] * size, rect[2] * 2 * size]
                    offset += rect[1] * spacing * size * 1.5
                elif fixed_size == 1:
                    offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + offset + rect[1], position[1] - rect[2] * 2, rect[1] * size, rect[2] * 2 * size * y_factor_relational]
                    offset += rect[1] * spacing * size * 1.5
                else:
                    offset += rect[1] * spacing * size * x_factor_fixed * 0.5
                    dest_rect = [position[0] + offset + rect[1], position[1] - rect[2] * 2, rect[1] * size * x_factor_fixed, rect[2] * 2 * size * y_factor_fixed]
                    offset += rect[1] * spacing * size * x_factor_fixed * 1.5

                if not self.stencil_rect is None:
                    org = dest_rect[:]

                    left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
                    right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
                    top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
                    bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

                    width = (right - left) / 2
                    height = (bottom - top) / 2

                    if width > 0 and height > 0:
                        dest_rect = [left + width, top + height, width, height]
                        source_and_color = (color[0] + rect[0] + rect[1] * (1 - dest_rect[0] / org[0]), color[1] + (1 - dest_rect[1] / org[1]), color[2] + rect[1] * (width / org[2]) - 0.00001, color[3] + ((height / org[3]) if (height / org[3]) < 1 else 0))
                        self.add_vbo_instance(dest_rect, source_and_color, (3, 0, 0, 0))
                else:
                    self.add_vbo_instance(dest_rect, source_and_color, (3, 0, 0, 0))

        return offset

    def draw_post_processing(self):
        self.add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (5, 0, 0, 0))

class TextureAtlas:
    def loadBlocks():
        """
        Load block texture atlas from files in a folder.
        """
        paths = glob.glob(util.File.path("data/blocks/**/*.png"), recursive=True)
        width = math.ceil(math.sqrt(len(paths)))
        height = math.ceil(len(paths) / width)
        image = pygame.Surface((width * 16, height * 16 + 1), SRCALPHA)
        block_indices = {}
        animation_frames = {}

        for i, path in enumerate(paths):
            y, x = divmod(i, width)
            file_name = os.path.basename(path).split(".")
            if len(file_name) == 2:
                block = file_name[0]
                frame = 1
            else:
                block = file_name[0]
                frame = int(file_name[1])
            if not block in animation_frames:
                block_indices[block] = i + 1
            block_surface = pygame.image.load(path)
            image.blit(block_surface, (x * 16, (height - y - 1) * 16))
            animation_frames[block] = max(animation_frames.get(block, 1), frame)
            
        x = 0
        for block in animation_frames:
            image.set_at((x, height * 16), (animation_frames[block], 0, 0))
            x += animation_frames[block]

        pygame.image.save(image, util.File.path("data/blocks.png"))
        return block_indices, image

    def loadImages():
        """
        Load image texture atlas from files in a folder.
        """
        try:        
            with open(util.File.path("data/images/images.properties"), "r") as file:
                images_data = file.readlines()
        except:
            raise ValueError("Could not find file data/images/images.properties")

        image_rects = [] # list of rects
        images = {} # "image": [rect_index, animation_frames]
        paths = {}

        width = 0
        height = 0

        for image_data in images_data:
            name, data = image_data.replace(" ", "").split(":")
            file_name = name.split(".")
            if len(file_name) == 1:
                image = file_name[0]
                frame = 1
            else:
                image = file_name[0]
                frame = int(file_name[1])
            rect = tuple([float(x) for x in data.replace("(", "").replace(")", "").split(",")])
            if frame == 1 or not image in images:
                images[image] = [1, len(image_rects)]
            else:
                images[image][0] = max(images[image][0], frame)

            width = max(width, rect[0] + rect[2])
            height = max(height, rect[1] + rect[3])
            
            image_path = glob.glob(util.File.path("data/images/**/" + name + ".png"), recursive=True)
            if not len(image_path):
                raise ValueError("Could not find file " + name + ".png in data/images")

            paths[str(image_path[0])] = len(image_rects)
            image_rects.append(rect)

        image = pygame.Surface((width, height), SRCALPHA)

        for image_path, i in paths.items():
            image.blit(pygame.image.load(util.File.path(image_path)), (image_rects[i][0], image_rects[i][1]))
            image_rects[i] = (image_rects[i][0] / width, 1 - image_rects[i][1] / height - image_rects[i][3] / height, image_rects[i][2] / width, image_rects[i][3] / height)

        pygame.image.save(image, util.File.path("data/images.png"))

        return image_rects, images, image


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

    def fromTTF(path, size=1, antialias=False, lower=True):
        """
        Load a font from a TrueTypeFont file.
        """
        font = pygame.font.Font(path, size)
        images = []
        letters = {}
        if lower: # upper letters :96 | lower letters :123
            limit = 123
        else:
            limit = 96

        font_height = font.render("".join([chr(i) for i in range(32, limit)]), antialias, (0, 0, 0)).get_height()
        font_width = 0

        space = font.render("A", antialias, (0, 0, 0))

        for i in range(32, limit):
            letter = chr(i)
            if letter != " ":
                image = font.render(letter, antialias, (255, 255, 255))
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

    def fromSYS(name, size=1, bold=False, antialias=False, lower=True):
        """
        Load a font from the system.
        """
        font = pygame.font.SysFont(name, size, bold=bold)
        images = []
        letters = {}
        if lower: # upper letters 32:96 | upper & lower letters 32:123
            limit = 123
        else:
            limit = 96

        font_height = font.render("".join([chr(i) for i in range(32, limit)]), antialias, (0, 0, 0)).get_height()
        font_width = 0

        space = font.render("A", antialias, (0, 0, 0))
        for i in range(32, limit):
            letter = chr(i)
            if letter != " ":
                image = font.render(letter, antialias, (255, 255, 255))
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


class Shader:
    active = None

    def __init__(self, vertex, fragment, replace={}, **variables):
        self.program = glCreateProgram()
        
        with open(vertex, "r") as file:
            content = file.read()
            for search, replacement in replace.items():
                content = content.replace(str(search), str(replacement))
            vertex_shader = compileShader(content, GL_VERTEX_SHADER)
        with open(fragment, "r") as file:
            content = file.read()
            for search, replacement in replace.items():
                content = content.replace(str(search), str(replacement))
            fragment_shader = compileShader(content, GL_FRAGMENT_SHADER)
        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)
        glLinkProgram(self.program)
        glValidateProgram(self.program)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        # Dict containing all variables which should be send to the fragment shader {variable1: (uniformLoc, glUniformFunc, value)}
        self.variables = {variable: Shader.get_uniform_loc(self.program, variable, variables[variable]) for variable in variables}

    def setvar(self, variable, *value):
        """
        Set the value of a variable, which is send to the shader by update
        """
        self.variables[variable][2] = value

    def activate(self):
        """
        Activate the shader.
        """
        glUseProgram(self.program)
        Shader.active = self

    def delete(self):
        """
        Delete the shader.
        """
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

    def update(self):
        """
        Update all variables.
        """
        for index, (loc, func, value) in self.variables.items():
            if value is None:
                continue
            func(loc, *value)
            self.variables[index][2] = None


class Camera:
    def __init__(self, window):
        self.resolution: int = window.options["resolution"]
        self.pixels_per_meter: int = window.options["resolution"] * 16
        self.threshold = 0.1

        self.pos: [float] = [0, 0]
        self.vel: [float] = [0, 0]
        self.dest: [float] = [0, 0]
        self.window: Window = window

    def set(self, pos):
        """
        Set the camera position.
        Use move() for slow movement.
        """
        self.pos = pos
        self.vel = [0, 0]
        self.dest = pos

    def move(self, pos: [float]):
        """
        Move the camera slowly to a position.
        Use set() for instant movement.
        """
        self.dest = pos

    def update(self):
        """
        Update the camera.
        """
        xvel = round((self.dest[0] - self.pos[0]) / 10, 3)
        yvel = round((self.dest[1] - self.pos[1]) / 10, 3)

        xvel = math.copysign(max(abs(xvel) - self.threshold, 0), xvel)
        yvel = math.copysign(max(abs(yvel) - self.threshold, 0), yvel)

        self.vel[0] = xvel
        self.vel[1] = yvel
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def map_coord(self, coord: [float], from_pixel: bool=True, from_centered: bool=True, from_world: bool=False, pixel: bool=False, centered: bool=True, world: bool=False):
        """
        Convert a coordinate to a different format.
        Current format specified by from_pixel, from_centered, from_world.
        Output format specified by pixel, centered, world.
        """
        if from_world:
            from_pixel = True
        if world:
            pixel = True
        coord = list(coord)

        if from_world and not world:
            for i in range(len(coord)):
                if i < 2:
                    coord[i] = (coord[i] - self.pos[i]) * self.pixels_per_meter
                else:
                    coord[i] = coord[i] * self.pixels_per_meter
        elif (not from_world) and world:
            for i in range(len(coord)):
                coord[i] = coord[i] / self.pixels_per_meter + self.pos[i % 2]

        if from_pixel and not pixel:
            for i in range(len(coord)):
                coord[i] /= (self.window.width, self.window.height)[i%2] / 2
        elif (not from_pixel) and pixel:
            for i in range(len(coord)):
                coord[i] /= (self.window.width, self.window.height)[i%2] / 2

        if (not from_centered) and centered:
            for i in range(2):
                coord[i] -= 1
        elif from_centered and not centered:
            for i in range(2):
                coord[i] += 1

        return coord

    def map_color(self, color):
        if not float in color:
            color = [i / 255 for i in color]
        if len(color) == 3:
            color = (*color, 1)
        return color

    def visible_blocks(self):
        center = (int(self.pos[0]),
                  int(self.pos[1]))
        start = (center[0] - math.floor(self.window.width / 2 / self.pixels_per_meter) - 2,
                 center[1] - math.floor(self.window.height / 2 / self.pixels_per_meter) - 2)
        end = (center[0] + math.ceil(self.window.width / 2 / self.pixels_per_meter) + 2,
               center[1] + math.ceil(self.window.height / 2 / self.pixels_per_meter) + 2)
        return start, end