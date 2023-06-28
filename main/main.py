import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
from scripts.game import Game

import math
import time
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


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


#import scripts.map_generator as map_generator
#world_width, world_height = 12, 6
#world_blocks = map_generator.default_states(world_width, world_height)
#blocks_to_color = {"air": (0, 0, 0), "dirt": (255, 248, 220), "stone": (128, 128, 128)}


#terrain = []
while True:
    
    
    # draw and generate blocks
    """
    block_width, block_height = 90, 90
    for y in range(len(world_blocks)):
        for x in range(len(world_blocks[0])):
            block_rect = pygame.Rect(block_width*x, block_height*y, block_width, block_height)
            if world_blocks[y][x] != "air":
                terrain.append(block_rect)
            rect = camera.map_coord(block_rect, fcentered=False)
            window.draw_rect(rect[:2], rect[2:], blocks_to_color[world_blocks[y][x]])
    """

    # draw fps
    window.draw_text((-0.98, 0.9), str(round(window.fps, 3)), (255, 0, 0))

    # move & draw player
    game.update()

    # Update window + shader
    window.update()
