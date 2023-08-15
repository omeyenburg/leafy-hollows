# -*- coding: utf-8 -*-
import math


class Camera:
    def __init__(self, window):
        self.resolution: int = window.options["resolution"]
        self.pixels_per_meter: int = window.options["resolution"] * 16
        self.threshold = 0.1

        self.pos: [float] = [0, 0]
        self.vel: [float] = [0, 0]
        self.dest: [float] = [0, 0]
        self.window: Window = window

    def reset(self):
        self.pos: [float] = [0, 0]
        self.vel: [float] = [0, 0]
        self.dest: [float] = [0, 0]

    def set(self, pos):
        """
        Set the camera position.
        Use move() for slow movement.
        """
        self.pos = pos
        self.vel = [0, 0]
        self.dest = pos

    def move(self, pos: [float]):
        """
        Move the camera slowly to a position.
        Use set() for instant movement.
        """
        self.dest = pos

    def update(self):
        """
        Update the camera.
        """
        xvel = round((self.dest[0] - self.pos[0]) / 10, 3)
        yvel = round((self.dest[1] - self.pos[1]) / 10, 3)

        xvel = math.copysign(max(abs(xvel) - self.threshold, 0), xvel)
        yvel = math.copysign(max(abs(yvel) - self.threshold, 0), yvel)

        self.vel[0] = xvel
        self.vel[1] = yvel
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    def map_coord(self, coord: [float], from_pixel: bool=True, from_centered: bool=True, from_world: bool=False, pixel: bool=False, centered: bool=True, world: bool=False):
        """
        Convert a coordinate to a different format.
        Current format specified by from_pixel, from_centered, from_world.
        Output format specified by pixel, centered, world.
        """
        if from_world:
            from_pixel = True
        if world:
            pixel = True
        coord = list(coord)

        if from_world and not world:
            for i in range(len(coord)):
                if i < 2:
                    coord[i] = (coord[i] - self.pos[i]) * self.pixels_per_meter
                else:
                    coord[i] = coord[i] * self.pixels_per_meter
        elif (not from_world) and world:
            for i in range(len(coord)):
                coord[i] = coord[i] / self.pixels_per_meter + self.pos[i % 2]

        if from_pixel and not pixel:
            for i in range(len(coord)):
                coord[i] /= (self.window.width, self.window.height)[i%2] / 2
        elif (not from_pixel) and pixel:
            for i in range(len(coord)):
                coord[i] /= (self.window.width, self.window.height)[i%2] / 2

        if (not from_centered) and centered:
            for i in range(2):
                coord[i] -= 1
        elif from_centered and not centered:
            for i in range(2):
                coord[i] += 1

        return coord

    def map_color(self, color):
        if not float in color:
            color = [i / 255 for i in color]
        if len(color) == 3:
            color = (*color, 1)
        return color

    def visible_blocks(self):
        center = (math.floor(self.pos[0]),
                  math.floor(self.pos[1]))
        start = (center[0] - math.floor(self.window.width / 2 / self.pixels_per_meter) - 3,
                 center[1] - math.floor(self.window.height / 2 / self.pixels_per_meter) - 3)
        end = (center[0] + math.ceil(self.window.width / 2 / self.pixels_per_meter) + 3,
               center[1] + math.ceil(self.window.height / 2 / self.pixels_per_meter) + 3)
        return start, end