# -*- coding: utf-8 -*-
from deep_translator import GoogleTranslator


class OnlineTranslator(GoogleTranslator):
    def __init__(self, language):
        super().__init__(source='english', target=language)

    def translate(self, text):
        return super().translate(text=text)


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
    "Limit the Fps at a cap.": "Begrenze die maximalen Fps.",
    "Vsync: Fps limit is": "Vsync: Das Limit ist",
    "synchronized with your": "synchronisiert mit",
    "screen's refresh rate.": "deinem Bildschirm.",
    "Set the resolution": "Setze die Aufloesung von",
    "of in-game objects.": "Objekten im Spiel fest.",
    "Limit the amount of": "Begrenze die Menge an",
    "particles, which can be": "Partikeln, die gleichzeitig",
    "spawned at once.": "erstellt werden koennen.",
    "When enabled, post": "Wenn aktiv, wird",
    "processing is performed": "das Bild mit visuellen",
    "after the actual rendering": "Effekten nachbearbeitet.",
    "for additional visual effects.": "",
    "Set the level of antialiasing.": "Lege den Grad der",
    "Antialiasing creates": "Antialiasing fest.",
    "smoother edges of": "Antialiasing erzeugt glattere",
    "shapes.": "Kanten von Formen.",
}


class Translator:
    def __init__(self, language):
        self.language = language.lower()

    def translate(self, text):
        if self.language == "english":
            return text
        elif self.language == "deutsch":
            if text in translate_german:
                return translate_german[text]
            text = list(text.split(": "))
            for i, part in enumerate(text):
                if part in translate_german:
                    text[i] = translate_german[part]
            text = ": ".join(text)
            return text
        raise Exception("Unknown language " + self.language)