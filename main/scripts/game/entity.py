# -*- coding: utf-8 -*-
from scripts.game.noise_functions import pnoise1
from scripts.game.baseentity import LivingEntity
from scripts.game.physics import PhysicsObject
from scripts.graphics.window import Window
from scripts.graphics import particle
from scripts.utility.const import *
import math


class Arrow(PhysicsObject):
    def __init__(self, spawn_pos: [float], speed: float=0, angle: float=0, owner: LivingEntity=None):
        super().__init__(5, spawn_pos, ARROW_RECT_SIZE)

        self.angle = angle
        self.owner = owner
        self.destroy_unloaded = True

        self.apply_force(speed, angle, 1, is_radians=True)

    def draw(self, window: Window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        # Draw arrow
        rect = window.camera.map_coord((self.rect.x - 0.25 + self.rect.w / 2, self.rect.y - 0.25 + self.rect.h / 2, 0.5, 0.5), from_world=True)
        window.draw_image("arrow", rect[:2], rect[2:], angle=math.degrees(self.angle))

    def update(self, world, window: Window):
        # Cancel when arrow in wall
        if self.block_above or self.block_below or self.block_left or self.block_right:
            return

        # Rotate along velocity
        self.angle = math.atan2(*self.vel[::-1]) + math.pi

        # Hurt entities

        for entity in world.loaded_entities:
            if (not (entity is self or entity is self.owner)) and isinstance(entity, LivingEntity) and self.rect.collide_rect(entity.rect):
                entity.damage(window, 1, self.vel)
                world.entities.discard(self)
                break

        super().update(world, window.delta_time)


class Slime(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(30, spawn_pos, SLIME_RECT_SIZE, health=5)

        # Enemy attributes
        self.level = 1             # Difficulty
        self.hit_damage = 1        # Damage applied to player on collision
        self.attack_cooldown = 3

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("slime_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def update(self, world, window: Window):
        if self.block_below:
            if self.hit_ground == 0:
                self.hit_ground = 0.2
                particle.spawn(window, "slime_particle", self.rect.centerx, self.rect.top)
            self.hit_ground -= window.delta_time
            self.vel[0] *= 0.8
            self.attack_cooldown = 0

            if self.hit_ground < -0.5:
                self.direction = int(world.player.rect.x < self.rect.x)
                self.vel[1] += 6
        else:
            self.hit_ground = 0
            self.vel[0] += 0.1 * (-self.direction + 0.5)

        vel_y = abs(self.vel[1])
        if vel_y > 3:
            self.state = "high_jump"
        elif vel_y != 0:
            self.state = "jump"
        else:
            self.state = "idle"

        if self.hit_ground > 0:
            self.state = "hit_ground"

        super().update(world, window.delta_time)

        # Attack player
        if self.attack_cooldown < 0 and self.vel[1] < 0 and self.rect.collide_rect(world.player.rect):
            world.player.damage(window, 1, self.vel)
            self.attack_cooldown = 5
        self.attack_cooldown -= window.delta_time

    def death(self, window):
        particle.spawn(window, "slime_particle", *self.rect.center)
        

class Goblin(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(30, spawn_pos, GOBLIN_RECT_SIZE, health=5)

        # Enemy attributes
        self.level = 1             # Difficulty
        self.hit_damage = 1        # Damage applied to player on collision
        self.attack_cooldown = 3
        self.max_speed = 3

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        rect = window.camera.map_coord((self.rect.x - 1 + self.rect.w / 2, self.rect.y, 2, 2), from_world=True)
        window.draw_image("goblin_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def update(self, world, window: Window):
        speed = min(self.max_speed, abs(world.player.rect.centerx - self.rect.centerx))
        if world.player.rect.centerx < self.rect.centerx:
            self.vel[0] = -speed
            self.direction = 1
            side_block = world.get_block(math.floor(self.rect.left - 0.6), round(self.rect.y))
        else:
            self.vel[0] = speed
            self.direction = 0
            side_block = world.get_block(math.floor(self.rect.right + 0.6), round(self.rect.y))

        # Auto jump
        if side_block and self.block_below:
            self.vel[1] += 6.5
            self.vel[0] *= 0.5
        
        if not self.block_below:
            self.state = "jump"
            self.hit_ground = 0.2
        elif self.hit_ground > 0:
            self.hit_ground = max(0, self.hit_ground - window.delta_time)
            self.state = "hit_ground"
            self.vel[0] *= 0.4
        elif abs(self.vel[0]) > 1:
            self.state = "walk"
        else:
            self.state = "idle"

        super().update(world, window.delta_time)


class Bat(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(30, spawn_pos, BAT_RECT_SIZE, health=3)

        # Enemy attributes
        self.level = 1             # Difficulty
        self.hit_damage = 1        # Damage applied to player on collision
        self.attack_cooldown = 3
        self.max_speed = 2.5

        # Animation states
        self.state: str = "fly"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("bat_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def update(self, world, window: Window):
        speed_x = min(self.max_speed, abs(world.player.rect.centerx - self.rect.centerx))
        if world.player.rect.centerx < self.rect.centerx:
            self.vel[0] = -speed_x
            self.direction = 1
        else:
            self.vel[0] = speed_x
            self.direction = 0

        speed_y = min(self.max_speed, abs(world.player.rect.centery - self.rect.centery))
        y_offset = pnoise1(window.time / 20 + self.uuid * 10, 5) * 10
        if world.player.rect.centery + y_offset < self.rect.centery:
            self.vel[1] = -speed_y
        else:
            self.vel[1] = speed_y

        super().update(world, window.delta_time)
