# -*- coding: utf-8 -*-
from scripts.utility.const import *
from scripts.game.weapon import *
import random


class Inventory:
    def __init__(self):
        self.weapons = [Weapon(5) for Weapon in random.choices((Sword, Axe, Pickaxe, Bow), k=10)]
        self.marked_weapons = []
