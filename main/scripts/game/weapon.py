# -*- coding: utf-8 -*-
from scripts.game.baseitem import MeleeWeapon, RangedWeapon, MagicWeapon
from scripts.graphics import particle
import math


class Stick(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=1, attack_speed=1, range=1.5, crit_chance=0.1, luck=luck)
        self.image = "stick"
        self.angle = 0
        self.max_angle_offset = math.pi / 3


class Sword(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=2, attack_speed=1.5, range=2.5, crit_chance=0.1, luck=luck)
        self.image = "sword"
        self.angle = 30
        self.max_angle_offset = math.pi / 4


class Axe(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=4, attack_speed=1, range=2, crit_chance=0.2, luck=luck)
        self.image = "axe"
        self.angle = 30
        self.max_angle_offset = math.pi / 3

 
class Pickaxe(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=6, attack_speed=0.5, range=1.5, crit_chance=0.3, luck=luck)
        self.image = "pickaxe"
        self.angle = 30
        self.max_angle_offset = math.pi / 6


class Bow(RangedWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=2, attack_speed=2, range=6, crit_chance=0.1, luck=luck)
        self.image = "bow"
        self.angle = -30
        self.max_angle_offset = math.pi / 4


class Banana(RangedWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=2, attack_speed=4, range=10, crit_chance=0.2, luck=luck)
        self.image = "banana"
        self.angle = 0
        self.max_angle_offset = math.pi / 4


class ArcaneStaff(MagicWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=5, attack_speed=1, range=20, crit_chance=0.5, luck=luck)
        self.image = "arcane_staff"
        self.angle = 30
