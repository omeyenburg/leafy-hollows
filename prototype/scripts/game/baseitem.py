# -*- coding: utf-8 -*-
from scripts.game.baseentity import LivingEntity
from scripts.game.projectile import Arrow
from scripts.graphics import particle
from scripts.utility.const import *
from scripts.graphics import sound


class BaseItem:
    def __init__(self, damage: float=0.0, attack_speed: float=0.0, range: float=0.0, crit_chance: float=0.0, luck: int=1):
        self.uuid = int(os.environ.get("item_count"))
        os.environ["item_count"] = str(self.uuid + 1)

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

    def apply_attributes(self, window, attacker, target):
        vampire_level = self.attributes.get("vampire", 0)
        if vampire_level:
            weapon_heal = vampire_level * ATTRIBUTE_BASE_MODIFIERS["vampire"] * 0.01 * attacker.max_health
            attacker.heal(window, weapon_heal)

        paralysis_level = self.attributes.get("paralysis", 0)
        if paralysis_level:
            weapon_paralysis = paralysis_level * ATTRIBUTE_BASE_MODIFIERS["paralysis"] * 0.01
            if weapon_paralysis > random.random():
                target.stunned += 1.5

    def get_weapon_stat_increase(self, world):
        damage = self.damage
        attack_speed = self.attack_speed
        weapon_range = self.range
        crit_chance = self.crit_chance

        ferocity_level = self.attributes.get("ferocity", 0)
        if ferocity_level:
            ferocity = ferocity_level * ATTRIBUTE_BASE_MODIFIERS["ferocity"] * 0.01
            damage *= 1 + ferocity
            attack_speed *= 1 + ferocity

        berserker_level = self.attributes.get("berserker", 0)
        if berserker_level:
            berserker = berserker_level * ATTRIBUTE_BASE_MODIFIERS["berserker"] * 0.01
            damage *= 1 + berserker

        agility_level = self.attributes.get("agility", 0)
        if agility_level:
            agility = agility_level * ATTRIBUTE_BASE_MODIFIERS["agility"] * 0.01
            attack_speed *= 1 + agility
        
        critical_level = self.attributes.get("critical", 0)
        if critical_level:
            critical = critical_level * ATTRIBUTE_BASE_MODIFIERS["critical"] * 0.01
            crit_chance += critical

        warrior_level = self.attributes.get("warrior", 0)
        if warrior_level:
            number_enemies = len(list(filter(lambda i: i.type == "enemy", world.loaded_entities)))
            warrior = warrior_level * ATTRIBUTE_BASE_MODIFIERS["warrior"] * 0.01 * number_enemies
            damage *= 1 + warrior

        assassin_level = self.attributes.get("assassin", 0)
        if assassin_level:
            assassin = assassin_level * ATTRIBUTE_BASE_MODIFIERS["assassin"] * 0.01
            attack_speed *= 1 + assassin
            crit_chance += assassin

        longshot_level = self.attributes.get("longshot", 0)
        if longshot_level:
            longshot = longshot_level * ATTRIBUTE_BASE_MODIFIERS["longshot"] * 0.01
            weapon_range *= 1 + longshot

        return damage, attack_speed, weapon_range, min(crit_chance, 1)


# Sword, Axe, Pickaxe
class MeleeWeapon(BaseItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attack(self, window, world, attacker, angle, arg_range=None):
        if self.cooldown > 0:
            return

        attacker.attack_animation = 1.5

        damage, attack_speed, weapon_range, crit_chance = self.get_weapon_stat_increase(world)
        if not arg_range is None:
            weapon_range = arg_range
        self.cooldown = 1 / attack_speed

        targets = set()
        for entity in world.loaded_entities:
            if entity is attacker or not isinstance(entity, LivingEntity):
                continue
            entity_distance = dist(attacker.rect.center, entity.rect.center)
            if entity_distance > weapon_range:
                continue
            if entity_distance < 1:
                targets.add((1, entity))
                continue
            entity_angle = atan2(entity.rect.centery - attacker.rect.centery, entity.rect.centerx - attacker.rect.centerx)
            angle_distance = abs(entity_angle - angle)
            if angle_distance < self.max_angle_offset:
                targets.add((angle_distance, entity))

        if not targets:
            sound.play(window, "sword_swing", x=(world.player.rect.x - attacker.rect.x) / 5)
            return
        sound.play(window, "sword_hit", x=(world.player.rect.x - attacker.rect.x) / 5)

        max_target_count = self.attributes.get("piercing", 0) + 1
        velocity = (
            attacker.vel[0] * 0.5 + cos(angle),
            attacker.vel[1] * 0.5 + sin(angle)
        )

        critical_multiplier = 1 + 0.5 * (crit_chance > random.random())

        if max_target_count == 1:
            target = min(targets, key=lambda i: i[0])[1]
            target.damage(window, damage * critical_multiplier, attacker.vel)
        else:
            targets = sorted(targets, key=lambda i: i[0])[:max_target_count]
            for target in targets:
                target[1].damage(window, damage * critical_multiplier, attacker.vel)
            target = targets[0][1]

        BaseItem.apply_attributes(self, window, attacker, target)
    
        attack_particle = random.choice(("impact", "swing"))
        if -pi < angle * 2 < pi:
            attack_particle += "_right"
        else:
            attack_particle += "_left"
        particle.spawn(window, attack_particle + "_particle", *attacker.rect.center)

        explosive = self.attributes.get("explosive", 0)
        if explosive:
            explosion_damage = damage * ATTRIBUTE_BASE_MODIFIERS["explosive"] * 0.01
            particle.explosion(window, *target.rect.center, size=2.0, time=0.5)
            sound.play(window, "explosion", x=(world.player.rect.x - target.rect.x) / 5)

            for entity in world.loaded_entities:
                if entity.type in ("enemy", "player"):
                    distance = dist(entity.rect.center, target.rect.center)
                    if distance < 3:
                        entity.stunned += 0.3
                        damage = explosion_damage * min(1, max(0, 3 - distance)) ** 0.4
                        entity.damage(window, damage, (0, 0))

# Bow, Banana
class RangedWeapon(BaseItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attack(self, window, world, attacker, angle):
        if self.cooldown > 0:
            return

        if attacker.type == "player":
            if attacker.inventory.arrows:
                attacker.inventory.arrows -= 1
            else:
                MeleeWeapon.attack(self, window, world, attacker, angle, arg_range=2)
                return
        sound.play(window, "bow_fling", x=(world.player.rect.x - attacker.rect.x) / 5)

        damage, attack_speed, weapon_range, crit_chance = self.get_weapon_stat_increase(world)
        world.add_entity(Arrow(attacker.rect.center, speed=weapon_range * 10, angle=angle, owner=attacker))
        self.cooldown = 1 / attack_speed
