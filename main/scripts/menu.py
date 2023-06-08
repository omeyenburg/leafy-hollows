import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import scripts.graphics as graphics
import scripts.util as util


def init(main_window):
    global window, font

    window = main_window
    font = graphics.Font(util.File.path("data/fonts/font.png"))


def update(): # Executed from main
    if not Page.opened is None:
        Page.opened.update()


class Page:
    opened = None
    
    def __init__(self, columns=1, spacing=0):
        self.children = []
        self.rect = pygame.Rect(0, 0, *window.size)
        self.columns = columns
        self.spacing = spacing

    def layout(self): # Position all widgets in a grid on a page
        width = [0 for _ in range(self.columns)]
        height = []

        for i, child in enumerate(self.children):
            width[child.column] = max(width[child.column], child.rect.w // child.columnspan - self.spacing * (child.columnspan - 1))
            if len(height) > child.row:
                height[child.row] = max(height[child.row], child.rect.h)
            else:
                height.append(child.rect.h)

        total_width = sum(width) - self.spacing * (self.columns - 1)
        total_height = sum(height) - self.spacing * (len(height) - 1)

        for i, child in enumerate(self.children):
            child.rect.centerx = sum(width[:child.column + 1]) - self.spacing * (self.columns - 1 - child.column - (child.columnspan - 1) / 2) - total_width//2 + width[child.column] * (child.columnspan - 1) / 2
            child.rect.centery = sum(height[:child.row + 1]) - self.spacing * (len(height) - 1 - child.row) - total_height//2

    def update(self):
        self.draw()
        for child in self.children:
            child.update()

    def draw(self):
        pass

    def coords(self):
        return pygame.Rect(self.rect.x + (window.size[0] - self.rect.w) // 2, self.rect.y + (window.size[1] - self.rect.h) // 2, self.rect.w, self.rect.h)

    def open(self):
        Page.opened = self


class Widget:
    def __init__(self, parent, size, row=0, column=0, columnspan=1):
        self.parent = parent
        self.children = []
        self.rect = pygame.Rect(0, 0, *size)
        self.parent.children.append(self)
        self.row = row
        self.column = column
        self.columnspan = columnspan

    def update(self):
        self.draw()
        for child in self.children:
            child.update()

    def coords(self):
        return pygame.Rect(self.rect.x + (window.size[0] - self.rect.w) // 2, self.rect.y + (window.size[1] - self.rect.h) // 2, self.rect.w, self.rect.h)

    def draw(self):
        raise NotImplementedError("Subclasses of Widget must implement the draw method")
             

class Button(Widget):
    def __init__(self, *args, text="", callback=None, duration=5, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.callback = callback # When button pressed: function executed once
        self.clicked = 0
        self.duration = duration # When button pressed: self.clicked > 0 for [duration] ticks

    def update(self): # 
        pos = pygame.mouse.get_pos()
        if 1 in window.mouse_buttons and self.coords().collidepoint(window.mouse_pos[:2]):
            self.clicked = self.duration
            if not self.callback is None:
                self.callback()

        if self.clicked:
            self.clicked -= 1
            self.draw_clicked()
        else:
            self.draw_idle()

    def draw_idle(self):
        pygame.draw.rect(window.world_surface, (255, 255, 255), self.coords(), 1)
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)

    def draw_clicked(self):
        pygame.draw.rect(window.world_surface, (255, 255, 255), self.coords())
        font.write(window.world_surface, self.text, (0, 0, 0), 4, self.coords().center, center=1)


class Label(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self):
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)


class Space(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self):
        pass


class Slider(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self):
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)


class Entry(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self):
        font.write(window.world_surface, self.text, (255, 255, 255), 4, self.coords().center, center=1)

