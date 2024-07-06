# -*- coding: utf-8 -*-
__version__ = "1.0.0"
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
import kivy

kivy.require("1.9.0")

class MyRoot(BoxLayout):
    def __init__(self):
        super(MyRoot, self).__init__()

    def calc_symbol(self, symbol):
        self.children[1].text += symbol

class CalculatorClass(App):
    def build(self):
        return MyRoot()


CalculatorClass().run()