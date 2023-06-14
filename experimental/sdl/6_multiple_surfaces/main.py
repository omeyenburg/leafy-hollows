from graphics import graphics
import sys


failed = graphics.window("Test", 1000)
if failed:
    print("Window creation failed.")
    sys.exit()


# Key constants
K_SPACE = graphics.key_identifier("space")


shader = graphics.load_shader("shaders/vertexTemplate.glsl", "shaders/fragmentTemplate.glsl", time="float")
graphics.activate_shader(shader)


tree_image = graphics.load_image("tree.jpg")
player_image = graphics.load_image("player.png")
font = graphics.load_font("fonts/font.ttf", 50)

for i in range(3):
    graphics.blit(tree_image, player_image, (5 + 20*i, 130 + 20*i))

t = 0.0
while graphics.update():
    t += 0.01
    graphics.update_shader_value(shader, 0, t)

    graphics.write(0, font, str(round(graphics.fps.value, 3)), (0, 0, 255), (500, 100))
    graphics.blit(0, tree_image, (20, 40))
    for x in range(20):
        graphics.blit(0, player_image, (214 + x * 30, 320))
    graphics.rect(0, (255, 0, 0), (*graphics.mouse_pos, 110, 80))
    graphics.circle(0, (255, 0, 255), (500, 480), 100, 20)
    graphics.circle(0, (255, 0, 255), (500, 480), 60, 20)
    graphics.circle(0, (255, 0, 255), (500, 480), 20)

    if graphics.keys[K_SPACE]:
        print("Space bar is pressed")
    if graphics.mouse_buttons[0]:
        print("Left mouse button is pressed")
    if graphics.mouse_wheel[1]:
        print("Mouse wheel moved")
