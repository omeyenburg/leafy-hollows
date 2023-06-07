import sys
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame



class Widget:
    def __init__(self, parent=None, size=(0, 0)):
        self.parent = parent
        self.children = []
        self.rect = pygame.Rect(0, 0, *size)
        self.parent.children.append(self)

    def update(self):
        self.draw()
        for child in self.children:
            child.update()

    def coords(self):
        return pygame.Rect(self.rect.x + (Page.window.size[0] - self.rect.w) // 2, self.rect.y + (Page.window.size[1] - self.rect.h) // 2, self.rect.w, self.rect.h)

    def draw(self):
        raise NotImplementedError("Subclasses of Widget must implement the draw method")


class Page(Widget):
    opened = None
    window = None
    
    def __init__(self, window, columns=1, spacing=20):
        self.children = []
        self.rect = pygame.Rect(0, 0, *window.size)
        self.columns = columns
        self.spacing = spacing
        Page.window = window

    def layout(self):
        width = [0 for _ in range(self.columns)]
        height = []

        for i, child in enumerate(self.children):
            width[child.col] = max(width[child.col], child.rect.w)
            if len(height) > child.row:
                height[child.row] = max(height[child.row], child.rect.h)
            else:
                height.append(child.rect.h)

        total_width = sum(width) - self.spacing * (self.columns - 1)
        total_height = sum(height) - self.spacing * (len(height) - 1)

        for i, child in enumerate(self.children):
            child.rect.centerx = sum(width[:child.col + 1]) - self.spacing * (self.columns - 1 - child.col) - total_width//2
            child.rect.centery = sum(height[:child.row + 1]) - self.spacing * (len(height) - 1 - child.row) - total_height//2

    def update(self, surface):
        self.draw(surface)
        for child in self.children:
            child.draw(surface)

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), self.coords(), 1)

    def open(self):
        Page.opened = self
             

class Button(Widget):
    def __init__(self, parent=None, size=(0, 0), text="", callback=None, row=0, col=0):
        super().__init__(parent, size)
        self.text = text
        self.callback = callback
        self.row = row
        self.col = col

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 255), self.coords(), 1)

        pos = pygame.mouse.get_pos()
        if 1 in Page.window.mouse_buttons and self.coords().collidepoint(Page.window.mouse_pos[:2]):
                pygame.draw.rect(surface, (255, 255, 255), self.coords())
                if not self.callback is None:
                    self.callback()

def update(surface):
    if not Page.opened is None:
        Page.opened.update(surface)

