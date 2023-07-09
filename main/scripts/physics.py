# -*- coding: utf-8 -*-
from scripts.util import realistic
import scripts.geometry as geometry
import math


if realistic:
    GRAVITY_CONSTANT: float = 9.81
else:
    GRAVITY_CONSTANT: float = 38
FRICTION_X: float = 0.1
FRICTION_Y: float = 0.04
JUMP_THRESHOLD: int = 3 # time to jump after leaving the ground in ticks
WALL_JUMP_THRESHOLD: float = 0.3 # time to jump after leaving a wall in seconds


class PhysicsObject:
    def __init__(self, mass: float, position: [float], size: [float], force_func=None):
        self.mass: float = mass
        self.rect: geometry.Rect = geometry.Rect(*position, *size)
        self.vel: [float] = [0.0, 0.0]
        if not force_func is None:
            self.apply_force = force_func

        self.onGround: int = 0
        self.onWallLeft: int = 0
        self.onWallRight: int = 0

    def apply_force(self, force: float, angle: float, delta_time: float): # angle in degrees; 0 is right, counterclockwise
        r_angle = math.radians(angle)
        self.vel[0] += math.cos(r_angle) * force / self.mass * delta_time
        self.vel[1] += math.sin(r_angle) * force / self.mass * delta_time
    
    def apply_velocity(self, world, delta_time: float):
        self.rect.x += self.vel[0] * delta_time
        self.rect.x = round(self.rect.x, 5) # bugs occur at higher precision
        self.x_collide(world, delta_time)
    
        self.rect.y += self.vel[1] * delta_time
        self.rect.y = round(self.rect.y, 5)
        self.y_collide(world)

        for x in range(math.floor(self.rect.left), math.ceil(self.rect.right)):
            for y in range(math.floor(self.rect.top), math.ceil(self.rect.bottom)):
                if world[x, y]:
                    ...#print("unresolved collision:", (x, y))

    def gravity(self, delta_time):
        self.apply_force(GRAVITY_CONSTANT * self.mass * delta_time, 270, 1)
    
    def x_collide(self, world, delta_time):
        for x in range(math.floor(round(self.rect.left, 5)), math.ceil(round(self.rect.right, 5))):
            for y in range(math.floor(round(self.rect.top, 5)), math.ceil(round(self.rect.bottom, 5))):
                if world[x, y]:
                    if self.vel[0] < 0:
                        self.rect.left = x + 1
                        self.vel[0] = 0
                        
                        if not realistic:
                            if self.vel[1] < 0:
                                friction = delta_time / FRICTION_Y
                                if friction + self.vel[1] > 0:
                                    self.vel[1] = 0
                                else:
                                    self.vel[1] += friction
                        
                        self.onWallRight = max(2, int(WALL_JUMP_THRESHOLD / delta_time))

                    if self.vel[0] > 0:
                        self.rect.right = x
                        self.vel[0] = 0
                        
                        if not realistic:
                            if self.vel[1] < 0:
                                friction = delta_time / FRICTION_Y
                                if friction + self.vel[1] > 0:
                                    self.vel[1] = 0
                                else:
                                    self.vel[1] += friction
                        
                        self.onWallLeft = max(2, int(WALL_JUMP_THRESHOLD / delta_time))
    
    def y_collide(self, world):
        for x in range(math.floor(round(self.rect.left, 5)), math.ceil(round(self.rect.right, 5))):
            for y in range(math.floor(round(self.rect.top, 5)), math.ceil(round(self.rect.bottom, 5))):
                if world[x, y]:
                    if self.vel[1] > 0:
                        self.rect.bottom = y
                        self.vel[1] = 0

                    if self.vel[1] < 0:
                        self.rect.top = y + 1
                        self.vel[1] = 0

                        self.onGround = JUMP_THRESHOLD

    def update(self, world, delta_time):
        self.gravity(delta_time)
        if self.onGround:
            self.onGround -= 1
            friction = math.copysign(delta_time / FRICTION_X, self.vel[0])
            if abs(friction) > abs(self.vel[0]):
                self.vel[0] = 0
            else:
                self.vel[0] -= friction
        if self.onWallLeft:
            self.onWallLeft -= 1
        if self.onWallRight:
            self.onWallRight -= 1

        self.apply_velocity(world, delta_time)
