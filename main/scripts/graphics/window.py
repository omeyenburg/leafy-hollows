# -*- coding: utf-8 -*-
from OpenGL.GL import *
import numpy
import math
import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from scripts.graphics.image import load_blocks, load_sprites, get_sprite_rect
from scripts.graphics.camera import Camera
from scripts.graphics.font import Font
from scripts.shader.shader import Shader
from pygame.locals import *
import scripts.utility.options as options
import scripts.game.world as world
import scripts.utility.util as util
import scripts.utility.file as file
import pygame


class Window:
    def __init__(self, caption):
        # Load options
        self.options: dict = options.load()

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
        if util.system == "Darwin":
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
        self.animation_speed: float = 0.3

        # Key press states
        if util.system == "Darwin":
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
        self.world_view = numpy.zeros((0, 0, 4))
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

        # Sprite texture
        image = load_sprites()
        self.texAtlas = self.texture(image)

        # Font texture
        self.font, image = Font(None, size=30, bold=True, antialias=True)
        self.texFont = self.texture(image)

        # Block texture
        self.block_data, image = load_blocks()
        self.texBlocks = self.texture(image)

        # World texture (contains world block data)
        self.world_size = (0, 0)
        self.texWorld = None
        
        # Instance shader
        self.instance_shader = Shader(
            "scripts/shader/vertex.glsl", "scripts/shader/fragment.glsl",
            replace={"block." + key: value for key, (value, *_) in self.block_data.items()},
            texAtlas="int", texFont="int", texBlocks="int", texWorld="int", offset="vec2", resolution="int", time="float"
        )

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
                if util.system == "Darwin":
                    key = key.replace("meta", "cmd")
                if key in self.keys:
                    self.keys[key] = 1
            elif event.type == KEYUP:
                key = pygame.key.name(event.key)
                if util.system == "Darwin":
                    key = key.replace("meta", "cmd")
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

    def set_antialiasing(self, level: int):
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
        options.save(self.options)

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
        # Drawing offset of world in blocks
        offset = (self.camera.pos[0] % 1
                    - (self.width / 2) % self.camera.pixels_per_meter / self.camera.pixels_per_meter + 2 - int(self.camera.pos[0] < 0),
                  self.camera.pos[1] % 1
                    - (self.height / 2) % self.camera.pixels_per_meter / self.camera.pixels_per_meter + 2 - int(self.camera.pos[1] < 0))
        self.instance_shader.setvar("offset", *offset) 

        # View size
        size = self.world_view.shape[:2]        
        data = numpy.array(numpy.swapaxes(self.world_view, 0, 1), dtype=numpy.int32)
        self.world_view = numpy.zeros((0, 0, 4))
        if self.world_size != size:
            if not self.texWorld is None:
                glDeleteTextures(1, (self.texWorld,))
                self.texWorld = None
            self.world_size = size
        
        if self.texWorld is None: # Generate texture if necessary
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32I, *self.world_size, 0, GL_RGBA_INTEGER, GL_INT, data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glBindTexture(GL_TEXTURE_2D, 0)
            self.texWorld = texture
        else: # Write world data into texture
            glBindTexture(GL_TEXTURE_2D, self.texWorld)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32I, *self.world_size, 0, GL_RGBA_INTEGER, GL_INT, data)
    
    def draw_image(self, image: str, position: [float], size: [float], angle: float=0.0, flip: [int]=(0, 0)):
        """
        Draw an image on the window.
        """
        rect = get_sprite_rect(image, self.time)

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

    def draw_rect(self, position: [float], size: [float], color: [int]):
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

    def draw_circle(self, position: [float], radius: int, color: [int]):
        """
        Draw a circle on the window.
        """
        self.add_vbo_instance((*position, radius / self.width * self.screen_size[1], radius / self.height * self.screen_size[1]), self.camera.map_color(color), (2, 0, 0, 0))

    def draw_line(self, start: [float], end: [float], width: int, color: [int]):
        """
        Draw a line on the window.
        """
        center = ((start[0] + end[0]) / 2,  (start[1] + end[1]) / 2)
        angle = math.atan2(start[1] - end[1], start[0] - end[0])
        sinAngle = abs(math.sin(angle))
        size = (math.sqrt(((start[0] - end[0]) / 2) ** 2 + ((start[1] - end[1]) / 2) ** 2),
                width / self.width * sinAngle + width / self.height * (1 - sinAngle))
        self.add_vbo_instance((*center, *size), self.camera.map_color(color), (1, 0, 0, angle))

    def draw_text(self, position: [float], text: str, color: [int], size: int=1, centered: bool=False, spacing: float=1.25, fixed_size: int=1, wrap: float=None):
        """
        Draw text on the window.
        fixed_size: 0 = stretch, 1 = relational size on both axis, 2 = fixed size
        Centered text cannot be wrapped.
        """
        x_offset = 0
        y_offset = 0
        x_factor_fixed = 1 / self.width * self.screen_size[0]
        y_factor_fixed = 1 / self.height * self.screen_size[1]
        y_factor_relational = 1 / self.height * self.screen_size[1] * self.width / self.screen_size[0]
        if len(color) == 3:
            color = (*color, 255)

        if centered:
            for letter in text:
                if fixed_size < 2:
                    x_offset -= self.font.get_rect(letter)[1] * spacing * size
                else:
                    x_offset -= self.font.get_rect(letter)[1] * spacing * size * x_factor_fixed

            for letter in text:
                rect = self.font.get_rect(letter)
                if fixed_size == 0:
                    x_offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + x_offset + rect[1], position[1] + y_offset * rect[2] * 3 * size, rect[1] * size, rect[2] * 2 * size]
                    x_offset += rect[1] * spacing * size * 1.5
                elif fixed_size == 1:
                    x_offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + x_offset + rect[1], position[1] + y_offset * rect[2] * 3 * size * y_factor_relational, rect[1] * size, rect[2] * 2 * size * y_factor_relational]
                    x_offset += rect[1] * spacing * size * 1.5
                else:
                    x_offset += rect[1] * spacing * size * x_factor_fixed * 0.5
                    dest_rect = [position[0] + x_offset + rect[1], position[1] + y_offset * rect[2] * 3 * size * y_factor_fixed, rect[1] * size * x_factor_fixed, rect[2] * 2 * size * y_factor_fixed]
                    x_offset += rect[1] * spacing * size * x_factor_fixed * 1.5
                
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
            line_height = 6

            for letter in text:
                if letter == "\n":
                    x_offset = 0
                    y_offset += 1
                    continue

                rect = self.font.get_rect(letter)
                source_and_color = (color[0] + rect[0], color[1], color[2] + rect[1] - 0.00001, color[3])
                if (not wrap is None) and x_offset + rect[1] * spacing * size * 0.5 + rect[1] * size > wrap:
                    x_offset = 0
                    y_offset += 1
                if fixed_size == 0:
                    x_offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + x_offset + rect[1], position[1] - rect[2] * 2 - y_offset * rect[2] * line_height * size, rect[1] * size, rect[2] * 2 * size]
                    x_offset += rect[1] * spacing * size * 1.5
                elif fixed_size == 1:
                    x_offset += rect[1] * spacing * size * 0.5
                    dest_rect = [position[0] + x_offset + rect[1], position[1] - rect[2] * 2 - y_offset * rect[2] * line_height * size * y_factor_relational, rect[1] * size, rect[2] * 2 * size * y_factor_relational]
                    x_offset += rect[1] * spacing * size * 1.5
                else:
                    x_offset += rect[1] * spacing * size * x_factor_fixed * 0.5
                    dest_rect = [position[0] + x_offset + rect[1], position[1] - rect[2] * 2 - y_offset * rect[2] * line_height * size * y_factor_fixed, rect[1] * size * x_factor_fixed, rect[2] * 2 * size * y_factor_fixed]
                    x_offset += rect[1] * spacing * size * x_factor_fixed * 1.5

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
        
            y_offset += 1
            if fixed_size == 0:
                return x_offset, rect[2] * 2 - y_offset * rect[2] * line_height * size
            elif fixed_size == 1:
                return x_offset, rect[2] * 2 - y_offset * rect[2] * line_height * size * y_factor_relational
            elif fixed_size == 2:
                return x_offset, rect[2] * 2 - y_offset * rect[2] * line_height * size * y_factor_fixed

    def draw_post_processing(self):
        self.add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (5, 0, 0, 0))

    def draw_block_highlight(self, x, y, color):
        if len(color) == 3:
            color = (*color, 100)
        rect = self.camera.map_coord((x, y, 1, 1), from_world=True)
        self.draw_rect(rect[:2], rect[2:], color)
