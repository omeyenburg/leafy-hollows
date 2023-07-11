# -*- coding: utf-8 -*-
import scripts.world as world
import scripts.geometry as geometry
import scripts.physics as physics
import scripts.player as player
import scripts.entity as entity
from scripts.util import realistic

class Game:
    def __init__(self, window):
        self.window: graphics.Window = window
        self.world: world.World = world.World(window.block_indices)
        if realistic:
            self.player: player.Player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.2, jump_force=17)
        else:
            self.player: player.Player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.1, jump_force=36)
        
        self.rope = entity.Rope(10, (0, 0), (11, 0))

    def update(self):
        #self.world.draw(self.window)
        self.player.update(self.world, self.window)
        self.rope.update(self.world, self.window)
