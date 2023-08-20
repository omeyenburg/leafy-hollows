# -*- coding: utf-8 -*-
from OpenGL.GL import *
import numpy
import math
import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from scripts.graphics.image import load_blocks, load_sprites, get_sprite_rect
from scripts.graphics.shader import Shader
from scripts.graphics.camera import Camera
from scripts.graphics.font import Font
from pygame.locals import *
import scripts.utility.options as options
import scripts.graphics.sound as sound
import scripts.game.world as world
import scripts.utility.util as util
import scripts.utility.file as file
import pygame


_OPENGL_VERSION: str = "3.3 core" # Explicitly use OpenGL 3.3 core (4.1 core also works)


class Window:
    def __init__(self, caption):
        # Load options
        self.options: dict = options.load()

        # Callbacks
        self.callback_quit = None

        # Initialize pygame
        pygame.init()

        # Load sounds
        self.loaded_sounds, self.played_sounds = sound.load()

        # Set OpenGL version
        opengl_major = int(_OPENGL_VERSION.split(".")[0])
        opengl_minor = int(_OPENGL_VERSION.split(".")[1][:1])
        opengl_core = "core" in _OPENGL_VERSION

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, opengl_major)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, opengl_minor)
        if opengl_core:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                            pygame.GL_CONTEXT_PROFILE_CORE)

        # MacOS support
        if util.system == "Darwin":
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

        # Antialiasing
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
        self.resolution: float = 1.0

        # Key press states
        if util.system == "Darwin":
            self._mod_names = {
                pygame.__dict__[identifier]: identifier[4:].replace("_R", "Right ").replace("_L", "Left ").replace("_", "").replace("META", "Cmd").title()
                for index, identifier in enumerate(pygame.__dict__.keys())
                if identifier.startswith("KMOD_") and not identifier[5:] in ("NONE", "CTRL", "SHIFT", "ALT", "GUI", "META")
            }
        else:
            self._mod_names = {
                pygame.__dict__[identifier]: identifier[4:].replace("_R", "Right ").replace("_L", "Left ").replace("_", "").title()
                for index, identifier in enumerate(pygame.__dict__.keys())
                if identifier.startswith("KMOD_") and not identifier[5:] in ("NONE", "CTRL", "SHIFT", "ALT", "GUI", "META")
            }
        self._key_names = [pygame.__dict__[identifier] for identifier in pygame.__dict__.keys() if identifier.startswith("K_")]
        self.get_keys_all = pygame.key.get_pressed
        self.get_keys_all = pygame.key.get_mods
        self.get_key_name = pygame.key.name
        self.get_mod_name = lambda mod: self._mod_names[mod]

        # Window variables
        info = pygame.display.Info()
        self.screen_size = info.current_w, info.current_h
        self.width, self.height = self.size = self.pre_fullscreen = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.stencil_rect = None
        self._fullscreen = False
        self._wireframe = False
        self._resize_supress = False
        self._refresh = False

        # Window
        flags = DOUBLEBUF | RESIZABLE | OPENGL
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.options["enable vsync"])
        self._clock = pygame.time.Clock()
        self.camera: Camera = Camera(self)
        self.world_view: numpy.array = numpy.zeros((0, 0, 4))
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
        self._instance_vao = glGenVertexArrays(1)
        glBindVertexArray(self._instance_vao)

        # Create vertex buffer objects
        self._vertices_vbo, self._ebo, self._dest_vbo, self._source_or_color_vbo, self._shape_transform_vbo = glGenBuffers(5)

        # Instanced shader inputs
        self._vbo_instances_length = 0
        self._vbo_instances_index = 0
  
        self._dest_vbo_array = numpy.zeros(0, dtype=numpy.float32)
        self._source_or_color_vbo_array = numpy.zeros(0, dtype=numpy.float32)
        self._shape_transform_vbo_array = numpy.zeros(0, dtype=numpy.float32)
        self._render_buffers_mapped = False

        # Vertices & texcoords
        vertices = numpy.array([
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            -1.0, 1.0, 0.0, 1.0,   # top-left
            1.0, 1.0, 1.0, 1.0,    # top-right
            1.0, -1.0, 1.0, 0.0    # bottom-right
        ], dtype=numpy.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self._vertices_vbo)
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

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, (GLuint * len(indices))(*indices), GL_STATIC_DRAW)

        # Create vertex buffer objects (VBOs) for draw data
        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, self._dest_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self._dest_vbo_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(2, 1)

        glEnableVertexAttribArray(3)
        glBindBuffer(GL_ARRAY_BUFFER, self._source_or_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self._source_or_color_vbo_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(3, 1)

        glEnableVertexAttribArray(4)
        glBindBuffer(GL_ARRAY_BUFFER, self._shape_transform_vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, self._shape_transform_vbo_array, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(4, 1)

        # Sprite texture
        image = load_sprites()
        self._texSprites = self._texture(image)

        # Font texture
        self._font_options = ("RobotoMono-Bold.ttf", "bold")
        self._font, image = Font(self._font_options[0], resolution=self.options["text resolution"], bold="bold" in self._font_options, antialias="antialias" in self._font_options)
        self._texFont = self._texture(image)

        # Block texture
        self.block_data, image = load_blocks()
        self._texBlocks = self._texture(image)

        # World texture (contains world block data)
        self._world_size = (0, 0)
        self._texWorld = None
        
        # Instance shader
        self._shader = Shader(
            "scripts/shader/vertex.glsl", "scripts/shader/fragment.glsl",
            replace={"block." + key: value for key, (value, *_) in self.block_data.items()},
            texSprites="int", texFont="int", texBlocks="int", texWorld="int", offset="vec2", camera="vec2", resolution="float", time="float"
        )

        self._shader.setvar("texSprites", 0)
        self._shader.setvar("texFont", 1)
        self._shader.setvar("texBlocks", 2)
        self._shader.setvar("texWorld", 3)
        self._shader.setvar("resolution", self.camera.resolution)

    def _add_vbo_instance(self, dest, source_or_color, shape_transform):
        """
        Queue a object to be drawn on the screen and resize buffers as necessary.
        """
        if self._vbo_instances_length == self._vbo_instances_index: # Resize all instanced vbos
            self._vbo_instances_length = int(1 + self._vbo_instances_length * 1.5)

            new_dest_vbo_array = numpy.zeros(self._vbo_instances_length * 4, dtype=numpy.float32)
            new_dest_vbo_array[:len(self._dest_vbo_array)] = self._dest_vbo_array
            glBindBuffer(GL_ARRAY_BUFFER, self._dest_vbo)
            glBufferData(GL_ARRAY_BUFFER, new_dest_vbo_array.nbytes, new_dest_vbo_array, GL_DYNAMIC_DRAW)
            self._dest_vbo_array = new_dest_vbo_array
 
            new_source_or_color_vbo_array = numpy.zeros(self._vbo_instances_length * 4, dtype=numpy.float32)
            new_source_or_color_vbo_array[:len(self._source_or_color_vbo_array)] = self._source_or_color_vbo_array
            glBindBuffer(GL_ARRAY_BUFFER, self._source_or_color_vbo)
            glBufferData(GL_ARRAY_BUFFER, new_source_or_color_vbo_array.nbytes, new_source_or_color_vbo_array, GL_DYNAMIC_DRAW)
            self._source_or_color_vbo_array = new_source_or_color_vbo_array

            new_shape_transform_vbo_array = numpy.zeros(self._vbo_instances_length * 4, dtype=numpy.float32)
            new_shape_transform_vbo_array[:len(self._shape_transform_vbo_array)] = self._shape_transform_vbo_array
            glBindBuffer(GL_ARRAY_BUFFER, self._shape_transform_vbo)
            glBufferData(GL_ARRAY_BUFFER, new_shape_transform_vbo_array.nbytes, new_shape_transform_vbo_array, GL_DYNAMIC_DRAW)
            self._shape_transform_vbo_array = new_shape_transform_vbo_array

        # Write drawing data into buffers
        self._dest_vbo_array[4 * self._vbo_instances_index:4 * self._vbo_instances_index + 4] = dest
        self._source_or_color_vbo_array[4 * self._vbo_instances_index:4 * self._vbo_instances_index + 4] = source_or_color
        self._shape_transform_vbo_array[4 * self._vbo_instances_index:4 * self._vbo_instances_index + 4] = numpy.array(shape_transform, dtype=numpy.float32)
        
        self._vbo_instances_index += 1

    def get_pressed_keys(self):
        """
        Returns a list with the names of all pressed keys.
        """
        keys = pygame.key.get_pressed()
        return [pygame.key.name(i).title() for i in self._key_names if keys[i]]

    def get_pressed_mods(self):
        """
        Returns a list with the names of all pressed mods.
        """
        mods = pygame.key.get_mods()
        return [self._mod_names[mod] for mod in self._mod_names if mods & mod]

    def resize(self):
        """
        Update fullscreen, window size and vsync flag.
        """
        if self._fullscreen:
            flags = FULLSCREEN
        else:
            flags = DOUBLEBUF | RESIZABLE

        # Called twice, because of Vsync...
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL)
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags | OPENGL, vsync=self.options["enable vsync"])
        glViewport(0, 0, self.width, self.height)

    def _events(self):
        self.keys = {key: (value if value != 1 else 2) for key, value in self.keys.items()}
        self.unicode = ""
        self.mouse_buttons = [2 if value == 1 else value for value in self.mouse_buttons]
        self.mouse_wheel[2], self.mouse_wheel[3] = 0, 0
        
        for event in pygame.event.get():
            if event.type == QUIT:
                self.quit()

            elif event.type == VIDEORESIZE:
                if self._resize_supress:
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
        self._events()
        self._clock.tick(self.options["max fps"])
        self.fps = self._clock.get_fps()
        self.delta_time = (1 / self.fps) if self.fps > 0 else self.delta_time
        self.time += self.delta_time

        # Reset
        glClear(GL_COLOR_BUFFER_BIT)

        # Use VAO
        glBindVertexArray(self._instance_vao)

        # Use instance shader
        self._shader.activate()

        # Send variables to shader
        self._update_world()
        self._shader.update()

        # Bind textures
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._texSprites)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self._texFont)

        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self._texBlocks)

        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, self._texWorld)

        # Send instance data to shader
        glBindBuffer(GL_ARRAY_BUFFER, self._dest_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self._dest_vbo_array.nbytes, self._dest_vbo_array)
        glBindBuffer(GL_ARRAY_BUFFER, self._source_or_color_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self._source_or_color_vbo_array.nbytes, self._source_or_color_vbo_array)
        glBindBuffer(GL_ARRAY_BUFFER, self._shape_transform_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self._shape_transform_vbo_array.nbytes, self._shape_transform_vbo_array)

        # Draw
        glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, self._vbo_instances_index)
        if self._refresh:
            pygame.display.flip()
        else:
            self._refresh = True

        # Reset instance index
        self._vbo_instances_index = 0

        # Move camera
        self.camera.update() # Better at the start, but currently at the end for sync of world and instanced rendering

        # Draw background and world
        self._shader.setvar("time", self.time)
        self._add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (4, 0, 0, 0))

    def toggle_fullscreen(self):
        """
        Toggle between fullscreen and normal mode.
        """
        self._fullscreen = not self._fullscreen
        self._resize_supress = True
        self._refresh = False

        if self._fullscreen:
            self.pre_fullscreen = self.size
            self.width, self.height = self.size = self.screen_size
        else:
            self.width, self.height = self.size = self.pre_fullscreen

        self.resize()

    def toggle_wire_frame(self):
        """
        Toggle between drawing only outlines and filled shapes.
        """
        self._wireframe = not self._wireframe
        if self._wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def set_text_resolution(self, text_resolution):
        """
        Set text resolution.
        """
        self.options["text resolution"] = text_resolution
        glDeleteTextures(1, (self._texFont,))
        self._font, image = Font(self._font_options[0], resolution=text_resolution, bold="bold" in self._font_options, antialias="antialias" in self._font_options)
        self._texFont = self._texture(image)

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

    def keybind(self, key):
        """
        Returns the state of an action key.
        """
        return self.keys[self.options["key." + key]]

    def _callback(self, function):
        if not function is None:
            function()

    def quit(self):
        """
        Quit the program
        """
        # Quit callback
        self._callback(self.callback_quit)

        # OpenGL cleanup
        glDeleteBuffers(5, (self._vertices_vbo, self._ebo, self._dest_vbo, self._source_or_color_vbo, self._shape_transform_vbo))
        glDeleteVertexArrays(1, (self._instance_vao,))
        glDeleteTextures(4, (self._texSprites, self._texFont, self._texBlocks, self._texWorld))
        self._shader.delete()

        # Save options
        options.save(self.options)

        # Quit
        pygame.quit()
        sys.exit()
    
    def _texture(self, image, blur=False):
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

    def _update_world(self, blur=0):
        """
        Update the world texture.
        """
        # Offset of world as a fraction of blocks
        offset = (
            self.camera.pos[0] % 1 - (self.width / 2 / self.camera.pixels_per_meter) % 1 + 3,
            self.camera.pos[1] % 1 - (self.height / 2 / self.camera.pixels_per_meter) % 1 + 3
        )

        # Send variables to shader
        self._shader.setvar("offset", *offset)
        self._shader.setvar("camera", *self.camera.pos)
        if self.resolution != self.camera.resolution:
            self.resolution = self.camera.resolution
        self._shader.setvar("resolution", self.camera.resolution)
        
        # View size
        size = self.world_view.shape[:2]        
        data = numpy.array(numpy.swapaxes(self.world_view, 0, 1), dtype=numpy.int32)
        self.world_view = numpy.zeros((0, 0, 4))
        if self._world_size != size:
            if not self._texWorld is None:
                glDeleteTextures(1, (self._texWorld,))
                self._texWorld = None
            self._world_size = size
        
        if self._texWorld is None:
            # Generate texture
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32I, *self._world_size, 0, GL_RGBA_INTEGER, GL_INT, data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glBindTexture(GL_TEXTURE_2D, 0)
            self._texWorld = texture
        else:
            # Write world data into texture
            glBindTexture(GL_TEXTURE_2D, self._texWorld)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32I, *self._world_size, 0, GL_RGBA_INTEGER, GL_INT, data)
    
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
                self._add_vbo_instance(dest_rect, rect, (0, *flip, angle / 180 * math.pi))
        else:
            self._add_vbo_instance(dest_rect, rect, (0, *flip, angle / 180 * math.pi))

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
                self._add_vbo_instance(dest_rect, self.camera.map_color(color), (1, 0, 0, 0))
        else:
            self._add_vbo_instance(dest_rect, self.camera.map_color(color), (1, 0, 0, 0))

    def draw_circle(self, position: [float], radius: int, color: [int]):
        """
        Draw a circle on the window.
        """
        self._add_vbo_instance((*position, radius / self.width * self.screen_size[1], radius / self.height * self.screen_size[1]), self.camera.map_color(color), (2, 0, 0, 0))

    def draw_line(self, start: [float], end: [float], width: int, color: [int]):
        """
        Draw a line on the window.
        """
        center = ((start[0] + end[0]) / 2,  (start[1] + end[1]) / 2)
        angle = math.atan2(start[1] - end[1], start[0] - end[0])
        sinAngle = abs(math.sin(angle))
        size = (math.sqrt(((start[0] - end[0]) / 2) ** 2 + ((start[1] - end[1]) / 2) ** 2),
                width / self.width * sinAngle + width / self.height * (1 - sinAngle))
        self._add_vbo_instance((*center, *size), self.camera.map_color(color), (1, 0, 0, angle))

    def draw_text(self, position: [float], text: str, color: [int], size: int=1, centered: bool=False, spacing: float=1.25, fixed_size: int=1, wrap: float=None):
        """
        Draw text on the window.
        fixed_size: 0 = stretch, 1 = relational size on both axis, 2 = fixed size
        When not using centered, the text can be wrapped and the width and height will be returned.
        """
        x_offset = 0
        y_offset = 0
        x_factor_fixed = 1 / self.width * self.screen_size[0] # Used when fixed_size == 1
        y_factor_fixed = 1 / self.height * self.screen_size[1] # Used when fixed_size == 1
        y_factor_relational = 1 / self.height * self.screen_size[1] * self.width / self.screen_size[0] # Used when fixed_size == 2
        if len(color) == 3:
            color = (*color, 255)

        if centered:
            char_size = self._font.get_rect("A")[2:]

            # Get start offset
            if fixed_size == 2:
                x_offset -= char_size[0] * spacing * size * (len(text) - 1) * x_factor_fixed
            else:
                x_offset -= char_size[0] * spacing * size * (len(text) - 1)

            for letter in text:
                rect = self._font.get_rect(letter)

                if fixed_size == 0:
                    dest_rect = [position[0] + x_offset + rect[2], position[1] + y_offset * rect[3] * 3 * size, rect[2] * size, rect[3] * 2 * size]
                    x_offset += rect[2] * spacing * size * 2
                elif fixed_size == 1:
                    dest_rect = [position[0] + x_offset, position[1] + y_offset * rect[3] * 3 * size * y_factor_relational, rect[2] * size, rect[3] * 2 * size * y_factor_relational]
                    x_offset += char_size[0] * spacing * size * 2
                else:
                    dest_rect = [position[0] + x_offset + rect[2], position[1] + y_offset * rect[3] * 3 * size * y_factor_fixed, rect[2] * size * x_factor_fixed, rect[3] * 2 * size * y_factor_fixed]
                    x_offset += rect[2] * spacing * size * x_factor_fixed * 2

                if letter == " ":
                    continue
                
                if not self.stencil_rect is None:
                    org = dest_rect[:]

                    left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
                    right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
                    top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
                    bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

                    width = (right - left) / 2
                    height = (bottom - top) / 2

                    if width < 0 or height < 0:
                        return
                    dest_rect = [left + width, top + height, width, height]

                    if org[2] - width > 0.0001 or org[3] - height > 0.0001:
                        source_and_color = (
                            color[0] + rect[0] + rect[2] * ((1 - dest_rect[2] / org[2]) if dest_rect[0] > org[0] else 0),
                            color[1] + rect[1] + rect[3] * (round(1 - dest_rect[3] / org[3], 6) if dest_rect[1] > org[1] else 0),
                            color[2] + rect[2] * (width / org[2]),
                            color[3] + rect[3] * ((height / org[3]) if (height / org[3]) < 1 else 0)
                        )

                    else:
                        source_and_color = (
                            color[0] + rect[0],
                            color[1] + rect[1],
                            color[2] + rect[2],
                            color[3] + rect[3]
                        )
    
                else:
                    source_and_color = (
                        color[0] + rect[0],
                        color[1] + rect[1],
                        color[2] + rect[2],
                        color[3] + rect[3]
                    )
                    
                self._add_vbo_instance(dest_rect, source_and_color, (3, 0, 0, 0))

        else: # Not centered; lines can wrap
            line_height = 5
            text += " "

            for i, letter in enumerate(text):
                # New line
                if letter == "\n":
                    x_offset = 0
                    y_offset += 1
                    continue
                elif letter == " " and (x_offset == 0 or i + 1 == len(text)):
                    continue

                # Get letter rect in texture
                rect = self._font.get_rect(letter)

                # Find next space
                next_space = text.find(" ", i) - i
                if (not wrap is None) and next_space >= 0 and x_offset + rect[2] * spacing * size * 2 * next_space > wrap:
                    x_offset = 0
                    y_offset += 1

                # Create destination rect
                if fixed_size == 0:
                    dest_rect = [position[0] + x_offset, position[1] - y_offset * rect[3] * line_height * size, rect[2] * size, rect[3] * 2 * size]
                    x_offset += rect[2] * spacing * size * 2
                elif fixed_size == 1:
                    dest_rect = [position[0] + x_offset, position[1] - y_offset * rect[3] * line_height * size * y_factor_relational, rect[2] * size, rect[3] * 2 * size * y_factor_relational]
                    x_offset += rect[2] * spacing * size * 2
                else:
                    dest_rect = [position[0] + x_offset, position[1] - y_offset * rect[3] * line_height * size * y_factor_fixed, rect[2] * size * x_factor_fixed, rect[3] * 2 * size * y_factor_fixed]
                    x_offset += rect[2] * spacing * size * x_factor_fixed * 2

                if letter == " ":
                    continue

                if not self.stencil_rect is None:
                    org = dest_rect[:]

                    left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
                    right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
                    top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
                    bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

                    width = (right - left) / 2
                    height = (bottom - top) / 2

                    if width < 0 or height < 0:
                        continue

                    dest_rect = [left + width, top + height, width, height]

                    if org[2] - width > 0.0001 or org[3] - height > 0.0001:
                        source_and_color = (
                            color[0] + rect[0] + rect[2] * ((1 - dest_rect[2] / org[2]) if dest_rect[0] > org[0] else 0),
                            color[1] + rect[1] + rect[3] * (round(1 - dest_rect[3] / org[3], 6) if dest_rect[1] > org[1] else 0),
                            color[2] + rect[2] * (width / org[2]),
                            color[3] + rect[3] * ((height / org[3]) if (height / org[3]) < 1 else 0)
                        )

                    else:
                        source_and_color = (
                            color[0] + rect[0],
                            color[1] + rect[1],
                            color[2] + rect[2],
                            color[3] + rect[3]
                        )

                else:
                    source_and_color = (
                        color[0] + rect[0],
                        color[1] + rect[1],
                        color[2] + rect[2],
                        color[3] + rect[3]
                    )

                self._add_vbo_instance(dest_rect, source_and_color, (3, 0, 0, 0))
        
            # Return width and height of text
            y_offset += 1
            if fixed_size == 0:
                return x_offset, rect[3] * 2 - y_offset * rect[3] * 2 * line_height * size
            elif fixed_size == 1:
                return x_offset, rect[3] * 2 - y_offset * rect[3] * 2 * line_height * size * y_factor_relational
            elif fixed_size == 2:
                return x_offset, rect[3] * 2 - y_offset * rect[3] * 2 * line_height * size * y_factor_fixed

    def draw_post_processing(self):
        self._add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (5, 0, 0, 0))

    def draw_block_highlight(self, x, y, color=(255, 0, 0)):
        if len(color) == 3:
            color = (*color, 100)
        rect = self.camera.map_coord((x, y, 1, 1), from_world=True)
        self.draw_rect(rect[:2], rect[2:], color)
