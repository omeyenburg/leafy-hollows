# -*- coding: utf-8 -*-
from scripts.utility.util import realistic
import scripts.utility.geometry as geometry
import scripts.game.physics as physics
import scripts.game.player as player
import scripts.game.entity as entity
import scripts.game.world as world

class Game:
    def __init__(self, window):
        self.window: graphics.Window = window
        self.world: world.World = world.World(window.block_indices)
        if realistic:
            self.player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.2, jump_force=17)
        else:
            self.player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.1, jump_force=36)
        self.world.entities.append(self.player)
        
        #self.rope = entity.Rope(10, (0, 0), (11, 0))
        #self.dust = entity.Dust((0, 0))

    def update(self):
        self.world.update(self.window)
        #self.world.draw(self.window)
        #self.player.update(self.world, self.window)
        #self.rope.update(self.world, self.window)
        #self.dust.update(self.world, self.window)
