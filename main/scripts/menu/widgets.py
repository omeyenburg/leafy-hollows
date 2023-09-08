# -*- coding: utf-8 -*-
from scripts.graphics.window import Window
from scripts.utility import geometry
from scripts.utility import options
from scripts.utility.const import *
from scripts.graphics import sound
from scripts.utility import file
import math
import sys
import os


class Page:
    opened = None
    
    def __init__(self, parent=None, columns: int=1, spacing: int=0, callback=None):
        self.parent: Page = parent
        self.children: [Widget] = []
        self.columns = columns
        self.spacing = spacing
        self.callback = callback
        self.auto_column = 0
        self.auto_row = 0
        self.opened_tick = 0

    def layout(self):
        """
        Position all widgets in a grid on a page.
        """
        width = [0 for _ in range(self.columns)]
        height = []

        for i, child in enumerate(self.children):
            width[child.column] = max(width[child.column], child.rect.w / child.columnspan - self.spacing * (child.columnspan - 1))
            if len(height) > child.row:
                height[child.row] = max(height[child.row], child.rect.h)
            else:
                height.append(child.rect.h)

        total_width = sum(width) + self.spacing * (self.columns - 1)
        total_height = sum(height) + self.spacing * (len(height) - 1)

        for i, child in enumerate(self.children):
            child.row = min(child.row, len(height) - 1)
            child.rect.centerx = sum(width[:child.column + 1]) - total_width / 2 + self.spacing * (child.column + (child.columnspan - 1) / 2) + width[child.column] * (child.columnspan - 1) / 2 - width[child.column] / 2
            child.rect.centery = sum(height[:child.row + 1]) - total_height / 2 + self.spacing * child.row - height[child.row] + child.rect.h - height[child.row] / 2
            child.rect.centery = -child.rect.centery
            child.layout()

    def layout_prepend(self):
        for child in self.children:
            if child.rect.x == None or child.rect.y == None:
                child.rect.x = -child.rect.w / 2
                child.rect.y = MENU_TEXT_POSITION_TOP - child.rect.h

    def layout_append(self):
        for child in self.children:
            if child.rect.x == None or child.rect.y == None:
                child.rect.x = -child.rect.w / 2
                child.rect.y = MENU_TEXT_POSITION_BOTTOM + child.rect.h

    def update(self, window: Window):
        self.draw(window)
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        for child in self.children:
            child.update(window)
            if child.rect.collidepoint(mouse_pos):
                if child.hover_time > MENU_DESCRIPTION_HOVER_TIME and not child.hover_callback is None:
                    child.hover_callback()
                else:
                    child.hover_time += window.delta_time
            else:
                child.hover_time = 0
        if not self.callback is None:
            self.callback()
        if window.keybind("return") == 1 and not self.parent is None:
            self.parent.open()

    def draw(self, window: Window):
        if self.opened_tick == 1:
            self.opened_tick = 0
            sound.play(window, "click")

    def open(self):
        Page.opened = self
        self.opened_tick = 1


class Widget:
    def __init__(self, parent, size: [float], row: int=None, column: int=None, columnspan: int=1, fontsize: float=1.0, hover_callback=None):
        self.parent: Page = parent
        self.rect = geometry.Rect(None, None, *size) # Rect will be moved, when parent.layout is called
        self.parent.children.append(self)

        # Adjust auto column/row of parent
        if column is None:
            if parent.auto_column + max(1, columnspan) > parent.columns:
                parent.auto_column = 0
                parent.auto_row += 1
            column = parent.auto_column
        if row is None:
            row = parent.auto_row
        
        if row >= parent.auto_row and column >= 0:
            parent.auto_column += columnspan
        elif column < 0:
            column = self.parent.children[-2].column
            row = self.parent.children[-2].row
        if parent.auto_column >= parent.columns:
            parent.auto_column = 0
            parent.auto_row += 1
        if columnspan == 0:
            columnspan = 1

        self.row = row
        self.column = column
        self.columnspan = columnspan
        self.fontsize = fontsize
        self.hover_callback = hover_callback
        self.hover_time = 0

        if not 0 <= self.column < parent.columns:
            raise ValueError("Invalid Column " + str(self.column) + " for parent with " + str(parent.columns) + " column(s).")

    def update(self, window: Window):
        self.draw()
        for child in self.children:
            child.update(window)

    def layout(self):
        return


class Label(Widget):
    def __init__(self, *args, text: str="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text

    def update(self, window: Window):
        window.draw_text(self.rect.center, self.text, (250, 250, 250, 200), self.fontsize, centered=True)


class Button(Widget):
    def __init__(self, *args, text: str="", callback=None, duration: float=0.2, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.callback = callback # When button pressed: function executed once
        self.clicked = 0
        self.duration = duration # When button pressed: self.clicked > 0 for [duration] seconds

    def update(self, window: Window):
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        if self.rect.collidepoint(mouse_pos):
            if (window.mouse_buttons[0] == 1 or window.mouse_buttons[0] and self.clicked):
                if self.duration > 0:
                    self.clicked = max(2, int(self.duration / window.delta_time))
                else:
                    self.clicked = self.duration
        elif self.clicked > 0:
            self.clicked = 0

        if self.clicked:
            self.clicked -= 1
            self.draw_clicked(window)
            if window.mouse_buttons[0] == 0 and self.clicked > 0:
                self.clicked = 0
            if self.clicked in (0, -2) and not self.callback is None:
                sound.play(window, "click")
                self.callback()
        else:
            self.draw_idle(window)

    def draw_idle(self, window: Window):
        if self.rect.w == MENU_BUTTON_SMALL_WIDTH:
            image = "small_button"
        else:
            image = "button"
        window.draw_image(image, self.rect[:2], self.rect[2:])
        window.draw_text(self.rect.center, self.text, (255, 255, 255, 200), self.fontsize, centered=True)

    def draw_clicked(self, window: Window):
        offset = MENU_OFFSET_HOVER
        if self.rect.w == MENU_BUTTON_SMALL_WIDTH:
            image = "small_button"
        else:
            image = "button"
        window.draw_image(image, (self.rect[0], self.rect[1] - offset), self.rect[2:])
        window.draw_text((self.rect.centerx, self.rect.centery - offset), self.text, (255, 255, 255, 200), self.fontsize, centered=True)


class Slider(Widget):
    def __init__(self, *args, callback=None, value=0.0, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.value = value
        self.selected = False
        self.slider_rect = self.rect.copy()
        self.text = text

    def update(self, window: Window):
        self.slider_rect.h = self.rect.h
        self.slider_rect.w = MENU_SLIDER_WIDTH
        self.slider_rect.x = self.rect.x + (self.rect.w - self.slider_rect.w) * self.value
        self.slider_rect.y = self.rect.y

        if self.rect.collidepoint((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)) and window.mouse_buttons[0] == 1:
            self.selected = True
        elif not window.mouse_buttons[0]:
            if self.selected:
                sound.play(window, "click")
            self.selected = False

        if self.selected:
            value = min(1, max(0, (window.mouse_pos[0] / window.width * 2 - self.rect.x) / self.rect.w))
            if value != self.value and not self.callback is None:
                if value < 0.02:
                    value = 0
                elif value > 0.98:
                    value = 1
                self.value = value
                self.callback()

        self.draw(window)

    def draw(self, window: Window):
        if self.selected:
            offset = MENU_OFFSET_HOVER
        else:
            offset = 0
        if self.rect.w == MENU_BUTTON_SMALL_WIDTH:
            image = "small_button"
        else:
            image = "button"
        window.draw_image(image, (self.rect[0], self.rect[1] - offset), self.rect[2:])
        window.draw_image("slider", (self.slider_rect[0], self.slider_rect[1] - offset), self.slider_rect[2:])
        window.draw_text((self.rect.centerx, self.rect.centery - offset), self.text, (255, 255, 255, 200), TEXT_SIZE_OPTION, centered=True)


class Entry(Widget):
    def __init__(self, *args, text="", **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.selected = False
        self.cursor = 0

    def update(self):
        if window.unicode == "\x08":
            self.text = self.text[:-1]
        elif window.unicode.isprintable():
            self.text += window.unicode

        self.draw()

    def draw(self):
        window.draw_rect(self.rect[:2], self.rect[2:], (255, 0, 0, 200))
        window.draw_text(self.rect.center, self.text, (0, 0, 0, 255), self.fontsize, centered=True)


class ScrollBox(Widget):
    def __init__(self, *args, columns=1, spacing=0.1, callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.children: Widget = []
        self.columns = columns
        self.spacing = spacing
        self.offset = 0
        self.start_offset = 0
        self.end_offset = 0
        self.offset_length = 0
        self.callback = callback
        self.auto_column = 0
        self.auto_row = 0

        # Slider
        self.slider_y = 0
        self.slider_rect = geometry.Rect(0, 0, self.spacing / 2, 0)
        self.slider_selected = False

    def update(self, window: Window):
        adjust_offset = max(self.offset, self.end_offset)
        adjust_offset = min(adjust_offset, self.start_offset)
        self.offset += window.mouse_wheel[3] / window.height * 10
        if adjust_offset != self.offset:
            self.offset = (adjust_offset + self.offset * 3) / 4

        # Slider
        if self.offset_length == 0:
            self.slider_y = 0
        else:
            self.slider_y = -round((self.start_offset - self.offset) / self.offset_length, 4)

        self.slider_rect.h = (1 - (self.start_offset - self.end_offset)) * self.rect.h
        self.slider_rect.x = self.rect.right
        self.slider_rect.y = self.rect.bottom - self.slider_y * (self.rect.h - self.slider_rect.h) - self.slider_rect.h

        if self.slider_rect.collidepoint((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)) and window.mouse_buttons[0] == 1:
            self.slider_selected = True
        elif not window.mouse_buttons[0]:
            if self.slider_selected:
                sound.play(window, "click")
            self.slider_selected = False

        if self.slider_selected and self.offset_length != 0:
            self.slider_y = -(window.mouse_pos[1] / window.height * 2 - self.rect.bottom) / self.rect.h
            self.offset = self.slider_y * self.offset_length + self.start_offset

        # Draw & Update children
        self.draw(window)
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, from_centered=1)
        window.stencil_rect = (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2, self.rect[2] / 2, self.rect[3] / 2)
        for child in self.children:
            y = child.rect.y
            child.rect.y -= self.offset
            child.update(window)
            child.rect.y = y
        window.stencil_rect = ()

        for child in self.children:
            rect = child.rect.copy()
            rect.y -= self.offset
            if rect.collidepoint(mouse_pos):
                if child.hover_time > MENU_DESCRIPTION_HOVER_TIME and not child.hover_callback is None:
                    child.hover_callback()
                else:
                    child.hover_time += window.delta_time
            else:
                child.hover_time = 0

        if not self.callback is None:
            self.callback()

    def layout(self):
        Page.layout(self)
        self.start_offset = self.children[0].rect.bottom - self.rect.bottom + self.spacing
        self.end_offset = self.children[-1].rect.y - self.rect.y - self.spacing
        self.offset = self.start_offset
        self.offset_length = min(0, self.end_offset - self.start_offset)

    def draw(self, window: Window):
        window.draw_rect(self.rect[:2], self.rect[2:], (60, 60, 60, 200))
        if self.offset_length != 0:
            x = self.slider_rect[0]
            y = max(self.slider_rect[1], self.rect[1])
            w = self.slider_rect[2]
            h = min(self.slider_rect[3] + self.slider_rect[1], self.rect[1] + self.rect[3]) - y
            window.draw_rect((x, y), (w, h), (200, 200, 200, 200))


def HoverBox(window: Window, rect: list, text: list):
    """
    Draw a box with multi colored text.
    text: [("text", (r, g, b, a))]
    """
    window.draw_rect(rect[:2], rect[2:], (150, 150, 150, 255))
    start = (0.025, rect[3] - 0.05)
    x = 0
    y = 0
    wrap = True
    for text_snippet, fontsize, color in text:
        if not text_snippet:
            continue

        pos = (rect[0] + start[0] + x,
                rect[1] + start[1] + y)
        x_offset, y_offset = window.draw_text(pos, text_snippet, color, size=fontsize, wrap=rect[2] - 0.05)
        wrap = text_snippet[-1] == "\n"
        if wrap:
            y += y_offset
            x = 0
        else:
            x += x_offset
