# -*- coding: utf-8 -*-
import pygame
import os


pygame.mixer.init()
pygame.mixer.set_num_channels(16)
load = pygame.mixer.Sound


def play(sound, x):
    channel = pygame.mixer.find_channel()
    channel.play(sound)
    channel.set_volume(abs(0.5 - x), abs(-0.5 - x))


"""
Usage:

sound = load(path) # .wav or .ogg
play(sound, x)     # -1.0 < x < 1.0
"""