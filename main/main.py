import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# Create window
window = graphics.Window("Test", use_opengl=False, keys=("w", "a", "s", "d"))
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
second_page.layout()

b4.callback = second_page.open
"""

class Player():
    def __init__(self, spawn_pos, player_size) -> None:
        self.pos = spawn_pos
        self.player_size = player_size

    def update(self):
        print(window.keys)
        self.draw()

    def draw(self):
        pygame.draw.rect(world_surface, (0,255,0), pygame.Rect((self.pos[0], self.pos[1]), (self.player_size[0], self.player_size[1])))


import scripts.map_generator as map_generator
world_width, world_height = 12, 6
world_blocks = map_generator.default_states(world_width, world_height)
blocks_to_color = {"air":(255,255,255), "dirt":(255,248,220), "stone":(128,128,128)}

player = Player(spawn_pos=[100, 100], player_size=[50, 100])

time = -1
while True:
    world_surface, ui_surface = window.surfaces()

    # Send variables to the fragment shader
    time += 1
    time += window.mouse_wheel[3] * 10 # y-axis-scroll
    shader.setvar("time", time)
    
    # Reset surfaces
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # Draw and update menu
    menu.update()

    # drawing blocks
    block_width, block_height = 100, 100   # scale to window
    for y in range(len(world_blocks)):
        for x in range(len(world_blocks[0])):
            pygame.draw.rect(world_surface, blocks_to_color[world_blocks[y][x]], (block_width*x, block_height*y, block_width, block_height))
    
    font.write(ui_surface, str(window.clock.get_fps()), (255, 0, 0), 2, (0, 0))   # FPS Counter
    
    player.update()

    # Update window + shader
    window.update()