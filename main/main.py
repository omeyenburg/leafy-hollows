import scripts.menu as menu
import scripts.graphics as graphics
import scripts.util as util
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import math


# Create window
window = graphics.Window("Test", use_opengl=False, keys=("w", "a", "s", "d", "space"))
world_surface, ui_surface = window.surfaces()

font = graphics.Font(util.File.path("data/fonts/font.png"))

PIXELS_PER_METER = 50

class Physics_Object():
    def __init__(self, mass: int, gravity: bool, rect: pygame.Rect, position: list[float, float]) -> None:
        self.mass: int = mass
        self.gravity: bool = gravity

        self.__pos: list[float, float] = position     # pos used for setting, rect used for reading
        print(position)
        self.vel: list[float, float] = [0.0, 0.0]
        self.rect: pygame.Rect = rect

    def move_position(self, mov: list[float, float]):
        self.__pos[0] += mov[0]
        self.__pos[1] += mov[1]

    def apply_force(self, force: float, angle: int):    # angle in degrees; 0 right, counterclockwise
        angle = math.radians(angle)
        self.vel[0] += ((math.cos(angle) * force) / self.mass) * delta_time
        self.vel[1] += -((math.sin(angle) * force) / self.mass) * delta_time
    
    def update(self):
        
        if self.gravity:
            self.apply_force((9.81 * PIXELS_PER_METER) * self.mass, 270)

        
        if self.rect.bottom >= window.height:  # on the ground (temp)
            if self.vel[1] > 0:
                self.vel[1] = 0
        
        self.move_position([vel * delta_time for vel in self.vel])     # move by frame velocity

        self.rect.center = self.__pos



class Player(Physics_Object):
    def __init__(self, spawn_pos: list[float, float], speed: float, jump_force: float) -> None:   # stats in SI-Units
        Physics_Object.__init__(self, 100, True, pygame.Rect((0, 0), (50, 100)), spawn_pos)

        self.speed: float = speed * PIXELS_PER_METER
        self.jump_force: float = jump_force * PIXELS_PER_METER

    def draw(self):
        pygame.draw.rect(world_surface, (0,255,0), self.rect)

        pygame.draw.line(ui_surface, (255, 0, 0), self.rect.center, (window.mouse_pos[0], window.mouse_pos[1]), width=1)

    def move(self):
        def mouse_pull():
            mouse_pos = [window.mouse_pos[0], window.mouse_pos[1]]
        
            dx, dy = mouse_pos[0] - self.rect.centerx, self.rect.centery - mouse_pos[1]
            angle_to_mouse = math.degrees(math.atan2(dy, dx))

            force = math.dist(self.rect.center, mouse_pos) * (10**4)

            self.apply_force(force, angle_to_mouse)

        keys = window.keys
        d_speed = self.speed * delta_time

        if keys["w"] > 0:
            if self.vel[1] > 0:
                if  self.vel[1] < d_speed:
                    self.vel[1] = 0
                else:
                    self.vel[1] -= d_speed
            else:
                self.rect.y -= d_speed

        if keys["a"] > 0:
            if self.vel[0] > 0:
                if  self.vel[0] < d_speed:
                    self.vel[0] = 0
                else:
                    self.vel[0] -= d_speed
            else:
                self.move_position([-d_speed, 0])

        if keys["s"] > 0:
            if self.vel[1] < 0:
                if  self.vel[1] > d_speed:
                    self.vel[1] = 0
                else:
                    self.vel[1] += d_speed
            else:
                self.rect.y += d_speed

        if keys["d"] > 0:
            if self.vel[0] < 0:
                if  self.vel[0] > d_speed:
                    self.vel[0] = 0
                else:
                    self.vel[0] += d_speed
            else:
                self.move_position([d_speed, 0])

        if keys["space"] == 1:
            jump_duration = 0.5   # how long is jump force applied --> variable jump height
            self.apply_force(self.jump_force * (jump_duration / delta_time), 90)


        if window.mouse_buttons[0] == 1:
            mouse_pull()    # constant activation balances out w/ gravity --> usable as rope

    def update(self):
        #print(self.rect.center, self.vel)

        Physics_Object.update(self)
        self.move()
        self.draw()


import scripts.map_generator as map_generator
world_width, world_height = 12, 6
world_blocks = map_generator.default_states(world_width, world_height)
blocks_to_color = {"air":(0,0,0), "dirt":(255,248,220), "stone":(128,128,128)}

player = Player(spawn_pos=[window.width / 2, window.height / 2], speed=5, jump_force=1000)

delta_time = 0
while True:
    delta_time = (1 / window.clock.get_fps()) if window.clock.get_fps() > 0 else delta_time

    world_surface, ui_surface = window.surfaces()
    
    # Reset surfaces
    world_surface.fill((0, 0, 0))
    ui_surface.fill((0, 0, 0))

    # drawing blocks
    block_width, block_height = 100, 100   # scale to window
    for y in range(len(world_blocks)):
        for x in range(len(world_blocks[0])):
            pygame.draw.rect(world_surface, blocks_to_color[world_blocks[y][x]], (block_width*x, block_height*y, block_width, block_height))
    
    font.write(ui_surface, str(window.clock.get_fps()), (255, 0, 0), 2, (0, 0))   # FPS Counter
    
    player.update()

    # Update window + shader
    window.update()