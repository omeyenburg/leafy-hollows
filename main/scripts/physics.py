import math
import scripts.geometry as geometry

GRAVITY_CONSTANT = 38 # 9.81
FRICTION_X = 0.1
FRICTION_Y = 0.04
JUMP_THRESHOLD = 3 # time to jump after leaving the ground in ticks
WALL_JUMP_THRESHOLD = 0.3 # time to jump after leaving a wall in seconds


class Physics_Object:
    def __init__(self, game, mass, position, size):
        self.window = game.window
        self.world = game.world

        self.mass = mass
        self.rect = geometry.Rect(*position, *size)
        self.vel = [0.0, 0.0]

        self.onGround = 0
        self.onWallLeft = 0
        self.onWallRight = 0

    def apply_force(self, force, angle): # angle in degrees; 0 is right, counterclockwise
        r_angle = math.radians(angle)
        self.vel[0] += (math.cos(r_angle) * force / self.mass) * self.window.delta_time
        self.vel[1] += (math.sin(r_angle) * force / self.mass) * self.window.delta_time
    
    def apply_velocity(self):
        self.rect.x += self.vel[0] * self.window.delta_time
        self.x_collide()
    
        self.rect.y += self.vel[1] * self.window.delta_time
        if self.rect.y <= 0:
            self.onGround = JUMP_THRESHOLD
            self.vel[1] = 0
        self.rect.y = max(self.rect.y, 0)
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

                        if self.vel[1] < 0:
                            friction = self.window.delta_time / FRICTION_Y
                            if friction + self.vel[1] > 0:
                                self.vel[1] = 0
                            else:
                                self.vel[1] += friction
                        self.onWallRight = max(2, int(WALL_JUMP_THRESHOLD * self.window.fps))

                    if self.vel[0] > 0:
                        self.rect.right = x
                        self.vel[0] = 0

                        if self.vel[1] < 0:
                            friction = self.window.delta_time / FRICTION_Y
                            if friction + self.vel[1] > 0:
                                self.vel[1] = 0
                            else:
                                self.vel[1] += friction
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
