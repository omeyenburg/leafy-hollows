# -*- coding: utf-8 -*-
from scripts.graphics import particle
from scripts.utility.const import *
import random
import math


class BaseItem:
    def __init__(self, damage: float=0.0, attack_speed: float=0.0, range: float=0.0, crit_chance: float=0.0, luck: int=1):
        attributes = random.sample(ATTRIBUTES, k=2)
        self.attributes: dict = {
            attributes[0]: random.randint(1, luck),
            attributes[1]: random.randint(1, luck),
        }

        self.damage: float = damage
        self.attack_speed: float = attack_speed
        self.range: float = range
        self.crit_chance: float = crit_chance
        self.cooldown: float = 0.0


# Sword, Axe, Pickaxe
class MeleeWeapon(BaseItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attack(self, window, world, attacker, angle):
        if self.cooldown > 0:
            return
        self.cooldown = 1 / self.attack_speed

        targets = set()
        for entity in world.loaded_entities:
            if entity is attacker:
                continue
            entity_distance = math.sqrt((attacker.rect.centerx - entity.rect.centerx) ** 2 + (attacker.rect.centery - entity.rect.centery) ** 2)
            if entity_distance > self.range:
                continue
            if entity_distance < 1:
                targets.add((1, entity))
                continue
            entity_angle = math.atan2(entity.rect.centery - attacker.rect.centery, entity.rect.centerx - attacker.rect.centerx)
            angle_distance = abs(entity_angle - angle)
            if angle_distance < self.max_angle_offset:
                targets.add((angle_distance, entity))
        
        if not targets:
            return

        max_target_count = self.attributes.get("piercing", 0) + 1
        velocity = (
            attacker.vel[0] * 0.5 + math.cos(angle),
            attacker.vel[1] * 0.5 + math.sin(angle)
        )

        if max_target_count == 1:
            target = min(targets, key=lambda i: i[0])[1]
            target.damage(window, self.damage, attacker.vel)
        else:
            targets = sorted(targets, key=lambda i: i[0])[:max_target_count]
            for target in targets:
                target[1].damage(window, self.damage, attacker.vel)

        if -math.pi < angle * 2 < math.pi:
            particle.spawn(window, "impact_right_particle", *attacker.rect.center)
        else:
            particle.spawn(window, "impact_left_particle", *attacker.rect.center)

# Bow, Banana
class RangedWeapon(BaseItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attack(self, window, world, attacker, angle):
        if self.cooldown > 0:
            return
        self.cooldown = 1 / self.attack_speed

        world.add_entity(Arrow(self.rect.center, speed=60, angle=angle, owner=attacker))

# Magic Wands
class MagicWeapon(BaseItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def generate_attribute(luck: float):
    ...
