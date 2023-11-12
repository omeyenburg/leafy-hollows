# -*- coding: utf-8 -*-
from scripts.utility.language import translate
from scripts.utility.thread import threaded
from scripts.menu.widgets import *


class Menu:
    def __init__(self, window: Window):
        self.window: Window = window
        self.game_state: str = "menu"
        self.game_intro: int = False
        self.save_world = None # Function
        self.hover_box = None


        ###---###  Main page  ###---###
        self.main_page = Page(columns=2, spacing=MENU_SPACING)
        Label(self.main_page, MENU_TITLE_SIZE, columnspan=2, text="Title", fontsize=TEXT_SIZE_HEADING)
        button_main_play = Button(self.main_page, MENU_BUTTON_SIZE, columnspan=2, text="Play", fontsize=TEXT_SIZE_BUTTON, callback=lambda: self.set_state("load_world"))
        button_main_settings = Button(self.main_page, MENU_BUTTON_SMALL_SIZE, text="Settings", fontsize=TEXT_SIZE_BUTTON)
        Button(self.main_page, MENU_BUTTON_SMALL_SIZE, callback=window.quit, text="Quit", fontsize=TEXT_SIZE_BUTTON)
        self.main_page.layout()


        ###---###  Pause page  ###---###
        def button_pause_play_update():
            if self.game_intro:
                self.game_state = "intro"
                self.game_intro = False
            else:
                self.game_state = "game"

        def button_pause_menu_update():
            if not self.save_world is None:
                self.save_world()
            self.game_state = "menu"
            self.main_page.open()

        self.pause_page = Page(columns=1, spacing=MENU_SPACING)
        Label(self.pause_page, MENU_HEADING_SIZE, text="Paused", fontsize=TEXT_SIZE_HEADING)
        button_pause_play = Button(self.pause_page, MENU_BUTTON_SIZE, text="Play", callback=button_pause_play_update, fontsize=TEXT_SIZE_BUTTON)
        button_pause_menu = Button(self.pause_page, MENU_BUTTON_SIZE, text="Main Menu", callback=button_pause_menu_update, fontsize=TEXT_SIZE_BUTTON)
        self.pause_page.layout()


        ###---###  Death page  ###---###
        def button_death_menu_update():
            self.game_state = "menu"
            self.main_page.open()

        self.death_page = Page(columns=1, spacing=MENU_SPACING)
        Label(self.death_page, MENU_HEADING_SIZE, text="You Died", fontsize=TEXT_SIZE_HEADING)
        button_death_menu = Button(self.death_page, MENU_BUTTON_SIZE, text="Main Menu", callback=button_death_menu_update, fontsize=TEXT_SIZE_BUTTON)
        self.death_page.layout()


        ###---###  Loading page  ###---###
        self.loading_page_title: str = ""
        self.loading_page_progress: float = 0.0
        
        def update_loading_page():
            title_loading_page.text = self.loading_page_title
            description_loading_page.text = self.window.loading_progress[0]
            if self.window.loading_progress[2]:
                add = self.window.delta_time * 0.1
                if self.window.loading_progress[1] % 1 + add < 1:
                    self.window.loading_progress[1] += add
                self.loading_page_progress = max(0.05, min(1.0, (self.loading_page_progress + self.window.loading_progress[1] / self.window.loading_progress[2]) / 2))
            progress_loading_page.value = self.loading_page_progress

        self.loading_page = Page(columns=1, spacing=MENU_SPACING, callback=update_loading_page)
        title_loading_page = Label(self.loading_page, MENU_TITLE_SIZE, fontsize=TEXT_SIZE_HEADING)
        progress_loading_page = LoadingBar(self.loading_page, MENU_BUTTON_SIZE)
        description_loading_page = Label(self.loading_page, MENU_BUTTON_SIZE, fontsize=TEXT_SIZE_BUTTON)
        self.loading_page.layout()


        ###---###  Settings page  ###---###
        settings_page = Page(parent=self.main_page, columns=2, spacing=MENU_SPACING)

        button_settings_video_open = Button(settings_page, MENU_BUTTON_SMALL_SIZE, text="Video Settings", fontsize=TEXT_SIZE_BUTTON)
        button_settings_audio_open = Button(settings_page, MENU_BUTTON_SMALL_SIZE, text="Audio Settings", fontsize=TEXT_SIZE_BUTTON)
        button_settings_control_open = Button(settings_page, MENU_BUTTON_SMALL_SIZE, text="Control Settings", fontsize=TEXT_SIZE_BUTTON)
        button_settings_world_open = Button(settings_page, MENU_BUTTON_SMALL_SIZE, text="World Settings", fontsize=TEXT_SIZE_BUTTON)

        settings_page.layout()
        Label(settings_page, MENU_HEADING_SIZE, columnspan=2, text="Settings", fontsize=TEXT_SIZE_HEADING)
        settings_page.layout_prepend()
        Button(settings_page, MENU_BUTTON_SIZE, columnspan=2, callback=self.main_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON)
        settings_page.layout_append()
        button_main_settings.callback = settings_page.open


        ###---###  Video settings page  ###---###
        settings_video_page = Page(parent=settings_page, spacing=MENU_SPACING, columns=2)

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
            slider_fps.text = "Max Fps: " + show_fps

        if window.options["enable vsync"]:
            value = 0
        else:
            value = window.options["max fps"] / 1000
        slider_fps = Slider(settings_video_page, MENU_BUTTON_SMALL_SIZE, value=value)
        slider_fps.callback = slider_fps_update
        slider_fps_update()
        slider_fps.hover_callback = lambda: self.info_hover_box(
            slider_fps.rect.centerx < 0,
            "Max Fps",
            "high",
            "Limit the Fps at a cap. When Vsync is enabled, the Fps limit is synchronized with your screen's refresh rate."
        )

        # Text resolution slider
        def slider_text_resolution_update():
            text_resolution = int(slider_text_resolution.value * 70) + 10
            slider_text_resolution.text = "Text Resolution: " + str(text_resolution)
            window.set_text_resolution(text_resolution)

        value = (window.options["text resolution"] - 10) / 70
        slider_text_resolution = Slider(settings_video_page, MENU_BUTTON_SMALL_SIZE, value=value)
        slider_text_resolution.callback = slider_text_resolution_update
        slider_text_resolution_update()
        slider_text_resolution.hover_callback = lambda: self.info_hover_box(
            slider_text_resolution.rect.centerx < 0,
            "Text Resolution",
            "medium"
        )

        # Particle slider
        def slider_particles_update():
            particles = int(slider_particles.value * 10)
            slider_particles.text = "Particle Density: " + f"{particles:2d}"
            window.options["particles"] = particles

        value = window.options["particles"] / 10
        slider_particles = Slider(settings_video_page, MENU_BUTTON_SMALL_SIZE, value=value)
        slider_particles.callback = slider_particles_update
        slider_particles_update()
        slider_particles.hover_callback = lambda: self.info_hover_box(
            slider_particles.rect.centerx < 0,
            "Particle Density",
            "medium",
            "Limit the amount of particles, which can be spawned at once."
        )

        # Antialiasing slider
        def slider_antialiasing_update():
            antialiasing = (0, 1, 2, 4, 8, 16)[round(slider_antialiasing.value * 5)]
            if antialiasing == 0:
                slider_antialiasing.text = "Antialiasing: Off"
            else:
                slider_antialiasing.text = "Antialiasing: " + f"{antialiasing:5d}"
            window.set_antialiasing(antialiasing)

        if window.options["antialiasing"]:
            value = [i / 5 for i in range(1, 6)][round(math.log2(window.options["antialiasing"]))]
        else:
            value = 0
        slider_antialiasing = Slider(settings_video_page, MENU_BUTTON_SMALL_SIZE, value=value)
        slider_antialiasing.callback = slider_antialiasing_update
        slider_antialiasing_update()
        slider_antialiasing.hover_callback = lambda: self.info_hover_box(
            slider_antialiasing.rect.centerx < 0,
            "Antialiasing",
            "low",
            "Set the level of antialiasing. Antialiasing creates smoother edges of shapes."
        )

        # Shadow resolution slider
        def slider_shadow_resolution_update():
            shadow_resolution = (0, 1, 2, 4, 8, 16, 32)[round(slider_shadow_resolution.value * 6)]
            if shadow_resolution == 0:
                slider_shadow_resolution.text = "Shadow Resolution: Off"
            else:
                slider_shadow_resolution.text = "Shadow Resolution: " + f"{shadow_resolution:5d}"
            window.options["shadow resolution"] = shadow_resolution
            window._instance_shader.setvar("shadow_resolution", window.options["shadow resolution"])

        if window.options["shadow resolution"]:
            value = [i / 6 for i in range(1, 7)][round(math.log2(window.options["shadow resolution"]))]
        else:
            value = 0
        slider_shadow_resolution = Slider(settings_video_page, MENU_BUTTON_SMALL_SIZE, value=value)
        slider_shadow_resolution.callback = slider_shadow_resolution_update
        slider_shadow_resolution_update()
        slider_shadow_resolution.hover_callback = lambda: self.info_hover_box(
            slider_shadow_resolution.rect.centerx < 0,
            "Shadow Resolution",
            "high",
            "Set the resolution of shadows or disable shadow rendering."
        )

        # Fullscreen button
        def button_fullscreen_update():
            if PLATFORM == "Darwin":
                return
            window.toggle_fullscreen()
            button_fullscreen.text = "Fullscreen: " + f"{str(window._fullscreen):5}"

        if PLATFORM != "Darwin":
            if PLATFORM == "Darwin":
                button_fullscreen = Button(settings_video_page, MENU_BUTTON_SMALL_SIZE, callback=button_fullscreen_update, text="Fullscreen: Disabled", fontsize=TEXT_SIZE_OPTION)
            else:
                button_fullscreen = Button(settings_video_page, MENU_BUTTON_SMALL_SIZE, callback=button_fullscreen_update, text="Fullscreen: False", fontsize=TEXT_SIZE_OPTION)
            button_fullscreen.hover_callback = lambda: self.info_hover_box(
                button_fullscreen.rect.centerx < 0,
                "Fullscreen",
                "none"
            )

        # Show fps button
        def button_show_fps_update():
            window.options["show fps"] = not window.options["show fps"]
            button_show_fps.text = "Show Fps: " + f"{str(window.options['show fps']):5}"

        button_show_fps = Button(settings_video_page, MENU_BUTTON_SMALL_SIZE, callback=button_show_fps_update, text="Show Fps: " + str(window.options["show fps"]), fontsize=TEXT_SIZE_OPTION)
        button_show_fps.hover_callback = lambda: self.info_hover_box(
            button_show_fps.rect.centerx < 0,
            "Show Fps",
            "none"
        )

        # Show debug button
        def button_show_debug_update():
            window.options["show debug"] = not window.options["show debug"]
            button_show_debug.text = "Show debug: " + f"{str(window.options['show debug']):5}"

        button_show_debug = Button(settings_video_page, MENU_BUTTON_SMALL_SIZE, callback=button_show_debug_update, text="Show debug: " + str(window.options["show debug"]), fontsize=TEXT_SIZE_OPTION)
        button_show_debug.hover_callback = lambda: self.info_hover_box(
            button_show_debug.rect.centerx < 0,
            "Show debug",
            "low",
            "Show debug information for developers."
        )

        # Language button
        def button_language_update():
            if window.options["language"] == "english":
                window.options["language"] = "deutsch"
            else:
                window.options["language"] = "english"
            button_language.text = "Language: " + window.options["language"].title()

        button_language = Button(settings_video_page, MENU_BUTTON_SMALL_SIZE, callback=button_language_update, text="Language: " + window.options["language"].title(), fontsize=TEXT_SIZE_OPTION)
        button_language.hover_callback = lambda: self.info_hover_box(
            button_language.rect.centerx < 0,
            "Language",
            "none",
            "Select either English or German as the language."
        )
        
        settings_video_page.layout()
        Label(settings_video_page, MENU_HEADING_SIZE, columnspan=2, text="Video Settings", fontsize=TEXT_SIZE_HEADING)
        settings_video_page.layout_prepend()
        Button(settings_video_page, MENU_BUTTON_SIZE, columnspan=2, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON)
        settings_video_page.layout_append()
        button_settings_video_open.callback = settings_video_page.open


        ###---###  Audio settings page  ###---###
        settings_audio_page = Page(parent=settings_page, columns=2, spacing=MENU_SPACING)
        
        # Volume slider
        def slider_volume_update(slider, category):
            volume = slider.value
            if category == "master volume":
                name = category.title()
            else:
                name = category.split(" volume")[0].title()
            slider.text = name + ": " + f"{int(volume * 100):3d}%"
            window.options[category] = volume

        for category in filter(lambda option: option.endswith(" volume"), window.options):
            value = window.options[category]
            if category == "master volume":
                slider_volume = Slider(settings_audio_page, MENU_BUTTON_SIZE, columnspan=2, value=value)
            else:
                slider_volume = Slider(settings_audio_page, MENU_BUTTON_SMALL_SIZE, value=value)
            slider_volume.callback = lambda s=slider_volume, c=category: slider_volume_update(s, c)
            slider_volume.callback()

        settings_audio_page.layout()
        Label(settings_audio_page, MENU_HEADING_SIZE, columnspan=2, text="Audio Settings", fontsize=TEXT_SIZE_HEADING)
        settings_audio_page.layout_prepend()
        Button(settings_audio_page, MENU_BUTTON_SIZE, columnspan=2, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON)
        settings_audio_page.layout_append()
        button_settings_audio_open.callback = settings_audio_page.open


        ###---###  World settings page  ###---###
        settings_world_page = Page(parent=settings_page, columns=2, spacing=MENU_SPACING)

        # Simulation distance
        def slider_simulation_distance_update():
            simulation_distance = int(slider_simulation_distance.value * 15 + 5)
            slider_simulation_distance.text = "Simulation Distance: " + f"{simulation_distance:2d}"
            window.options["simulation distance"] = simulation_distance

        value = (window.options["simulation distance"] - 5) / 15
        slider_simulation_distance = Slider(settings_world_page, MENU_BUTTON_SMALL_SIZE, value=value)
        slider_simulation_distance.callback = slider_simulation_distance_update
        slider_simulation_distance_update()
        slider_simulation_distance.hover_callback = lambda: self.info_hover_box(
            slider_simulation_distance.rect.centerx < 0,
            "Simulation Distance",
            "high",
            "Set the distance of blocks, which are updated around the visible region."
        )

        # Delete world
        def button_delete_world_update():
            if file.exists("data/user/world.data"):
                delete_world_page.open()

        button_delete_world = Button(settings_world_page, MENU_BUTTON_SMALL_SIZE, callback=button_delete_world_update, text="Delete World", fontsize=TEXT_SIZE_BUTTON)
        button_delete_world.hover_callback = lambda: self.info_hover_box(
            button_delete_world.rect.centerx < 0,
            "Delete World",
            description="If you delete your world, a new world will be created."
        )

        settings_world_page.layout()
        Label(settings_world_page, MENU_HEADING_SIZE, columnspan=2, text="World Settings", fontsize=TEXT_SIZE_HEADING)
        settings_world_page.layout_prepend()
        Button(settings_world_page, MENU_BUTTON_SIZE, columnspan=2, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON)
        settings_world_page.layout_append()
        button_settings_world_open.callback = settings_world_page.open


        ###---###  Delete world page  ###---###
        def button_delete_world_confirm_update():
            file.delete("data/user/world.data")
            settings_world_page.open()

        delete_world_page = Page(parent=settings_world_page, columns=1, spacing=MENU_SPACING)
        Label(delete_world_page, MENU_HEADING_SIZE, text="If you delete your world, a new world will be created.", fontsize=TEXT_SIZE_BUTTON)
        button_delete_world_confirm = Button(delete_world_page, MENU_BUTTON_SIZE, callback=button_delete_world_confirm_update, text="Delete my world!", fontsize=TEXT_SIZE_BUTTON)
        Button(delete_world_page, MENU_BUTTON_SIZE, callback=settings_world_page.open, text="Cancel", fontsize=TEXT_SIZE_BUTTON)
        delete_world_page.layout()
        Label(delete_world_page, MENU_HEADING_SIZE, text="World Settings", fontsize=TEXT_SIZE_HEADING)
        delete_world_page.layout_prepend()

        
        ###---###  Controls settings page  ###---###
        settings_control_page = Page(parent=settings_page, columns=2, spacing=MENU_SPACING)
        Label(settings_control_page, MENU_BUTTON_SMALL_SIZE) 
        Label(settings_control_page, MENU_HEADING_SIZE, columnspan=2, text="Click a button and press a key to bind a new key to an action", fontsize=TEXT_SIZE_TEXT)

        scrollbox = ScrollBox(settings_control_page, (MENU_BUTTON_WIDTH + MENU_SPACING, MENU_SCROLL_BOX_HEIGHT), columnspan=2, columns=2, spacing=MENU_SPACING)
        keys = list(filter(lambda x: x.startswith("key."), window.options))
        buttons = {}
        selected = None

        def select_key(key):
            nonlocal selected
            if not scrollbox.selected:
                return

            for i in buttons:
                if i != key:
                    buttons[i].clicked = 0
            if selected == key:
                return
            selected = key
            scrollbox.parent = None
            for i, _ in enumerate(window.mouse_buttons):
                window.mouse_buttons[i] = 0            

        def update_key():
            nonlocal selected
            if scrollbox.selected and not selected is None:
                keys = window.get_pressed_mods() + window.get_pressed_keys() + window.get_pressed_mouse()
                
                if keys:
                    if selected == "key.return" and keys[0].lower() == "left click":
                        keys[0] = "Escape"
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
            Label(scrollbox, MENU_BUTTON_SMALL_SIZE, row=i, column=0, text=key.split(".")[1].title(), fontsize=TEXT_SIZE_TEXT)
            buttons[key] = Button(scrollbox, MENU_BUTTON_SMALL_SIZE, row=i, column=1, callback=lambda key=key: select_key(key), text=window.options[key].title(), duration=-1, fontsize=TEXT_SIZE_BUTTON)
            buttons[key].key_identifer = key
        scrollbox.callback = update_key

        Button(settings_control_page, MENU_BUTTON_SMALL_SIZE, callback=settings_page.open, text="Back", fontsize=TEXT_SIZE_BUTTON)
        Button(settings_control_page, MENU_BUTTON_SMALL_SIZE, callback=reset_keys, text="Reset", fontsize=TEXT_SIZE_BUTTON)
        settings_control_page.layout()
        Label(settings_control_page, MENU_HEADING_SIZE, columnspan=2, text="Control Settings", fontsize=TEXT_SIZE_HEADING)
        settings_control_page.layout_prepend()
        button_settings_control_open.callback = settings_control_page.open

    def update(self):
        """
        Update all widgets on the currently opened page.
        """
        if not Page.opened is None:
            Page.opened.update(self.window)
        if not self.hover_box is None:
            HoverBox(self.window, *self.hover_box)
            self.hover_box = None

    def translate(self, text):
        return translate(self.window.options["language"], text)

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
        )

        return [self.translate(text) % value for text, value in zip(intro_texts, formatter)]

    def info_hover_box(self, side, title="", performance_impact="", description="", height=1):
        performance_impact_color = {
            "": None,
            "none": (50, 220, 0, 200),
            "low": (250, 250, 0, 200),
            "medium": (250, 150, 0, 200),
            "high": (200, 0, 0, 200),
        }[performance_impact]

        if performance_impact:
            texts = (
                (title + "\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
                ("Performance impact: ", TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200)),
                (performance_impact + "\n", TEXT_SIZE_DESCRIPTION, performance_impact_color),
                (description, TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200))
            )
        else:
            texts = (
            (title + "\n", TEXT_SIZE_TEXT, (250, 250, 250, 200)),
            (description, TEXT_SIZE_DESCRIPTION, (250, 250, 250, 200))
        )

        rect = [0, -height / 2 + MENU_DESCRIPTION_BOX_Y, MENU_BUTTON_SMALL_WIDTH + MENU_SPACING, MENU_DESCRIPTION_BOX_HEIGHT * height]

        if not side:
            rect[0] -= rect[2]

        self.hover_box = (rect, texts)

    def set_state(self, state):
        self.game_state = state

    def load_threaded(self, title, prepare_state, func, *args, **kwargs):
        self.loading_page.open()
        self.loading_page.opened_tick = 0
        self.loading_page_title = title
        self.loading_page_progress = 0.0
        self.window.loading_progress = ["", 0, 0]

        # Wait for thread
        finished = False
        while not finished:
            self.update()
            self.window.update()
            value, finished = threaded(func, *args, **kwargs)

            # Write fps
            if self.window.options["show fps"]:
                self.window.draw_text(
                    (-0.98, 0.95),
                    str(round(self.window.fps, 3)),
                    (250, 250, 250, 200),
                    size=TEXT_SIZE_DESCRIPTION
                )

        self.game_state = prepare_state
        return value