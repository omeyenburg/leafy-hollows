# -*- coding: utf-8 -*-
import random
import math


def setup(window, image: str, time: float, delay: float, size: tuple=(1, 1), gravity: float=None, growth: float=0, speed: float=None, angle: float=None, divergence: float=None):
    """
    Create a particle type.
    image: image name
    time: time to live
    delay: delay between spawned particles
    gravity: own gravity
    growth: grow or shrink the particle over time (0 = neutral)
    """
    window.particle_types[image] = ([delay], image, time, delay, gravity, growth, speed, angle, divergence, size)


def spawn(window, name, x: float, y: float, speed: float=None, angle: float=None, divergence: float=None, amount: float=1.0):
    """
    Spawn a particle.
    """
    particle_multiplier = window.options["particles"]
    if (not particle_multiplier) or window.particle_types[name][0][0] > window.time:
        return

    window.particle_types[name][0][0] = window.time + window.particle_types[name][3]

    if speed is None:
        speed = window.particle_types[name][6]
    if angle is None:
        angle = window.particle_types[name][7]
    if divergence is None:
        divergence = window.particle_types[name][8]

    for _ in range(int(particle_multiplier * amount)):
        if divergence:
            x += divergence * (random.random() - 0.5) / 4
            y += divergence * (random.random() - 0.5) / 4

        window.particles.append([name, x, y, window.time + window.particle_types[name][2], speed, angle + divergence * (random.random() - 0.5)])

        if not divergence:
            return


def text(window, text: str, x: float, y: float, size: float=1.0, color: [float]=(0, 0, 0, 0), time: float=1.0, offset_radius: float=0):
    if offset_radius:
        angle = math.pi * random.random() # Only upper half of circle
        x += math.cos(angle) * offset_radius
        y += math.sin(angle) * offset_radius
    window.particles.append(["text", text, x, y, size, window.time + time, *color])


def update(window):
    for i, particle in enumerate(window.particles):
        if particle[0] != "text":
            update_particle(window, i, particle)
        else:
            update_text(window, i, particle)


def update_particle(window, i, particle):
    name, x, y, time, speed, angle = particle
    if window.time > time:
        window.particles.pop(i)
        return

    window.particles[i][1] += math.cos(angle) * speed * window.delta_time
    window.particles[i][2] += (math.sin(angle) * speed - window.particle_types[name][4]) * window.delta_time
    if window.particle_types[name][8]:
        window.particles[i][5] += random.random() * window.particle_types[name][8] / 200
    size = 1 - (time - window.time) / window.particle_types[name][2] * window.particle_types[name][5]

    rect = window.camera.map_coord((x, y, window.particle_types[name][9][0] * size, window.particle_types[name][9][1] * size), from_world=True)
    window.draw_image(name, rect[:2], rect[2:])
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