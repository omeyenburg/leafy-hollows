# -*- coding: utf-8 -*-
from scripts.game.baseentity import LivingEntity
from scripts.game.physics import PhysicsObject
from scripts.graphics.window import Window
from scripts.graphics import particle
from scripts.utility.const import *
import math


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
            if (not (entity is self or entity is self.owner)) and isinstance(entity, LivingEntity) and self.rect.intersection(entity.rect):
                entity.damage(window, 1, self.vel)
                world.entities.discard(self)

        super().update(world, window.delta_time)


class Slime(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(30, spawn_pos, SLIME_RECT_SIZE, health=5)

        # Enemy attributes
        self.level = 1             # Difficulty
        self.hit_damage = 1        # Damage applied to player on collision
        self.attack_cooldown = 3

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("slime_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0))

    def update(self, world, window: Window):
        if self.block_below:
            if self.hit_ground == 0:
                self.hit_ground = 0.2
                particle.spawn(window, world, "slime_particle", self.rect.centerx, self.rect.top, amount=0.5)
            self.hit_ground -= window.delta_time
            self.vel[0] *= 0.8
            self.attack_cooldown = 0

            if self.hit_ground < -0.5:
                self.direction = int(world.player.rect.x < self.rect.x)
                self.vel[1] += 6
        else:
            self.hit_ground = 0
            self.vel[0] += 0.1 * (-self.direction + 0.5)

        vel_y = abs(self.vel[1])
        if vel_y > 3:
            self.state = "high_jump"
        elif vel_y != 0:
            self.state = "jump"
        else:
            self.state = "idle"

        if self.hit_ground > 0:
            self.state = "hit_ground"

        super().update(world, window.delta_time)

        # Attack player
        if self.attack_cooldown < 0 and self.vel[1] < 0 and self.rect.intersection(world.player.rect):
            world.player.damage(window, 1, self.vel)
            self.attack_cooldown = 5
        self.attack_cooldown -= window.delta_time
        