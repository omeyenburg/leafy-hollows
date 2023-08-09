# -*- coding: utf-8 -*-
from scripts.utility.util import realistic
import scripts.utility.geometry as geometry
import scripts.game.physics as physics
import scripts.game.player as player
import scripts.game.entity as entity
import scripts.game.world as world
from threading import Thread
import time


class Game:
    def __init__(self, window, world):
        self.window: graphics.Window = window
        #self.world: world.World = world.World(window.block_indices)
        self.world = world
        if realistic:
            self.player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.2, jump_force=17)
        else:
            self.player = player.Player(spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.1, jump_force=36)
        self.world.entities.append(self.player)
        
        #self.rope = entity.Rope(10, (0, 0), (11, 0))
        #self.dust = entity.Dust((0, 0))

    def update(self):
        self.world.update(self.window)

    def generate_world_thread(block_indices, result):
        instance = world.World(block_indices)
        time.sleep(2) # wait for normal fps
        result[0] = instance

    def generate_world(window):
        result = [None]
        thread = Thread(target=Game.generate_world_thread, daemon=True, args=(window.block_indices, result))
        thread.result = result
        thread.start()
        return thread

    def get_world(thread: Thread):
        return thread.result[0]