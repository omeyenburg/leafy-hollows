import scripts.world as world
import scripts.geometry as geometry
import scripts.physics as physics
import scripts.player as player


class Game:
    def __init__(self, window):
        self.window = window
        self.world = world.World()
        self.player = player.Player(self, spawn_pos=[0, 0], speed=6, sprint_speed=10, acceleration_time=0.1, jump_force=35)

    def update(self):
        self.world.draw(self.window)
        self.player.update()