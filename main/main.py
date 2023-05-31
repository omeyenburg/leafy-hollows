import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# Create window
window = graphics.Window()

# Create and activate shader
vert = util.File.path("data/shaders/template.vert")
frag = util.File.path("data/shaders/wave.frag")
shader = graphics.shader.Shader(vert, frag, time="uint")
shader.activate()

# Pygame stuff for testing
tree = pygame.image.load("data/images/tree.jpg")
world_surface = pygame.Surface(window.size)
ui_surface = pygame.Surface(window.size)
font = pygame.freetype.SysFont(None, 20)

time = 0
while True:
    time += 1
    shader.setvar("time", time)
    
    # Reset
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # Draw
    pygame.draw.circle(ui_surface, (255, 0, 0), (200, 200), 60)
    pos = pygame.mouse.get_pos()
    world_surface.blit(tree, pos)
    font.render_to(ui_surface, (100, 100), str(window.clock.get_fps()), (255, 255, 255))

    # Update window + shader
    window.update(world_surface, ui_surface)
