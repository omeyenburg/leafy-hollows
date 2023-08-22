# -*- coding: utf-8 -*-
from scripts.game.world import World
from scripts.utility.const import *
import scripts.utility.geometry as geometry
import scripts.game.physics as physics
import scripts.game.player as player
import scripts.game.entity as entity


class Game:
    def __init__(self, window):
        self.window: graphics.Window = window
        self.world = World(window.block_data)
        
        if PHYSICS_REALISTIC:
            self.player: player.Player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, crouch_speed=2, swim_speed=3, acceleration_time=0.2, jump_force=17)
        else:
            self.player: player.Player = player.Player(spawn_pos=[0, 0], speed=5, sprint_speed=7, crouch_speed=3, swim_speed=3, acceleration_time=.1, jump_force=21)
        self.world.add_entity(self.player)

    def update(self):
        self.world.update(self.window)

    def draw(self):
        self.world.draw(self.window)
