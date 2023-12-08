# -*- coding: utf-8 -*-
from random import shuffle
from math import *


class Rect:
    def __init__(self, *args):
        args_length = len(args)

        if args_length == 4:
            self.x, self.y, self.w, self.h = args
            self._w_half: float = self.w / 2
            self._h_half: float = self.h / 2
            return

        if args_length == 2:
            (self.x, self.y), (self.w, self.h) = args
            self._w_half: float = self.w / 2
            self._h_half: float = self.h / 2
            return

        if args_length != 1 or len(args[0]) != 4:
            raise TypeError("rect expected 1 list, 2 list or 4 numeric arguments, got " + str(args_length))

        args = args[0]
        if isinstance(args, (list, tuple, Rect)):
            self.x, self.y, self.w, self.h = args
            self._w_half: float = self.w / 2
            self._h_half: float = self.h / 2
            return

        raise TypeError("argument must be list, tuple or rect, got '" + type(args) + "'")

    def __repr__(self):
        return f"Rect({self.x}, {self.y}, {self.w}, {self.h})"

    def __getitem__(self, index):
        return (self.x, self.y, self.w, self.h)[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
            return
        if index == 1:
            self.y = value
            return
        if index == 2:
            self.w = value
            return
        if index == 3:
            self.h = value
            return
        raise IndexError("Index out of range, expected 0 to 3")

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.w
        yield self.h

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

    def collide_point(self, point):
        return self.x < point[0] < self.x + self.w and self.y < point[1] < self.y + self.h

    def collide_line(self, start, end):
        return (
            self.x < start[0] < self.x + self.w and self.y < start[1] < self.y + self.h or # Start point in rect
            self.x < end[0] < self.x + self.w and self.y < end[1] < self.y + self.h or # End point in rect
            min(start[0], end[0]) < self.x < max(start[0], end[0]) and self.y < (self.x - start[0]) / (end[0] - start[0]) * (end[1] - start[1]) + start[1] < self.y + self.h or                    # Line intersects with right edge
            min(start[0], end[0]) < self.x + self.w < max(start[0], end[0]) and self.y < (self.x + self.w - start[0]) / (end[0] - start[0]) * (end[1] - start[1]) + start[1] < self.y + self.h or  # Line intersects with left edge
            min(start[1], end[1]) < self.y < max(start[1], end[1]) and self.x < (self.y - start[1]) / (end[1] - start[1]) * (end[0] - start[0]) + start[0] < self.x + self.w                       # Line intersects with top edge
        )

    def collide_rect(self, other):
        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.y + self.h <= other.y
            or self.y >= other.y + other.h
        )

    @staticmethod
    def multi_intersection(rectangles):
        for rect1 in rectangles:
            others = rectangles[:]
            others.remove(rect1)
            for rect2 in others:
                if Rect.collide_rect(Rect(*rect1), Rect(*rect2)):
                    return True
        return False


class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        # args_length = len(args)
        # if args_length == 2:
        #     self.x, self.y = args
        #     return

        # if args_length == 1:
        #     self.x, self.y = args[0]
        #     return
        
        # raise TypeError("Vec expected a list, Vec or 2 numeric arguments, got " + str(args))

    def __repr__(self):
        return f"Vec({self.x}, {self.y})"

    def __getitem__(self, index):
        return (self.x, self.y)[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
            return
        if index == 1:
            self.y = value
            return
        raise IndexError("Index out of range, expected 0 to 1")

    def __iter__(self):
        yield self.x
        yield self.y

    def __reduce__(self):
        return (self.__class__, (self.x, self.y)) # Define values to pickle

    def __eq__(self, rect):
        return self.x == rect.x and self.y == rect.y

    def __add__(self, value):
        return Vec(self[0] + value[0], self[1] + value[1])

    def __radd__(self, value):
        return Vec(self[0] + value[0], self[1] + value[1])

    def __sub__(self, value):
        return Vec(self[0] - value[0], self[1] - value[1])

    def __rsub__(self, value):
        return Vec(self[0] - value[0], self[1] - value[1])

    def __mul__(self, value):
        return Vec(self[0] * value, self[1] * value)

    def __rmul__(self, value):
        return Vec(self[0] * value, self[1] * value)

    def __truediv__(self, value):
        return Vec(self[0] / value, self[1] / value)

    def __rtruediv__(self, value):
        return Vec(self[0] / value, self[1] / value)

    def __floordiv__(self, value):
        return Vec(self[0] // value, self[1] // value)

    def __neg__(self, value):
        return Vec(-self[0], -self[1])

    def __abs__(self):
        return sqrt(self[0] ** 2 + self[1] ** 2)

    @property
    def normalized(self):
        length = abs(self)
        return (self.x / length, self.y / length)

    def copy(self):
        return Vec(self.x, self.y)

    def rotate(self, angle):
        length = abs(self)
        angle = atan2(self.y, self.x) + angle
        self.x = cos(angle) * length
        self.y = sin(angle) * length


def angle(a):
    return a % (2 * pi)


def shuffled_range(n):
    numbers = list(range(n))
    shuffle(numbers)
    for i in numbers:
        yield i
