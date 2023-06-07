import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# Create window
window = graphics.Window("Test")

# Create and activate shader
vert = util.File.path("data/shaders/template.vert")
frag = util.File.path("data/shaders/template.frag")
shader = graphics.shader.Shader(vert, frag, time="int")
shader.activate()

# Pygame stuff for testing
tree = pygame.image.load("data/images/tree.jpg").convert()
world_surface = pygame.Surface(window.size)
ui_surface = pygame.Surface(window.size)
font = graphics.Font(util.File.path("data/fonts/font.png"))

import scripts.map_generator as map_generator

world_width, world_height = window.width // 10, window.height // 10
world_blocks = map_generator.default_states(world_width, world_height)
blocks_to_color = {"air":(255,255,255), "dirt":(255,248,220), "stone":(128,128,128)}

time = -1
while True:
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll
    shader.setvar("time", time)
    
    # Reset
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # Draw
    """
    pygame.draw.circle(ui_surface, (255, 0, 0), (200, 200), 60)
    pos = pygame.mouse.get_pos()
    world_surface.blit(tree, pos)
    """
    width_factor, height_factor = window.width // world_width, window.height // world_height   # scale to window
    for y in range(len(world_blocks)):
        for x in range(len(world_blocks[0])):
            pygame.draw.rect(world_surface, blocks_to_color[world_blocks[y][x]], (width_factor*x, height_factor*y, width_factor, height_factor))
    
    font.write(ui_surface, str(window.clock.get_fps()), (255, 0, 0), 2, (0, 0))   # FPS Counter

    # Update window + shader
    window.update(world_surface, ui_surface)
