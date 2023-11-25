# -*- coding: utf-8 -*-
import opensimplex
import math


try:
    from noise import *
except ModuleNotFoundError:
    def pnoise1(x: float, octaves: int=1, persistence: float=0.5, lacunarity: float=2.0, repeat: float=0):
        z = 0
        octaves = min(octaves, 3)

        if repeat:
            x = abs(math.sin(x * math.pi / repeat + 2.928) * repeat)

        for i in range(octaves):
            divisor = 2 ** i
            z += opensimplex.noise2(x / divisor, math.e) / divisor

        return z

    def snoise2(x: float, y: float, octaves: int=1, persistence: float=0.5, lacunarity: float=2.0, repeatx: float=0, repeaty: float=0):
        z = 0
        octaves = min(octaves, 3)

        if repeatx:
            x = abs(math.sin(x * math.pi / repeatx + 0.214) * repeatx)
        if repeaty:
            y = abs(math.sin(y * math.pi / repeaty + 1.331) * repeaty)

        for i in range(octaves):
            divisor = 2 ** i
            z += opensimplex.noise2(x / divisor, y / divisor) / divisor

        return z
