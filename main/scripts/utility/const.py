# -*- coding: utf-8 -*-
import platform


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

PHYSICS_REALISTIC: bool = False
PHYSICS_PREVENT_MOVEMENT_IN_AIR: bool = False
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
WORLD_VEGETATION_FLOOR_DENSITY: float = 1.0
WORLD_VEGETATION_CEILING_DENSITY: float = 0.4
WORLD_VEGETATION_WALL_DENSITY: float = 0.05

BLOCKS_CLIMBABLE: tuple = ("pole", "vines0", "vines0_flipped")
