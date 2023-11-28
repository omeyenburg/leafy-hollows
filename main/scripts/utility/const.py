# -*- coding: utf-8 -*-
import platform
import random
import numpy
import math
import os


OPENGL_VERSION: str = "3.3 core"
PLATFORM: str = platform.system()
CREATE_TEXTURE_ATLAS_FILE: bool = True

MENU_SPACING: float = 0.05 # Spacing between buttons, etc.
MENU_BUTTON_SMALL_WIDTH: float = 0.65 # Width of short buttons
MENU_BUTTON_WIDTH: float = 2 * MENU_BUTTON_SMALL_WIDTH + MENU_SPACING # Width of normal buttons
MENU_BUTTON_HEIGHT: float = 0.16 # Heigth of buttons and sliders
MENU_BUTTON_SMALL_SIZE: [float] = (MENU_BUTTON_SMALL_WIDTH, MENU_BUTTON_HEIGHT)
MENU_BUTTON_SIZE: [float] = (MENU_BUTTON_WIDTH, MENU_BUTTON_HEIGHT)
MENU_SLIDER_WIDTH: float = 0.03125
MENU_HEADING_SIZE: [float] = (MENU_BUTTON_SMALL_WIDTH, 0.3)
MENU_TITLE_SIZE: [float] = (MENU_BUTTON_SMALL_WIDTH, 0.5)
MENU_SCROLL_BOX_HEIGHT: float = 0.91
MENU_DESCRIPTION_HOVER_TIME: float = 0.3 # Hover time until description is visible
MENU_DESCRIPTION_BOX_HEIGHT: float = 0.9
MENU_DESCRIPTION_BOX_Y: float = 0.05
MENU_OFFSET_HOVER: float = MENU_BUTTON_HEIGHT / 16
MENU_TEXT_POSITION_TOP: float = 0.9
MENU_TEXT_POSITION_BOTTOM: float = -1

FONT_CHARACTERS: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789äÄüÜöÖß_.,:;?!<=>#@%\'\"+-*/()[]"
FONT_CHARACTERS_INDEX: dict = {char: FONT_CHARACTERS.find(char) for char in FONT_CHARACTERS}
FONT_CHARACTERS_LENGTH: int = len(FONT_CHARACTERS)

TEXT_SIZE_HEADING: float = 0.4
TEXT_SIZE_BUTTON: float = 0.17
TEXT_SIZE_OPTION: float = 0.14
TEXT_SIZE_TEXT: float = 0.15
TEXT_SIZE_DESCRIPTION: float = 0.13

CAMERA_RESOLUTION_INTRO: float = 1.0
CAMERA_RESOLUTION_GAME: float = 3.0

INTRO_REPEAT: int = 64
INTRO_LENGTH: int = INTRO_REPEAT * 24

PLAYER_RECT_SIZE_NORMAL: [float] = (0.9, 1.8)
PLAYER_RECT_SIZE_CROUCH: [float] = (1.8, 1)
PLAYER_RECT_SIZE_SWIM: [float] = (0.9, 0.9)

ARROW_RECT_SIZE: [float] = (0.2, 0.2)
SLIME_RECT_SIZE: [float] = (0.7, 0.7)
GOBLIN_RECT_SIZE: [float] = (0.9, 1.8)
BAT_RECT_SIZE: [float] = (0.7, 0.7)

PHYSICS_REALISTIC: bool = False
PHYSICS_PREVENT_MOVEMENT_IN_AIR: bool = False
PHYSICS_GRAVITY_CONSTANT: float = 9.81 if PHYSICS_REALISTIC else 15
PHYSICS_GRAVITY_CONSTANT_WATER: float = PHYSICS_GRAVITY_CONSTANT
PHYSICS_FRICTION_X: float = 0.1
PHYSICS_JUMP_THRESHOLD: int = 3 # Time to jump after leaving the ground in ticks
PHYSICS_WALL_JUMP_THRESHOLD: float = 0.3 # Time to jump after leaving a wall in seconds
PHYSICS_MAX_MOVE_DISTANCE: float = 1.0 # Maximum distance in blocks, which an object can travel each tick

BLOCKS_CLIMBABLE: tuple = ("pole", "vines0", "vines0_flipped")

WORLD_CHUNK_SIZE_POWER = 5
WORLD_CHUNK_SIZE = 2 ** WORLD_CHUNK_SIZE_POWER
WORLD_WATER_PER_BLOCK: int = 1000
WORLD_WATER_SPEED: float = 0.1 # Water update interval
WORLD_WIND_STRENGTH: int = 20
WORLD_BLOCK_SIZE: int = 16

WORLD_VEGETATION_FLOOR_DENSITY: float = 1.0
WORLD_VEGETATION_CEILING_DENSITY: float = 0.4
WORLD_VEGETATION_WALL_DENSITY: float = 0.05

WORLD_GENERATION_CAVE_BORDER_PADDING: int = 4
WORLD_GENERATION_HORIZONTAL_CAVE_RADIUS: int = 3
WORLD_GENERATION_STEP_SIZE: float = 0.5
WORLD_GENERATION_INTERPOLATION_LENGTH: int = 20

INT_TO_ROMAN: dict = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV", 16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX"}

ATTRIBUTES: [str] = (
    "piercing",
    "ferocity",
    "vampire",
    "looting",
    "explosive",
    "paralysis",
    "berserker",
    "agility",
    "soul drain",
    "shielding",
    "critical",
    "warrior",
    "assassin",
    "longshot"
)

ATTRIBUTE_BASE_MODIFIERS: dict = {
    "piercing": 1,
    "ferocity": 15,
    "vampire": 5,
    "looting": 1,
    "explosive": 20,
    "paralysis": 15,
    "berserker": 25,
    "agility": 15,
    "soul drain": 20,
    "shielding": 10,
    "critical": 30,
    "warrior": 5,
    "assassin": 20,
    "longshot": 10
}

ATTRIBUTE_DESCRIPTIONS: dict = {
    "piercing": "Allows your weapon to cut through enemies, hitting %s additional targets in its path.",
    "ferocity": "Enhances the weapon's aggressiveness, increasing damage and attack speed by %s%% each.",
    "vampire": "Regenerate %s%% health with every successful hit, siphoning life from enemies.",
    "looting": "Increases the possible level of an attribute on dropped weapons by %s.",
    "explosive": "Attacks detonate on impact, dealing %s%% of your weapon's damage to the target and nearby enemies.",
    "paralysis": "Strikes have a %s%% chance to temporarily stun enemies.",
    "berserker": "Increases damage by %s%%, but at the cost of a corresponding reduction in defense.",
    "agility": "Increases your movement and attack speed by %s%% each, allowing for quicker strikes.",
    "soul drain": "Absorb your enemies' souls, regenerating %s%% health with each successfull kill.",
    "shielding": "Reduces damage taken by %s%%.",
    "critical": "Increases the chance for a critical hit by %s%%.",
    "warrior": "Increases your weapon's damage by %s%% per enemy around you.",
    "assassin": "Increases your attack speed and crit chance by %s%% each.",
    "longshot": "Expands your weapon's range by by %s%%, allowing you to hit enemies from a greater distance."
}

ATTRIBUTE_BESCHREIBUNGEN: dict = {
    
}

{
    "piercing": "Durchschlag",
    "ferocity": "Wildheit",
    "vampire": "Vampier",
    "looting": "Pl<ue>nderer",
    "explosive": "Explosiv",
    "paralysis": "L<ae>hmung",
    "berserker": "Berserker",
    "agility": "Beweglichkeit",
    "soul drain": "Seelenraub",
    "shielding": "Schutz",
    "critical": "Kritisch",
    "warrior": "Krieger",
    "assassin": "Attent<ae>ter",
    "longshot": "Fernschuss"
}