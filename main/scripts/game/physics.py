# -*- coding: utf-8 -*-
from scripts.utility.const import *
import scripts.utility.geometry as geometry
import uuid
import math


def _generate_uuid():
    return str(uuid.uuid4()) # 2^128 unique ids; low collision chance


class CollisionPhysicsObject:
    def __init__(self, mass: float, position: [float], size: [float], force_func=None):
        self.uuid = _generate_uuid()
        self.mass: float = mass
        self.rect: geometry.Rect = geometry.Rect(*position, *size)
        self.vel: [float] = [0.0, 0.0]
        if not force_func is None:
            self.apply_force = force_func

        self.onGround: int = 0
        self.onWallLeft: int = 0
        self.onWallRight: int = 0
        self.inWater: bool = False
        self.underWater: bool = False

    def apply_force(self, force: float, angle: float, delta_time: float): # angle in degrees; 0 is right, counterclockwise
        """
        Applies force to the object.
        """
        if self.underWater:
            force /= 3
        r_angle = math.radians(angle)
        self.vel[0] += math.cos(r_angle) * force / self.mass * delta_time
        self.vel[1] += math.sin(r_angle) * force / self.mass * delta_time
    
    def apply_velocity(self, world, delta_time: float):
        """
        Applies velocity to the object.
        """
        last_position = self.rect.topleft

        self.rect.x += min(PHYSICS_MAX_MOVE_DISTANCE, max(-PHYSICS_MAX_MOVE_DISTANCE, self.vel[0] * delta_time))
        self.rect.x = round(self.rect.x, 5) # Bugs occur at higher precision
        self.x_collide(world, delta_time)
    
        self.rect.y += min(PHYSICS_MAX_MOVE_DISTANCE, max(-PHYSICS_MAX_MOVE_DISTANCE, self.vel[1] * delta_time))
        self.rect.y = round(self.rect.y, 5)
        self.y_collide(world)

        # Reset object position
        if self.get_collision(world):
            self.rect.topleft = last_position
            self.vel = [0, 0]

        # Push water to adjacent blocks
        stength = (abs(self.vel[0]) + abs(self.vel[1])) * 5
        block_feet = (math.floor(self.rect.centerx), round(self.rect.top))
        ...

    def get_collision(self, world):
        """
        Returns whether the object collides with a block.
        """
        for x in range(math.floor(self.rect.left), math.ceil(self.rect.right)):
            for y in range(math.floor(self.rect.top), math.ceil(self.rect.bottom)):
                if world.get_block(x, y):
                    return True
        return False

    def gravity(self, delta_time):
        """
        Applies gravity to the object.
        """
        if self.inWater:
            gravity = PHYSICS_GRAVITY_CONSTANT_WATER
        else:
            gravity = PHYSICS_GRAVITY_CONSTANT
        self.apply_force(gravity * self.mass * delta_time, 270, 1)
    
    def x_collide(self, world, delta_time):
        """
        Resolves collisions on the x-axis.
        """
        for x in range(math.floor(round(self.rect.left, 5)), math.ceil(round(self.rect.right, 5))):
            for y in range(math.floor(round(self.rect.top, 5)), math.ceil(round(self.rect.bottom, 5))):
                if world.get_block(x, y):
                    if self.vel[0] < 0:
                        self.rect.left = x + 1
                        self.vel[0] = 0
                        self.onWallRight = max(2, int(PHYSICS_WALL_JUMP_THRESHOLD / delta_time))

                    if self.vel[0] > 0:
                        self.rect.right = x
                        self.vel[0] = 0                        
                        self.onWallLeft = max(2, int(PHYSICS_WALL_JUMP_THRESHOLD / delta_time))
    
    def y_collide(self, world):
        """
        Resolves collisions on the y-axis.
        """
        for x in range(math.floor(round(self.rect.left, 5)), math.ceil(round(self.rect.right, 5))):
            for y in range(math.floor(round(self.rect.top, 5)), math.ceil(round(self.rect.bottom, 5))):
                if world.get_block(x, y):
                    if self.vel[1] > 0:
                        self.rect.bottom = y
                        self.vel[1] = 0

                    if self.vel[1] < 0:
                        self.rect.top = y + 1
                        self.vel[1] = 0

                        self.onGround = PHYSICS_JUMP_THRESHOLD

    def update(self, world, delta_time):
        """
        Moves the object.
        """
        self.gravity(delta_time)
        if not (hasattr(self, "can_move") and not self.can_move):
            self.apply_force(delta_time * abs(world.wind) / (self.mass), 90 + 90 * min(1, max(-1, -world.wind)), self.mass)
        if self.onGround:
            self.onGround -= 1
            friction = math.copysign(delta_time / PHYSICS_FRICTION_X, self.vel[0])
            if abs(friction) > abs(self.vel[0]):
                self.vel[0] = 0
            else:
                self.vel[0] -= friction
        if self.onWallLeft:
            self.onWallLeft -= 1
        if self.onWallRight:
            self.onWallRight -= 1

        block_feet = (math.floor(self.rect.centerx), round(self.rect.top))
        block_head = (math.floor(self.rect.centerx), round(self.rect.bottom))

        self.inWater = world.get_water(*block_feet) > 0.2
        self.underWater = self.inWater and world.get_water(*block_head) > 0.2

        self.apply_velocity(world, delta_time)


class PhysicsObject: # No collision
    def __init__(self, mass: float, position: [float], size: [float], gravity: float=9.81):
        self.uuid = _generate_uuid()
        self.mass: float = mass
        self.rect: geometry.Rect = geometry.Rect(*position, *size)
        self.vel: [float] = [0.0, 0.0]
        self.gravity_constant = gravity

    def apply_force(self, force: float, angle: float, delta_time: float): # angle in degrees; 0 is right, counterclockwise
        """
        Applies force to the object.
        """
        r_angle = math.radians(angle)
        self.vel[0] += math.cos(r_angle) * force / self.mass * delta_time
        self.vel[1] += math.sin(r_angle) * force / self.mass * delta_time

    def update(self, world, delta_time):
        """
        Moves the object.
        """
        self.apply_force(self.gravity_constant * self.mass * delta_time, 270, 1)
        self.apply_force(delta_time * abs(world.wind) / (self.mass / 5), 90 + 90 * min(1, max(-1, -world.wind)), self.mass)
        self.rect.x += self.vel[0] * delta_time
        self.rect.x = round(self.rect.x, 5) # bugs occur at higher precision
        self.rect.y += self.vel[1] * delta_time
        self.rect.y = round(self.rect.y, 5)
