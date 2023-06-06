import scripts.menu as menu
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

# Menu
main_page = menu.Page(window.size, columns=2, spacing=10)

b1 = menu.Button(main_page, (150, 50), row=0, col=0, callback=lambda: print(0, 0))
b2 = menu.Button(main_page, (150, 50), row=0, col=1, callback=lambda: print(0, 1))
b3 = menu.Button(main_page, (150, 50), row=1, col=0, callback=lambda: print(1, 0))
b4 = menu.Button(main_page, (150, 50), row=1, col=1, callback=lambda: print(1, 1))
b5 = menu.Button(main_page, (150, 50), row=2, col=0, callback=lambda: print(2, 0))
b6 = menu.Button(main_page, (150, 50), row=2, col=1, callback=lambda: print(2, 1))

main_page.layout()
main_page.open()

time = -1
while True:
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll
    shader.setvar("time", time)
    
    # Reset
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    menu.update(world_surface, window.size)

    # Draw
    pygame.draw.circle(ui_surface, (255, 0, 0), (200, 200), 60)
    pos = pygame.mouse.get_pos()
    world_surface.blit(tree, pos)
    font.write(ui_surface, str(window.clock.get_fps()), (255, 255, 0), 7, (100, 100))

    # Update window + shader
    window.update(world_surface, ui_surface)
