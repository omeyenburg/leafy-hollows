# -*- coding: utf-8 -*-
from scripts.utility.language import Translator
from scripts.graphics.window import Window
from scripts.utility.const import *
import scripts.utility.geometry as geometry
import scripts.utility.options as options
import math
import sys
import os


class Page:
    opened = None
    
    def __init__(self, parent=None, columns: int=1, spacing: int=0, callback=None):
        self.children = [] # List of all widgets
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

    def update(self, window: Window):
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

    def draw(self, window: Window):
        pass

    def open(self):
        Page.opened = self


class Widget:
    def __init__(self, parent, size: [float], row: int=0, column: int=0, columnspan: int=1, fontsize: float=1.0, hover_callback=None, translator=None):
        self.parent = parent
        self.children = [] # List of all child widgets (not used)
        self.rect = geometry.Rect(0, 0, *size) # Rect will be moved, when parent.layout is called
        self.parent.children.append(self)
        self.row = row
        self.column = column
        self.columnspan = columnspan
        self.fontsize = fontsize
        self.hover_callback = hover_callback
        self.translator = translator

        if not 0 <= self.column < parent.columns:
            raise ValueError("Invalid Column " + str(self.column) + " for parent with " + str(parent.columns) + " column(s).")

    def update(self, window: Window):
        self.draw()
        for child in self.children:
            child.update(window)

    def layout(self):
        return


class Label(Widget):
    def __init__(self, *args, text: str="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self, window: Window):
        window.draw_text(self.rect.center, self.translator.translate(self.text), (250, 250, 250, 200), self.fontsize, centered=True)


class Button(Widget):
    def __init__(self, *args, text: str="", callback=None, duration: float=0.2, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.callback = callback # When button pressed: function executed once
        self.clicked = 0
        self.duration = duration # When button pressed: self.clicked > 0 for [duration] seconds

    def update(self, window: Window):
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

    def draw_idle(self, window: Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (250, 0, 0, 200))
        window.draw_text(self.rect.center, self.translator.translate(self.text), (50, 0, 0, 250), self.fontsize, centered=True)

    def draw_clicked(self, window: Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (200, 0, 0, 200))
        window.draw_text(self.rect.center, self.translator.translate(self.text), (0, 0, 0, 250), self.fontsize, centered=True)


class Slider(Widget):
    def __init__(self, *args, callback=None, value=0.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.value = value
        self.selected = False
        self.slider_rect = self.rect.copy()

    def update(self, window: Window):
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

    def draw(self, window: Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (60, 0, 0, 200))
        window.draw_rect(self.slider_rect[:2], self.slider_rect[2:], (250, 0, 0, 200))

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

    def update(self, window: Window):
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

    def draw(self, window: Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (60, 60, 60, 200))


def HoverBox(window: Window, rect: list, text: list, translator=None):
    """
    Draw a box with multi colored text.
    text: [("text", (r, g, b, a))]
    """
    window.draw_rect(rect[:2], rect[2:], (60, 60, 60, 250))
    start = (0.025, rect[3] - 0.05)
    x = 0
    y = 0
    wrap = True
    for text_snippet, fontsize, color in text:
        text_snippet = translator.translate(text_snippet)
        pos = (rect[0] + start[0] + x,
                rect[1] + start[1] + y)
        x_offset, y_offset = window.draw_text(pos, text_snippet, color, size=fontsize, wrap=rect[2] - 0.05)
        wrap = text_snippet[-1] == "\n"
        if wrap:
            y += y_offset
            x = 0
        else:
            x += x_offset


class Menu:
    def __init__(self, window: Window):
        self.window = window
        self.game_state = "menu"
        self.translator = Translator(window.options["language"])


        ###---###  Main page  ###---###
        self.main_page = Page(columns=2, spacing=0.1)
        Label(self.main_page, (1, .3), row=0, column=0, columnspan=2, text="Title", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        button_main_play = Button(self.main_page, (1.4, .2), row=1, column=0, columnspan=2, text="Play", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        button_main_settings = Button(self.main_page, (.65, .2), row=2, column=0, text="Settings", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        Button(self.main_page, (.65, .2), row=2, column=1, callback=window.quit, text="Quit", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        self.main_page.layout()
        self.main_page.open()


        ###---###  Generate world page  ###---###
        def open_generate_world():
            generate_world_page.open()
            self.game_state = "generate"
        
        def update_generate_world():
            dots = int(window.time * 2 % 4)
            label_generate_world.text = "Generating World" + "." * dots + " " * (3 - dots)
            
        generate_world_page = Page(columns=1, callback=update_generate_world)
        label_generate_world = Label(generate_world_page, (0.9, .3), text="Generating World   ", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        generate_world_page.layout()
        button_main_play.callback = open_generate_world


        ###---###  Settings page  ###---###
        settings_page = Page(parent=self.main_page, columns=2, spacing=0.1)
        Label(settings_page, (1, .3), row=0, column=0, columnspan=2, text="Settings", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        button_settings_video_open = Button(settings_page, (.65, .2), row=1, column=0, text="Video Settings", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        button_settings_audio_open = Button(settings_page, (.65, .2), row=1, column=1, text="Audio Settings", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        button_settings_control_open = Button(settings_page, (.65, .2), row=2, column=0, text="Control Settings", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        button_settings_world_open = Button(settings_page, (.65, .2), row=2, column=1, text="World Settings", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        button_settings_back = Button(settings_page, (1.4, .2), row=3, column=0, columnspan=2, callback=self.main_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        settings_page.layout()
        button_main_settings.callback = settings_page.open

        """
        Settings
            Video
                (brightness)
                (animations)
                show fps
                show debug menu
                (opengl version)
                relational font size
            Audio
                Volume
                (music)
                ambient
            Gameplay
                (world generation threads)
                (pregenerate distance)
                simulation distance
        """


        ###---###  Video settings page  ###---###
        settings_video_page = Page(parent=settings_page, spacing=0.1)
        Label(settings_video_page, (1, .1), row=0, column=0, text="Video Settings", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        Label(settings_video_page, (1, .1), row=1, column=0, text="Scroll to see more options and hover over options to see descriptions", fontsize=TEXT_SIZE_TEXT, translator=self.translator)
        settings_video_scrollbox = ScrollBox(settings_video_page, (1.4, 1), row=2, column=0, columns=2)

        def settings_video_hover(side, *description):
            HoverBox(window, (settings_video_scrollbox.rect[2] / 2 * side + settings_video_scrollbox.rect[0] + settings_video_scrollbox.spacing / 4,
                              settings_video_scrollbox.rect[1] + settings_video_scrollbox.spacing / 2,
                              settings_video_scrollbox.rect[2] / 2 - settings_video_scrollbox.spacing / 2,
                              settings_video_scrollbox.rect[3] - settings_video_scrollbox.spacing),
                     description, translator=self.translator)

        # Fps slider
        def slider_fps_update():
            fps = round(slider_fps.value * 100) * 10
            if fps:
                show_fps = f"{fps:5d}"
                window.options["max fps"] = fps
                if window.options["enable vsync"]:
                    window.options["enable vsync"] = False
                    window.resize()
            else:
                show_fps = "Vsync"
                window.options["max fps"] = 1000
                if not window.options["enable vsync"]:
                    window.options["enable vsync"] = True
                    window.resize()
            label_fps.text = "Max Fps: " + show_fps

        if window.options["enable vsync"]:
            value = 0
        else:
            value = window.options["max fps"] / 1000
        slider_fps = Slider(settings_video_scrollbox, (.6, 0.18), row=1, column=0, value=value)
        slider_fps.callback = slider_fps_update
        label_fps = Label(settings_video_scrollbox, (.6, 0.18), row=1, column=0, fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        slider_fps_update()
        label_fps.hover_callback = lambda: settings_video_hover(1,
            ("Max Fps\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("high\n", TEXT_SIZE_DESCRIPTION, (250, 0, 0, 200)),
            ("Limit the Fps at a cap.\nVsync: Fps limit is synchronized with your screen's refresh rate.", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200))
        )

        # Text resolution slider
        def slider_text_resolution_update():
            text_resolution = int(slider_text_resolution.value * 70) + 10
            label_text_resolution.text = "Text Resolution: " + str(text_resolution)
            window.set_text_resolution(text_resolution)

        value = (window.options["text resolution"] - 10) / 70
        slider_text_resolution = Slider(settings_video_scrollbox, (.6, 0.18), row=1, column=1, value=value)
        slider_text_resolution.callback = slider_text_resolution_update
        label_text_resolution = Label(settings_video_scrollbox, (.6, 0.18), row=1, column=1, text="Text Resolution: " + str(window.options["text resolution"]), fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        label_text_resolution.hover_callback = lambda: settings_video_hover(0,
            ("Text Resolution\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("medium\n", TEXT_SIZE_DESCRIPTION, (250, 150, 0, 200))
        )

        # Fullscreen button
        def button_fullscreen_update():
            if PLATFORM == "Darwin":
                return
            window.toggle_fullscreen()
            button_fullscreen.text = "Fullscreen: " + f"{str(window.fullscreen):5}"

        if PLATFORM == "Darwin":
            button_fullscreen = Button(settings_video_scrollbox, (0.6, .18), row=2, column=0, callback=button_fullscreen_update, text="Fullscreen: Disabled", fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        else:
            button_fullscreen = Button(settings_video_scrollbox, (0.6, .18), row=2, column=0, callback=button_fullscreen_update, text="Fullscreen: False", fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        button_fullscreen.hover_callback = lambda: settings_video_hover(1,
            ("Fullscreen\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("none", TEXT_SIZE_DESCRIPTION, (0, 250, 0, 200))
        )

        # Particle slider
        def slider_particles_update():
            particles = int(slider_particles.value * 10)
            label_particles.text = "Particle Density: " + f"{particles:2d}"
            window.options["particles"] = particles

        value = window.options["particles"] / 10
        slider_particles = Slider(settings_video_scrollbox, (.6, 0.18), row=2, column=1, value=value)
        slider_particles.callback = slider_particles_update
        label_particles = Label(settings_video_scrollbox, (.6, 0.18), row=2, column=1, fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        slider_particles_update()
        label_particles.hover_callback = lambda: settings_video_hover(0,
            ("Particle Density\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("high\n", TEXT_SIZE_DESCRIPTION, (250, 0, 0, 200)),
            ("Limit the amount of particles, which can be spawned at once.", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200))
        )

        # Show fps button
        def button_show_fps_update():
            window.options["show fps"] = not window.options["show fps"]
            button_show_fps.text = "Show Fps: " + f"{str(window.options['show fps']):5}"

        button_show_fps = Button(settings_video_scrollbox, (0.6, .18), row=3, column=0, callback=button_show_fps_update, text="Show Fps: " + str(window.options["show fps"]), fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        button_show_fps.hover_callback = lambda: settings_video_hover(1,
            ("Show Fps\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("low", TEXT_SIZE_DESCRIPTION, (250, 250, 0, 200))
        )

        # Show debug button
        def button_show_debug_update():
            window.options["show debug"] = not window.options["show debug"]
            button_show_debug.text = "Show debug: " + f"{str(window.options['show debug']):5}"

        button_show_debug = Button(settings_video_scrollbox, (0.6, .18), row=3, column=1, callback=button_show_debug_update, text="Show debug: " + str(window.options["show debug"]), fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        button_show_debug.hover_callback = lambda: settings_video_hover(0,
            ("Show debug\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("low", TEXT_SIZE_DESCRIPTION, (250, 250, 0, 200))
        )

        # Antialiasing slider
        def slider_antialiasing_update():
            antialiasing = (0, 1, 2, 4, 8, 16)[round(slider_antialiasing.value * 5)]
            if antialiasing == 0:
                label_antialiasing.text = "Antialiasing: False"
            else:
                label_antialiasing.text = "Antialiasing: " + f"{antialiasing:5d}"
            window.set_antialiasing(antialiasing)

        if window.options["antialiasing"]:
            value = [i / 5 for i in range(1, 6)][round(math.log2(window.options["antialiasing"]))]
        else:
            value = 0
        slider_antialiasing = Slider(settings_video_scrollbox, (.6, 0.18), row=4, column=0, value=value)
        slider_antialiasing.callback = slider_antialiasing_update
        label_antialiasing = Label(settings_video_scrollbox, (.6, 0.18), row=4, column=0, fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        slider_antialiasing_update()
        label_antialiasing.hover_callback = lambda: settings_video_hover(1,
            ("Antialiasing\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("low\n", TEXT_SIZE_DESCRIPTION, (250, 250, 0, 200)),
            ("Set the level of antialiasing.\nAntialiasing creates smoother edges of shapes.", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200))
        )

        # Language button
        def button_language_update():
            if window.options["language"] == "english":
                window.options["language"] = "deutsch"
            else:
                window.options["language"] = "english"
            self.translator.language = window.options["language"]
            button_language.text = "Language: " + window.options["language"].title()

        button_language = Button(settings_video_scrollbox, (0.6, .18), row=4, column=1, callback=button_language_update, text="Language: " + window.options["language"].title(), fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        button_language.hover_callback = lambda: settings_video_hover(0,
            ("Language\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
            ("none\n", TEXT_SIZE_DESCRIPTION, (0, 250, 0, 200)),
            ("Select either English or German as the language.", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200))
        )

        button_settings_back = Button(settings_video_page, (1.4, .2), row=3, column=0, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        settings_video_page.layout()
        button_settings_video_open.callback = settings_video_page.open


        ###---###  Audio settings page  ###---###
        settings_audio_page = Page(parent=settings_page, columns=1, spacing=0.1)
        Label(settings_audio_page, (1, .3), row=0, column=0, text="Audio Settings", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        
        # Volume slider
        def slider_volume_update():
            volume = slider_volume.value
            label_volume.text = "Volume: " + f"{int(volume * 100):3d}%"
            window.options["volume"] = volume

        value = window.options["volume"]
        slider_volume = Slider(settings_audio_page, (1.4, 0.18), row=1, column=0, value=value)
        slider_volume.callback = slider_volume_update
        label_volume = Label(settings_audio_page, (1.4, 0.18), row=1, column=0, fontsize=TEXT_SIZE_OPTION, translator=self.translator)
        slider_volume_update()

        Button(settings_audio_page, (1.4, .2), row=2, column=0, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        settings_audio_page.layout()
        button_settings_audio_open.callback = settings_audio_page.open


        ###---###  World settings page  ###---###
        settings_world_page = Page(parent=settings_page, columns=1, spacing=0.1)
        Label(settings_world_page, (1, .3), row=0, column=0, text="World Settings", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        Button(settings_world_page, (1.4, .2), row=1, column=0, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        settings_world_page.layout()
        button_settings_world_open.callback = settings_world_page.open


        ###---###  Controls settings page  ###---###
        settings_control_page = Page(parent=settings_page, columns=2, spacing=0.1)
        Label(settings_control_page, (1, .2), row=0, column=0, columnspan=2, text="Control Settings", fontsize=TEXT_SIZE_HEADING, translator=self.translator)
        Label(settings_control_page, (1, .1), row=1, column=0, columnspan=2, text="Click a button and press a key to bind a new key to an action", fontsize=TEXT_SIZE_TEXT, translator=self.translator)

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
                keys = window.get_pressed_mods() + window.get_pressed_keys()
                if keys:
                    buttons[selected].clicked = 0
                    buttons[selected].text = keys[0]
                    window.options[buttons[selected].key_identifer] = keys[0].lower()
                    window.keys: dict = dict.fromkeys([value for key, value in window.options.items() if key.startswith("key.")], 0)
                    selected = None
                    scrollbox.parent = settings_page

        def reset_keys():
            for option, value in options.default.items():
                if not option.startswith("key."):
                    continue
                window.options[option] = value
                window.keys: dict = dict.fromkeys([value for key, value in window.options.items() if key.startswith("key.")], 0)
                buttons[option].text = value.title()

        for i, key in enumerate(keys):
            Label(scrollbox, (0.6, .18), row=i, column=0, text=key.split(".")[1].title(), fontsize=TEXT_SIZE_TEXT, translator=self.translator)
            buttons[key] = Button(scrollbox, (0.6, .18), row=i, column=1, callback=lambda key=key: select_key(key), text=window.options[key].title(), duration=-1, fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
            buttons[key].key_identifer = key
        scrollbox.callback = update_key

        Button(settings_control_page, (0.65, .2), row=3, column=0, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        Button(settings_control_page, (0.65, .2), row=3, column=1, callback=reset_keys, text="Reset", fontsize=TEXT_SIZE_BUTTON, translator=self.translator)
        settings_control_page.layout()
        button_settings_control_open.callback = settings_control_page.open

    def update(self):
        """
        Update all widgets on the currently opened page.
        """
        if not Page.opened is None:
            Page.opened.update(self.window)

    def get_intro_texts(self):
        intro_texts = [
            "Title",
            "Move with [%s] and [%s]",
            "Jump with [%s]",
            "Crouch with [%s]",
            "Sprint with [%s]",
            "Escape from the caves!"
        ]

        formatter = (
            (),
            (self.window.options['key.left'].title(), self.window.options['key.right'].title()),
            (self.window.options['key.jump'].title(),),
            (self.window.options['key.crouch'].title(),),
            (self.window.options['key.sprint'].title(),),
            (),
            (),
        )

        intro_texts = [self.translator.translate(text) % value for text, value in zip(intro_texts, formatter)]

        return intro_texts