import graphics
import util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame

window = graphics.Window()

vert = util.File.path("shaders/template.vert")
frag = util.File.path("shaders/wave.frag")
shader = graphics.shader.Shader(vert, frag)
shader.activate()

tree = pygame.image.load("tree.jpg")

world_surface = pygame.Surface((window.width // 1, window.height // 1))
ui_surface = pygame.Surface((window.width // 1, window.height // 1))

font0 = pygame.freetype.SysFont(None, 20)

running = True
while running:
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    pygame.draw.circle(ui_surface, (255, 0, 0), (200, 200), 60)
    pos = pygame.mouse.get_pos()
    for _ in range(1):
        world_surface.blit(tree, (pos[0] // 1, pos[1] // 1))
    font0.render_to(ui_surface, (100, 100), str(window.clock.get_fps()),
                    (255, 255, 255))

    window.update(world_surface, ui_surface)
