from scripts.physics import *


class Player(Physics_Object):
    def __init__(self, game, spawn_pos, speed, sprint_speed, acceleration_time, jump_force):
        Physics_Object.__init__(self, game, 50, (0, 0), (0.9, 1.8))

        self.speed = speed
        self.sprint_speed = sprint_speed
        self.acceleration_time = acceleration_time
        self.jump_force = jump_force

    def draw(self):
        rect = self.window.camera.map_coord((self.rect.x * self.world.PIXELS_PER_METER, self.rect.y * self.world.PIXELS_PER_METER, self.rect.w * self.world.PIXELS_PER_METER, self.rect.h * self.world.PIXELS_PER_METER))
        self.window.draw_rect(rect[:2], rect[2:], (255, 0, 0))
    
    def jump(self, duration):
        force = self.jump_force * duration / self.window.delta_time
        if self.onGround: # Normal jump
            self.apply_force(force, 90)
        elif self.onWallLeft and self.window.keys["a"] and self.window.keys["space"] == 1: # Wall jump left
            angle = 120
            force *= 3
            self.apply_force(force, angle)
            self.onWallLeft = 0
        elif self.onWallRight and self.window.keys["d"] and self.window.keys["space"] == 1: # Wall jump right
            angle = 60
            force *= 3
            self.apply_force(force, angle)
            self.onWallRight = 0
        
    def move(self):
        def mouse_pull(strenght):
            mouse_pos = (self.window.mouse_pos[0] / self.world.PIXELS_PER_METER, self.window.mouse_pos[1] / self.world.PIXELS_PER_METER)
        
            dx, dy = mouse_pos[0] - self.rect.centerx, mouse_pos[1] - self.rect.centery
            angle_to_mouse = math.degrees(math.atan2(dy, dx))

            force = min(math.dist(self.rect.center, mouse_pos), 3) * (10**strenght)
            self.apply_force(force, angle_to_mouse)

        keys = self.window.keys

        max_speed = self.speed
        if keys["left shift"]: # keeps sprinting once key pressed / stops faster as long as pressed
            max_speed = self.sprint_speed

        d_speed = (self.window.delta_time / self.acceleration_time) * max_speed
        if not (self.onGround or self.onWallLeft or self.onWallRight):
            d_speed /= 10
        
        if keys["d"]: # d has priority over a
            if self.vel[0] < max_speed:
                if self.vel[0] + d_speed > max_speed: # guaranteeing exact max speed
                    self.vel[0] = max_speed
                else:
                    self.vel[0] += d_speed
        elif keys["a"]:
            if self.vel[0] > -max_speed:
                if self.vel[0] - d_speed < -max_speed:
                    self.vel[0] = -max_speed
                else:
                    self.vel[0] -= d_speed
        else:   
            if abs(self.vel[0]) <= d_speed:
                self.vel[0] = 0
            else:
                if self.vel[0] > 0:
                    self.vel[0] -= d_speed
                else:
                    self.vel[0] += d_speed
        if keys["space"]:
            self.jump(5) # how long is jump force applied --> variable jump height

        if self.window.mouse_buttons[0] == 1:
            mouse_pull(4.5) # constant activation balances out w/ gravity --> usable as rope
        if self.window.mouse_buttons[2] == 1:
            mouse_pos = (self.window.mouse_pos[0] / self.world.PIXELS_PER_METER, self.window.mouse_pos[1] / self.world.PIXELS_PER_METER)
            self.world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])] = not self.world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])]

    def update(self):
        self.move()
        Physics_Object.update(self)
        self.draw()
