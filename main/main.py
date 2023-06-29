import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
from scripts.game import Game

import math
import time
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# C test
from scripts.cfunctions.lib import lib
print("Hello World from Python!")
lib.c_print()


# Create window
window: graphics.Window = graphics.Window("Test", keys=("w", "a", "s", "d", "space", "left shift"))
game: Game = Game(window)

vertPath: str = util.File.path("data/shaders/template.vert", __file__)
fragPath: str = util.File.path("data/shaders/template.frag", __file__)
shader: graphics.Shader = graphics.Shader(vertPath, fragPath, ("texAtlas", "texFont"))
shader.activate()

window.bind_atlas(graphics.TextureAtlas.load(util.File.path("data/atlas", __file__)))
window.bind_font(graphics.Font.fromPNG(util.File.path("data/fonts/font.png", __file__)))


while True:
    # Update & draw all game objects
    game.update()

    # Write
    window.draw_text((-0.98, 0.9), str(round(window.fps, 3)), (255, 255, 255, 200))
    window.draw_text((-0.98, 0.75), str((round(game.player.rect[0]), round(game.player.rect[1]))), (255, 255, 255, 200))

    # Move camera
    pos = (game.player.rect.centerx - game.player.vel[0] / 20, game.player.rect.centery - game.player.vel[0] / 20)
    window.camera.move(pos)

    # Update window + shader
    window.update()
