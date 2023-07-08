# -*- coding: utf-8 -*-
import scripts.physics as physics


class Entity(physics.PhysicsObject):
    ...


class LivingEntity(physics.PhysicsObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.health = 0


class Particle(physics.PhysicsObject):
    ...