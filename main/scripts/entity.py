# -*- coding: utf-8 -*-
import scripts.baseentity as baseentity


class Rope(baseentity.ChainedEntity):
    def __init__(self, length=0, start=None, end=None, element_radius=1):
        super().__init__(length=length, start=start, end=end, element_radius=element_radius)
        

    def update(self, world, window):
        super().update(world, window)
