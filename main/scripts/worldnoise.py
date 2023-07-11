import noise
import random


def seed():
    return random.randint(-9999999, 9999999) + random.random()


def terrain(x: int, y: int, seed: float):
    return noise.snoise2(x / 30 + seed + 0.1, y / 30 + seed + 0.1, octaves=3, persistence=0.1, lacunarity=3)


