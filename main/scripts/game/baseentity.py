# -*- coding: utf-8 -*-
from scripts.game import physics
from scripts.graphics import sound


class LivingEntity(physics.PhysicsObject):
    def __init__(self, *args, health: int=1, **kwargs):
        super().__init__(*args, *kwargs)
        self.health: int = health
        self.max_health: int = health

    def damage(self, window, amount: float=0, velocity: [float]=(0, 0)):
        self.health -= amount

        self.vel[0] += velocity[0] * 0.5
        self.vel[1] += velocity[1] * 0.5

        x = (self.rect.centerx - window.camera.pos[0]) * 0.1
        sound.play(window, "damage", x)