import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import math


# Create window
window = graphics.Window("Test", use_opengl=False, keys=("w", "a", "s", "d", "space", "left shift"))
world_surface, ui_surface = window.surfaces()

font = graphics.Font(util.File.path("data/fonts/font.png"))

PIXELS_PER_METER = 50
GRAVITY_CONSTANT = 9.81

class Physics_Object():
    def __init__(self, mass: int, gravity: float, rect: pygame.Rect, position: list[float, float]) -> None:
        self.mass: int = mass
        self.gravity_constant: float = gravity

        self.pos: list[float, float] = position     # pos used for writing, rect used for reading
        self.vel: list[float, float] = [0.0, 0.0]
        self.rect: pygame.Rect = rect

    def apply_force(self, force: float, angle: int):    # angle in degrees; 0 right, counterclockwise
        angle = math.radians(angle)
        self.vel[0] += ((math.cos(angle) * force) / self.mass) * delta_time
        self.vel[1] += -((math.sin(angle) * force) / self.mass) * delta_time

    def gravity(self):
        self.apply_force((self.gravity_constant * PIXELS_PER_METER) * self.mass, 270)
    
    def apply_velocity(self):
        self.pos[0] += self.vel[0] * delta_time
        #self.horizontal_collide()
        self.pos[1] += self.vel[1] * delta_time
        #self.vertical_collide()
    
    def horizontal_collide(self):
        for rect in terrain:
            if self.rect.colliderect(rect):
                print(self.vel)
                if self.vel[0] < 0:
                    self.rect.left = rect.right
                    self.pos[0] = self.rect.centerx
                    self.vel[0] = 0

                elif self.vel[0] > 0:
                    self.rect.right = rect.left
                    self.pos[0] = self.rect.centerx
                    self.vel[0] = 0
    
    def vertical_collide(self):
        for rect in terrain:
            if self.rect.colliderect(rect):
                if self.vel[1] < 0:
                    self.rect.top = rect.bottom
                    self.pos[1] = self.rect.centerx
                    self.vel[1] = 0

                elif self.vel[1] > 0:
                    self.rect.bottom = rect.top
                    self.pos[1] = self.rect.centerx
                    self.vel[1] = 0

    def update(self):
        if self.gravity != 0:
            self.gravity()
        if self.rect.bottom >= window.height:  # on the ground (temp)
            if self.vel[1] > 0:
                self.vel[1] = 0

        self.apply_velocity()

        self.rect.center = self.pos # update reading position



class Player(Physics_Object):
    def __init__(self, spawn_pos: list[float, float], speed: float, sprint_speed: float, acceleration_time: float, jump_force: float) -> None:   # stats in SI-Units
        Physics_Object.__init__(self, 100, GRAVITY_CONSTANT, pygame.Rect((0, 0), (50, 100)), spawn_pos)

        self.speed: float = speed * PIXELS_PER_METER
        self.sprint_speed: float = sprint_speed * PIXELS_PER_METER
        self.acceleration_time: float = acceleration_time

        self.jump_force: float = jump_force * PIXELS_PER_METER

    def draw(self):
        pygame.draw.rect(world_surface, (0,255,0), self.rect)

        pygame.draw.line(ui_surface, (255, 0, 0), self.rect.center, (window.mouse_pos[0], window.mouse_pos[1]), width=1)
    
    def jump(self, duration: float):
        self.apply_force(self.jump_force * (duration / delta_time), 90)

    def move(self):
        def mouse_pull(strenght: int):
            mouse_pos = [window.mouse_pos[0], window.mouse_pos[1]]
        
            dx, dy = mouse_pos[0] - self.rect.centerx, self.rect.centery - mouse_pos[1]
            angle_to_mouse = math.degrees(math.atan2(dy, dx))

            force = math.dist(self.rect.center, mouse_pos) * (10**strenght)

            self.apply_force(force, angle_to_mouse)

        keys = window.keys

        max_speed = self.speed
        if keys["left shift"] > 0:  # keeps sprinting once key pressed / stops faster as long as pressed
            max_speed = self.sprint_speed

        d_speed = (delta_time / self.acceleration_time) * max_speed
        

        if keys["d"] > 0:   # d priority over a
            if self.vel[0] < max_speed:
                    if self.vel[0] + d_speed > max_speed:
                        self.vel[0] = max_speed
                    else:
                        self.vel[0] += d_speed

        elif keys["a"] > 0:
            if self.vel[0] > -max_speed:
                if self.vel[0] - d_speed < -max_speed:
                    self.vel[0] = -max_speed
                else:
                    self.vel[0] -= d_speed
        
        else:   
            if abs(self.vel[0]) <= d_speed:
                self.vel[0] = 0
            else:
                if self.vel[0] > 0:
                    self.vel[0] -= d_speed
                else:
                    self.vel[0] += d_speed

        if keys["space"] == 1:
            self.jump(0.5)   # how long is jump force applied --> variable jump height
            


        if window.mouse_buttons[0] == 1:
            mouse_pull(5)    # constant activation balances out w/ gravity --> usable as rope

        """
        if self.vel[0] > 0:
                if  self.vel[0] < d_speed:
                    self.vel[0] = 0
                else:
                    self.vel[0] -= d_speed
            else:
                self.pos[0] -= d_speed 
        """

    def update(self):
        #print(self.rect.center, self.vel)

        Physics_Object.update(self)
        self.move()
        self.draw()


import scripts.map_generator as map_generator
world_width, world_height = 12, 6
world_blocks = map_generator.default_states(world_width, world_height)
blocks_to_color = {"air":(0,0,0), "dirt":(255,248,220), "stone":(128,128,128)}

player = Player(spawn_pos=[window.width / 2, window.height / 2], speed=4, sprint_speed=10, acceleration_time=0.2, jump_force=1000)

terrain: list[pygame.Rect] = []

delta_time = 0
while True:
    delta_time = (1 / window.clock.get_fps()) if window.clock.get_fps() > 0 else delta_time

    world_surface, ui_surface = window.surfaces()
    
    # Reset surfaces
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # drawing blocks
    block_width, block_height = 90, 90   # scale to window
    for y in range(len(world_blocks)):
        for x in range(len(world_blocks[0])):
            block_rect = pygame.Rect(block_width*x, block_height*y, block_width, block_height)
            if world_blocks[y][x] != "air":
                terrain.append(block_rect)
            pygame.draw.rect(world_surface, blocks_to_color[world_blocks[y][x]], block_rect)
    
    font.write(ui_surface, str(window.clock.get_fps()), (255, 0, 0), 2, (0, 0))   # FPS Counter
    
    player.update()

    # Update window + shader
    window.update()