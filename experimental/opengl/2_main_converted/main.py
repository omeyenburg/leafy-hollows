#import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# Create window
window = graphics.Window("Test")

# Pygame stuff for testing
player_image = pygame.image.load(util.File.path("data/images/tree.jpg", __file__)).convert()

texture_atlas = graphics.TextureAtlas(player=player_image)
window.bind_atlas(texture_atlas)
player = 0


font = window.bind_font(graphics.Font.fromPNG(util.File.path("data/fonts/font.png", __file__)))
print(font)
font = window.bind_font(graphics.Font.fromSYS(None, 30))
print(font)

# Menu
"""
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
s1 = menu.Slider(second_page, (150, 50), row=2, column=0, value=0)
e1 = menu.Entry(second_page, (150, 50), row=3, column=0)
second_page.layout()

b4.callback = second_page.open
"""

time = -1
while True:

    # Send variables to the fragment shader
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll


    #shader.setvar("time", time)
    
    # Reset surfaces
    #world_surface.fill((0, 100, 0))
    #ui_surface.fill((0, 0, 0))

    # Draw and update menu
    #menu.update()

    # Draw
    #font.write(ui_surface, str(window.clock.get_fps()), (255, 255, 0), 3, (20, 20))

    # Update window + shader
    window.draw(player, (-0.4, -0.4), 1)
    window.write(font, str(window.clock.get_fps()), (-0.8, 0.8))

    window.update()