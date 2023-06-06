import pygame
import sys

pygame.init()

window_size import pygame
import sys


class Widget:
    def __init__(self, parent=None, size=(0, 0)):
        self.parent = parent
        self.children = []
        self.rect = pygame.Rect(0, 0, *size)
        self.parent.children.append(self)

    def coords(self):
        return pygame.Rect(self.rect.x + (Page.window_size[0] - self.rect.w) // 2, self.rect.y + (Page.window_size[1] - self.rect.h) // 2, self.rect.w, self.rect.h)

    def draw(self):
        raise NotImplementedError("Subclasses of Widget must implement the draw method")


class Page(Widget):
    opened = None
    window_size = (0, 0)
    
    def __init__(self, size, columns=1, spacing=20):
        self.children = []
        self.rect = pygame.Rect(0, 0, *size)
        self.columns = columns
        self.spacing = spacing

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
        self.rect.size = Page.window_size
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
        if self.coords().collidepoint(pos):
            if pygame.mouse.get_pressed()[0]:
                pygame.draw.rect(surface, (255, 255, 255), self.coords())
                if not self.callback is None:
                    self.callback()

def update(surface, window_size):
    Page.window_size = window_size
    if not Page.opened is None:
        Page.opened.update(surface)

# Widgets:
#    Page
#    Label
#    Button
#    Slider
#    Entry
#    Switch
#    Options
    

"""
main_page = Page(columns=2, spacing=10)

b1 = Button(main_page, (150, 50), row=0, col=0, callback=lambda: print(0, 0))
b2 = Button(main_page, (150, 50), row=0, col=1, callback=lambda: print(0, 1))
b3 = Button(main_page, (150, 50), row=1, col=0, callback=lambda: print(1, 0))
b4 = Button(main_page, (150, 50), row=1, col=1, callback=lambda: print(1, 1))
b5 = Button(main_page, (150, 50), row=2, col=0, callback=lambda: print(2, 0))
b6 = Button(main_page, (150, 50), row=2, col=1, callback=lambda: print(2, 1))


main_page.layout()
main_page.open()





while True:
    window.fill((0, 0, 0))
    update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            window_size = event.size
            window = pygame.display.set_mode(window_size, flags=pygame.RESIZABLE)
            

    pygame.display.update()
    
"""ygame.display.set_mode(window_size, flags=pygame.RESIZABLE)


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
        return pygame.Rect(self.rect.x + (window_size[0] - self.rect.w) // 2, self.rect.y + (window_size[1] - self.rect.h) // 2, self.rect.w, self.rect.h)

    def draw(self):
        raise NotImplementedError("Subclasses of Widget must implement the draw method")


class Page(Widget):
    opened = None
    
    def __init__(self, columns=1, spacing=20):
        self.children = []
        self.rect = pygame.Rect(0, 0, *window_size)
        self.columns = columns
        self.spacing = spacing

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

    def update(self):
        self.rect.size = window_size
        self.draw()
        for child in self.children:
            child.update()

    def draw(self):
        pygame.draw.rect(window, (255, 255, 255), self.coords(), 1)

    def open(self):
        Page.opened = self
             

class Button(Widget):
    def __init__(self, parent=None, size=(0, 0), text="", callback=None, row=0, col=0):
        super().__init__(parent, size)
        self.text = text
        self.callback = callback
        self.row = row
        self.col = col

    def draw(self):
        pygame.draw.rect(window, (255, 255, 255), self.coords(), 1)

        pos = pygame.mouse.get_pos()
        if self.coords().collidepoint(pos):
            if pygame.mouse.get_pressed()[0]:
                pygame.draw.rect(window, (255, 255, 255), self.coords())
                if not self.callback is None:
                    self.callback()


# Widgets:
#    Page
#    Label
#    Button
#    Slider
#    Entry
#    Switch
#    Options
    


main_page = Page(columns=2, spacing=10)

b1 = Button(main_page, (150, 50), row=0, col=0, callback=lambda: print(0, 0))
b2 = Button(main_page, (150, 50), row=0, col=1, callback=lambda: print(0, 1))
b3 = Button(main_page, (150, 50), row=1, col=0, callback=lambda: print(1, 0))
b4 = Button(main_page, (150, 50), row=1, col=1, callback=lambda: print(1, 1))
b5 = Button(main_page, (150, 50), row=2, col=0, callback=lambda: print(2, 0))
b6 = Button(main_page, (150, 50), row=2, col=1, callback=lambda: print(2, 1))


main_page.layout()
main_page.open()


def update():
    if not Page.opened is None:
        Page.opened.update()


while True:
    window.fill((0, 0, 0))
    update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            window_size = event.size
            window = pygame.display.set_mode(window_size, flags=pygame.RESIZABLE)
            

    pygame.display.update()
    
