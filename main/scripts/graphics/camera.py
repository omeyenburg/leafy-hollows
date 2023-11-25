# -*- coding: utf-8 -*- 
from scripts.utility.const import *


class Camera:
    def __init__(self, window):
        self.resolution: float = 1.0
        self.resolution_start: float = 1.0
        self.resolution_goal: float = 1.0
        self.resolution_speed: float = 0.0
        self.resolution_index: float = 1.0
        self.pixels_per_meter: float = WORLD_BLOCK_SIZE
        self.threshold: float = 0
        self.speed: float = 1.0

        self.pos: [float] = [0, 0]
        self.vel: [float] = [0, 0]
        self.dest: [float] = [0, 0]
        self.shift_pos: float = 0.0
        self.shift_dest: float = 0.0
        self.window: Window = window

    def reset(self):
        self.resolution: float = 1.0
        self.resolution_start: float = 1.0
        self.resolution_goal: float = 1.0
        self.resolution_speed: float = 0.0
        self.resolution_index: float = 1.0
        self.pixels_per_meter: float = WORLD_BLOCK_SIZE

        self.pos: [float] = [0, 0]
        self.vel: [float] = [0, 0]
        self.dest: [float] = [0, 0]
        self.shift_pos: float = 0.0
        self.shift_dest: float = 0.0

    def set_zoom(self, resolution: float):
        self.resolution = self.resolution_goal = resolution
        self.pixels_per_meter = self.resolution * WORLD_BLOCK_SIZE
        self.resolution_index = 1

    def zoom(self, resolution: float, speed: float):
        if speed == 0:
            self.set_zoom(resolution)
        else:
            self.resolution_goal = resolution
            self.resolution_speed = 1 / speed
            self.resolution_index = 0

    def set(self, pos):
        """
        Set the camera position.
        Use move() for slow movement.
        """
        self.pos = list(pos)
        self.vel = [0, 0]
        self.dest = pos

    def move(self, pos: [float]):
        """
        Move the camera slowly to a position.
        Use set() for instant movement.
        """
        self.dest = pos

    def shift_x(self, x: [float]):
        """
        Move the camera slower than self.move() to a x offset.
        """
        self.shift_dest = x * 0.1

    def update(self):
        """
        Update the camera.
        """
        # Move slowly to goal
        self.pos[0] -= self.shift_pos
        xvel = round((self.dest[0] - self.pos[0]) * self.window.delta_time * self.speed, 3)
        yvel = round((self.dest[1] - self.pos[1]) * self.window.delta_time * self.speed, 3)
        #self.pos[0] += self.shift_pos * self.shift_impact

        #xvel = round((self.dest[0] - self.pos[0]) * 0.1, 3)
        #yvel = round((self.dest[1] - self.pos[1]) * 0.1, 3)

        xvel = math.copysign(max(abs(xvel) - self.threshold, 0), xvel)
        yvel = math.copysign(max(abs(yvel) - self.threshold, 0), yvel)

        self.vel[0] = xvel
        self.vel[1] = yvel
        self.pos[0] += self.vel[0] 
        self.pos[1] += self.vel[1]

        # Maximum goal offset
        x_distance = self.pos[0] - self.dest[0]
        y_distance = self.pos[1] - self.dest[1]
        x_deviation = self.window.width / 4 / self.pixels_per_meter
        y_deviation = self.window.height / 4 / self.pixels_per_meter

        if x_distance > x_deviation:
            self.pos[0] = self.dest[0] + x_deviation
        elif x_distance < -x_deviation:
            self.pos[0] = self.dest[0] - x_deviation

        if y_distance > y_deviation:
            self.pos[1] = self.dest[1] + y_deviation
        elif y_distance < -y_deviation:
            self.pos[1] = self.dest[1] - y_deviation

        # Update zoom
        if self.resolution_index < 1:
            self.resolution_index = self.resolution_index + self.resolution_speed * self.window.delta_time * 60
            factor = 1000 ** -((self.resolution_index - 1) ** 2) # f(x) = 1000^[-(x-1)^2]
            self.resolution = self.resolution_start * (1 - factor) + self.resolution_goal * factor
            self.pixels_per_meter = self.resolution * WORLD_BLOCK_SIZE

        self.shift_pos += (self.shift_dest - self.shift_pos) * self.window.delta_time * 0.5
        self.pos[0] += self.shift_pos

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
        simulation_distance = self.window.options["simulation distance"]
        center = (math.floor(self.pos[0]),
                  math.floor(self.pos[1]))
        start = (center[0] - math.floor(self.window.width / 2 / self.pixels_per_meter) - simulation_distance,
                 center[1] - math.floor(self.window.height / 2 / self.pixels_per_meter) - simulation_distance)
        end = (center[0] + math.ceil(self.window.width / 2 / self.pixels_per_meter) + simulation_distance,
               center[1] + math.ceil(self.window.height / 2 / self.pixels_per_meter) + simulation_distance)
        return start, end
