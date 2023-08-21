# -*- coding: utf-8 -*-
import json
import scripts.utility.file as file


translate_german = file.read_json("data/translations/german.json")


class Translator:
    def __init__(self, language):
        self.language = language.lower()

    def translate(self, text):
        if ": " in text:
            return ": ".join([self.translate(text) for text in text.split(": ")])

        if self.language == "english":
            return text

        elif self.language == "deutsch":
            spaces_left = len(text) - len(text.lstrip(" "))
            spaces_right = len(text) - len(text.rstrip(" "))
            text = text.strip(" ")

            if text.endswith("\n"):
                text = text[:-1]
                wrap = "\n"
            else:
                wrap = ""

            if text in translate_german:
                text = translate_german[text]

            return " " * spaces_left + text + " " * spaces_right + wrap

        raise Exception("Unknown language " + self.language)