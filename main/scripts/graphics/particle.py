# -*- coding: utf-8 -*-
from math import *
import random


def setup(window, image: str, time: float, delay: float, size: tuple=(1, 1), gravity: float=None, growth: float=0, speed: float=None, angle: float=None, divergence: float=None, amount: float=1.0):
    """
    Create a particle type.
    image: image name
    time: time to live
    delay: delay between spawned particles
    gravity: own gravity fractor
    growth: grow or shrink the particle over time (0 = neutral)
    speed: velocity
    angle: direction of velocity
    divergence: random spawn offset and changing angle
    amount: relative amount of spawned particles (negative values -> absolute amount)
    """
    window.particle_types[image] = ([delay], time, delay, gravity, growth, speed, angle, divergence, size, amount)


def spawn_possible(window, name):
    """
    Test if particle can be spawned.
    """
    return window.options["particles"] and window.particle_types[name][0][0] < window.time


def spawn(window, name, x: float, y: float, speed: float=None, angle: float=None, divergence: float=None):
    """
    Spawn a particle.
    """
    if not spawn_possible(window, name):
        return

    window.particle_types[name][0][0] = window.time + window.particle_types[name][2]

    if speed is None:
        speed = window.particle_types[name][5]
    if angle is None:
        angle = window.particle_types[name][6]
    if divergence is None:
        divergence = window.particle_types[name][7]

    amount = window.particle_types[name][9]
    if divergence == 0:
        absolute_amount = 1
    elif amount < 0:
        absolute_amount = -round(amount)
    else:
        absolute_amount = round(window.options["particles"] * amount)

    for _ in range(absolute_amount):
        if divergence:
            x += divergence * (random.random() - 0.5) / 4
            y += divergence * (random.random() - 0.5) / 4

        window.particles.append([name, x, y, window.time + window.particle_types[name][1], speed, angle + divergence * (random.random() - 0.5)])


def text(window, text: str, x: float, y: float, size: float=1.0, color: [float]=(0, 0, 0, 0), time: float=1.0, offset_radius: float=0):
    if offset_radius:
        angle = pi * random.random() # Only upper half of circle
        x += cos(angle) * offset_radius
        y += sin(angle) * offset_radius
    window.particles.append(["text", text, x, y, size, window.time + time, *color])


def explosion(window, x: float, y: float, size: float=1.0, time: float=1.0):
    window.particles.append(["explosion", x, y, size, window.time + time, time])


def update(window):
    for i, particle in enumerate(window.particles):
        if particle[0] == "text":
            update_text(window, i, particle)
        elif particle[0] == "explosion":
            update_explosion(window, i, particle)
        else:
            update_particle(window, i, particle)


def update_particle(window, i, particle):
    name, x, y, time, speed, angle = particle
    if window.time > time:
        window.particles.pop(i)
        return

    window.particles[i][1] += cos(angle) * speed * window.delta_time
    window.particles[i][2] += (sin(angle) * speed - window.particle_types[name][3]) * window.delta_time
    if window.particle_types[name][7]:
        window.particles[i][5] += (random.random() - 0.5 + window.particle_wind) * window.particle_types[name][7] / 200
    size_factor = 1 - (time - window.time) / window.particle_types[name][1] * window.particle_types[name][4]
    size = (window.particle_types[name][8][0] * size_factor, window.particle_types[name][8][1] * size_factor)

    rect = window.camera.map_coord((x - size[0] / 2, y - size[1] / 2, *size), from_world=True)
    window.draw_image(name, rect[:2], rect[2:])
    if -window.particle_types[name][3] + sin(angle) > -window.particle_types[name][3]:
        window.particles[i][4] *= 0.9

    if not (-1 < rect[0] < 2 and -1 < rect[1] < 2):
        window.particles.pop(i)


def update_text(window, i, particle):
    _, text, x, y, size, time, *color = particle
    if window.time > time:
        window.particles.pop(i)
        return

    pos = window.camera.map_coord((x, y), from_world=True)
    window.draw_text(pos, text, color, size, centered=True)

    if not (-1 < pos[0] < 2 and -1 < pos[1] < 2):
        window.particles.pop(i)


def update_explosion(window, i, particle):
    _, x, y, size, time, total_time = particle
    if window.time > time:
        window.particles.pop(i)
        return

    image = "explosion_" + chr(ord("a") + round(6 - (time - window.time) / total_time * 6))

    rect = window.camera.map_coord((x - size/2, y - size/2, size, size), from_world=True)
    window.draw_image(image, rect[:2], rect[2:])

    if not (-1 < rect[0] < 2 and -1 < rect[1] < 2):
        window.particles.pop(i)
    
