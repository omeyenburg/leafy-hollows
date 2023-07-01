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
#window.bind_font(graphics.Font.fromSYS(None, 15))



# Menu stuff
main_page = menu.Page(columns=2, spacing=0.1)
l1 = menu.Label(main_page, (1, .5), row=0, column=0, columnspan=2, text="Hello, World!")
b1 = menu.Button(main_page, (1.1, .3), row=1, column=0, columnspan=2, text="Play")
b2 = menu.Button(main_page, (.5, .3), row=2, column=0, text="Options")
b3 = menu.Button(main_page, (.5, .3), row=2, column=1, callback=window.toggle_fullscreen, text="Fullscreen")
main_page.layout()
main_page.open()

options_page = menu.Page(spacing=0.1)
l2 = menu.Label(options_page, (1, .5), row=0, column=0, text="Options")
b4 = menu.Button(options_page, (1, .3), row=1, column=0, callback=main_page.open, text="Back")
options_page.layout()

in_game = False
def toggle_in_game():
    global in_game
    in_game = ~in_game

b1.callback = toggle_in_game
b2.callback = options_page.open
b4.callback = main_page.open


while True:
    if in_game:
        # Update & draw all game objects
        game.update()

        # Write fps & player position
        window.draw_text((-0.98, 0.95), "FPS: " + str(round(window.fps, 3)), (255, 255, 255, 200))
        window.draw_text((-0.98, 0.75), "Player: " + str((round(game.player.rect.centerx, 1), round(game.player.rect.centery, 1))), (255, 255, 255, 200))
        pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, world=1)
        window.draw_text((-0.98, 0.55), "Mouse: " + str((math.floor(pos[0]), math.floor(pos[1]))), (255, 255, 255, 200))

        # Move camera
        pos = (game.player.rect.centerx - game.player.vel[0] / 20, game.player.rect.centery - game.player.vel[0] / 20)
        window.camera.move(pos)
    else:
        # Update and draw the menu
        menu.update(window)

        # Write fps
        window.draw_text((-0.98, 0.95), str(round(window.fps, 3)), (255, 255, 255, 200), 1.3)

    # Update window + shader
    window.update()
