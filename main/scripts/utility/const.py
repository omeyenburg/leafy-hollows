# -*- coding: utf-8 -*-
import platform


OPENGL_VERSION: str = "3.3 core"
PLATFORM: str = platform.system()
INTRO_REPEAT: int = 64
INTRO_LENGTH: int = INTRO_REPEAT * 24
PLAYER_SIZE: [int] = (0.9, 1.8)
PHYSICS_REALISTIC: bool = False
PHYSICS_GRAVITY_CONSTANT: float = 9.81 if PHYSICS_REALISTIC else 15
PHYSICS_GRAVITY_CONSTANT_WATER: float = PHYSICS_GRAVITY_CONSTANT
PHYSICS_FRICTION_X: float = 0.1
PHYSICS_JUMP_THRESHOLD: int = 3 # Time to jump after leaving the ground in ticks
PHYSICS_WALL_JUMP_THRESHOLD: float = 0.3 # Time to jump after leaving a wall in seconds
PHYSICS_MAX_MOVE_DISTANCE: float = 1.0 # Maximum distance in blocks, which an object can travel each tick
WORLD_WATER_PER_BLOCK: int = 1000
WORLD_WATER_SPEED: float = 0.1 # Water update delay
WORLD_WIND_STRENGTH: int = 20
WORLD_BLOCK_SIZE: int = 16
FONT_CHARACTERS: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789äÄüÜöÖß_.,:;?!<=>#@%\'\"+-*/()[]"
FONT_CHARACTERS_INDEX: dict = {char: FONT_CHARACTERS.find(char) for char in FONT_CHARACTERS}
FONT_CHARACTERS_LENGTH: int = len(FONT_CHARACTERS)
TEXT_SIZE_HEADING: float = 0.4
TEXT_SIZE_BUTTON: float = 0.2
TEXT_SIZE_OPTION: float = 0.14
TEXT_SIZE_TEXT: float = 0.15
TEXT_SIZE_DESCRIPTION: float = 0.14
CAMERA_RESOLUTION_INTRO: float = 1.0
CAMERA_RESOLUTION_GAME: float = 3.0
BLOCKS_GRASS: tuple = ("flat_grass", "small_grass", "medium_grass", "tall_grass", "bush0", "bush1", "plant0", "wood0")
BLOCKS_MUSHROOM: tuple = ("mushroom0", "mushroom1", "mushroom2", "mushroom3", "mushroom4", "mushroom5", "mushroom6")