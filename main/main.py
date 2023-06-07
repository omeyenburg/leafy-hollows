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

#
import time
t0 = time.time()
import wfc

dirt = wfc.State(
    "dirt",
    wfc.Rule(
        lambda x, y: {
            (x, y+1): ["dirt", "grass"],
            (x, y-1): ["stone", "dirt"]
        }
    )
)

stone = wfc.State(
    "stone",
    wfc.Rule(
        lambda x, y : {
            (x, y+1): ["stone", "dirt"]
        }
    )
)

air = wfc.State(
    "air",
    wfc.Rule(
        lambda x, y : {
            (x, y+1): ["air"]
        }
    )
)

landscape_wave = wfc.Wave(
    (10, 70),
    [dirt, stone, air]
)
landscape = landscape_wave.collapse()

block_map = []
for row in landscape:
    block_map.append([item.state.name for item in row])

block_to_color = {
    "air": pygame.Color(255, 255, 255),
    "dirt": pygame.Color(255,248,220),
    "stone": pygame.Color(128, 128, 128)
}

print(f"wfc time: {time.time() - t0}")

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
    for y in range(len(block_map)):
        for x in range(len(block_map[0])):
            pygame.draw.rect(world_surface, block_to_color[block_map[y][x]], (15*x, 15*y, 15, 15))
    
    font.write(ui_surface, str(window.clock.get_fps()), (255, 255, 0), 2, (0, 0))   # FPS Counter

    # Update window + shader
    window.update(world_surface, ui_surface)
