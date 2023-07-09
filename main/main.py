# -*- coding: utf-8 -*-
import scripts.graphics as graphics
import scripts.util as util
from scripts.game import Game
from scripts.menu import Menu

import numpy
import math
import time
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# C test
from scripts.cfunctions.lib import lib
print("Hello World from Python!")
lib.c_print()

# Create window
window: graphics.Window = graphics.Window("Test")
game: Game = Game(window)
menu: Menu = Menu(window)


while True:
    if menu.in_game:
        # Update & draw all game objects
        game.update()

        # Write fps & player position
        window.draw_text((-0.98, 0.95), "FPS: " + str(round(window.fps, 3)), (255, 255, 255, 200))
        window.draw_text((-0.98, 0.8), "Player: " + str((round(game.player.rect.centerx, 1), round(game.player.rect.centery, 1))), (255, 255, 255, 200))
        pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, world=1)
        window.draw_text((-0.98, 0.65), "Mouse: " + str((math.floor(pos[0]), math.floor(pos[1]))), (255, 255, 255, 200))
        window.draw_text((-0.98, 0.5), "Seed: " + str(game.world.seed), (255, 255, 255, 200))


        # Move camera
        pos = (game.player.rect.centerx - game.player.vel[0] / 50, game.player.rect.centery - game.player.vel[0] / 50)
        window.camera.move(pos)

        # Update window + shader
        data = game.world.view(*window.camera.visible_blocks())
        window.update(data)

        # Open menu
        if window.keybind("return") == 1:
            menu.in_game = False
    else:
        # Update and draw the menu
        menu.update()

        # Write fps
        window.draw_text((-0.98, 0.95), str(round(window.fps, 3)), (255, 255, 255, 200), 1.3)

        # Update window + shader
        window.update()
