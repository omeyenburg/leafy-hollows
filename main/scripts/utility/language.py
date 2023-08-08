# -*- coding: utf-8 -*-
import json
import scripts.utility.file as file


translate_german = file.read_json("data/translations/german.json")


"""
from deep_translator import GoogleTranslator
class OnlineTranslator(GoogleTranslator):
    def __init__(self, language):
        super().__init__(source='english', target=language)

    def translate(self, text):
        return super().translate(text=text)
"""


class Translator:
    def __init__(self, language):
        self.language = language.lower()

    def translate(self, text):
        if self.language == "english":
            return text
        elif self.language == "deutsch":
            wrap = text.endswith("\n")
            if wrap:
                text = text[:-1]
            if text in translate_german:
                text = translate_german[text]
                if wrap:
                    text += "\n"
                return text
            text = list(text.split(": "))
            for i, part in enumerate(text):
                if part in translate_german:
                    text[i] = translate_german[part]
            text = ": ".join(text)
            if wrap:
                text += "\n"
            return text
        raise Exception("Unknown language " + self.language)