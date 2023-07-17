# -*- coding: utf-8 -*-
from scripts.baseentity import *


class Rope(ChainedEntity):
    def __init__(self, length=0, start=None, end=None, element_radius=1):
        super().__init__(length=length, start=start, end=end, element_radius=element_radius)
        
    def update(self, world, window):
        super().update(world, window)


class Dust(Particle):
    def __init__(self, position):
        super().__init__(1, position, (0.1, 0.1), gravity=1)

    def update(self, world, window):
        super().update(world, window.delta_time)
        self.draw(window)

    def draw(self, window):
        rect = window.camera.map_coord(self.rect, from_world=True)
        window.draw_circle(rect[:2], self.rect[2], (255, 255, 255))