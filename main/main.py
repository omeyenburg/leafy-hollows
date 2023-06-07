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
frag = util.File.path("data/shaders/wave.frag")
shader = graphics.shader.Shader(vert, frag, time="int")
shader.activate()

# Pygame stuff for testing
tree = pygame.image.load("data/images/tree.jpg").convert()
world_surface = pygame.Surface(window.size)
ui_surface = pygame.Surface(window.size)
font = graphics.Font(util.File.path("data/fonts/font.png"))

# Menu
menu.Style()

main_page = menu.Page(window, columns=2, spacing=10)

b1 = menu.Button(main_page, (150, 50), row=0, col=0, callback=lambda: print(0, 0), text="Hello")
b2 = menu.Button(main_page, (150, 50), row=0, col=1, callback=lambda: print(0, 1))
b3 = menu.Button(main_page, (150, 50), row=1, col=0, callback=lambda: print(1, 0))
b4 = menu.Button(main_page, (150, 50), row=1, col=1, callback=lambda: print(1, 1), text="World")
b5 = menu.Button(main_page, (150, 50), row=2, col=0, callback=lambda: print(2, 0))
b6 = menu.Button(main_page, (150, 50), row=2, col=1, callback=lambda: print(2, 1))

main_page.layout()
main_page.open()

time = -1
while True:
    # Send variables to the fragment shader
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll
    shader.setvar("time", time)
    
    # Reset surfaces
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # Draw and update menu
    menu.update(world_surface)

    # Draw
    font.write(ui_surface, str(window.clock.get_fps()), (255, 255, 0), 3, (20, 20))

    # Update window + shader
    window.update(world_surface, ui_surface)
