import math
import scripts.geometry as geometry

from scripts.util import realistic

if realistic:
    GRAVITY_CONSTANT: float = 9.81
else:
    GRAVITY_CONSTANT: float = 38

FRICTION_X: float = 0.1
FRICTION_Y: float = 0.04
JUMP_THRESHOLD: int = 3 # time to jump after leaving the ground in ticks
WALL_JUMP_THRESHOLD: float = 0.3 # time to jump after leaving a wall in seconds


class Physics_Object:
    def __init__(self, game, mass: float, position: [float], size: [float]):
        self.window: graphics.Window = game.window
        self.world: world.World = game.world

        self.mass: float = mass
        self.rect: geometry.Rect = geometry.Rect(*position, *size)
        self.vel: [float] = [0.0, 0.0]

        self.onGround: int = 0
        self.onWallLeft: int = 0
        self.onWallRight: int = 0

    def apply_force(self, force: float, angle: float): # angle in degrees; 0 is right, counterclockwise
        r_angle = math.radians(angle)
        self.vel[0] += (math.cos(r_angle) * force / self.mass) * self.window.delta_time
        self.vel[1] += (math.sin(r_angle) * force / self.mass) * self.window.delta_time
    
    def apply_velocity(self):
        self.rect.x += self.vel[0] * self.window.delta_time
        self.x_collide()
    
        self.rect.y += self.vel[1] * self.window.delta_time
        self.y_collide()

        for x in range(math.floor(self.rect.left), math.ceil(self.rect.right)):
            for y in range(math.floor(self.rect.top), math.ceil(self.rect.bottom)):
                if self.world[x, y]:
                    print("unresolved collision:", (x, y))

    def gravity(self):
        self.apply_force(GRAVITY_CONSTANT * self.mass, 270)
    
    def x_collide(self):
        for x in range(math.floor(self.rect.left), math.ceil(self.rect.right)):
            for y in range(math.floor(self.rect.top), math.ceil(self.rect.bottom)):
                if self.world[x, y]:
                    if self.vel[0] < 0:
                        self.rect.left = x + 1
                        self.vel[0] = 0
                        """   
                        if self.vel[1] < 0:
                            friction = self.window.delta_time / FRICTION_Y
                            if friction + self.vel[1] > 0:
                                self.vel[1] = 0
                            else:
                                self.vel[1] += friction
                        """
                        self.onWallRight = max(2, int(WALL_JUMP_THRESHOLD * self.window.fps))

                    if self.vel[0] > 0:
                        self.rect.right = x
                        self.vel[0] = 0
                        """
                        if self.vel[1] < 0:
                            friction = self.window.delta_time / FRICTION_Y
                            if friction + self.vel[1] > 0:
                                self.vel[1] = 0
                            else:
                                self.vel[1] += friction
                        """
                        self.onWallLeft = max(2, int(WALL_JUMP_THRESHOLD * self.window.fps))
    
    def y_collide(self):
        for x in range(math.floor(self.rect.left), math.ceil(self.rect.right)):
            for y in range(math.floor(self.rect.top), math.ceil(self.rect.bottom)):
                if self.world[x, y]:
                    if self.vel[1] > 0:
                        self.rect.bottom = y
                        self.vel[1] = 0

                    if self.vel[1] < 0:
                        self.rect.top = y + 1
                        self.vel[1] = 0

                        self.onGround = JUMP_THRESHOLD

    def update(self):
        self.gravity()
        if self.onGround:
            self.onGround -= 1
            friction = math.copysign(self.window.delta_time / FRICTION_X, self.vel[0])
            if abs(friction) > abs(self.vel[0]):
                self.vel[0] = 0
            else:
                self.vel[0] -= friction
        if self.onWallLeft:
            self.onWallLeft -= 1
        if self.onWallRight:
            self.onWallRight -= 1

        self.apply_velocity()
