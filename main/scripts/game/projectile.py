# -*- coding: utf-8 -*-
from scripts.game.baseentity import LivingEntity
from scripts.game.physics import PhysicsObject
from scripts.graphics.window import Window
from scripts.utility.const import *


class Arrow(PhysicsObject):
    def __init__(self, spawn_pos: [float], speed: float=0, angle: float=0, owner: LivingEntity=None):
        super().__init__(5, spawn_pos, ARROW_RECT_SIZE)

        self.angle = angle
        self.owner = owner
        self.destroy_unloaded = True

        self.apply_force(speed, angle, 1, is_radians=True)

    def draw(self, window: Window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        # Draw arrow
        rect = window.camera.map_coord((self.rect.x - 0.25 + self.rect.w / 2, self.rect.y - 0.25 + self.rect.h / 2, 0.5, 0.5), from_world=True)
        window.draw_image("arrow", rect[:2], rect[2:], angle=math.degrees(self.angle))

    def update(self, world, window: Window):
        # Cancel when arrow in wall
        if self.block_above or self.block_below or self.block_left or self.block_right:
            return

        # Rotate along velocity
        self.angle = math.atan2(*self.vel[::-1]) + math.pi

        # Hurt entities
        for entity in world.loaded_entities:
            if (not (entity is self or entity is self.owner)) and isinstance(entity, LivingEntity) and self.rect.collide_rect(entity.rect):
                entity.damage(window, 1, self.vel)
                self.owner.holding.apply_attributes(window, self.owner, entity)
                world.entities.discard(self)
                break

        super().update(world, window.delta_time)