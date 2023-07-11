# -*- coding: utf-8 -*-
import math
import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

import scripts.geometry as geometry
import scripts.graphics as graphics
import scripts.util as util


class Page:
    opened = None
    
    def __init__(self, columns: int=1, spacing: int=0, callback=None):
        self.children = []
        self.columns = columns
        self.spacing = spacing
        self.callback = callback

    def layout(self):
        """
        Position all widgets in a grid on a page.
        """
        width = [0 for _ in range(self.columns)]
        height = []

        for i, child in enumerate(self.children):
            width[child.column] = max(width[child.column], child.rect.w / child.columnspan - self.spacing * (child.columnspan - 1))
            if len(height) > child.row:
                height[child.row] = max(height[child.row], child.rect.h)
            else:
                height.append(child.rect.h)

        total_width = sum(width) + self.spacing * (self.columns - 1)
        total_height = sum(height) + self.spacing * (len(height) - 1)

        for i, child in enumerate(self.children):
            child.row = min(child.row, len(height) - 1)
            child.rect.centerx = sum(width[:child.column + 1]) - total_width / 2 + self.spacing * (child.column + (child.columnspan - 1) / 2) + width[child.column] * (child.columnspan - 1) / 2 - width[child.column] / 2
            child.rect.centery = sum(height[:child.row + 1]) - total_height / 2 + self.spacing * child.row - height[child.row] + child.rect.h - height[child.row] / 2
            child.rect.centery = -child.rect.centery
            child.layout()

    def update(self, window: graphics.Window):
        self.draw(window)
        for child in self.children:
            child.update(window)
        if not self.callback is None:
            self.callback()

    def draw(self, window: graphics.Window):
        pass

    def open(self):
        Page.opened = self


class Widget:
    def __init__(self, parent, size: [float], row: int=0, column: int=0, columnspan: int=1, fontsize: float=1.0):
        self.parent = parent
        self.children = []
        self.rect = geometry.Rect(0, 0, *size)
        self.parent.children.append(self)
        self.row = row
        self.column = column
        self.columnspan = columnspan
        self.fontsize = fontsize

        if not 0 <= self.column < parent.columns:
            raise ValueError("Invalid Column " + str(self.column) + " for parent with " + str(parent.columns) + " column(s).")

    def update(self, window: graphics.Window):
        self.draw()
        for child in self.children:
            child.update(window)

    def layout(self):
        return


class Label(Widget):
    def __init__(self, *args, text: str="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self, window: graphics.Window):
        window.draw_text(self.rect.center, self.text, (255, 255, 255, 255), self.fontsize, centered=True)


class Button(Widget):
    def __init__(self, *args, text: str="", callback=None, duration: float=0.2, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.callback = callback # When button pressed: function executed once
        self.clicked = 0
        self.duration = duration # When button pressed: self.clicked > 0 for [duration] seconds

    def update(self, window: graphics.Window):
        pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        if window.mouse_buttons[0] and self.rect.collidepoint(pos):
            self.clicked = max(2, int(self.duration / window.delta_time))

        if self.clicked:
            self.clicked -= 1
            self.draw_clicked(window)
            if self.clicked == 0 and not self.callback is None:
                self.callback()
        else:
            self.draw_idle(window)

    def draw_idle(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (255, 0, 0, 255))
        window.draw_text(self.rect.center, self.text, (0, 0, 0, 255), self.fontsize, centered=True)

    def draw_clicked(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (255, 0, 0, 200))
        window.draw_text(self.rect.center, self.text, (0, 0, 0, 255), self.fontsize, centered=True)


class Space(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self, window: graphics.Window):
        ...


class Slider(Widget):
    def __init__(self, *args, callback=None, value=0.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.value = value
        self.selected = False
        self.slider_rect = self.rect.copy()

    def update(self, window: graphics.Window):
        self.slider_rect.h = self.rect.h
        self.slider_rect.w = self.rect.h / 6
        self.slider_rect.x = self.rect.x + (self.rect.w - self.slider_rect.w) * self.value
        self.slider_rect.y = self.rect.y

        if self.slider_rect.collidepoint((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)) and window.mouse_buttons[0] == 1:
            self.selected = True
        elif not window.mouse_buttons[0]:
            self.selected = False

        if self.selected:
            value = min(1.0, max(0.0, (window.mouse_pos[0] / window.width * 2 - self.rect.x) / self.rect.w))
            if value != self.value and not self.callback is None:
                if value < 0.02:
                    value = 0
                elif value > 0.98:
                    value = 1
                self.callback()
            self.value = value

        self.draw(window)

    def draw(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (50, 0, 0, 200))
        window.draw_rect(self.slider_rect[:2], self.slider_rect[2:], (100, 0, 0, 200))
        #window.draw_rect((self.rect[0], self.rect.centery - self.rect[3] / 8), (self.rect[2], self.rect[3] / 4), (50, 0, 0, 200))
        #window.draw_rect(self.slider_rect[:2], self.slider_rect[2:], (100, 0, 0, 200))
        #window.draw_circle(self.slider_rect.center, self.slider_rect.h_half, (200, 0, 0, 255))


class Entry(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.selected = False
        self.cursor = 0

    def update(self):
        if window.unicode == "\x08":
            self.text = self.text[:-1]
        elif window.unicode.isprintable():
            self.text += window.unicode

        self.draw()

    def draw(self):
        window.draw_rect(self.rect[:2], self.rect[2:], (255, 0, 0, 200))
        window.draw_text(self.rect.center, self.text, (0, 0, 0, 255), self.fontsize, centered=True)


class Switch(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self):
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)


class ScrollBox(Widget):
    def __init__(self, *args, columns=1, spacing=0.1, callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.children = []
        self.columns = columns
        self.spacing = spacing
        self.offset = 0
        self.start_offset = 0
        self.callback = callback

    def update(self, window: graphics.Window):
        adjust_offset = min(self.offset, self.children[0].rect.bottom - self.rect.bottom + self.spacing)
        adjust_offset = max(adjust_offset, self.children[-1].rect.y - self.rect.y - self.spacing)
        self.offset += window.mouse_wheel[3] / window.height * 6
        if adjust_offset != self.offset:
            self.offset = (adjust_offset + self.offset * 3) / 4

        self.draw(window)
        window.stencil_rect = (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2, self.rect[2] / 2, self.rect[3] / 2)
        for child in self.children:
            y = child.rect.y
            child.rect.y -= self.offset
            child.update(window)
            child.rect.y = y
        window.stencil_rect = None

        if not self.callback is None:
            self.callback()

    def layout(self):
        Page.layout(self)
        self.offset = self.children[0].rect.bottom - self.rect.bottom + self.spacing
        self.start_offset = self.offset

    def draw(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (60, 60, 60, 200))


class Menu:
    def __init__(self, window: graphics.Window):
        self.window = window

        self.in_game = False
        def toggle_in_game():
            self.in_game = not self.in_game

        # Main page
        main_page = Page(columns=2, spacing=0.1)
        Label(main_page, (1, .3), row=0, column=0, columnspan=2, text="Hello, World!", fontsize=2)
        button_play = Button(main_page, (1.4, .2), row=1, column=0, columnspan=2, callback=toggle_in_game, text="Play")
        button_settings = Button(main_page, (.65, .2), row=2, column=0, text="Settings")
        Button(main_page, (.65, .2), row=2, column=1, callback=window.quit, text="Quit")
        main_page.layout()
        main_page.open()

        # Settings page
        settings_page = Page(columns=2, spacing=0.1)
        Label(settings_page, (1, .3), row=0, column=0, columnspan=2, text="Options", fontsize=2)
        button_settings_video_open = Button(settings_page, (.65, .2), row=1, column=0, text="Video Settings")
        button_settings_audio_open = Button(settings_page, (.65, .2), row=1, column=1, text="Audio Settings")
        button_settings_control_open = Button(settings_page, (.65, .2), row=2, column=0, text="Control Settings")
        button_settings_back = Button(settings_page, (1.4, .2), row=3, column=0, columnspan=2, callback=main_page.open, text="Back")
        settings_page.layout()
        button_settings.callback = settings_page.open

        # Video settings page
        settings_video_page = Page(columns=2, spacing=0.1)
        Label(settings_video_page, (1, .3), row=0, column=0, columnspan=2, text="Video Settings", fontsize=2)

        if window.options["enableVsync"]:
            value = 0
        else:
            value = window.options["maxFps"] / 1000
        slider_fps = Slider(settings_video_page, (.65, 0.2), row=1, column=0, value=value)
        label_fps = Label(settings_video_page, (.65, 0.2), row=1, column=0)
        def slider_fps_update():
            fps = round(slider_fps.value * 100) * 10
            if fps:
                show_fps = str(fps)
                window.options["maxFps"] = fps
                if window.options["enableVsync"]:
                    window.options["enableVsync"] = False
                    window.resize()
            else:
                show_fps = "Vsync"
                window.options["maxFps"] = 1000
                if not window.options["enableVsync"]:
                    window.options["enableVsync"] = True
                    window.resize()
            label_fps.text = "Max FPS: " + show_fps
        slider_fps_update()
        slider_fps.callback = slider_fps_update

        value = window.options["particles"] / 10
        slider_particles = Slider(settings_video_page, (.65, 0.2), row=1, column=1, value=value)
        label_particles = Label(settings_video_page, (.65, 0.2), row=1, column=1)
        def slider_particles_update():
            particles = int(slider_particles.value * 10)
            label_particles.text = "Particle Density: " + str(particles)
            window.options["particles"] = particles
        slider_particles.callback = slider_particles_update
        slider_particles_update()

        button_settings_back = Button(settings_video_page, (0.65, .2), row=2, column=0, callback=window.toggle_fullscreen, text="Fullscreen")
        button_settings_back = Button(settings_video_page, (0.65, .2), row=2, column=1, callback=window.toggle_wire_frame, text="Wireframe")

        button_settings_back = Button(settings_video_page, (1.4, .2), row=3, column=0, columnspan=2, callback=settings_page.open, text="Back")
        settings_video_page.layout()
        button_settings_video_open.callback = settings_video_page.open

        # Audio settings page
        settings_audio_page = Page(columns=1, spacing=0.1)
        Label(settings_audio_page, (1, .3), row=0, column=0, text="Audio Settings", fontsize=2)
        Button(settings_audio_page, (1.4, .2), row=1, column=0, callback=settings_page.open, text="Back")
        settings_audio_page.layout()
        button_settings_audio_open.callback = settings_audio_page.open

        # Controls settings page
        settings_control_page = Page(columns=1, spacing=0.1)
        Label(settings_control_page, (1, .3), row=0, column=0, text="Control Settings", fontsize=2)

        scrollbox = ScrollBox(settings_control_page, (1.4, 1.2), row=1, column=0, columns=2)
        keys = list(filter(lambda x: x.startswith("key."), window.options))
        buttons = {}
        selected = None

        def select_key(key):
            nonlocal selected
            selected = key

        def update_key():
            nonlocal selected
            if not selected is None:
                keys = window.get_pressed_keys() + window.get_pressed_mods()
                if keys:
                    buttons[selected].text = keys[0]
                    window.options[buttons[selected].key_identifer] = keys[0].lower()
                    window.keys: dict = dict.fromkeys([value for key, value in window.options.items() if key.startswith("key.")], 0)
                    selected = None

        for i, key in enumerate(keys):
            Label(scrollbox, (0.6, .2), row=i, column=0, text=key.split(".")[1].title())
            buttons[key] = Button(scrollbox, (0.6, .2), row=i, column=1, callback=lambda key=key: select_key(key), text=window.options[key].title())
            buttons[key].key_identifer = key
        scrollbox.callback = update_key

        Button(settings_control_page, (1.4, .2), row=2, column=0, callback=settings_page.open, text="Back")
        settings_control_page.layout()
        button_settings_control_open.callback = settings_control_page.open

    def update(self):
        """
        Update all widgets on the currently opened page.
        """
        if not Page.opened is None:
            Page.opened.update(self.window)