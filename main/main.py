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

time = -1
while True:
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll
    shader.setvar("time", time)
    
    # Reset
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # Draw
    pygame.draw.circle(ui_surface, (255, 0, 0), (200, 200), 60)
    pos = pygame.mouse.get_pos()
    world_surface.blit(tree, pos)
    font.write(ui_surface, str(window.clock.get_fps()), (255, 255, 0), 7, (100, 100))

    # Update window + shader
    window.update(world_surface, ui_surface)
