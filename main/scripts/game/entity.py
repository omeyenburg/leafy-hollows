# -*- coding: utf-8 -*-
from scripts.game.baseentity import LivingEntity
from scripts.game.physics import PhysicsObject
from scripts.graphics.window import Window
from scripts.graphics import particle
from scripts.utility.const import *
from scripts.graphics import sound
from scripts.game.weapon import *
from scripts.game.pathfinding import a_star


class GreenSlime(LivingEntity):
    def __init__(self, spawn_pos: [float], health=5, hit_damage=1):
        health = min(round(health * (1 + spawn_pos[0] / 400 / health)), 40)
        super().__init__(30, spawn_pos, SLIME_RECT_SIZE, health=health)
        self.type = "enemy"
        self.image = "slime"
        self.slime_variant = "green"

        # Enemy attributes
        self.item_drop_chance = 0.3
        self.hit_damage = min(hit_damage + 2, round(hit_damage * (1 + spawn_pos[0] / 400 / hit_damage)))
        self.attack_cooldown: float = 3
        self.jump_strength = 1

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        super().draw(window)
        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("_".join((self.slime_variant, self.image, self.state)), rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def update(self, world, window: Window):
        super().update(world, window.delta_time)

        if self.stunned:
            return

        if self.block_below and not self.stunned:
            if self.hit_ground == 0:
                self.hit_ground = 0.2
                particle.spawn(window, self.slime_variant + "_slime_particle", self.rect.centerx, self.rect.top)
                sound.play(window, "slime", x=(self.rect.x - world.player.rect.x) / 5)

            self.hit_ground -= window.delta_time
            self.vel[0] *= 0.8
            self.attack_cooldown = 0

            if self.hit_ground < -0.5:
                self.direction = int(world.player.rect.x < self.rect.x)
                self.vel[1] += 6 * self.jump_strength
        else:
            self.hit_ground = 0
            self.vel[0] += 0.1 * (-self.direction + 0.5) * self.jump_strength

        if self.underWater:
            self.vel[1] *= 0.8

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
            world.player.damage(window, self.hit_damage, self.vel)
            self.attack_cooldown = 5
        self.attack_cooldown -= window.delta_time

    def death(self, window):
        particle.spawn(window, self.slime_variant + "_slime_particle", *self.rect.center)


class YellowSlime(GreenSlime):
    def __init__(self, spawn_pos: [float]):
        super().__init__(spawn_pos, health=15, hit_damage=3)
        self.slime_variant = "yellow"

        # Enemy attributes
        self.item_drop_chance = 0.4
        self.attack_cooldown: float = 3
        self.jump_strength = 1.5


class BlueSlime(GreenSlime):
    def __init__(self, spawn_pos: [float]):
        super().__init__(spawn_pos, health=30, hit_damage=4)
        self.slime_variant = "blue"

        # Enemy attributes
        self.item_drop_chance = 0.4
        self.attack_cooldown: float = 2
        self.jump_strength = 2
        

class Goblin(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        base_health = 10
        health = min(round(base_health * (1 + spawn_pos[0] / 100 / base_health)), 30)
        super().__init__(30, spawn_pos, GOBLIN_RECT_SIZE, health=health)
        self.type = "enemy"
        self.image = "goblin"

        # Enemy attributes
        self.item_drop_chance = 0.4
        self.max_speed = 3
        self.prepare_attack_length: float = 0.5
        self.prepare_attack: float = self.prepare_attack_length

        self.holding = random.choice((Stick, Sword, Axe, Pickaxe, Bow))(1)
        if isinstance(self.holding, Bow):
            self.holding.attributes["longshot"] = 3
            self.prepare_attack_length *= 8

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

    def draw(self, window: Window):
        rect = window.camera.map_coord((self.rect.x - 1 + self.rect.w / 2, self.rect.y, 2, 2), from_world=True)
        window.draw_image("goblin_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)
        super().draw(window)

    def update(self, world, window: Window):
        super().update(world, window.delta_time)

        if self.stunned:
            self.state = "hit_ground"
            return

        if self.underWater:
            self.vel[0] *= 0.9

        holding_bow = isinstance(self.holding, Bow)
        distance_player = abs(world.player.rect.centerx - self.rect.centerx)

        if holding_bow and distance_player < 10:
            speed = 0
        else:
            speed = min(self.max_speed, distance_player)

        moving = abs(self.vel[0]) > 1
        if world.player.rect.centerx < self.rect.centerx:
            self.vel[0] = -speed
            self.direction = 1
            side_block = world.get_block(math.floor(self.rect.left - 0.6), round(self.rect.y)) and not world.get_block(math.floor(self.rect.left - 0.6), round(self.rect.y + 1))
        else:
            self.vel[0] = speed
            self.direction = 0
            side_block = world.get_block(math.floor(self.rect.right + 0.6), round(self.rect.y)) and not world.get_block(math.floor(self.rect.right + 0.6), round(self.rect.y + 1))

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
        elif moving:
            self.state = "walk"
        else:
            self.state = "idle"

        sound.play(window, "goblin", identifier=str(self.uuid), x=(self.rect.x - world.player.rect.x) / 5)

        if self.rect.collide_rect(world.player.rect) or holding_bow:
            self.prepare_attack -= window.delta_time

            if self.prepare_attack < 0:
                angle = math.atan2(world.player.rect.centery - self.rect.centery, world.player.rect.centerx - self.rect.centerx)
                if holding_bow:
                    angle += math.cos(angle) * 0.015 * distance_player
                self.holding.attack(window, world, self, angle)
                self.prepare_attack = self.prepare_attack_length
        elif not holding_bow:
            self.prepare_attack = self.prepare_attack_length


class Bat(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        base_health = 5
        health = min(round(base_health * (1 + spawn_pos[0] / 200 / base_health)), 20)
        super().__init__(30, spawn_pos, BAT_RECT_SIZE, health=health)
        self.type = "enemy"
        self.image = "bat"

        # Enemy attributes
        self.item_drop_chance = 0.2
        self.hit_damage = min(round(1 * (1 + spawn_pos[0] / 200)), 4)
        self.max_speed = 2.5
        self.prepare_attack_length: float = 4.0
        self.prepare_attack: float = self.prepare_attack_length

        # Animation states
        self.state: str = "fly"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation

        self.last_position = spawn_pos

        

    def draw(self, window: Window):
        super().draw(window)
        rect = window.camera.map_coord((self.rect.x - 0.5 + self.rect.w / 2, self.rect.y, 1, 1), from_world=True)
        window.draw_image("bat_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0), animation_offset=self.uuid)

    def move(self, world, window: Window): # pathfinding implementation
        def pathfind() -> list[int, int]:
            grid: list[list[int, int]] = []
            for y in range(world.view.shape[1]):
                grid.append([])
                for x in range(world.view.shape[0]):
                    grid[y].append(0 if world.view[x, y, 0] == 0 else 1)
            grid.reverse()

            """
            print(window.camera.pos, len(grid[0]), len(grid), str())
            offset = [window.camera.pos[0] - ((len(grid[0]) - 1) / 2), window.camera.pos[1] - ((len(grid) - 1) / 2)]  # offset between center of grid (relative) and camera_pos (absolute)
            start_pos: list[int, int] = [round(self.rect.center[i] - offset[i]) for i in range(2)]
            end_pos: list[int, int] = [round(world.player.rect.center[i] - offset[i]) for i in range(2)]
            print(start_pos, end_pos, offset, self.rect.center, world.player.rect.center)
            """
            # vector approach; flipped vector directions, now it works, don't know why
            relative_camera_pos = [len(grid[0]) // 2, len(grid) // 2]
            start_pos = [round((self.rect.center[0] - window.camera.pos[0]) + relative_camera_pos[0]), round((window.camera.pos[1] - self.rect.center[1]) + relative_camera_pos[1])]
            end_pos = [round((world.player.rect.center[0] - window.camera.pos[0]) + relative_camera_pos[0]), round((window.camera.pos[1] - world.player.rect.center[1]) + relative_camera_pos[1])]
            
            
            

            result = a_star(grid=grid, start_pos=start_pos, end_pos=end_pos, full_path=True)

            if result:
                next_pos = [(result[2][0] - relative_camera_pos[0]) + window.camera.pos[0], (relative_camera_pos[1] - result[2][1]) + window.camera.pos[1]]   # vector approach

                """
                print(relative_camera_pos, start_pos, end_pos, result[2])
                for y, _ in enumerate(grid):
                    for x, _ in enumerate(grid[y]):
                        if [x, y] == start_pos:
                            print("\x1b[41m" + " " + "\x1b[0m", end="")
                        elif [x, y] == end_pos:
                            print("\x1b[42m" + " " + "\x1b[0m", end="")
                        elif [x, y] == relative_camera_pos:
                            print("\x1b[43m" + " " + "\x1b[0m", end="")
                        elif [x, y] == result[2]:
                            print("\x1b[44m" + " " + "\x1b[0m", end="")
                        else:
                            print("\x1b[47m" + " " + "\x1b[0m" if int(grid[y][x]) == 0 else "\x1b[40m" + " " + "\x1b[0m", end="")
                    print()
                """

                return next_pos
            return None

        if math.dist(self.rect.center, world.player.rect.center) > 3:   # find path for longer distances
            """
            if not [round(_) for _ in self.rect.center] == self.last_position:
                self.last_position = [round(_) for _ in self.rect.center]
            """
            next_pos = pathfind()

            if not next_pos:
                return

            if next_pos[0] < self.rect.centerx:
                self.vel[0] = -self.max_speed
                self.direction = 1
            else:
                self.vel[0] = self.max_speed
                self.direction = 0
            
            if next_pos[1] < self.rect.centery:
                self.vel[1] = -self.max_speed
            else:
                self.vel[1] = self.max_speed

        
        else:
            speed_x = min(self.max_speed, abs(world.player.rect.centerx - self.rect.centerx))
            if world.player.rect.centerx < self.rect.centerx:
                self.vel[0] = -speed_x
                self.direction = 1
            else:
                self.vel[0] = speed_x
                self.direction = 0

        y_offset = self.prepare_attack * 2
        speed_y = min(self.max_speed, abs(world.player.rect.centery + y_offset - self.rect.centery))
        if world.player.rect.centery + y_offset < self.rect.centery and not self.underWater:
            self.vel[1] = -speed_y
        else:
            self.vel[1] = speed_y

    def update(self, world, window: Window):
        super().update(world, window.delta_time)

        if self.stunned:
            return
          
        self.move(world, window)

        # Attack
        if self.rect.collide_rect(world.player.rect) and self.prepare_attack < 0:
            world.player.damage(window, self.hit_damage, self.vel)
            self.prepare_attack = self.prepare_attack_length
        elif self.prepare_attack >= 0:
            self.prepare_attack -= window.delta_time

        if not random.randint(0, int(window.fps * 10)):
            sound.play(window, "bat_fly", identifier=str(self.uuid), x=(self.rect.x - world.player.rect.x) / 5)
        elif not random.randint(0, int(window.fps * 10)):
            sound.play(window, "bat_scream", identifier=str(self.uuid), x=(self.rect.x - world.player.rect.x) / 5)
