# -*- coding: utf-8 -*-
from scripts.language import Translator
import scripts.geometry as geometry
import scripts.graphics as graphics
import scripts.util as util
import math
import sys
import os


class Page:
    opened = None
    
    def __init__(self, parent=None, columns: int=1, spacing: int=0, callback=None):
        self.children = []
        self.parent = parent
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
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        for child in self.children:
            child.update(window)
            if (not child.hover_callback is None) and child.rect.collidepoint(mouse_pos):
                child.hover_callback()
        if not self.callback is None:
            self.callback()
        if window.keybind("return") == 1 and not self.parent is None:
            self.parent.open()

    def draw(self, window: graphics.Window):
        pass

    def open(self):
        Page.opened = self


class Widget:
    def __init__(self, parent, size: [float], row: int=0, column: int=0, columnspan: int=1, fontsize: float=1.0, hover_callback=None, translator=None):
        self.parent = parent
        self.children = []
        self.rect = geometry.Rect(0, 0, *size)
        self.parent.children.append(self)
        self.row = row
        self.column = column
        self.columnspan = columnspan
        self.fontsize = fontsize
        self.hover_callback = hover_callback
        self.translator = translator

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
        window.draw_text(self.rect.center, self.translator.translate(self.text), (250, 250, 250, 200), self.fontsize, centered=True)


class Button(Widget):
    def __init__(self, *args, text: str="", callback=None, duration: float=0.2, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.callback = callback # When button pressed: function executed once
        self.clicked = 0
        self.duration = duration # When button pressed: self.clicked > 0 for [duration] seconds

    def update(self, window: graphics.Window):
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        if window.mouse_buttons[0] and self.rect.collidepoint(mouse_pos):
            if self.duration > 0:
                self.clicked = max(2, int(self.duration / window.delta_time))
            else:
                self.clicked = self.duration

        if self.clicked:
            self.clicked -= 1
            self.draw_clicked(window)
            if window.mouse_buttons[0] == 0 and self.clicked > 0:
                self.clicked = 0
            if self.clicked in (0, -2) and not self.callback is None:
                self.callback()
            
        else:
            self.draw_idle(window)

    def draw_idle(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (250, 0, 0, 200))
        window.draw_text(self.rect.center, self.translator.translate(self.text), (50, 0, 0, 250), self.fontsize, centered=True)

    def draw_clicked(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (200, 0, 0, 200))
        window.draw_text(self.rect.center, self.translator.translate(self.text), (0, 0, 0, 250), self.fontsize, centered=True)


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
            value = min(1, max(0, (window.mouse_pos[0] / window.width * 2 - self.rect.x) / self.rect.w))
            if value != self.value and not self.callback is None:
                if value < 0.02:
                    value = 0
                elif value > 0.98:
                    value = 1
                self.value = value
                self.callback()

        self.draw(window)

    def draw(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (60, 0, 0, 200))
        window.draw_rect(self.slider_rect[:2], self.slider_rect[2:], (250, 0, 0, 200))
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
        self.slider_y = 0

    def update(self, window: graphics.Window):
        adjust_offset = max(self.offset, self.children[-1].rect.y - self.rect.y - self.spacing)
        adjust_offset = min(adjust_offset, self.children[0].rect.bottom - self.rect.bottom + self.spacing)
        self.offset += window.mouse_wheel[3] / window.height * 10
        if adjust_offset != self.offset:
            self.offset = (adjust_offset + self.offset * 3) / 4

        self.draw(window)
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        window.stencil_rect = (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2, self.rect[2] / 2, self.rect[3] / 2)
        for child in self.children:
            y = child.rect.y
            child.rect.y -= self.offset
            child.update(window)
            child.rect.y = y
        window.stencil_rect = None

        for child in self.children:
            rect = child.rect.copy()
            rect.y -= self.offset
            if (not child.hover_callback is None) and rect.collidepoint(mouse_pos):
                child.hover_callback()

        if not self.callback is None:
            self.callback()

    def layout(self):
        Page.layout(self)
        self.offset = self.children[0].rect.bottom - self.rect.bottom + self.spacing
        self.start_offset = self.offset

    def draw(self, window: graphics.Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (60, 60, 60, 200))


def HoverBox(window: graphics.Window, rect: list, text: list, translator=None):
    """
    Draw a box with multi colored text.
    text: [("text", (r, g, b, a))]
    """
    window.draw_rect(rect[:2], rect[2:], (60, 60, 60, 250))
    start = (0.02, rect[3] - 0.04)
    x = 0
    y = 0
    for text, fontsize, color in text:
        for i, text_snippet in enumerate(text.split("\n")):
            text_snippet = translator.translate(text_snippet)
            pos = (rect[0] + start[0] + x,
                   rect[1] + start[1] + y)
            x += window.draw_text(pos, text_snippet, color, size=fontsize)
            if i != len(text.split("\n")) - 1:
                y -= 0.1 * fontsize
                x = 0


class Menu:
    def __init__(self, window: graphics.Window):
        self.window = window
        self.in_game = False
        def toggle_in_game():
            self.in_game = not self.in_game
        translator = Translator(window.options["language"])

        ###---###  Main page  ###---###
        main_page = Page(columns=2, spacing=0.1)
        Label(main_page, (1, .3), row=0, column=0, columnspan=2, text="Hello, World!", fontsize=2, translator=translator)
        button_play = Button(main_page, (1.4, .2), row=1, column=0, columnspan=2, callback=toggle_in_game, text="Play", translator=translator)
        button_settings = Button(main_page, (.65, .2), row=2, column=0, text="Settings", translator=translator)
        Button(main_page, (.65, .2), row=2, column=1, callback=window.quit, text="Quit", translator=translator)
        main_page.layout()
        main_page.open()

        ###---###  Settings page  ###---###
        settings_page = Page(parent=main_page, columns=2, spacing=0.1)
        Label(settings_page, (1, .3), row=0, column=0, columnspan=2, text="Settings", fontsize=2, translator=translator)
        button_settings_video_open = Button(settings_page, (.65, .2), row=1, column=0, text="Video Settings", translator=translator)
        button_settings_audio_open = Button(settings_page, (.65, .2), row=1, column=1, text="Audio Settings", translator=translator)
        button_settings_control_open = Button(settings_page, (.65, .2), row=2, column=0, text="Control Settings", translator=translator)
        button_settings_world_open = Button(settings_page, (.65, .2), row=2, column=1, text="World Settings", translator=translator)
        button_settings_back = Button(settings_page, (1.4, .2), row=3, column=0, columnspan=2, callback=main_page.open, text="Back", translator=translator)
        settings_page.layout()
        button_settings.callback = settings_page.open

        """
        Settings
            Video
                brightness
                animations
                show fps
                show debug menu
                opengl version
                relational font size
            Audio
                Volume
                (music)
                ambient
            Gameplay
                world generation threads
                pregenerate distance
                simulation distance
        """

        ###---###  Video settings page  ###---###
        settings_video_page = Page(parent=settings_page, spacing=0.1)
        Label(settings_video_page, (1, .1), row=0, column=0, text="Video Settings", fontsize=2, translator=translator)
        Label(settings_video_page, (1, .1), row=1, column=0, text="Scroll to see more options and hover over options to see descriptions", fontsize=1, translator=translator)
        settings_video_scrollbox = ScrollBox(settings_video_page, (1.4, 1), row=2, column=0, columns=2)

        def settings_video_hover(side, *description):
            HoverBox(window, (settings_video_scrollbox.rect[2] / 2 * side + settings_video_scrollbox.rect[0] + settings_video_scrollbox.spacing / 4,
                              settings_video_scrollbox.rect[1] + settings_video_scrollbox.spacing / 2,
                              settings_video_scrollbox.rect[2] / 2 - settings_video_scrollbox.spacing / 2,
                              settings_video_scrollbox.rect[3] - settings_video_scrollbox.spacing),
                     description, translator=translator)

        # Fps slider
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

        if window.options["enableVsync"]:
            value = 0
        else:
            value = window.options["maxFps"] / 1000
        slider_fps = Slider(settings_video_scrollbox, (.6, 0.18), row=1, column=0, value=value)
        slider_fps.callback = slider_fps_update
        label_fps = Label(settings_video_scrollbox, (.6, 0.18), row=1, column=0, translator=translator)
        slider_fps_update()
        label_fps.hover_callback = lambda: settings_video_hover(1,
            ("Max Fps\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("high\n\n", 0.8, (250, 0, 0, 200)),
            ("Limit the Fps at a cap.\nVsync: Fps limit is\nsynchronized with your\nscreen's refresh rate.", 0.8, (250, 250, 250, 200))
        )

        # Resolution slider
        def slider_resolution_update():
            resolution = int(slider_resolution.value * 3) + 1
            label_resolution.text = "Resolution: " + str(resolution)
            window.set_resolution(resolution)

        value = (window.options["resolution"] - 1) / 3
        slider_resolution = Slider(settings_video_scrollbox, (.6, 0.18), row=1, column=1, value=value)
        slider_resolution.callback = slider_resolution_update
        label_resolution = Label(settings_video_scrollbox, (.6, 0.18), row=1, column=1, text="Resolution: " + str(window.options["resolution"]), translator=translator)
        label_resolution.hover_callback = lambda: settings_video_hover(0,
            ("Resolution\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("medium\n\n", 0.8, (250, 150, 0, 200)),
            ("Set the resolution\nof in-game objects.", 0.8, (250, 250, 250, 200))
        )

        # Fullscreen button
        def button_fullscreen_update():
            if util.system == "Darwin":
                return
            window.toggle_fullscreen()
            button_fullscreen.text = "Fullscreen: " + str(window.fullscreen)

        if util.system == "Darwin":
            button_fullscreen = Button(settings_video_scrollbox, (0.6, .18), row=2, column=0, callback=button_fullscreen_update, text="Fullscreen: Disabled", translator=translator)
        else:
            button_fullscreen = Button(settings_video_scrollbox, (0.6, .18), row=2, column=0, callback=button_fullscreen_update, text="Fullscreen: False", translator=translator)
        button_fullscreen.hover_callback = lambda: settings_video_hover(1,
            ("Fullscreen\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("none", 0.8, (0, 250, 0, 200))
        )

        # Particle slider
        def slider_particles_update():
            particles = int(slider_particles.value * 10)
            label_particles.text = "Particle Density: " + str(particles)
            window.options["particles"] = particles

        value = window.options["particles"] / 10
        slider_particles = Slider(settings_video_scrollbox, (.6, 0.18), row=2, column=1, value=value)
        slider_particles.callback = slider_particles_update
        label_particles = Label(settings_video_scrollbox, (.6, 0.18), row=2, column=1, translator=translator)
        slider_particles_update()
        label_particles.hover_callback = lambda: settings_video_hover(0,
            ("Particle Density\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("high\n\n", 0.8, (250, 0, 0, 200)),
            ("Limit the amount of\nparticles, which can be\nspawned at once.", 0.8, (250, 250, 250, 200))
        )

        # Show fps button
        def button_show_fps_update():
            window.options["show fps"] = not window.options["show fps"]
            button_show_fps.text = "Show Fps: " + str(window.options["show fps"])

        button_show_fps = Button(settings_video_scrollbox, (0.6, .18), row=3, column=0, callback=button_show_fps_update, text="Show Fps: " + str(window.options["show fps"]), translator=translator)
        button_show_fps.hover_callback = lambda: settings_video_hover(1,
            ("Show Fps\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("low\n\n", 0.8, (250, 250, 0, 200))
        )

        # Show debug button
        def button_show_debug_update():
            window.options["show debug"] = not window.options["show debug"]
            button_show_debug.text = "Show debug: " + str(window.options["show debug"])

        button_show_debug = Button(settings_video_scrollbox, (0.6, .18), row=3, column=1, callback=button_show_debug_update, text="Show debug: " + str(window.options["show debug"]), translator=translator)
        button_show_debug.hover_callback = lambda: settings_video_hover(0,
            ("Show debug info\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("low\n\n", 0.8, (250, 250, 0, 200))
        )

        # Post processing button
        def button_post_processing_update():
            window.options["post processing"] = not window.options["post processing"]
            button_post_processing.text = "Post process: " + str(window.options["post processing"])

        button_post_processing = Button(settings_video_scrollbox, (0.6, .18), row=4, column=0, callback=button_post_processing_update, text="Post process: " + str(window.options["post processing"]), translator=translator)
        button_post_processing.hover_callback = lambda: settings_video_hover(1,
            ("Post processing\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("medium\n\n", 0.8, (250, 150, 0, 200)),
            ("When enabled, post\nprocessing is performed\nafter the actual rendering\nfor additional visual effects.", 0.8, (250, 250, 250, 200))
        )

        # Language button
        def button_language_update():
            if window.options["language"] == "english":
                window.options["language"] = "deutsch"
            else:
                window.options["language"] = "english"
            translator.language = window.options["language"]
            button_language.text = "Language: " + window.options["language"].title()

        button_language = Button(settings_video_scrollbox, (0.6, .18), row=4, column=1, callback=button_language_update, text="Language: " + window.options["language"].title(), translator=translator)
        button_language.hover_callback = lambda: settings_video_hover(0,
            ("Language\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("none\n\n", 0.8, (0, 250, 0, 200)),
            ("Select either English\nor German as the\nused language.", 0.8, (250, 250, 250, 200))
        )

        # Antialiasing slider
        def slider_antialiasing_update():
            antialiasing = (0, 1, 2, 4, 8, 16)[round(slider_antialiasing.value * 5)]
            if antialiasing == 0:
                label_antialiasing.text = "Antialiasing: Off"
            else:
                label_antialiasing.text = "Antialiasing: " + str(antialiasing)
            window.set_antialiasing(antialiasing)

        if window.options["antialiasing"]:
            value = [i / 5 for i in range(1, 6)][round(math.log2(window.options["antialiasing"]))]
        else:
            value = 0
        slider_antialiasing = Slider(settings_video_scrollbox, (.6, 0.18), row=5, column=0, value=value)
        slider_antialiasing.callback = slider_antialiasing_update
        label_antialiasing = Label(settings_video_scrollbox, (.6, 0.18), row=5, column=0, translator=translator)
        slider_antialiasing_update()
        label_antialiasing.hover_callback = lambda: settings_video_hover(1,
            ("Antialiasing\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("low\n\n", 0.8, (250, 250, 0, 200)),
            ("Set the level of antialiasing.\nAntialiasing creates\nsmoother edges of\nshapes.", 0.8, (250, 250, 250, 200))
        )
        """
        # Map buffers button
        def button_map_buffers_update():
            window.toggle_map_buffers()
            button_map_buffers.text = "Map Buffers: " + str(window.options["map buffers"])

        button_map_buffers = Button(settings_video_scrollbox, (0.6, .18), row=5, column=1, callback=button_map_buffers_update, text="Map Buffers: " + str(window.options["map buffers"]), translator=translator)
        button_map_buffers.hover_callback = lambda: settings_video_hover(0,
            ("Map Buffers\n", 1, (250, 250, 250, 200)),
            ("Performance impact: ", 0.8, (250, 250, 250, 200)),
            ("none\n\n", 0.8, (0, 250, 0, 200)),
            ("When enabled, rendering\ndata is directly copied\ninto buffers.", 0.8, (250, 250, 250, 200))
        )
        """

        button_settings_back = Button(settings_video_page, (1.4, .2), row=3, column=0, callback=settings_page.open, text="Back", translator=translator)
        settings_video_page.layout()
        button_settings_video_open.callback = settings_video_page.open

        ###---###  Audio settings page  ###---###
        settings_audio_page = Page(parent=settings_page, columns=1, spacing=0.1)
        Label(settings_audio_page, (1, .3), row=0, column=0, text="Audio Settings", fontsize=2, translator=translator)
        Button(settings_audio_page, (1.4, .2), row=1, column=0, callback=settings_page.open, text="Back", translator=translator)
        settings_audio_page.layout()
        button_settings_audio_open.callback = settings_audio_page.open

        settings_world_page = Page(parent=settings_page, columns=1, spacing=0.1)
        Label(settings_world_page, (1, .3), row=0, column=0, text="World Settings", fontsize=2, translator=translator)
        Button(settings_world_page, (1.4, .2), row=1, column=0, callback=settings_page.open, text="Back", translator=translator)
        settings_world_page.layout()
        button_settings_world_open.callback = settings_world_page.open

        ###---###  Controls settings page  ###---###
        settings_control_page = Page(parent=settings_page, columns=2, spacing=0.1)
        Label(settings_control_page, (1, .2), row=0, column=0, columnspan=2, text="Control Settings", fontsize=2, translator=translator)
        Label(settings_control_page, (1, .1), row=1, column=0, columnspan=2, text="Click a button and press a key to bind a new key to an action", fontsize=1, translator=translator)

        scrollbox = ScrollBox(settings_control_page, (1.4, 1), row=2, column=0, columnspan=2, columns=2)
        keys = list(filter(lambda x: x.startswith("key."), window.options))
        buttons = {}
        selected = None

        def select_key(key):
            nonlocal selected
            for i in buttons:
                if i != key:
                    buttons[i].clicked = 0
            selected = key
            scrollbox.parent = None

        def update_key():
            nonlocal selected
            if not selected is None:
                keys = window.get_pressed_keys() + window.get_pressed_mods()
                if keys:
                    buttons[selected].clicked = 0
                    buttons[selected].text = keys[0]
                    window.options[buttons[selected].key_identifer] = keys[0].lower()
                    window.keys: dict = dict.fromkeys([value for key, value in window.options.items() if key.startswith("key.")], 0)
                    selected = None
                    scrollbox.parent = settings_page

        def reset_keys():
            for option, value in window.options_default.items():
                if not option.startswith("key."):
                    continue
                window.options[option] = value
                window.keys: dict = dict.fromkeys([value for key, value in window.options.items() if key.startswith("key.")], 0)
                buttons[option].text = value.title()

        for i, key in enumerate(keys):
            Label(scrollbox, (0.6, .18), row=i, column=0, text=key.split(".")[1].title(), translator=translator)
            buttons[key] = Button(scrollbox, (0.6, .18), row=i, column=1, callback=lambda key=key: select_key(key), text=window.options[key].title(), duration=-1, translator=translator)
            buttons[key].key_identifer = key
        scrollbox.callback = update_key

        Button(settings_control_page, (0.65, .2), row=3, column=0, callback=settings_page.open, text="Back", translator=translator)
        Button(settings_control_page, (0.65, .2), row=3, column=1, callback=reset_keys, text="Reset", translator=translator)
        settings_control_page.layout()
        button_settings_control_open.callback = settings_control_page.open

    def update(self):
        """
        Update all widgets on the currently opened page.
        """
        if not Page.opened is None:
            Page.opened.update(self.window)