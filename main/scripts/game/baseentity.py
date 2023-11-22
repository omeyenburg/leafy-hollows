# -*- coding: utf-8 -*-
from scripts.graphics import particle
from scripts.graphics import sound
from scripts.game import physics


class LivingEntity(physics.PhysicsObject):
    def __init__(self, *args, health: int=1, **kwargs):
        super().__init__(*args, *kwargs)
        self.holding = None
        self.health: int = health
        self.max_health: int = health

    def update(self, world, delta_time):
        if not self.holding is None:
            self.holding.cooldown -= delta_time
        super().update(world, delta_time)

    def damage(self, window, amount: float=0, velocity: [float]=(0, 0)):
        self.health -= amount

        self.vel[0] += velocity[0] * 0.5
        self.vel[1] += velocity[1] * 0.5

        x = (self.rect.centerx - window.camera.pos[0]) * 0.1
        sound.play(window, "damage", x)
        particle.text(window, "-" + str(amount), *self.rect.center, size=0.2, color=(165, 48, 48, 255), time=0.5, offset_radius=self.rect.h)

        if self.health <= 0:
            self.death(window)
            return

        if self.type == "player":
            window.effects["damage_screen"] = 1
            window.damage_time = 0.3

    def death(self, window):
        particle.spawn(window, "dust_particle", *self.rect.center)
        particle.spawn(window, "blood_particle", *self.rect.center)
