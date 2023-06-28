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
window = graphics.Window("Test", keys=("w", "a", "s", "d", "space", "left shift"))
window.camera = graphics.Camera(window)

game = Game(window)

vertPath = util.File.path("data/shaders/template.vert", __file__)
fragPath = util.File.path("data/shaders/template.frag", __file__)
shader = graphics.Shader(vertPath, fragPath, ("texAtlas", "texFont"))
shader.activate()

window.bind_atlas(graphics.TextureAtlas.load(util.File.path("data/atlas", __file__)))
window.bind_font(graphics.Font.fromPNG(util.File.path("data/fonts/font.png", __file__)))


while True:
    # draw fps
    window.draw_text((-0.98, 0.9), str(round(window.fps, 3)), (255, 0, 0))

    # move & draw player
    game.update()

    # Update window + shader
    window.update()
