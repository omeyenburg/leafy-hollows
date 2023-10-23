# -*- coding: utf-8 -*-
import random
import math


def setup(world, image: str, time: float, delay: float, size: tuple=(1, 1), gravity: float=None, growth: float=0, speed: float=None, direction: float=None, divergence: float=None):
    """
    Create a particle type.
    image: image name
    time: time to live
    delay: delay between spawned particles
    gravity: own gravity
    growth: grow or shrink the particle over time (0 = neutral)
    """
    world.particle_types[image] = ([delay], image, time, delay, gravity, growth, speed, direction, divergence, size)


def spawn(window, world, name, x: float, y: float, speed: float=None, direction: float=None, divergence: float=None):
    """
    Spawn a particle.
    """
    particle_multiplier = window.options["particles"]
    if (not particle_multiplier) or world.particle_types[name][0][0] > window.time:
        return

    world.particle_types[name][0][0] = window.time + world.particle_types[name][3]

    if speed is None:
        speed = world.particle_types[name][6]
    if direction is None:
        direction = world.particle_types[name][7]
    if divergence is None:
        divergence = world.particle_types[name][8]

    for _ in range(particle_multiplier):
        if divergence:
            x += divergence * random.random() / 4
            y += divergence * random.random() / 4
            divergence *= random.random()

        world.particles.append([name, x, y, window.time + world.particle_types[name][2], speed, direction + divergence])

        if not divergence:
            return


def update(window, world):
    for i, particle in enumerate(world.particles):
        name, x, y, time, speed, direction = particle
        if window.time > time:
            world.particles.pop(i)
            continue

        world.particles[i][1] += math.cos(direction) * speed * window.delta_time
        world.particles[i][2] += (math.sin(direction) * speed - world.particle_types[name][4]) * window.delta_time
        if world.particle_types[name][8]:
            world.particles[i][5] += random.random() * world.particle_types[name][8] / 200
        size = 1 - (time - window.time) / world.particle_types[name][2] * world.particle_types[name][5]

        rect = window.camera.map_coord((x, y, world.particle_types[name][9][0] * size, world.particle_types[name][9][1] * size), from_world=True)
        window.draw_image(name, rect[:2], rect[2:])

        if not (-1 < rect[0] < 2 and -1 < rect[1] < 2):
            world.particles.pop(i)
