# -*- coding: utf-8 -*-
from scripts.game.baseitem import MeleeWeapon, RangedWeapon, MagicWeapon
from scripts.graphics import particle
import math


class Hand(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=2, attack_speed=2, range=2, crit_chance=0.1, luck=luck)
        self.image = "sword"
        self.max_angle_offset = math.pi / 4
        


class Sword(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=2, attack_speed=2, range=2, crit_chance=0.1, luck=luck)
        self.image = "sword"
        self.max_angle_offset = math.pi / 4


class Axe(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=4, attack_speed=1, range=1.5, crit_chance=0.2, luck=luck)
        self.image = "axe"
        self.max_angle_offset = math.pi / 3

 
class Pickaxe(MeleeWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=6, attack_speed=1, range=1.5, crit_chance=0.3, luck=luck)
        self.image = "pickaxe"
        self.max_angle_offset = math.pi / 8


class Bow(RangedWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=3, attack_speed=2, range=20, crit_chance=0.1, luck=luck)
        self.image = "bow"


class Banana(RangedWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=2, attack_speed=4, range=17, crit_chance=0.2, luck=luck)
        self.image = "banana"


class ArcaneStaff(MagicWeapon):
    def __init__(self, luck: int=1):
        super().__init__(damage=5, attack_speed=1, range=20, crit_chance=0.5, luck=luck)
        self.image = "arcane_staff"
