from scripts.physics import *

from scripts.util import realistic


class Player(Physics_Object):
    def __init__(self, game, spawn_pos: [float], speed: float, sprint_speed: float, acceleration_time: float, jump_force: int):
        Physics_Object.__init__(self, game, 50, spawn_pos, (0.9, 1.8))

        self.speed: float = speed
        self.sprint_speed: float = sprint_speed
        self.acceleration_time: float = acceleration_time
        self.jump_force: int = jump_force

    def draw(self):
        rect = self.window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        self.window.draw_rect(rect[:2], rect[2:], (255, 0, 0))
    
    def jump(self, duration: float):
        force = self.jump_force * duration / self.window.delta_time
        if self.onGround: # Normal jump
            self.apply_force(force, 90)
        elif self.onWallLeft and self.window.keys["a"] and self.window.keys["space"] == 1: # Wall jump left
            self.apply_force(force * 2.5, 120)
            self.onWallLeft = 0
        elif self.onWallRight and self.window.keys["d"] and self.window.keys["space"] == 1: # Wall jump right
            self.apply_force(force * 2.5, 60)
            self.onWallRight = 0
        
    def move(self):
        def mouse_pull(strenght):
            mouse_pos = self.window.camera.map_coord(self.window.mouse_pos[:2], world=True)
        
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
            if realistic:
                d_speed = 0
            else:
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

        if self.window.mouse_buttons[1] == 1:
            mouse_pull(4.5) # constant activation balances out w/ gravity --> usable as rope

        if self.window.mouse_buttons[0] == 1:
            mouse_pos = self.window.camera.map_coord(self.window.mouse_pos[:2], world=True)
            spawn_particle(self, mouse_pos)

        if self.window.mouse_buttons[2] == 1:
            mouse_pos = self.window.camera.map_coord(self.window.mouse_pos[:2], world=True)
            self.world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])] = not self.world[math.floor(mouse_pos[0]), math.floor(mouse_pos[1])]

    def update(self):
        self.move()
        Physics_Object.update(self)
        self.draw()
        for particle in particle_list:
            particle.update()
            tmp_draw_rect(self, particle.rect.topleft, [particle.rect.w, particle.rect.h], (0, 255, 255))


def spawn_particle(self, pos: list[float, float]):
    from scripts.game import Game
    g = Game(self.window)
    g.world = self.world
    particle_list.append(Physics_Object(g, 10, pos, [1, 1]))

def tmp_draw_rect(self, pos, size, color):
    rect = self.window.camera.map_coord((pos[0], pos[1], size[0], size[1]), from_world=True)
    self.window.draw_rect(rect[:2], rect[2:], color)


particle_list: list[Physics_Object] = []