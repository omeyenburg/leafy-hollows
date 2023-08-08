# -*- coding: utf-8 -*-
import random
import noise
import math


def seed():
    return random.randint(-9999999, 9999999) + random.random() + 0.1


def terrain(x: int, y: int, seed: float):
    x = noise.snoise2(x / 30 + seed, y / 30 + seed, octaves=3, persistence=0.1, lacunarity=3)
    #dist = max(0, 1 - abs(y) / 1)
    return x# * (1 - dist)

def wind(x: int, y: int, wind):
    return (math.sin(x) + math.cos(y)) / 4 + 0.75 * min(30, max(-30, wind)) + random.random() * 2



#def biome(x: int, y: int, seed: float):
#    return noise.snoise2(x / 200 + seed * 2, y / 200 - seed, octaves=3, persistence=0.1, lacunarity=3)

