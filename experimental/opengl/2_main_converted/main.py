#import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

# Create window
window = graphics.Window("Test")
camera = graphics.Camera(window)

vertPath = util.File.path("data/shaders/template.vert", __file__)
fragPath = util.File.path("data/shaders/template.frag", __file__)
shader = graphics.Shader(vertPath, fragPath, ("texAtlas", "texFont"))
shader.activate()

window.bind_atlas(graphics.TextureAtlas.load(util.File.path("data/atlas", __file__)))
window.bind_font(graphics.Font.fromPNG(util.File.path("data/fonts/font.png", __file__)))


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

while True:
    for x in range(30):
        for y in range(20):
            rect = camera.map_coord((x * 30, y * 30, 15, 15), fcentered=False)
            window.draw_image(("stone", "dirt", "grass")[(x+y * 3)%3], rect[:2], rect[2:])
    window.draw_circle((0.6, 0), 0.3, (0.5, 0, 1, 1))
    window.draw_text((0.5, 0), str(round(window.clock.get_fps(), 3)), (0, 1, 0.5, 1))
    
    window.update()