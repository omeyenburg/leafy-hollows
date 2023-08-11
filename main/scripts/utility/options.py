# -*- coding: utf-8 -*-
import scripts.utility.file as file
import os


default: dict = {
    "enableVsync": True,
    "maxFps": 1000,
    "particles": 1,
    "map buffers": False, # remove
    "antialiasing": 16,
    "resolution": 2,
    "post processing": True,
    "show fps": False,
    "show debug": False,
    "language": "deutsch",
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
    user_options = file.read_json("data/user/options.json")

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
    file.write_json("data/user/options.json", options)