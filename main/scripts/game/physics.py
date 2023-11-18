# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.utility import geometry
import uuid
import math


def _generate_uuid():
    return str(uuid.uuid4()) # 2^128 unique ids; low collision chance


class PhysicsObject:
    def __init__(self, mass: float, position: [float], size: [float]):
        self.uuid = _generate_uuid()
        self.type = "physics_object"
        self.mass: float = mass
        self.rect: geometry.Rect = geometry.Rect(*position, *size)
        self.vel: [float] = [0.0, 0.0]

        self.inWater: bool = False
        self.underWater: bool = False

        # Blocks next to object (when object collides with them)
        self.block_below: int = 0
        self.block_above: int = 0
        self.block_left: int = 0
        self.block_right: int = 0

        # Destroy projectiles
        self.destroy_unloaded: bool = False

    def apply_force_horizontal(self, force: float, delta_time: float):
        """
        Applies only horizontal force to the object.
        Equivalent to apply_force with angle = 0.
        """
        acceleration = force / self.mass
        self.vel[0] += acceleration * delta_time

    def apply_force_vertical(self, force: float, delta_time: float):
        """
        Applies only vertical force to the object.
        Equivalent to apply_force with angle = 90.
        """
        acceleration = force / self.mass
        self.vel[1] += acceleration * delta_time

    def apply_force(self, force: float, angle: float, delta_time: float, is_radians: bool=False):
        """
        Applies force to the object.
        Angle in degrees; 0 equals right; counterclockwise
        """
        if self.underWater:
            force /= 3

        # Horizontal and vertical only force to skip sin/cos
        if angle == 0:
            return self.apply_force_horizontal(force, delta_time)
        elif angle == 90:
            return self.apply_force_vertical(force, delta_time)
        elif angle == 180:
            return self.apply_force_horizontal(-force, delta_time)
        elif angle == 270:
            return self.apply_force_vertical(-force, delta_time)

        if not is_radians:
            angle = math.radians(angle)
            
        acceleration = force / self.mass
        self.vel[0] += math.cos(angle) * acceleration * delta_time
        self.vel[1] += math.sin(angle) * acceleration * delta_time
    
    def apply_velocity(self, world, delta_time: float):
        """
        Applies velocity to the object.
        """
        last_position = self.rect.center

        self.rect.x += min(PHYSICS_MAX_MOVE_DISTANCE, max(-PHYSICS_MAX_MOVE_DISTANCE, self.vel[0] * delta_time))
        self.rect.x = round(self.rect.x, 5) # Bugs occur at higher precision
        self.x_collide(world, delta_time)
    
        self.rect.y += min(PHYSICS_MAX_MOVE_DISTANCE, max(-PHYSICS_MAX_MOVE_DISTANCE, self.vel[1] * delta_time))
        self.rect.y = round(self.rect.y, 5)
        self.y_collide(world)

        # Reset object position
        if self.get_collision(world):
            self.rect.center = last_position
            self.vel = [0, 0]

        # Push water to adjacent blocks
        stength = (abs(self.vel[0]) + abs(self.vel[1])) * 5
        #block_feet = (math.floor(self.rect.centerx), round(self.rect.y))
        block_feet = (math.floor(self.rect.centerx), round(self.rect.top))
        ...

    def get_collision(self, world):
        """
        Returns whether the object collides with a block.
        """
        for x in range(math.floor(self.rect.left), math.ceil(self.rect.right)):
            #for y in range(math.floor(self.rect.y), math.ceil(self.rect.y + self.rect.h)):
            for y in range(math.floor(self.rect.top), math.ceil(self.rect.bottom)):
                if world.get_block(x, y):
                    return True
        return False

    def apply_gravity_force(self, delta_time):
        """
        Applies gravity force to the object.
        """
        if self.inWater:
            gravity = PHYSICS_GRAVITY_CONSTANT_WATER
        else:
            gravity = PHYSICS_GRAVITY_CONSTANT
        self.apply_force(gravity * self.mass, 270, delta_time)

    def apply_friction_force(self, delta_time):
        """
        Applies friction force against velocity direction to the object.
        """
        if not all(self.vel):
            return
        velocity_product = -self.vel[0]# * min(1, abs(self.vel[1]))


        block_friction = 0.5 * 10
        
        # Horizontal friction on ground or ceiling
        touching = max(self.block_below, self.block_above)
        if touching:
            force = velocity_product * block_friction * self.mass
            #print(1, round(self.vel[0], 2))
            self.apply_force_horizontal(force, delta_time)
            #print(2, round(self.vel[0], 2))
        
        # Vertical friction on walls
        touching = max(self.block_left, self.block_right)
        if touching:
            force = velocity_product * block_friction * self.mass
            self.apply_force_vertical(force, delta_time)
        
    
    def x_collide(self, world, delta_time):
        """
        Resolves collisions on the x-axis.
        """
        last_y = self.rect.y
        collision = False
        if self.vel[0]:
            self.block_right = self.block_left = 0

        for x in range(math.floor(round(self.rect.left, 5)), math.ceil(round(self.rect.right, 5))):
            #for y in range(math.floor(round(self.rect.y, 5)), math.ceil(round(self.rect.y + self.rect.h, 5))):
            for y in range(math.floor(round(self.rect.top, 5)), math.ceil(round(self.rect.bottom, 5))):
                if world.get_block(x, y):
                    
                    # Push player up if possible (instead of colliding)
                    self.rect.y = math.ceil(self.rect.y)
                    if not (self.type != "player" or abs(self.vel[0]) < 1 or self.rect.y - last_y > 0.5 or collision or self.get_collision(world)):
                        self.vel[1] *= 0.8
                        continue

                    if self.vel[0] < 0:
                        self.rect.left = x + 1
                        self.block_left = world.get_block(x, y, generate=False)

                    if self.vel[0] > 0:
                        self.rect.right = x
                        self.block_right = world.get_block(x, y, generate=False)
                    collision = True

        if collision:
            self.vel[0] = 0
            self.rect.y = last_y

        return collision

    
    def y_collide(self, world):
        """
        Resolves collisions on the y-axis.
        """
        if any(self.vel):
            self.block_above = self.block_below = 0
        for x in range(math.floor(round(self.rect.left, 5)), math.ceil(round(self.rect.right, 5))):
            #for y in range(math.floor(round(self.rect.y, 5)), math.ceil(round(self.rect.y + self.rect.h, 5))):
            for y in range(math.floor(round(self.rect.top, 5)), math.ceil(round(self.rect.bottom, 5))):
                if world.get_block(x, y):
                    if self.vel[1] > 0:
                        self.rect.bottom = y
                        self.block_above = world.get_block(x, y, generate=False)

                    if self.vel[1] < 0:
                        self.rect.top = y + 1
                        self.block_below = world.get_block(x, y, generate=False)

                    self.vel[1] = 0#self.vel[1] // 2


    def update(self, world, delta_time):
        """
        Moves the object.
        """


        #if (not hasattr(self, "can_move") and not self.can_move):
        #    self.apply_force(delta_time * abs(world.wind) / (self.mass), 90 + 90 * min(1, max(-1, -world.wind)), self.mass)
        #if self.block_below:
        #    self.block_below -= 1

            #block_friction = self.get_ground_friction(world)
            #block_friction = 0.1
            #friction = math.copysign(delta_time / block_friction, self.vel[0])
            #if abs(friction) > abs(self.vel[0]):
            #    self.vel[0] = 0
            #else:
            #    self.vel[0] -= friction
        #if self.block_left:
        #    self.block_left -= 1
        #if self.block_right:
        #    self.block_right -= 1

        block_feet = (math.floor(self.rect.centerx), round(self.rect.top))
        block_head = (math.floor(self.rect.centerx), round(self.rect.bottom))
        #block_feet = (math.floor(self.rect.centerx), round(self.rect.y))
        #block_head = (math.floor(self.rect.centerx), round(self.rect.y + self.rect.h))

        self.inWater = world.get_water(*block_feet) > 0.2
        if self.inWater and world.get_water(*block_head) > 0.2:
            self.underWater = 5
        elif self.underWater:
            self.underWater -= 1

        # Add velocity to position
        self.apply_velocity(world, delta_time)

        # Apply gravity and friction
        self.apply_gravity_force(delta_time)
        #self.apply_friction_force(delta_time)

        # Save ground block
        #if self.block_below:
        #    self.ground_block = world.get_block(math.floor(self.rect.centerx), round(self.rect.y - 1), generate=False)
        #else:
        #    self.ground_block = 0
