# -*- coding: utf-8 -*-
from scripts.utility import file


translate_german = file.read("data/translations/german.json", file_format="json")


def translate(language, text):
    if ": " in text: # Recursive translation
        return ": ".join([translate(language, text) for text in text.split(": ")])
    if language == "english": # No translation
        return text
    if language == "deutsch": # German translation
        # Format text
        spaces_left = len(text) - len(text.lstrip(" "))
        spaces_right = len(text) - len(text.rstrip(" "))
        text = text.strip(" ")
        if text.endswith("\n"):
            text = text[:-1]
            wrap = "\n"
        else:
            wrap = ""

        # Translate text
        if text in translate_german:
            text = translate_german[text]

        return " " * spaces_left + text + " " * spaces_right + wrap

    raise Exception("Unknown language " + language)
