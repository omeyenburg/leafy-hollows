# -*- coding: utf-8 -*-
from scripts.game.world_noise import pnoise1, snoise2
from scripts.utility.const import *
import random
import numpy
import math


def generate_points_segment(position: [float], length, start_angle: float, deviation: float):
    angle = start_angle
    points = set()

    angle_change = 0
    max_angle_change = 0.5

    for i in range(length):
        position[0] = position[0] + math.cos(angle) * WORLD_GENERATION_STEP_SIZE
        position[1] = position[1] + math.sin(angle) * WORLD_GENERATION_STEP_SIZE
        points.add(tuple(position))
        angle_change = snoise2(i * 20.215 + 0.0142, 1, octaves=3) * max_angle_change
        angle_change -= (angle - start_angle) / deviation * max_angle_change
        angle += angle_change

    return points


def line_cave(world, position, length, angle, deviation, radius):
    points = generate_points_segment(position, length, angle, deviation)

    for (x, y) in points:
        p_radius = int(pnoise1((x + y) / 2 + 100, octaves=3) * 2 + radius)
        for delta_x in range(-p_radius - WORLD_GENERATION_CAVE_BORDER_PADDING, p_radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
            for delta_y in range(-p_radius - WORLD_GENERATION_CAVE_BORDER_PADDING, p_radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
                coord = (int(x + delta_x), int(y + delta_y))
                if delta_x ** 2 + delta_y ** 2 <= p_radius ** 2:
                    world.set_block(*coord, 0)
                elif not world.get_block_exists(*coord):
                    world.set_block(*coord, world.block_name["dirt_block"])


# Called from generate_world
def intro(world, window, position):
    surface_size = (80, 50)
    for x in range(-surface_size[0], surface_size[0] + 1):
        surface_level = pnoise1(x / 20 + world.seed, octaves=3) * 9
        for y in range(-surface_size[0], surface_size[0] + 1):
            if surface_level < y:
                world.set_block(x, y, 0)
            
    window.loading_progress[1] = 2

    points = set()
    start_angle = angle = -math.pi/2
    length = INTRO_LENGTH
    deviation = 5
    lowest = 0

    for i in range(length):
        position[0] = pnoise1(i * 16 + world.seed, octaves=2, repeat=INTRO_REPEAT * 16) * deviation
        position[1] = -i
        points.add(tuple(position))

    window.loading_progress[1] = 3

    for (x, y) in points:
        radius = int((pnoise1(y + world.seed, octaves=3, repeat=INTRO_REPEAT) + 2) * 2)
        for delta_x in range(-radius - WORLD_GENERATION_CAVE_BORDER_PADDING, radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
            for delta_y in range(-radius - WORLD_GENERATION_CAVE_BORDER_PADDING, radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
                coord = (int(x + delta_x), int(y + delta_y))
                if delta_x ** 2 + (delta_y * 0.5) ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                    if y + delta_y < lowest:
                        lowest = y + delta_y
                elif not world.get_block_exists(*coord):
                    world.set_block(*coord, world.block_name["dirt_block"])
    position[1] = lowest
    

def horizontal(world, position):
    angle = snoise2(position[0] / 100 + world.seed, world.seed, octaves=4) * 0.6
    length = random.randint(50, 150)
    deviation = random.randint(2, 5)
    radius = 3

    line_cave(world, position, length, angle, deviation, WORLD_GENERATION_HORIZONTAL_CAVE_RADIUS)


def interpolated(world, position, start_angle=None, end_angle=None, start_radius=None, end_radius=None):
    if start_angle is None:
        start_angle = snoise2(position[0] / 100 + world.seed, world.seed, octaves=4) * 0.6
    if end_angle is None:
        end_angle = snoise2((position[0] + WORLD_GENERATION_INTERPOLATION_LENGTH * WORLD_GENERATION_STEP_SIZE) / 100 + world.seed, world.seed, octaves=4) * 0.6
    if start_radius is None:
        start_radius = int(pnoise1(sum(position) / 2 + 100, octaves=3) * 2 + WORLD_GENERATION_HORIZONTAL_CAVE_RADIUS)
    if end_radius is None:
        end_radius = int(pnoise1((sum(position) + WORLD_GENERATION_INTERPOLATION_LENGTH * WORLD_GENERATION_STEP_SIZE) / 2 + 100, octaves=3) * 2 + WORLD_GENERATION_HORIZONTAL_CAVE_RADIUS)


    for i in range(WORLD_GENERATION_INTERPOLATION_LENGTH):
        interpolation = i / WORLD_GENERATION_INTERPOLATION_LENGTH
        angle = start_angle * (1 - interpolation) + end_angle * interpolation
        radius = round(start_radius * (1 - interpolation) + end_radius * interpolation)

        x = position[0] = position[0] + math.cos(angle) * WORLD_GENERATION_STEP_SIZE
        y = position[1] = position[1] + math.sin(angle) * WORLD_GENERATION_STEP_SIZE

        for delta_x in range(-radius - WORLD_GENERATION_CAVE_BORDER_PADDING, radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
            for delta_y in range(-radius - WORLD_GENERATION_CAVE_BORDER_PADDING, radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
                coord = (int(x + delta_x), int(y + delta_y))
                if delta_x ** 2 + delta_y ** 2 <= radius ** 2:
                    world.set_block(*coord, 0)
                elif not world.get_block_exists(*coord):
                    world.set_block(*coord, world.block_name["dirt_block"])


def vertical(world, position):
    angle = math.pi / 2 * 3 * (random.randint(0, 1) * 2 - 1)
    length = random.randint(40, 50)
    deviation = 0.5
    radius = 1

    line_cave(world, position, length, angle, deviation, radius)


def blob(world, position):
    radius = int((pnoise1(position[0] + world.seed, octaves=3) + 3) * 3)
    for delta_x in range(-radius - WORLD_GENERATION_CAVE_BORDER_PADDING, radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
        for delta_y in range(-radius - WORLD_GENERATION_CAVE_BORDER_PADDING, radius + WORLD_GENERATION_CAVE_BORDER_PADDING + 1):
            coord = (int(position[0] + delta_x), int(position[1] + delta_y))
            if delta_y > 0 and delta_x ** 2 + (delta_y * 0.8) ** 2 <= radius ** 2:
                world.set_block(*coord, 0)
            elif delta_x ** 2 + (delta_y * 2) ** 2 <= radius ** 2:
                world.set_block(*coord, 0)
