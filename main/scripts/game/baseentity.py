# -*- coding: utf-8 -*-
from scripts.game import physics


class LivingEntity(physics.PhysicsObject):
    def __init__(self, *args, health: int=1, **kwargs):
        super().__init__(*args, *kwargs)
        self.health: int = health
        self.max_health: int = health

    def damage(self, amount):
        self.health -= amount