# -*- coding: utf-8 -*-
from scripts.graphics.image import load_sprites, get_sprite_rect
from scripts.utility.language import translate
from scripts.graphics.camera import Camera
from scripts.utility.const import PLATFORM
from scripts.graphics import particle
from scripts.utility import options
from scripts.utility import file
from math import *
import pygame
import numpy


class Window:
    def __init__(self, caption, block_data, block_atlas_image):
        # Load options
        self.options: dict = options.load()
        self.no_sounds = True

        # Callbacks
        self.callback_quit = None
        self.loading_progress: [str, int] = ["", 0, 0] # description, progress, total progress

        # Initialize pygame
        pygame.init()

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
                for _, identifier in enumerate(pygame.__dict__.keys())
                if identifier.startswith("KMOD_") and not identifier[5:] in ("NONE", "CTRL", "SHIFT", "ALT", "GUI", "META")
            }
        else:
            self._mod_names = {
                pygame.__dict__[identifier]: identifier[4:].replace("_R", "Right ").replace("_L", "Left ").replace("_", "").title()
                for _, identifier in enumerate(pygame.__dict__.keys())
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
        flags = pygame.DOUBLEBUF | pygame.RESIZABLE
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.options["enable vsync"])
        self._clock = pygame.time.Clock()
        self.camera: Camera = Camera(self)
        self.world_view: numpy.array = numpy.empty((0, 0, 4))
        pygame.display.set_caption(caption)
        pygame.key.set_repeat(500, 50)

        # Create sprite texture
        self.sprites, self.sprite_rects, self.hand_positions, sprite_atlas_image = load_sprites()
        self._texSprites = sprite_atlas_image

        # Font texture
        self._font_options = ("RobotoMono-Bold.ttf", "bold")
        self._font = pygame.font.Font(file.abspath("data/fonts/" + self._font_options[0]), self.options["text resolution"] * 5)

        # Create world texture (contains world block data)
        self._world_size = (0, 0)
        self._texWorld = None

        # Create block texture
        self._texBlocks = block_atlas_image

        # Create shadow texture
        self._shadow_texture_size = (self.width // 2, self.height // 2)
        self._texShadow = ...

    def setup(self):
        """
        Threaded function called after __init__().
        """
        # Create particle types
        self.loading_progress[:2] = "Loading particles", 2
        self.particles: list = []
        self.particle_types: dict = {}
        self.particle_wind: float = 0.0
        particle_data = file.load(file.abspath("data/particles/particles.json"), file_format="json")
        for particle_name, kwargs in particle_data.items():
            kwargs["angle"] *= pi / 180
            particle.setup(self, particle_name, **kwargs)

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
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.options["enable vsync"])
        self._window = pygame.display.set_mode((self.width, self.height), flags=flags, vsync=self.options["enable vsync"])

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
            if self.damage_time < 0:
                self.damage_time = 0

        pygame.display.flip()

        color_float = 1 - self.damage_time / 0.3
        inverse_color_float = 1 - color_float
        bg_color = (100, 127, 108)
        blood_color = (90, 40, 50)
        fill_color = (
            bg_color[0] * color_float + blood_color[0] * inverse_color_float,
            bg_color[1] * color_float + blood_color[1] * inverse_color_float,
            bg_color[2] * color_float + blood_color[2] * inverse_color_float
        )
        self._window.fill(fill_color)
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
        return

    def set_antialiasing(self, level: int):
        """
        Toggle antialiasing.
        """
        return

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
        return image

    def _centered_text(self, position: [float], text: str, color: [int], size: int=1, spacing: float=1.25, fixed_size: int=1):
        """
        Draw centered text. Called from draw_text.
        """
        source = pygame.transform.scale_by(self._font.render(text, 0, (255, 255, 255)), size)
        size = source.get_size()
        position = (position[0] - size[0]/2, position[1] - size[1]/2)
        self._window.blit(source, position)

    def _uncentered_text(self, position: [float], text: str, color: [int], size: int=1, spacing: float=1.25, fixed_size: int=1, wrap: float=None):
        """
        Draw uncentered text. Called from draw_text.
        """
        letter_size = self._font.render("A", 0, (0,0,0)).get_size()
        if not wrap is None:
            wrap = int(wrap * self.width * 0.5 / letter_size[0] / size)
            text = text.strip() + " "
            new_text = ""
            line_length = 0
            last_space_index = 0
            for i in range(text.count(" ")):
                next_space_index = text.find(" ", last_space_index + 1)
                if i == text.count(" ") - 1:
                    if line_length + len(text[last_space_index:]) > wrap:
                        new_text += "\n"
                    new_text += text[last_space_index:]
                    break
                if line_length + next_space_index - last_space_index <= wrap:
                    new_text += text[last_space_index:next_space_index]
                    line_length += next_space_index - last_space_index
                    last_space_index = next_space_index
                else:
                    new_text += "\n"
                    line_length = -1

            text = "\n".join(map(lambda s: s.strip(), new_text.split("\n"))) + " "

        source = pygame.transform.scale_by(self._font.render(text, 0, color), size)
        self._window.blit(source, (position[0], position[1] - letter_size[1] * size * 0.5))
        total_text_size = source.get_size()
        return (total_text_size[0] / self.width * 2, -3 * total_text_size[1] / self.height)
    
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

        dest_rect = (
            (dest_rect[0] + 1) * self.width / 2,
            (-dest_rect[1] + 1) * self.height / 2,
            dest_rect[2] * self.width,
            dest_rect[3] * self.height
        )
        width, height = self._texSprites.get_size()
        rect = (
            rect[0] * width,
            height - rect[1] * height - rect[3] * height,
            rect[2] * width,
            rect[3] * height,
        )
        source = pygame.Surface(rect[2:], pygame.SRCALPHA)
        source.blit(self._texSprites, (0, 0), rect)
        source = pygame.transform.rotate(pygame.transform.flip(pygame.transform.scale(source, dest_rect[2:]), *flip), angle)
        self._window.blit(source, (dest_rect[0] - dest_rect[2] * 0.5, dest_rect[1] - dest_rect[3] * 0.5))

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

        dest_rect = (
            (dest_rect[0] + 1 - dest_rect[2]) * self.width / 2,
            (-dest_rect[1] + 1 - dest_rect[3]) * self.height / 2,
            dest_rect[2] * self.width,
            dest_rect[3] * self.height
        )
        if len(color) == 4:
            rect = pygame.Surface(dest_rect[2:])
            rect.fill(color)
            rect.set_alpha(color[3])
            self._window.blit(rect, dest_rect[:2])
        else:
            pygame.draw.rect(self._window, color, dest_rect, border_radius=2)

    def draw_circle(self, position: [float], radius: int, color: [int]):
        """
        Draw a circle on the window.
        """
        position = (
            round((position[0] + 1) * self.width / 2),
            round((-position[1] + 1) * self.height / 2)
        )
        radius *= self.width * 0.5
        if len(color) == 4:
            circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle, color, (radius, radius), radius)
            self._window.blit(circle, (position[0] - radius, position[1] - radius))
        else:
            pygame.draw.circle(self._window, color, position, radius)

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

        position = (
            (position[0] + 1) * self.width / 2,
            (-position[1] + 1) * self.height / 2
        )

        # Draw text
        if centered:
            self._centered_text(position, text, color, size, spacing, fixed_size)
        else: # Lines can wrap
            return self._uncentered_text(position, text, color, size, spacing, fixed_size, wrap)

    def draw_post_processing(self):
        """
        Draw world and post processing.
        """
        offset = (
            self.camera.pos[0] % 1 - (self.width / 2 / self.camera.pixels_per_meter) % 1,
            self.camera.pos[1] % 1 - (self.height / 2 / self.camera.pixels_per_meter) % 1
        )

        for x_coord, y_coord in numpy.ndindex(self.world_view.shape[:2]):
            for layer in (2, 0, 1):
                block = self.world_view[x_coord, y_coord][layer]
                if block != 0:
                    rect = self.camera.map_coord((x_coord + 1 + floor(self.camera.pos[0] - self.world_view.shape[0] / 2 - offset[0]), y_coord + floor(self.camera.pos[1] - self.world_view.shape[1] / 2 - offset[1]), 1, 1), from_world=True)
                    dest_rect = (
                        (rect[0] + 1 - rect[2]) * self.width / 2,
                        (-rect[1] + 1 - rect[3]) * self.height / 2,
                        rect[2] * self.width / 2,
                        rect[3] * self.height / 2
                    )
                    width, height = self._texBlocks.get_size()

                    y, x = divmod(block // 2, width // 16)
                    rect = (
                        x * 16,
                        height - (y + 1) * 16 - height % 16,
                        16,
                        16
                    )
                    source = pygame.Surface(rect[2:], pygame.SRCALPHA)
                    source.blit(self._texBlocks, (0, 0), rect)
                    source = pygame.transform.scale(pygame.transform.flip(source, not block % 2, 0), dest_rect[2:])
                    self._window.blit(source, (dest_rect[0], dest_rect[1]))

    def draw_block_highlight(self, x_coord, y_coord, color=(255, 0, 0)):
        """
        Highlight a single block.
        """
        if len(color) == 3:
            color = (*color, 100)
        rect = self.camera.map_coord((x_coord, y_coord, 1, 1), from_world=True)
        dest_rect = (
            (rect[0] + 1 - rect[2]) * self.width / 2,
            (-rect[1] + 1 - rect[3]) * self.height / 2,
            rect[2] * self.width,
            rect[3] * self.height
        )
        pygame.draw.rect(self._window, color, dest_rect, border_radius=1)
