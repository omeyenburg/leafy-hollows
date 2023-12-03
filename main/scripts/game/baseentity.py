# -*- coding: utf-8 -*-
from scripts.graphics.image import get_hand_position
from scripts.graphics import particle
from scripts.utility.const import *
from scripts.graphics import sound
from scripts.game import physics


class LivingEntity(physics.PhysicsObject):
    def __init__(self, *args, health: int=1, **kwargs):
        super().__init__(*args, *kwargs)
        self.holding = None
        self.health: int = health
        self.max_health: int = health
        self.stunned: float = 0

    def draw(self, window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        # Health bar
        unmapped_rect = (self.rect.x - 0.5 + self.rect.w / 2, self.rect.y + self.rect.h + 0.5, 1, 4/16)
        length = self.health / self.max_health

        rect = window.camera.map_coord(unmapped_rect, from_world=True)
        window.draw_image("health_bar", rect[:2], rect[2:])

        rect = window.camera.map_coord((unmapped_rect[0] + 1/16 + 14/16 * length, unmapped_rect[1] + 1/16, 14/16 * (1 - length), 2/16), from_world=True)
        window.draw_rect(rect[:2], rect[2:], (30, 29, 57))

        # Holding Item
        if not self.holding is None:
            self.draw_holding_item(window)

    def draw_holding_item(self, window):
        hand_position = get_hand_position(window, self.image + "_" + self.state, offset=self.uuid)

        if "climb" in self.state:
            flip = (0, 0)
            weapon_offset = (-0.1, 0)
        else:
            flip = (not self.direction, 0)
            if self.holding.image == "banana":
                weapon_offset = (0.15, -0.05)
            elif self.holding.image == "bow":
                weapon_offset = (-0.15, -0.1)        
            else:
                weapon_offset = (0, 0)

        if self.direction:
            center = (
                self.rect.centerx - hand_position[0] - weapon_offset[0],
                self.rect.centery + hand_position[1] + weapon_offset[1]
            )
            angle = -hand_position[2]
        else:
            #center = (self.rect.right + 0.2, self.rect.centery - 0.1)
            #angle = -40
            center = (
                self.rect.centerx + hand_position[0] + weapon_offset[0],
                self.rect.centery + hand_position[1] + weapon_offset[1]
            )
            angle = hand_position[2]
        

        weapon_size = 0.6
        rect = window.camera.map_coord((center[0] - weapon_size / 2, center[1] - weapon_size / 2, weapon_size, weapon_size), from_world=True)
        window.draw_image(self.holding.image, rect[:2], rect[2:], angle, flip)

    def update(self, world, delta_time):
        if not self.holding is None:
            self.holding.cooldown -= delta_time
        if self.stunned:
            self.stunned = max(0, self.stunned - delta_time)
        super().update(world, delta_time)

    def damage(self, window, amount: float=0, velocity: [float]=(0, 0)):
        if not self.holding is None:
            damage_multiplier = 1

            shielding_level = self.holding.attributes.get("shielding", 0)
            if shielding_level:
                damage_multiplier -= shielding_level * ATTRIBUTE_BASE_MODIFIERS["shielding"] * 0.01

            berserker_level = self.holding.attributes.get("berserker", 0)
            if berserker_level:
                damage_multiplier += berserker_level * ATTRIBUTE_BASE_MODIFIERS["berserker"] * 0.01

            amount *= damage_multiplier
        amount = round(amount, 1)

        self.stunned += 0.2
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

    def heal(self, window, amount: float=0):
        if self.health < self.max_health:
            sound.play(window, "heal")
            particle.text(window, "+", *self.rect.center, size=0.2, color=(165, 48, 48, 255), time=0.5, offset_radius=self.rect.h)
            self.health = min(self.health + amount, self.max_health)

    def death(self, window):
        particle.spawn(window, "dust_particle", *self.rect.center)
        particle.spawn(window, "blood_particle", *self.rect.center)
