# -*- coding: utf-8 -*-
from scripts.utility.util import realistic
from scripts.graphics.window import Window
from scripts.game.physics import *


class Player(CollisionPhysicsObject):
    def __init__(self, spawn_pos: [float], speed: float, sprint_speed: float, acceleration_time: float, jump_force: int):
        super().__init__(50, spawn_pos, (0.9, 1.8))

        self.speed: float = speed
        self.sprint_speed: float = sprint_speed
        self.acceleration_time: float = acceleration_time
        self.jump_force: int = jump_force
        self.state: str = "idle" # state is used for movement & animations
        self.direction: int = 0 # 0 = right; 1 = left
        self.hit_ground = 0

    def draw(self, window: Window):
        # hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0))

        # player
        rect = window.camera.map_coord((self.rect.x - 1 + self.rect.w / 2, self.rect.y, 2, 2), from_world=True)
        window.draw_image("player_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0))
    
    def jump(self, window, duration: float):
        force = self.jump_force * duration / window.delta_time
        if self.onGround: # Normal jump
            self.apply_force(force, 90, window.delta_time)
        elif self.vel[1] > 1.5: # Max wall jump velocity
            return
        elif self.onWallLeft and window.keybind("left") and window.keybind("jump") == 1: # Wall jump left
            self.apply_force(force * 2.5, 120, window.delta_time)
            self.onWallLeft = 0
        elif self.onWallRight and window.keybind("right") and window.keybind("jump") == 1: # Wall jump right
            self.apply_force(force * 2.5, 60, window.delta_time)
            self.onWallRight = 0
        
    def move(self, world, window: Window):
        def mouse_pull(strenght):
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
        
            dx, dy = mouse_pos[0] - self.rect.centerx, mouse_pos[1] - self.rect.centery
            angle_to_mouse = math.degrees(math.atan2(dy, dx))

            force = min(math.dist(self.rect.center, mouse_pos), 3) / window.delta_time * strenght
            self.apply_force(force, angle_to_mouse, window.delta_time)

        max_speed = self.speed
        if window.keybind("sprint"): # Keeps sprinting once key pressed / stops faster as long as pressed
            max_speed = self.sprint_speed

        d_speed = (window.delta_time / self.acceleration_time) * max_speed
        if not (self.onGround or self.onWallLeft or self.onWallRight):
            if realistic:
                d_speed = 0
            else:
                d_speed /= 10

        # animation states
        wall_block = (round(self.rect.x + 0.8), round(self.rect.y + 1))
        if self.vel[1] < 0:
            self.state = "fall"
            self.hit_ground = 0.2
        elif self.onGround:
            if self.hit_ground > 0:
                self.hit_ground -= window.delta_time
                self.state = "hit_ground"
            else:
                self.state = "idle"
        elif (self.onWallLeft and self.direction == 0 and world[wall_block]
              or self.onWallRight and self.direction == 1 and world[wall_block[0] - 2, wall_block[1]]):
            self.state = "climb"
        elif self.vel[1] > 0:
            if abs(self.vel[0]) > 1.5 or self.state == "jump":
                self.state = "jump"
            else:
                self.state = "high_jump"
        if self.vel[0] > 1:
            self.direction = 0
        elif self.vel[0] < -1:
            self.direction = 1

        if window.keybind("right"): # d has priority over a
            if self.vel[0] < max_speed:
                if self.vel[0] + d_speed > max_speed: # guaranteeing exact max speed
                    self.vel[0] = max_speed
                else:
                    self.vel[0] += d_speed
            if self.onGround and abs(self.vel[0]) > 1:
                self.state = "walk"
        elif window.keybind("left"):
            if self.vel[0] > -max_speed:
                if self.vel[0] - d_speed < -max_speed:
                    self.vel[0] = -max_speed
                else:
                    self.vel[0] -= d_speed
            if self.onGround and abs(self.vel[0]) > 1:
                self.state = "walk"
        else:   
            if abs(self.vel[0]) <= d_speed:
                self.vel[0] = 0
            else:
                if self.vel[0] > 0:
                    self.vel[0] -= d_speed
                else:
                    self.vel[0] += d_speed
        if window.keybind("jump"):
            self.jump(window, 5) # how long is jump force applied --> variable jump height

        if window.mouse_buttons[0] == 1: # left click: pull player to mouse
            mouse_pull(300) # constant activation balances out w/ gravity --> usable as rope

        if window.mouse_buttons[1] == 1: # middle click: spawn particle
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            spawn_particle(mouse_pos)

        if window.mouse_buttons[2] == 1: # right click: place/break block
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            if world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])] > 0:
                world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])] = 0
            else:
                world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])] = world.blocks["dirt"]

    def update(self, world, window: Window):
        self.move(world, window)
        super().update(world, window.delta_time)
        self.draw(window)
        for particle in particle_list:
            particle.update(world, window.delta_time)
            tmp_draw_rect(window, particle.rect.topleft, [particle.rect.w, particle.rect.h], (0, 255, 255))


def spawn_particle(pos: list[float, float]):
    particle_list.append(PhysicsObject(10, pos, [0.5, 0.5]))

def tmp_draw_rect(window: Window, pos: [float, float], size: [float, float], color: [int, int, int]):
    rect = window.camera.map_coord((pos[0], pos[1], size[0], size[1]), from_world=True)
    window.draw_rect(rect[:2], rect[2:], color)


particle_list: list[PhysicsObject] = []