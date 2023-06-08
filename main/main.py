import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# Create window
window = graphics.Window("Test")
world_surface, ui_surface = window.surfaces()

# Create and activate shader
vert = util.File.path("data/shaders/template.vert")
frag = util.File.path("data/shaders/wave.frag")
shader = graphics.shader.Shader(vert, frag, time="int")
shader.activate()

# Pygame stuff for testing
tree = pygame.image.load("data/images/tree.jpg").convert()
font = graphics.Font(util.File.path("data/fonts/font.png"))

# Menu
menu.init(window)

main_page = menu.Page(columns=2, spacing=10)
l1 = menu.Label(main_page, (150, 50), row=0, column=0, columnspan=2, text="Main Page")
b1 = menu.Button(main_page, (150, 50), row=1, column=0, callback=lambda: print(1, 0), text="Hello")
b2 = menu.Button(main_page, (150, 50), row=1, column=1, callback=lambda: print(1, 1), text="World")
b3 = menu.Button(main_page, (150, 50), row=2, column=0, callback=window.toggle_fullscreen, text="Fullscreen")
b4 = menu.Button(main_page, (150, 50), row=2, column=1, text="Swap Page")
main_page.layout()
main_page.open()

second_page = menu.Page(spacing=10)
l2 = menu.Label(second_page, (150, 50), row=0, column=0, text="Second Page")
b5 = menu.Button(second_page, (150, 50), row=1, column=0, callback=main_page.open, text="Back")
second_page.layout()

b4.callback = second_page.open

time = -1
while True:
    world_surface, ui_surface = window.surfaces()

    # Send variables to the fragment shader
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll
    shader.setvar("time", time)
    
    # Reset surfaces
    world_surface.fill((0, 100, 0))
    ui_surface.fill((0, 0, 0))

    # Draw and update menu
    menu.update()

    # Draw
    font.write(ui_surface, str(window.clock.get_fps()), (255, 255, 0), 3, (20, 20))

    # Update window + shader
    window.update()