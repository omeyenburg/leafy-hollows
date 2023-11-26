# -*- coding: utf-8 -*-
from scripts.utility.noise_functions import pnoise1
from scripts.game.baseentity import LivingEntity
from scripts.game.physics import PhysicsObject
from scripts.graphics.window import Window
from scripts.graphics import particle
from scripts.utility.const import *
from scripts.game.weapon import *
from scripts.game.pathfinding import a_star


class Slime(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(30, spawn_pos, SLIME_RECT_SIZE, health=5)
        self.type = "enemy"

        # Enemy attributes
        self.item_drop_chance = 0.3
        self.hit_damage = 1 # Damage applied to player on collision
        self.attack_cooldown: float = 3

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        super().draw(window)
        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("slime_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def update(self, world, window: Window):
        super().update(world, window.delta_time)

        if self.stunned:
            return

        if self.block_below and not self.stunned:
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
        self.type = "enemy"

        # Enemy attributes
        self.item_drop_chance = 0.5
        self.max_speed = 3
        self.prepare_attack_length: float = 0.5
        self.prepare_attack: float = self.prepare_attack_length

        self.holding = random.choice((Sword, Axe, Pickaxe, Bow))(1)

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        super().draw(window)
        rect = window.camera.map_coord((self.rect.x - 1 + self.rect.w / 2, self.rect.y, 2, 2), from_world=True)
        window.draw_image("goblin_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def update(self, world, window: Window):
        super().update(world, window.delta_time)

        if self.stunned:
            self.state = "hit_ground"
            return

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

        #player_distance = math.sqrt((self.rect.centerx - world.player.rect.centerx) ** 2 + (self.rect.centery - world.player.rect.centery) ** 2)
        if self.rect.collide_rect(world.player.rect) or self.holding is Bow:
            self.prepare_attack -= window.delta_time

            if self.prepare_attack < 0:
                angle = math.atan2(world.player.rect.centery - self.rect.centery, world.player.rect.centerx - self.rect.centerx)
                self.holding.attack(window, world, self, angle)
                self.prepare_attack = self.prepare_attack_length
        else:
            self.prepare_attack_time = self.prepare_attack_length


class Bat(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(30, spawn_pos, BAT_RECT_SIZE, health=3)
        self.type = "enemy"

        # Enemy attributes
        self.item_drop_chance = 0.2
        self.hit_damage = 1 # Damage applied to player on collision
        self.max_speed = 2.5
        self.prepare_attack_length: float = 4.0
        self.prepare_attack: float = self.prepare_attack_length

        # Animation states
        self.state: str = "fly"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        super().draw(window)
        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("bat_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def move(self, world): # pathfinding implementation
        def pathfind() -> list[int, int]:
            self_pos = [round(_) for _ in self.rect.center]
            target_pos = [round(_) for _ in world.player.rect.center]
            print(self_pos, target_pos)
            print(world.get_block(x= 0, y= 0))
            grid = [[None] * abs(self_pos[0] - target_pos[0])] * abs(self_pos[1] - target_pos[1])

            max_x, max_y = len(grid[0]) - 1, len(grid) - 1
            start_pos = [0 if self_pos[0] < target_pos[0] else max_x, 0 if self_pos[1] < target_pos[1] else max_y]  # translate to relative positions
            end_pos = [max_x if self_pos[0] < target_pos[0] else 0, max_y if self_pos[1] < target_pos[1] else 0]

            x_offset = self_pos[0] - start_pos[0]
            y_offset = self_pos[1] - start_pos[1]


            for y, _ in enumerate(grid):
                for x, _ in enumerate(grid[y]):
                    grid[y][x] = world.get_block(x=x + x_offset, y=y + y_offset)

            print(len(grid), len(grid[0]))
            print(grid)

            
            next_pos = a_star(grid=world, start_pos=self.rect.center, end_pos=world.player.rect.center, allow_diagonals=True, full_path=False)
            print(next_pos)
            return next_pos
        
        if math.dist(self.rect.center, world.player.rect.center) > 3:   # find path for longer distances
            next_pos = pathfind()

            if next_pos[0] < self.rect.centerx:
                self.vel[0] = -self.max_speed
                self.direction = 1
            else:
                self.vel[0] = -self.max_speed
                self.direction = 0
            
            if next_pos[1] < self.rect.centery:
                self.vel[1] = -speed_y
            else:
                self.vel[1] = speed_y

        
        else:
            speed_x = min(self.max_speed, abs(world.player.rect.centerx - self.rect.centerx))
            if world.player.rect.centerx < self.rect.centerx:
                self.vel[0] = -speed_x
                self.direction = 1
            else:
                self.vel[0] = speed_x
                self.direction = 0

            y_offset = self.prepare_attack#pnoise1(window.time / 20 + self.uuid * 10, 5) * 4

            speed_y = min(self.max_speed, abs(world.player.rect.centery + y_offset - self.rect.centery))
            if world.player.rect.centery + y_offset < self.rect.centery:
                self.vel[1] = -speed_y
            else:
                self.vel[1] = speed_y

    def update(self, world, window: Window):
        super().update(world, window.delta_time)

        if self.stunned:
            return

        self.move(world)

        # Attack
        if self.rect.collide_rect(world.player.rect) and self.prepare_attack < 0:
            world.player.damage(window, 1, self.vel)
            self.prepare_attack = self.prepare_attack_length
        elif self.prepare_attack >= 0:
            self.prepare_attack -= window.delta_time
