# -*- coding: utf-8 -*-
from scripts.utility import file


default: dict = {
    "enable vsync": True,
    "max fps": 1000,
    "text resolution": 20,
    "shadow resolution": 0,
    "particles": 10,
    "antialiasing": 0,
    "reduce camera movement": False,
    "show fps": False,
    "show debug": False,
    "language": "english",
    "master volume": 1.0,
    "player volume": 1.0,
    "enemy volume": 1.0,
    "ambient volume": 1.0,
    "menu volume": 1.0,
    "simulation distance": 5,
    "save world": True,
    "auto jump": False,
    "test.draw_hitboxes": False,
    "test.draw_pathfinding": False,
    "test.player_leap": False,
    "test.edit_blocks": False,
    "test.place_water": False,
    "test.scroll_zoom": False,
    "test.edit_holding_enabled": False,
    "test.edit_holding_entity": "player",
    "test.edit_holding_state": "idle",
    "key.left": "a",
    "key.right": "d",
    "key.jump": "space",
    "key.sprint": "left shift",
    "key.crouch": "c",
    "key.return": "escape",
    "key.inventory": "e"
}


def load():
    """
    Loads the options from the options.txt file.
    """
    options = default.copy()
    user_options = file.load("data/user/options.json", default=default, file_format="json")

    for keyword, value in user_options.items():
        if not keyword in default:
            raise ValueError(f"Invalid option \"{keyword}\"")
        if ((isinstance(options[keyword], (int, bool)) and not isinstance(value, (int, bool))) or
            (isinstance(options[keyword], float) and not isinstance(value, (float, int, bool))) or
            (isinstance(options[keyword], str) and not isinstance(value, str))):
            raise ValueError("Invalid value type (\"" + str(value) + "\") for " + keyword)
        options[keyword] = value
                
    return options


def save(options):
    """
    Save the options in the options.txt file.
    """
    file.save("data/user/options.json", options, file_format="json")
