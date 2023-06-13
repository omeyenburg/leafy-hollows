from cfunctions import graphics
import sys


failed = graphics.window("Test", 1000)
if failed:
    print("Window creation failed.")
    sys.exit()


shader = graphics.load_shader("shaders/vertexTemplate.glsl", "shaders/fragmentTemplate.glsl")
graphics.activate_shader(shader)


tree_image = graphics.load_image("tree.jpg")
player_image = graphics.load_image("player.png")
font = graphics.load_font("fonts/font.ttf", 50)

for i in range(3):
    graphics.blit(tree_image, player_image, (5 + 20*i, 130 + 20*i))

running = True
while running:
    graphics.write(0, font, str(round(graphics.get_fps(), 3)), (0, 0, 255), (500, 100))
    graphics.blit(0, tree_image, (20, 40))
    for x in range(20):
        graphics.blit(0, player_image, (214 + x * 30, 320))
    graphics.rect(0, (255, 0, 0), (*graphics.get_mousepos(), 110, 80))
    graphics.circle(0, (255, 0, 255), (500, 480), 100, 20)
    graphics.circle(0, (255, 0, 255), (500, 480), 60, 20)
    graphics.circle(0, (255, 0, 255), (500, 480), 20)
    running = graphics.update()
