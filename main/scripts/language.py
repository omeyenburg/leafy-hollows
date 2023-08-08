# -*- coding: utf-8 -*-


translate_german = {
    "True": "An",
    "False": "Aus",
    "high": "hoch",
    "medium": "mittel",
    "low": "gering",
    "none": "keiner",
    "Disabled": "Deaktiviert",
    "Left": "Links",
    "Right": "Rechts",
    "Up": "Open",
    "Down": "Unten",
    "Reset": "Zuruecksetzen",
    "Play": "Spielen",
    "Settings": "Optionen",
    "Quit": "Schliessen",
    "Video Settings": "Videooptionen",
    "Audio Settings": "Audiooptionen",
    "Control Settings": "Steuerungsoptionen",
    "World Settings": "Weltoptionen",
    "Back": "Zurueck",
    "Resolution": "Aufloesung",
    "Show Fps": "Zeige Fps",
    "Show debug": "Zeige Debug",
    "Post process": "Nachbearbeitung",
    "Particle Density": "Partikeldichte",
    "Performance impact": "Leistungseinfluss",
    "Jump": "Springen",
    "Sprint": "Sprinten",
    "Return": "Zurueckgehen",
    "Scroll to see more options and hover over options to see descriptions": "Scrolle, um weitere Optionen zu sehen",
    "Click a button and press a key to bind a new key to an action": "Klicke einen Knopf und eine Taste, um sie an die Aktion zu binden",
    "Limit the Fps at a cap.\nVsync: Fps limit is synchronized with your screen's refresh rate.": "Begrenze die maximalen Fps.\nVsync: Das Limit ist synchronisiert mit deinem Bildschirm.",
    "Set the resolution of in-game objects.": "Setze die Aufloesung von Objekten im Spiel fest.",
    "Limit the amount of particles, which can be spawned at once.": "Begrenze die Menge an Partikeln, die gleichzeitig erstellt werden koennen.",
    "When enabled, post processing is performed after the actual rendering for additional visual effects.": "Wenn aktiv, wird das Bild mit visuellen Effekten nachbearbeitet.",
    "Select either English or German as the language.": "Waehle entweder Englisch oder Deutsch, als die verwendete Sprache.",
    "Set the level of antialiasing.\nAntialiasing creates smoother edges of shapes.": "Lege den Grad der Antialiasing fest.\nAntialiasing erzeugt glattere Kanten von Formen.",
}


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