# -*- coding: utf-8 -*-
from scripts.graphics.image import load_sprites, get_sprite_rect
from scripts.utility.const import OPENGL_VERSION, PLATFORM
from scripts.utility.language import translate
from scripts.graphics.shader import Shader
from scripts.graphics.camera import Camera
from scripts.graphics.font import Font
from scripts.graphics import particle
from scripts.utility import options
from scripts.graphics import shadow
from scripts.graphics import sound
from scripts.utility import file
from OpenGL import GL
from math import *
import pygame
import ctypes
import numpy


class Window:
    def __init__(self, caption, block_data, block_atlas_image):
        # Load options
        self.options: dict = options.load()
        self.no_sounds = False

        # Callbacks
        self.callback_quit = None
        self.loading_progress: [str, int] = ["", 0, 0] # description, progress, total progress

        # Initialize pygame
        pygame.init()

        # Set OpenGL version
        opengl_major = int(OPENGL_VERSION.split(".")[0])
        opengl_minor = int(OPENGL_VERSION.split(".")[1][:1])
        opengl_core = "core" in OPENGL_VERSION

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, opengl_major)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, opengl_minor)
        if opengl_core:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                            pygame.GL_CONTEXT_PROFILE_CORE)

        # MacOS support
        if PLATFORM == "Darwin":
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
        self.average_fps: int = 0
        self.average_fps_delay: float = 0
        self.previous_fps: float = 0
        self.delta_time: float = 1.0
        self.time: float = 0.0
        self.resolution: float = 1.0
        self.damage_time: float = 0.0

        # Key press states
        if PLATFORM == "Darwin":
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

        self._key_names = tuple([pygame.__dict__[identifier] for identifier in pygame.__dict__.keys() if identifier.startswith("K_")])
        self._button_names = ("left click", "middle click", "right click")
        self.get_keys_all = pygame.key.get_pressed
        self.get_keys_all = pygame.key.get_mods
        self.get_key_name = pygame.key.name
        self.get_mod_name = lambda mod: self._mod_names[mod]
        self.event_types = (
            pygame.QUIT,
            pygame.VIDEORESIZE,
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEWHEEL
        )

        # Window variables
        info = pygame.display.Info()
        self.screen_size = info.current_w, info.current_h
        self.width, self.height = self.size = self.pre_fullscreen = (int(info.current_w / 3 * 2), int(info.current_h / 5 * 3))
        self.stencil_rect = ()
        self._fullscreen = False
        self._wireframe = False
        self._resize_supress = False
        self.effects = {}

        # Window
        flags = pygame.DOUBLEBUF | pygame.RESIZABLE | pygame.OPENGL
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.options["enable vsync"])
        self._clock = pygame.time.Clock()
        self.camera: Camera = Camera(self)
        self.world_view: numpy.array = numpy.empty((0, 0, 4))
        pygame.display.set_caption(caption)
        pygame.key.set_repeat(500, 50)
        
        # OpenGL setup
        GL.glViewport(0, 0, self.width, self.height)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        if self.options["antialiasing"]:
            GL.glEnable(GL.GL_MULTISAMPLE)
        else:
            GL.glDisable(GL.GL_MULTISAMPLE)

        # Create vertex array object
        self._instance_vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self._instance_vao)

        # Create vertex buffer objects
        self._vertices_vbo, self._ebo, self._dest_vbo, self._source_or_color_vbo, self._shape_transform_vbo = GL.glGenBuffers(5)

        # Instanced shader inputs
        self._vbo_instances_length = 0
        self._vbo_instances_index = 0
  
        self._dest_vbo_array = numpy.empty(0, dtype=numpy.float32)
        self._source_or_color_vbo_array = numpy.empty(0, dtype=numpy.float32)
        self._shape_transform_vbo_array = numpy.empty(0, dtype=numpy.float32)

        # Vertices & texcoords
        vertices = numpy.array([
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            -1.0, 1.0, 0.0, 1.0,   # top-left
            1.0, 1.0, 1.0, 1.0,    # top-right
            1.0, -1.0, 1.0, 0.0    # bottom-right
        ], dtype=numpy.float32)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertices_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        
        # Create element buffer object (EBO) for indices
        indices = numpy.array([
            0, 1, 2,
            0, 2, 3
        ], dtype=numpy.uint32)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, (GL.GLuint * len(indices))(*indices), GL.GL_STATIC_DRAW)

        # Create vertex buffer objects (VBOs) for draw data
        GL.glEnableVertexAttribArray(2)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._dest_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, 0, self._dest_vbo_array, GL.GL_STREAM_COPY)
        GL.glVertexAttribPointer(2, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, ctypes.c_void_p(0))
        GL.glVertexAttribDivisor(2, 1)

        GL.glEnableVertexAttribArray(3)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._source_or_color_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, 0, self._source_or_color_vbo_array, GL.GL_STREAM_COPY)
        GL.glVertexAttribPointer(3, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, ctypes.c_void_p(0))
        GL.glVertexAttribDivisor(3, 1)

        GL.glEnableVertexAttribArray(4)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._shape_transform_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, 0, self._shape_transform_vbo_array, GL.GL_STREAM_COPY)
        GL.glVertexAttribPointer(4, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, ctypes.c_void_p(0))
        GL.glVertexAttribDivisor(4, 1)

        # Create sprite texture
        self.sprites, self.sprite_rects, self.hand_positions, sprite_atlas_image = load_sprites()
        self._texSprites = self._texture(sprite_atlas_image)

        # Font texture
        self._font_options = ("RobotoMono-Bold.ttf", "bold")
        self._font, font_atlas_image = Font(
            self._font_options[0],
            resolution=self.options["text resolution"],
            bold="bold" in self._font_options,
            antialias="antialias" in self._font_options
        )
        self._texFont = self._texture(font_atlas_image)

        # Create world texture (contains world block data)
        self._world_size = (0, 0)
        self._texWorld = None

        # Create block texture
        self._texBlocks = self._texture(block_atlas_image)

        # Create shadow texture
        self._shadow_texture_size = (self.width // 2, self.height // 2)
        self._texShadow = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texShadow)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RED, *self._shadow_texture_size, 0, GL.GL_RED, GL.GL_UNSIGNED_BYTE, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # Instance shader
        self._instance_shader = Shader(
            vertex="data/shader/instance.vert",
            fragment="data/shader/instance.frag",
            variables={
                "texSprites": "int",
                "texFont": "int",
                "texBlocks": "int",
                "texWorld": "int",
                "texShadow": "int",
                "offset": "vec2",
                "camera": "vec2",
                "resolution": "float",
                "shadow_resolution": "float",
                "time": "float",
                "gray_screen": "int",
                "damage_screen": "float"
            },
            constants={
                "block." + key: value for key, (value, *_) in block_data.items()
            },
        )

        self._instance_shader.setvar("texSprites", 0)
        self._instance_shader.setvar("texFont", 1)
        self._instance_shader.setvar("texBlocks", 2)
        self._instance_shader.setvar("texWorld", 3)
        self._instance_shader.setvar("texShadow", 4)
        self._instance_shader.setvar("resolution", self.camera.resolution)
        self._instance_shader.setvar("shadow_resolution", self.options["shadow resolution"])

        # Use instance shader
        self._instance_shader.activate()
        GL.glBindVertexArray(self._instance_vao)

        # Bind textures (except world texture)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texSprites)

        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texFont)

        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texBlocks)

        GL.glActiveTexture(GL.GL_TEXTURE4)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texShadow)

    def setup(self):
        """
        Threaded function called after __init__().
        """
        # Load sounds
        self.loading_progress[:3] = "Loading sounds", 1, 2
        self.loaded_sounds, self.played_sounds = sound.load()
    
        # Create particle types
        self.loading_progress[:2] = "Loading particles", 2
        self.particles: list = []
        self.particle_types: dict = {}
        self.particle_wind: float = 0.0
        particle_data = file.load(file.abspath("data/particles/particles.json"), file_format="json")
        for particle_name, kwargs in particle_data.items():
            kwargs["angle"] *= pi / 180
            particle.setup(self, particle_name, **kwargs)

    def _add_vbo_instance(self, dest, source_or_color, shape_transform):
        """
        Queue a object to be drawn on the screen and resize buffers as necessary.
        """
        if self._vbo_instances_length == self._vbo_instances_index:
            # Resize all instanced vbos, adding 10 additional instances
            self._vbo_instances_length += 10

            new_dest_vbo_array = numpy.empty(self._vbo_instances_length * 4, dtype=numpy.float32)
            new_dest_vbo_array[:len(self._dest_vbo_array)] = self._dest_vbo_array
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._dest_vbo)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, new_dest_vbo_array.nbytes, new_dest_vbo_array, GL.GL_STREAM_COPY)
            self._dest_vbo_array = new_dest_vbo_array
 
            new_source_or_color_vbo_array = numpy.empty(self._vbo_instances_length * 4, dtype=numpy.float32)
            new_source_or_color_vbo_array[:len(self._source_or_color_vbo_array)] = self._source_or_color_vbo_array
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._source_or_color_vbo)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, new_source_or_color_vbo_array.nbytes, new_source_or_color_vbo_array, GL.GL_STREAM_COPY)
            self._source_or_color_vbo_array = new_source_or_color_vbo_array

            new_shape_transform_vbo_array = numpy.empty(self._vbo_instances_length * 4, dtype=numpy.float32)
            new_shape_transform_vbo_array[:len(self._shape_transform_vbo_array)] = self._shape_transform_vbo_array
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._shape_transform_vbo)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, new_shape_transform_vbo_array.nbytes, new_shape_transform_vbo_array, GL.GL_STREAM_COPY)
            self._shape_transform_vbo_array = new_shape_transform_vbo_array

        # Write drawing data into buffers
        index = 4 * self._vbo_instances_index
        self._dest_vbo_array[index:index + 4] = dest
        self._source_or_color_vbo_array[index:index + 4] = source_or_color
        self._shape_transform_vbo_array[index:index + 4] = shape_transform
        
        # Increment instance counter
        self._vbo_instances_index += 1

    def get_pressed_keys(self):
        """
        Returns a list containing all names of pressed keys.
        """
        keys = pygame.key.get_pressed()
        return [pygame.key.name(i).title() for i in self._key_names if keys[i]]

    def get_pressed_mods(self):
        """
        Returns a list containing all names of pressed mods.
        """
        mods = pygame.key.get_mods()
        return [self._mod_names[mod] for mod in self._mod_names if mods & mod]

    def get_pressed_mouse(self):
        """
        Returns a list containing all names of mouse buttons.
        """
        return [("Left Click", "Middle Click", "Right Click")[i] for i, pressed in enumerate(self.mouse_buttons) if pressed == 1]

    def resize(self):
        """
        Update fullscreen, window size and vsync flag.
        """
        if self._fullscreen:
            flags = pygame.FULLSCREEN
        else:
            flags = pygame.DOUBLEBUF | pygame.RESIZABLE

        # Toggle vsync: Restart required on Windows; Instant on Darwin
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags | pygame.OPENGL, vsync=self.options["enable vsync"])
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags | pygame.OPENGL, vsync=self.options["enable vsync"])
        GL.glViewport(0, 0, self.width, self.height)

    def _events(self):
        """
        Process input events.
        """
        self.unicode = ""
        self.mouse_buttons = [2 if value == 1 else value for value in self.mouse_buttons]
        self.mouse_wheel[2], self.mouse_wheel[3] = 0, 0
        for key, value in self.keys.items():
            if value == 1:
                self.keys[key] = 2
        
        events = filter(lambda i: i.type in self.event_types, pygame.event.get())
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()

            elif event.type == pygame.VIDEORESIZE:
                if self._resize_supress:
                    self._resize_supress = False
                    continue
                self.size = event.size
                self.width, self.height = event.w, event.h
                self.resize()

            elif event.type == pygame.KEYDOWN:
                if event.unicode != "":
                    self.unicode = event.unicode
                key = pygame.key.name(event.key)
                if PLATFORM == "Darwin":
                    key = key.replace("meta", "cmd")
                if key in self.keys:
                    self.keys[key] = 1

            elif event.type == pygame.KEYUP:
                key = pygame.key.name(event.key)
                if PLATFORM == "Darwin":
                    key = key.replace("meta", "cmd")
                if key in self.keys:
                    self.keys[key] = 0

            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = (event.pos[0] - self.width / 2, self.height / 2 - event.pos[1], event.rel[0], -event.rel[1])

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button < 4:
                    self.mouse_buttons[event.button - 1] = 1
                    button_name = self._button_names[event.button - 1]
                    if button_name in self.keys:
                        self.keys[button_name] = 1

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button < 4:
                    self.mouse_buttons[event.button - 1] = 0
                    button_name = self._button_names[event.button - 1]
                    if button_name in self.keys:
                        self.keys[button_name] = 0

            elif event.type == pygame.MOUSEWHEEL:
                self.mouse_wheel = [self.mouse_wheel[0] + event.x, self.mouse_wheel[1] + event.y, event.x, event.y]

    def update(self, player_position=(0, 0)):
        """
        Update the window and inputs.
        """
        # Update pygame
        self._events()

        fps_limit = self.options["max fps"]
        if fps_limit == 1000 or self.options["enable vsync"]:
            fps_limit = 0
        self._clock.tick(fps_limit)
        #self.fps = 1000 / max(1, self._clock.tick(fps_limit))

        self.fps = self._clock.get_fps()
        if self.fps != 0:
            self.delta_time = (self.delta_time + 1 / self.fps) * 0.5
            if self.average_fps_delay <= 0:
                self.average_fps_delay = 0.5
                self.average_fps = self.previous_fps
            else:
                self.average_fps_delay -= self.delta_time
                self.previous_fps = (self.previous_fps * 3 + self.fps) * 0.25

        self.time += self.delta_time
        if self.damage_time:
            self.damage_time -= self.delta_time
            self._instance_shader.setvar("damage_screen", self.damage_time * 3)
            if self.damage_time < 0:
                self.damage_time = 0
                self._instance_shader.setvar("damage_screen", 0)

        self._update_world(player_position)

        # Send variables to shader
        for effect, value in self.effects.items():
            self._instance_shader.setvar(effect, value)

        self._instance_shader.update()

        # Rebind textures
        #GL.glActiveTexture(GL.GL_TEXTURE1)
        #GL.glBindTexture(GL.GL_TEXTURE_2D, self._texFont)

        GL.glActiveTexture(GL.GL_TEXTURE4)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texShadow)

        # Send instance data to shader
        size = int(self._dest_vbo_array.nbytes * min((self._vbo_instances_index + 1) / self._vbo_instances_length, 1))
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._dest_vbo)
        GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, size, self._dest_vbo_array)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._source_or_color_vbo)
        GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, size, self._source_or_color_vbo_array)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._shape_transform_vbo)
        GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, size, self._shape_transform_vbo_array)

        # Draw
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glDrawElementsInstanced(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None, self._vbo_instances_index)
        pygame.display.flip()

        # Reset instance index
        self._vbo_instances_index = 0

        # Draw background and world
        self._instance_shader.setvar("time", self.time)
        self._add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (4, 0, 0, 0))
        self.effects.clear()

    def toggle_fullscreen(self):
        """
        Toggle between fullscreen and normal mode.
        """
        self._fullscreen = not self._fullscreen
        self._resize_supress = True

        if self._fullscreen:
            self.pre_fullscreen = self.size
            self.width, self.height = self.size = self.screen_size
        else:
            self.width, self.height = self.size = self.pre_fullscreen

        self.resize()

    def set_text_resolution(self, text_resolution):
        """
        Set text resolution.
        """
        self.options["text resolution"] = text_resolution
        GL.glDeleteTextures(1, (self._texFont,))
        self._font, image = Font(
            self._font_options[0],
            resolution=text_resolution,
            bold="bold" in self._font_options,
            antialias="antialias" in self._font_options
        )
        self._texFont = self._texture(image)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texFont)

    def set_antialiasing(self, level: int):
        """
        Toggle antialiasing.
        """
        self.options["antialiasing"] = level
        if self.options["antialiasing"]:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, self.options["antialiasing"])
            GL.glEnable(GL.GL_MULTISAMPLE)
        else:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
            GL.glDisable(GL.GL_MULTISAMPLE)
        self.resize()

    def keybind(self, key):
        """
        Returns the state of an action key.
        """
        return self.keys[self.options["key." + key]]

    def _callback(self, function):
        """
        Execute a callback.
        """
        if not function is None:
            function()

    def quit(self):
        """
        Quit the program
        """
        # Quit callback
        self._callback(self.callback_quit)

        # OpenGL cleanup
        GL.glDeleteBuffers(5, (
            self._vertices_vbo,
            self._ebo,
            self._dest_vbo,
            self._source_or_color_vbo,
            self._shape_transform_vbo,
        ))
        GL.glDeleteVertexArrays(1, (self._instance_vao,))
        textures = [
            self._texSprites,
            self._texFont,
            self._texBlocks,
            self._texWorld,
            self._texShadow,
        ]
        while None in textures:
            textures.remove(None)
        GL.glDeleteTextures(len(textures), textures)
        self._instance_shader.delete()

        # Save options
        options.save(self.options)

        # Quit window
        pygame.quit()
        
        # Quit the program; can be catched for profiling
        raise SystemExit()

    def clear_world(self):
        """
        Clear the world view.
        """
        self.world_view.fill(0)
    
    def _texture(self, image, blur=False):
        """
        Create a texture from an image.
        """
        data = pygame.image.tostring(image, "RGBA", 1)
        texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, *image.get_size(), 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, data)

        if blur:
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        else:
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        return texture

    def _update_world(self, player_position=(0, 0)):
        """
        Update the world texture.
        """
        # Offset of world as a fraction of blocks
        offset = (
            self.camera.pos[0] % 1 - (self.width / 2 / self.camera.pixels_per_meter) % 1 + self.options["simulation distance"],
            self.camera.pos[1] % 1 - (self.height / 2 / self.camera.pixels_per_meter) % 1 + self.options["simulation distance"]
        )

        if not all(self.world_view.shape):
            if not self._texWorld is None:
                GL.glDeleteTextures(1, (self._texWorld,))
                self._texWorld = None
                self._world_size =  (0, 0)
            return

        # Draw shadows
        if any(player_position) and self.options["shadow resolution"]:
            self._draw_shadows(offset, player_position)

        # Send variables to shader
        self._instance_shader.setvar("offset", *offset)
        self._instance_shader.setvar("camera", *self.camera.pos)
        if self.resolution != self.camera.resolution:
            self.resolution = self.camera.resolution
            self._instance_shader.setvar("resolution", self.camera.resolution)

        # View size
        size = self.world_view.shape[:2]
        data = numpy.array(numpy.swapaxes(self.world_view, 0, 1), dtype=numpy.int32)

        if self._world_size != size:
            if not self._texWorld is None:
                GL.glDeleteTextures(1, (self._texWorld,))
                self._texWorld = None
            self._world_size = size
        
        if self._texWorld is None:
            # Generate new texture
            texture = GL.glGenTextures(1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32I, *self._world_size, 0, GL.GL_RGBA_INTEGER, GL.GL_INT, data)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE3)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            self._texWorld = texture
        else:
            # Write world data into texture
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texWorld)
            #GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32I, *self._world_size, 0, GL.GL_RGBA_INTEGER, GL.GL_INT, data)
            GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, *self._world_size, GL.GL_RGBA_INTEGER, GL.GL_INT, data)
            #GL.glBufferData(GL.GL_TEXTURE_2D, data.nbytes, data, GL.GL_STREAM_COPY)

    def _draw_shadows(self, offset, player_position):
        """
        Calculate and draw shadows.
        """
        #t = time.time()
        # Create view copy
        view = self.world_view.copy()[:, :, 0]
        view[0, :] = 0
        view[:, 0] = 0
        view[-1, :] = 0
        view[:, -1] = 0

        # Create shadow surface
        shadow_resolution = self.options["shadow resolution"]
        surface_size = (round(view.shape[0] * shadow_resolution), round(view.shape[1] * shadow_resolution))
        surface = pygame.Surface(surface_size)

        # Use torches as light source
        # light_sources = (
        #     list(numpy.argwhere(self.world_view[:, :, 1] == self.block_data["torch"][0]))
        #   + list(numpy.argwhere(self.world_view[:, :, 1] == self.block_data["torch_flipped"][0]))
        # )
        # for player_position in light_sources:
        #     ...

        # Use player as light source
        center = (floor(self.camera.pos[0]),
                    floor(self.camera.pos[1]))
        start = (center[0] - floor(self.width / 2 / self.camera.pixels_per_meter) - self.options["simulation distance"],
                    center[1] - floor(self.height / 2 / self.camera.pixels_per_meter) - self.options["simulation distance"])
        player_position = (player_position[0] - start[0] - 1.0, player_position[1] - start[1] - 1.0)

        # Find corners
        corners, additional_corners = shadow.find_corners(view)

        # Find edges
        edges = shadow.find_edges(corners)

        # Generate triangle_points
        corners = list(additional_corners.union(corners))
        triangle_points = shadow.get_triangle_points(view, shadow.List(player_position), numpy.array(corners), shadow.List(edges))
        triangle_points.sort(key=lambda n: n[0], reverse=False)

        # Draw to shadow surface
        triangle_points = tuple(map(lambda n: (round(n[1] * shadow_resolution), round(n[2] * shadow_resolution)), triangle_points))
        if len(triangle_points) > 2:
            pygame.draw.polygon(surface, (255, 0, 0), triangle_points)

        #print(1, time.time() - t)
        #t = time.time()

        # Convert shadow surface to numpy array
        surface_data = pygame.surfarray.pixels_red(surface).transpose()

        #print(2, time.time() - t)
        #t = time.time()

        # Convert shadow surface array to texture
        if surface_size != self._shadow_texture_size:
            #print(4)
            self._shadow_texture_size = surface_size
            GL.glActiveTexture(GL.GL_TEXTURE4)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texShadow)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RED, *surface_data.shape[::-1], 0, GL.GL_RED, GL.GL_UNSIGNED_BYTE, surface_data)
            #GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            #GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE4)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texShadow)
        else:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texShadow)
            #GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, *surface_data.shape[::-1], GL.GL_RED, GL.GL_UNSIGNED_BYTE, surface_data)
            GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, *surface_data.shape[::-1], GL.GL_RED, GL.GL_UNSIGNED_BYTE, surface_data)
            #GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RED, *surface_data.shape[::-1], 0, GL.GL_RED, GL.GL_UNSIGNED_BYTE, surface_data)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        #print(3, time.time() - t)

    def _centered_text(self, position: [float], text: str, color: [int], size: int=1, spacing: float=1.25, fixed_size: int=1):
        """
        Draw centered text. Called from draw_text.
        """
        x_offset = 0
        x_factor_fixed = 1 / self.width * self.screen_size[0] # Used when fixed_size == 1
        y_factor_fixed = 1 / self.height * self.screen_size[1] # Used when fixed_size == 1
        y_factor_relational = 1 / self.height * self.screen_size[1] * self.width / self.screen_size[0] # Used when fixed_size == 2
        if len(color) == 3:
            color = (*color, 255)
        char_size = self._font.get_rect("A")[2:]

        # Get start offset
        if fixed_size == 2:
            x_offset -= char_size[0] * spacing * size * (len(text) - 1) * x_factor_fixed
        else:
            x_offset -= char_size[0] * spacing * size * (len(text) - 1)

        for letter in text:
            rect = self._font.get_rect(letter)

            if fixed_size == 0:
                dest_rect = (position[0] + x_offset + rect[2], position[1], rect[2] * size, rect[3] * 2 * size)
                x_offset += rect[2] * spacing * size * 2
            elif fixed_size == 1:
                dest_rect = (position[0] + x_offset, position[1], rect[2] * size, rect[3] * 2 * size * y_factor_relational)
                x_offset += char_size[0] * spacing * size * 2
            else:
                dest_rect = (position[0] + x_offset + rect[2], position[1], rect[2] * size * x_factor_fixed, rect[3] * 2 * size * y_factor_fixed)
                x_offset += rect[2] * spacing * size * x_factor_fixed * 2

            if letter == " ":
                continue                
            if self.stencil_rect:
                org = dest_rect[:]

                left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
                right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
                top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
                bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

                width = (right - left) / 2
                height = (bottom - top) / 2

                if width < 0 or height < 0:
                    return
                dest_rect = (left + width, top + height, width, height)

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

    def _uncentered_text(self, position: [float], text: str, color: [int], size: int=1, spacing: float=1.25, fixed_size: int=1, wrap: float=None):
        """
        Draw uncentered text. Called from draw_text.
        """
        x_offset = 0
        y_offset = 0
        x_factor_fixed = 1 / self.width * self.screen_size[0] # Used when fixed_size == 1
        y_factor_fixed = 1 / self.height * self.screen_size[1] # Used when fixed_size == 1
        y_factor_relational = 1 / self.height * self.screen_size[1] * self.width / self.screen_size[0] # Used when fixed_size == 2
        if len(color) == 3:
            color = (*color, 255)
        line_height = 5
        text += " "

        if not len(text.strip()):
            rect = self._font.get_rect("A")
            x_offset = rect[2] * spacing * size * 2 * (len(text) - 1)
        else:
            for i, letter in enumerate(text):
                # New line
                if letter == "\n":
                    x_offset = 0
                    y_offset += 1
                    continue
                
                if letter == " " and i + 1 == len(text):
                    continue

                # Get letter rect in texture
                rect = self._font.get_rect(letter)

                # Create destination rect
                if fixed_size == 0:
                    dest_rect = (position[0] + x_offset, position[1] - y_offset * rect[3] * line_height * size, rect[2] * size, rect[3] * 2 * size)
                    letter_x_offset = rect[2] * spacing * size * 2
                elif fixed_size == 1:
                    dest_rect = (position[0] + x_offset, position[1] - y_offset * rect[3] * line_height * size * y_factor_relational, rect[2] * size, rect[3] * 2 * size * y_factor_relational)
                    letter_x_offset = rect[2] * spacing * size * 2
                else:
                    dest_rect = (position[0] + x_offset, position[1] - y_offset * rect[3] * line_height * size * y_factor_fixed, rect[2] * size * x_factor_fixed, rect[3] * 2 * size * y_factor_fixed)
                    letter_x_offset = rect[2] * spacing * size * x_factor_fixed * 2

                x_offset += letter_x_offset

                # Find next space
                next_space = text.find(" ", i + 1) - i
                if (not wrap is None) and next_space >= 0 and x_offset + letter_x_offset * next_space > wrap:
                    x_offset = 0
                    y_offset += 1

                if letter == " ":
                    continue

                if self.stencil_rect:
                    org = dest_rect[:]

                    left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
                    right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
                    top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
                    bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

                    width = (right - left) / 2
                    height = (bottom - top) / 2

                    if width < 0 or height < 0:
                        continue

                    dest_rect = (left + width, top + height, width, height)

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
            return (
                x_offset,
                rect[3] * 2 - y_offset * rect[3] * 2 * line_height * size
            )
        elif fixed_size == 1:
            return (
                x_offset,
                rect[3] * 2 - y_offset * rect[3] * 2 * line_height * size * y_factor_relational
            )
        elif fixed_size == 2:
            return (
                x_offset,
                rect[3] * 2 - y_offset * rect[3] * 2 * line_height * size * y_factor_fixed
            )
    
    def draw_image(self, image: str, position: [float], size: [float], angle: float=0.0, flip: [int]=(0, 0), animation_offset: float=0):
        """
        Draw an image on the window.
        """
        rect = get_sprite_rect(self, image, offset=animation_offset)

        dest_rect = (position[0] + size[0] / 2, position[1] + size[1] / 2, size[0] / 2, size[1] / 2)
        if self.stencil_rect:
            org = dest_rect[:]

            left = max(dest_rect[0] - dest_rect[2], self.stencil_rect[0] - self.stencil_rect[2])
            right = min(dest_rect[0] + dest_rect[2], self.stencil_rect[0] + self.stencil_rect[2])
            top = max(dest_rect[1] - dest_rect[3], self.stencil_rect[1] - self.stencil_rect[3])
            bottom = min(dest_rect[1] + dest_rect[3], self.stencil_rect[1] + self.stencil_rect[3])

            width = (right - left) / 2
            height = (bottom - top) / 2

            if width > 0 and height > 0:
                dest_rect = (left + width, top + height, width, height)
                if org[2] - width > 0.0001 or org[3] - height > 0.0001:
                    rect = (
                            rect[0] + rect[2] * ((1 - dest_rect[2] / org[2]) if dest_rect[0] > org[0] else 0),
                            rect[1] + rect[3] * (round(1 - dest_rect[3] / org[3], 6) if dest_rect[1] > org[1] else 0),
                            rect[2] * (width / org[2]),
                            rect[3] * ((height / org[3]) if (height / org[3]) < 1 else 0)
                        )
                self._add_vbo_instance(dest_rect, rect, (0, *flip, angle / 180 * pi))
        else:
            self._add_vbo_instance(dest_rect, rect, (0, *flip, angle / 180 * pi))

    def draw_rect(self, position: [float], size: [float], color: [int]):
        """
        Draw a rectangle on the window.
        """
        dest_rect = (position[0] + size[0] / 2, position[1] + size[1] / 2, size[0] / 2, size[1] / 2)
        if self.stencil_rect:
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
        angle = atan2(start[1] - end[1], start[0] - end[0])
        sinAngle = abs(sin(angle))
        size = (sqrt(((start[0] - end[0]) / 2) ** 2 + ((start[1] - end[1]) / 2) ** 2),
                width / self.width * sinAngle + width / self.height * (1 - sinAngle))
        self._add_vbo_instance((*center, *size), self.camera.map_color(color), (1, 0, 0, angle))

    def draw_text(self, position: [float], text: str, color: [int], size: int=1, centered: bool=False, spacing: float=1.25, fixed_size: int=1, wrap: float=None):
        """
        Draw text on the window.
        fixed_size: 0 = stretch, 1 = relational size on both axis, 2 = fixed size
        When not using centered, the text can be wrapped and the width and height will be returned.
        """
        if not text:
            return (0, 0)

        # Translate text
        text = translate(self.options["language"], text)

        # Draw text
        if centered:
            self._centered_text(position, text, color, size, spacing, fixed_size)
        else: # Lines can wrap
            return self._uncentered_text(position, text, color, size, spacing, fixed_size, wrap)

    def draw_post_processing(self):
        """
        Draw world and post processing.
        """
        self._add_vbo_instance((0, 0, 1, 1), (0, 0, 0, 0), (5, 0, 0, 0))

    def draw_block_highlight(self, x_coord, y_coord, color=(255, 0, 0)):
        """
        Highlight a single block.
        """
        if len(color) == 3:
            color = (*color, 100)
        rect = self.camera.map_coord((x_coord, y_coord, 1, 1), from_world=True)
        self.draw_rect(rect[:2], rect[2:], color)
