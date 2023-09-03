# -*- coding: utf-8 -*-
from scripts.utility.geometry import angle
from scripts.game import physics
import math
math.angle = angle


class Entity(physics.PhysicsObject): # Used for ropes etc.
    ...


class LivingEntity(physics.PhysicsObject):
    def __init__(self, *args, health: int=0, **kwargs):
        super().__init__(*args, *kwargs)
        self.health: int = health

    def damage(self, amount):
        self.health -= amount
