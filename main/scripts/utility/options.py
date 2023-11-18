# -*- coding: utf-8 -*-
from scripts.utility import file


default: dict = {
    "enable vsync": True,
    "max fps": 1000,
    "text resolution": 40,
    "shadow resolution": 0,
    "particles": 1,
    "antialiasing": 16,
    "show fps": False,
    "show debug": False,
    "language": "english",
    "master volume": 1.0,
    "player volume": 1.0,
    "ambient volume": 1.0,
    "simulation distance": 5,
    "key.left": "a",
    "key.right": "d",
    "key.jump": "space",
    "key.sprint": "left shift",
    "key.crouch": "c",
    "key.return": "escape"
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
