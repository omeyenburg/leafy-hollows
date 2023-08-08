# -*- coding: utf-8 -*-

# Apple: signing bundle
# https://gist.github.com/txoof/0636835d3cc65245c6288b2374799c43
# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OSX-Code-Signing
# https://support.apple.com/en-us/HT204397

import scripts.utility.util as util
from scripts.graphics.window import Window
from scripts.graphics.menu import Menu
from scripts.game.game import Game

import numpy
import math
import time
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# C test
#from scripts.cfunctions.lib import lib
#print("Hello World from Python!")
#lib.c_print()

# Create window
window: Window = Window("Hello World")
game: Game = Game(window)
menu: Menu = Menu(window)


while True:
    if menu.in_game:
        # Update & draw all game objects
        game.update()

        # Post processing
        if window.options["post processing"]:
            window.draw_post_processing()

        # Write fps & debug info
        if window.options["show fps"]:
            window.draw_text((-0.98, 0.95), "FPS: " + str(round(window.fps, 3)), (250, 250, 250, 200))
            y_offset = 0.15
        else:
            y_offset = 0
        if window.options["show debug"]:
            pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, world=1)
            window.draw_text((-0.98, 0.95 - y_offset), "Player: " + str((round(game.player.rect.centerx, 1), round(game.player.rect.centery, 1))), (250, 250, 250, 200))
            window.draw_text((-0.98, 0.8 - y_offset), "Mouse: " + str((math.floor(pos[0]), math.floor(pos[1]))), (250, 250, 250, 200))
            window.draw_text((-0.98, 0.65 - y_offset), "Seed: " + str(game.world.seed), (250, 250, 250, 200))
            
        # Move camera
        pos = (game.player.rect.centerx - game.player.vel[0] / 100, game.player.rect.centery - game.player.vel[0] / 100)
        window.camera.move(pos)

        # Update window + shader
        window.update()

        # Open menu
        if window.keybind("return") == 1:
            menu.in_game = False
    else:
        # Update and draw the menu
        menu.update()

        # Write fps
        if window.options["show fps"]:
            window.draw_text((-0.98, 0.95), str(round(window.fps, 3)), (250, 250, 250, 200))

        # Update window + shader
        window.update()
