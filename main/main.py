# -*- coding: utf-8 -*-

# Apple: signing bundle
# https://gist.github.com/txoof/0636835d3cc65245c6288b2374799c43
# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OSX-Code-Signing
# https://support.apple.com/en-us/HT204397

from scripts.game.world_generation import generate_world
from scripts.utility.thread import threaded
from scripts.graphics.window import Window
from scripts.graphics.menu import Menu
from scripts.game.world import World
from scripts.game.game import Game
from scripts.utility.const import *
import numpy
import math
import time
import os


# Create window
window: Window = Window("Title")
menu: Menu = Menu(window)
game: Game = None


def generate():
    global game

    window.camera.reset()

    # Create game
    game = Game(window)

    # Wait for world generation thread
    while True:
        menu.update()
        window.update()

        done = threaded(generate_world, game.world, wait=True)
        if done: break

        # Open menu
        if window.keybind("return") == 1:
            menu.main_page.open()
            menu.game_state = "menu"

        # Write fps
        if window.options["show fps"]:
            window.draw_text((-0.98, 0.95), str(round(window.fps, 3)), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)

    menu.game_state = "intro"
    window.camera.pos[1] = 30
    game.player.vel[1] = 5


def draw_game():
    # Update & draw all game objects
    game.draw()

    # Draw foreground blocks & post processing
    window.draw_post_processing()

    # Write fps & debug info
    if window.options["show fps"]:
        window.draw_text((-0.98, 0.95), "FPS: " + str(round(window.fps, 3)), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)
        y_offset = 0.1
    else:
        y_offset = 0
    if window.options["show debug"]:
        pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, world=1)
        window.draw_text((-0.98, 0.95 - y_offset), "Player Pos: " + str((round(game.player.rect.centerx, 1), round(game.player.rect.centery, 1))), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)
        window.draw_text((-0.98, 0.85 - y_offset), "Mouse Pos: " + str((math.floor(pos[0]), math.floor(pos[1]))), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)
        window.draw_text((-0.98, 0.75 - y_offset), "Seed: " + str(game.world.seed), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)
        window.draw_text((-0.98, 0.65 - y_offset), str(game.world.get((math.floor(pos[0]), math.floor(pos[1])), 0)), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)


def draw_intro():
    # Move camera
    pos = (0, game.player.rect.centery - game.player.vel[0] / 100)
    window.camera.move(pos)

    # Draw intro text
    intro_texts = menu.get_intro_texts()

    intro_text_position = (-game.player.rect.centery / INTRO_LENGTH - 0.01) * 1.12
    if 0 < intro_text_position < 1:
        skip_text = menu.translator.translate("Press [%s] to skip intro") % window.options['key.jump'].title()
        window.draw_text((-0.95, -0.9), skip_text, (255, 255, 255), 0.14)

        intro_text_index = int(intro_text_position * len(intro_texts))
        intro_text_fract = intro_text_position * len(intro_texts) - int(intro_text_position * len(intro_texts))
        intro_text_size = 0.5 if intro_text_index == 0 else 0.16
        y = 2 * (2 * intro_text_fract - 1) ** 21
        intro_text = intro_texts[intro_text_index].split("\n")
        for i, text in enumerate(intro_text):
            window.draw_text((0.6, y - (i - len(intro_text) / 2) * 0.1), text, (255, 255, 255), intro_text_size, centered=True)

    # Update window + shader
    window.update()

    # Skip intro
    if window.keybind("jump") == 1 and 0 < intro_text_position < 1:
        original = game.player.rect.y
        game.player.rect.y = min(game.player.rect.y, -INTRO_LENGTH + INTRO_REPEAT + game.player.rect.y % INTRO_REPEAT)
        window.camera.pos[1] += game.player.rect.y - original

    # Pause
    if window.keybind("return") == 1:
        menu.pause_page.open()
        menu.game_state = "pause"
        menu.game_intro = True

    # End intro
    if game.player.onGround:
        window.camera.zoom(2.0, 100.0)
        menu.game_state = "game"
        game.player.can_move = True


while True:
    if menu.game_state == "generate":
        generate()

    elif menu.game_state == "intro":
        game.update()
        draw_game()
        draw_intro()

    elif menu.game_state == "game":
        # Update and draw the game
        game.update()
        draw_game()

        # Update and draw the menu
        window.update()

        # Move camera
        pos = (game.player.rect.centerx - game.player.vel[0] / 100, game.player.rect.centery - game.player.vel[0] / 100)
        window.camera.move(pos)

        # Pause
        if window.keybind("return") == 1:
            menu.pause_page.open()
            menu.game_state = "pause"

    elif menu.game_state == "pause":
        # Only draw the game
        draw_game()

        # Draw intro text
        if menu.game_intro:
            intro_texts = menu.get_intro_texts()

            intro_text_position = (-game.player.rect.centery / INTRO_LENGTH - 0.01) * 1.12
            if 0 < intro_text_position < 1:
                skip_text = menu.translator.translate("Press [%s] to skip intro") % window.options['key.jump'].title()
                window.draw_text((-0.95, -0.9), skip_text, (255, 255, 255), 0.14)

                intro_text_index = int(intro_text_position * len(intro_texts))
                intro_text_fract = intro_text_position * len(intro_texts) - int(intro_text_position * len(intro_texts))
                intro_text_size = 0.5 if intro_text_index == 0 else 0.16
                y = 2 * (2 * intro_text_fract - 1) ** 21
                intro_text = intro_texts[intro_text_index].split("\n")
                for i, text in enumerate(intro_text):
                    window.draw_text((0.6, y - (i - len(intro_text) / 2) * 0.1), text, (255, 255, 255), intro_text_size, centered=True)

        # Update and draw the menu
        menu.update()

        # Update window + shader
        window.update(camera=False)

        # Game
        if window.keybind("return") == 1:
            if menu.game_intro:
                menu.game_state = "intro"
                menu.game_intro = False
            else:
                menu.game_state = "game"

    else:
        # Update and draw the menu
        window.clear_world()
        menu.update()

        # Write fps
        if window.options["show fps"]:
            window.draw_text((-0.98, 0.95), str(round(window.fps, 3)), (250, 250, 250, 200), size=TEXT_SIZE_DESCRIPTION)

        # Update window + shader
        window.update()
