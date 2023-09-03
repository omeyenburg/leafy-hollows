# -*- coding: utf-8 -*-
import random
import math


class Rect:
    def __init__(self, x, y, w, h):
        self.x: float = x
        self.y: float = y
        self.w: float = w
        self.h: float = h
        self._w_half: float = w/2
        self._h_half: float = h/2

    def __repr__(self):
        return f"Rect({self.x}, {self.y}, {self.w}, {self.h})"

    def __getitem__(self, index):
        return (self.x, self.y, self.w, self.h)[index]

    def __setitem__(self, index, value):
        self.__dict__["xywh"[index]] = value

    def __iter__(self):
        for value in (self.x, self.y, self.w, self.h):
            yield value

    def __eq__(self, rect):
        return self.x == rect.x and self.y == rect.y and self.w == rect.w and self.h == rect.h and self.angle == rect.angle

    @property
    def topleft(self):
        return (self.x, self.y)

    @topleft.setter
    def topleft(self, value):
        self.x, self.y = value[0], value[1]

    @property
    def center(self):
        return (self.x + self._w_half, self.y + self._h_half)

    @center.setter
    def center(self, value):
        self.x, self.y = value[0] - self._w_half, value[1] - self._h_half

    @property
    def centerx(self):
        return self.x + self._w_half

    @centerx.setter
    def centerx(self, a):
        self.x = a - self._w_half

    @property
    def centery(self):
        return self.y + self._h_half

    @centery.setter
    def centery(self, value):
        self.y = value - self._h_half

    @property
    def left(self):
        return self.x

    @left.setter
    def left(self, value):
        self.x = value

    @property
    def right(self):
        return self.x + self.w

    @right.setter
    def right(self, value):
        self.x = value - self.w

    @property
    def top(self):
        return self.y

    @top.setter
    def top(self, value):
        self.y = value

    @property
    def bottom(self):
        return self.y + self.h

    @bottom.setter
    def bottom(self, value):
        self.y = value - self.h

    @property
    def size(self):
        return self.w, self.h

    @size.setter
    def size(self, value):
        self.w, self.h = value

    def copy(self):
        return Rect(self.x, self.y, self.w, self.h)

    def collidepoint(self, point):
        return self.x < point[0] < self.right and self.y < point[1] < self.bottom

    def intersection(self, other):
        return not (self.right <= other.left
                    or self.left >= other.right
                    or self.bottom <= other.top
                    or self.top >= other.bottom)

    @staticmethod
    def multi_intersection(rectangles):
        for rect1 in rectangles:
            others = rectangles[:]
            others.remove(rect1)
            for rect2 in others:
                if Rect.intersection(Rect(*rect1), Rect(*rect2)):
                    return True
        return False


def angle(a):
    return a % (2 * math.pi)


def shuffled_range(n):
    numbers = list(range(n))
    random.shuffle(numbers)
    for i in numbers:
        yield i
