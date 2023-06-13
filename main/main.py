import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import math


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

class Physics_Object():
    def __init__(self, mass: int, gravity: bool, hitbox, position: list[float, float]) -> None:
        self.mass: int = mass
        self.gravity: bool = gravity
        self.hitbox = hitbox

        self.pos: list[float, float] = position
        self.vel: list[float, float] = [0.0, 0.0]

    
    def apply_force(self, force: float, angle: int):    # angle in degrees; 0 straight up, clockwise
        angle = math.radians(angle)
        self.vel[0] += ((math.sin(angle) * force) / self.mass) * delta_time
        self.vel[1] += ((-math.cos(angle) * force) / self.mass) * delta_time
    
    def update(self):
        self.pos[0] += self.vel[0] * delta_time
        self.pos[1] += self.vel[1] * delta_time


class Player(Physics_Object):
    def __init__(self, spawn_pos: list[float, float], size: int, speed: int) -> None:
        Physics_Object.__init__(self, 100, True, 0, spawn_pos)

        #self.pos: list[float, float] = spawn_pos
        #self.vel: list[float, float] = [0.0, 0.0]
        self.size: int = size
        self.speed: int = speed

    def draw(self):
        pygame.draw.rect(world_surface, (0,255,0), pygame.Rect((self.pos[0] - (self.size[0] // 2), self.pos[1] - (self.size[1] // 2)), (self.size[0], self.size[1])))

    def move(self):
        keys = window.keys
        force = 1000
        if keys["w"] > 0:
            #self.vel[1] = -self.speed
            self.apply_force(force, 0)
        if keys["a"] > 0:
            #self.vel[0] = -self.speed
            self.apply_force(force, 270)
        if keys["s"] > 0:
            #self.vel[1] = self.speed 
            self.apply_force(force, 180)
        if keys["d"] > 0:
            #self.vel[0] = self.speed 
            self.apply_force(force, 90)


        if window.mouse_buttons[0] == 1:
            self.apply_force(force, 0)

    def update(self):
        print(self.pos, self.vel)
        Physics_Object.update(self)
        self.move()
        self.draw()


import scripts.map_generator as map_generator
world_width, world_height = 12, 6
world_blocks = map_generator.default_states(world_width, world_height)
blocks_to_color = {"air":(255,255,255), "dirt":(255,248,220), "stone":(128,128,128)}

player = Player(spawn_pos=[100, 100], size=[50, 100], speed=250)

time = -1

delta_time = 0
while True:
    delta_time = (1 / window.clock.get_fps()) if window.clock.get_fps() > 0 else delta_time

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