# -*- coding: utf-8 -*-
import scripts.utility.file as file
import pygame
import random
import os


def load():
    """
    Load all sounds from a .wav or .ogg files.
    All sounds have to be in monophonic sounds.
    """
    pygame.mixer.init(channels=16)
    sound_paths = file.find("data/sounds", "*.json", True)
    sound_files = {file.basename(path): path for path in file.find("data/sounds", "*.wav", True) + file.find("data/sounds", "*.wav", True)}

    loaded_sounds = {}
    played_sounds = {}

    for path in sound_paths:
        data = file.read(path, file_format="json")
        name = data["name"]
        speed = data["speed"]
        volume = data["volume"]
        files = tuple([pygame.mixer.Sound(sound_files[sound_file]) for sound_file in data["sounds"]])
        loaded_sounds[name] = (speed, volume, files)

    return loaded_sounds, played_sounds


def play(window, sound: str, x: float=0.0, identifier: str=None, channel_volume: float=1.0):
    """
    Play a sound at a location.
    identifier: A unique delay is stored for each identifier.
    """
    loaded_sounds = window.loaded_sounds
    played_sounds = window.played_sounds

    delay, volume, files = loaded_sounds[sound]

    if delay != 0.0:
        if identifier is None:
            key = sound
        else:
            key = sound + identifier
        if key in played_sounds and played_sounds[key] > window.time:
            return # sound blocked
        played_sounds[key] = window.time + delay

    if len(files) > 1:
        index = random.randint(0, len(files) - 1)
    else:
        index = 0

    if x < 0.5:
        volume = 2 ** (-(x + 0.5) ** 2) * volume * channel_volume
        side = (1, 0)
    elif x > 0.5:
        volume = 2 ** (-(x - 0.5) ** 2) * volume * channel_volume
        side = (0, 1)
    else:
        volume = volume * channel_volume
        side = (0.5, 0.5)

    files[index].set_volume(volume * window.options["volume"])
    channel = pygame.mixer.find_channel()
    channel.play(files[index], fade_ms=100)
    channel.set_volume(*side)
    