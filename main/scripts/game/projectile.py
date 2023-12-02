# -*- coding: utf-8 -*-
from scripts.game.baseentity import LivingEntity
from scripts.game.physics import PhysicsObject
from scripts.graphics.window import Window
from scripts.graphics import particle
from scripts.utility.const import *
from scripts.graphics import sound


class Arrow(PhysicsObject):
    def __init__(self, spawn_pos: [float], speed: float=0, angle: float=0, owner: LivingEntity=None):
        super().__init__(5, spawn_pos, ARROW_RECT_SIZE)

        self.bow = owner.holding
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
            if any(self.vel):
                self.explode(window, world)
            return

        # Rotate along velocity
        self.angle = math.atan2(*self.vel[::-1]) + math.pi

        last_center = self.rect.center
        super().update(world, window.delta_time)

        # Hurt entities
        for entity in world.loaded_entities:
            if (not (entity is self or entity is self.owner)) and isinstance(entity, LivingEntity) and entity.rect.collide_line(self.rect.center, last_center):
                damage, attack_speed, weapon_range, crit_chance = self.bow.get_weapon_stat_increase(world)
                damage *= 1 + 0.5 * (crit_chance > random.random())
                entity.damage(window, damage, self.vel)

                self.bow.apply_attributes(window, self.owner, entity)
                self.explode(window, world)
                world.entities.discard(self)
                break

    def explode(self, window, world):
        explosive = self.bow.attributes.get("explosive", 0)
        if explosive:
            explosion_damage = self.bow.damage * explosive * ATTRIBUTE_BASE_MODIFIERS["explosive"] * 0.01
            particle.explosion(window, *self.rect.center, size=2.0, time=0.5)
            world.entities.discard(self)
            sound.play(window, "explosion", (self.rect.x - world.player.rect.x) / 10)

            for entity in world.loaded_entities:
                if entity.type in ("enemy", "player"):
                    distance = math.dist(entity.rect.center, self.rect.center)
                    if distance < 3:
                        entity.stunned += 0.3
                        damage = explosion_damage * min(1, max(0, 3 - distance)) ** 0.4
                        entity.damage(window, damage, (0, 0))
