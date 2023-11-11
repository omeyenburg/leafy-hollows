# -*- coding: utf-8 -*-
from scripts.game.baseentity import LivingEntity
from scripts.graphics.window import Window
from scripts.utility.const import *
from scripts.game.physics import *
from scripts.game.entity import *
from scripts.graphics import sound
import random


class Player(LivingEntity):
    def __init__(self, spawn_pos: [float]):
        super().__init__(50, spawn_pos, PLAYER_RECT_SIZE_NORMAL, health=10)

        # Player rect size (based on state)
        self.rect_size = PLAYER_RECT_SIZE_NORMAL
        self.rect_size_crouch = PLAYER_RECT_SIZE_CROUCH
        self.rect_size_swim = PLAYER_RECT_SIZE_SWIM

        # Player speed (based on state)
        self.walk_speed: float = 4
        self.sprint_speed: float = 6
        self.crouch_speed: float = 2
        self.swim_speed: float = 3

        # Physics attributes
        self.acceleration_time: float = 0.1
        self.jump_force: int = 23
        self.on_pole: bool = False

        # Animation states
        self.state: str = "idle"    # state is used for movement & animations
        self.direction: int = 0     # 0 -> right; 1 -> left
        self.hit_ground = 0         # Used for hit ground animation
        self.can_move: bool = False # Disabled during intro

        # Long crouch jump
        self.charge_crouch_jump: float = 0

    def draw(self, window: Window):
        """
        Draw the player.
        """
        # Draw hitbox
        #rect = window.camera.map_coord((self.rect.x, self.rect.y, self.rect.w, self.rect.h), from_world=True)
        #window.draw_rect(rect[:2], rect[2:], (255, 0, 0, 100))

        # Draw player
        rect = window.camera.map_coord((self.rect.x - 1 + self.rect.w / 2, self.rect.y, 2, 2), from_world=True)
        window.draw_image("player_" + self.state, rect[:2], rect[2:], flip=(self.direction, 0))

    def move_normal(self, world, window: Window):
        """
        Move player: idle, walk, crouch and jump
        """
        if not self.can_move:
            return # Movement disabled during intro

        # Friction
        block_fricton = world.get_block_friction(self.block_below)

        # Walking
        key_right = window.keybind("right")
        key_left = window.keybind("left")

        # Set max speed
        max_speed = self.walk_speed
        if window.keybind("sprint"): # Keeps sprinting once key pressed / stops faster as long as pressed
            max_speed = self.sprint_speed
        if self.state == "crouch":
            max_speed = self.crouch_speed
        if self.inWater:
            max_speed *= 0.7
        if self.underWater:
            max_speed /= 2

        # Set current speed
        acceleration_speed = max_speed * block_fricton * self.acceleration_time * (1 + block_fricton)

        # Adjust movement in air
        if not (self.block_below or self.block_right or self.block_left):
            max_speed = 0
            if PHYSICS_REALISTIC or PHYSICS_PREVENT_MOVEMENT_IN_AIR or not (key_right and key_left):
                acceleration_speed = 0    # Stop movement while in air
            else:
                acceleration_speed *= 0.1 # Reduced control in air

        # Apply acceleration to the right
        if key_right and self.vel[0] < max_speed:
            if self.vel[0] + acceleration_speed > max_speed: # Guaranteeing exact max speed
                self.vel[0] = max_speed
            else:
                self.vel[0] += acceleration_speed

        # Apply acceleration to the left
        if key_left and self.vel[0] > -max_speed:
            if self.vel[0] - acceleration_speed < -max_speed: # Guaranteeing exact max speed
                self.vel[0] = -max_speed
            else:
                self.vel[0] -= acceleration_speed

        # Adjust animation
        if self.block_below and abs(self.vel[0]) > 1 and not (self.block_right or self.block_left):
            if self.state == "crouch":
                self.state = "crawl"
            elif window.keybind("sprint"):
                self.state = "sprint"
            else:
                self.state = "walk"
        
        # Friction
        acceleration_speed *= window.delta_time * block_fricton * 10
        if abs(self.vel[0]) <= acceleration_speed:
            self.vel[0] = 0
        else:
            if self.vel[0] > 0:
                self.vel[0] -= acceleration_speed
            else:
                self.vel[0] += acceleration_speed
        if not (key_right or key_left):
            self.vel[0] *= 0.99

        # Jumping
        if window.keybind("jump") and (self.block_below or self.block_right and key_left or self.block_left and key_right):
            if self.state == "crouch" and self.block_below:
                # Charge crouch jump
                self.charge_crouch_jump += window.delta_time
            elif not self.charge_crouch_jump:
                # Normal jump
                self.jump(window, 5)
        elif self.block_below and self.charge_crouch_jump and self.state == "crouch":
            # Crouch jump
            self.jump(window, 5 * min(1, self.charge_crouch_jump)) # 1 second to charge max crouch jump
            self.charge_crouch_jump = 0
            self.block_below = 0
        else:
            # Reset crouch jump charge
            self.charge_crouch_jump = 0

    def move_under_water(self, world, window: Window):
        """
        Swimming under water.
        """
        if window.keybind("jump") and self.vel[1] < self.swim_speed:
            self.vel[1] += 1
            if self.block_right or self.block_left:
                self.vel[1] += 3
        elif window.keybind("crouch") and -self.vel[1] < self.swim_speed:
            self.vel[1] -= 1
        if window.keybind("right") and self.vel[0] < self.swim_speed:
            self.vel[0] += 1
        if window.keybind("left") and -self.vel[0] < self.swim_speed:
            self.vel[0] -= 1

        # Water resistance
        self.vel[0] *= 0.6
        self.vel[1] *= 0.7

    def move_climb(self, world, window: Window):
        """
        Climb poles and vines.
        """
        block_feet = world.get_block(round(self.rect.x), round(self.rect.y + 0.8), layer=2)
        block_head = world.get_block(round(self.rect.x), round(self.rect.y - 0.2), layer=2)
        grab_pole = block_feet in world.blocks_climbable
        on_pole = block_head in world.blocks_climbable or grab_pole

        if window.keybind("jump") and (on_pole or grab_pole):
            self.on_pole = True
            if (window.keybind("left") or window.keybind("right")) and on_pole:
                if abs(self.vel[0]) < 1:
                    if window.keybind("right"):
                        self.direction = 0
                        self.vel[0] += 10 * window.delta_time ** 0.2
                    else:
                        self.direction = 1
                        self.vel[0] -= 10 * window.delta_time ** 0.2
                    self.vel[1] = 5
            elif grab_pole and not window.keybind("crouch"):
                self.rect.x = round(self.rect.x)
                self.vel[0] = 0
                self.vel[1] = max(2, self.vel[1])
                self.state = "climb_pole"
            elif (not grab_pole) or window.keybind("crouch"):
                self.rect.x = round(self.rect.x)
                self.vel[0] = 0
                self.vel[1] = max(0.15, self.vel[1])
                self.state = "on_pole"
        else:
            self.on_pole = False
        
    def animation_normal(self, world, window: Window):
        """
        Normal and crouch animations.
        """
        # Block_coords
        wall_block_right = (round(self.rect.x + 0.8), round(self.rect.y + 1))
        wall_block_left = (round(self.rect.x - 0.8), round(self.rect.y + 1))
        wall_block_top_right = (round(self.rect.x + 0.8), round(self.rect.y + 1.3))
        wall_block_top_left = (round(self.rect.x - 0.8), round(self.rect.y + 1.3))

        key_right = window.keybind("right")
        key_left = window.keybind("left")

        # Animation states
        if self.vel[1] < -5:
            # Fall
            self.state = "fall"
            self.hit_ground = 0.3
        elif self.block_below and window.keybind("crouch"):
            # Crouch
            self.state = "crouch"
        elif self.block_below:
            # Idle
            if self.hit_ground > 0:
                self.hit_ground -= window.delta_time
                self.state = "hit_ground"
            else:
                self.state = "idle"
        elif (key_right and self.block_right and world.get_block(*wall_block_right) or
              key_left and self.block_left and world.get_block(*wall_block_left)) and not self.block_below:
            # On Wall
            self.state = "climb"
            if self.vel[1] < 0:
                self.vel[1] /= 2

            if (world.get_block(*wall_block_right) and
               not world.get_block(wall_block_right[0], round(self.rect.y + 1.3)) or
               world.get_block(*wall_block_left) and
               not world.get_block(wall_block_left[0], round(self.rect.y + 1.3))):
                # On upper edge of wall
                self.rect.bottom = round(self.rect.bottom)
                self.vel[1] = max(self.vel[1], 0)

                if window.keybind("jump") == 1:
                    self.vel[1] = 7
                    self.state = "high_jump"
                    self.rect.y = math.ceil(self.rect.y)
                    if self.direction:
                        self.vel[0] = -1
                    else:
                        self.vel[0] = 1

        elif self.vel[1] > 0 and self.state != "crouch_jump":
            # Crouch jump
            if ((abs(self.vel[0]) > 2 or self.state == "jump") and
                not (world.get_block(*wall_block_right) and world.get_block(*wall_block_left))):
                self.state = "jump"
            else:
                self.state = "high_jump"
        elif self.vel[1] < 0 and self.state != "crouch_jump":
            # Slow fall
            self.state = "fall_slow"  
        #print(f"{round(self.vel[1], 2): 5}", key_right, self.block_right, world.get_block(*wall_block_right))
        #window.draw_block_highlight(*wall_block_right)
        #window.draw_block_highlight(*wall_block_top_right, (0, 255, 0, 100))
        #window.draw_circle(window.camera.map_coord((self.rect.centerx, self.rect.bottom), from_world=True), 0.01, (255, 0, 0, 100))

    def animation_under_water(self, world, window: Window):
        """
        Player animation under water.
        """
        if abs(self.vel[1]) < abs(self.vel[0]) > 0.5:
            self.state = "swim"
        elif self.vel[1] > 0.5:
            self.state = "dive_up"
        elif window.keybind("crouch"):
            self.state = "dive_down"
        else:
            self.state = "float"

    def sounds_normal(self, world, window: Window):
        """
        Play walking sounds.
        """
        ground_block_coord = (round(self.rect.centerx), round(self.rect.top - 1))
        ground_block = world.get_block(*ground_block_coord)
        sound_file = ""

        if self.state == "sprint":
            if ground_block == world.block_name["grass_block"]:
                sound_file = "player_run_grass"
            elif ground_block == world.block_name["stone_block"]:
                sound_file = "player_run_stone"
        else:
            if ground_block in (world.block_name["grass_block"], world.block_name["dirt_block"]):
                sound_file = "player_walk_grass"
            elif ground_block == world.block_name["stone_block"]:
                sound_file = "player_walk_stone"

        if sound_file:
            volume = min(1, (abs(self.vel[0]) + abs(self.vel[1])) / 8)
            sound.play(window, sound_file, channel_volume=volume)

    def sounds_under_water(self, world, window: Window):
        """
        Play swimming sounds.
        """
        speed = abs(self.vel[0]) + abs(self.vel[1])
        if speed > 0.5:
            sound.play(window, "player_swim", channel_volume=min(1, speed))

    def jump(self, window, strength: float):
        """
        Jumping: normal jump, crouch jump and wall jump
        """
        force = self.jump_force * strength
         
        if self.direction == 1 and self.charge_crouch_jump and not window.keybind("left"):
            # Crouch jump left
            self.apply_force(force * 7, 160, 1)
            self.state = "crouch_jump"
            self.block_below = 0
            sound.play(window, "player_hit_ground")
        elif self.direction == 0 and self.charge_crouch_jump and not window.keybind("right"):
            # Crouch jump right
            self.apply_force(force * 7, 20, 1)
            self.state = "crouch_jump"
            self.block_below = 0
            sound.play(window, "player_hit_ground")
        elif self.block_below:
            # Normal jump
            self.apply_force(force * 2.8, 90, 1)
            self.block_below = 0
        elif self.vel[1] > 2:
            # Max wall jump velocity
            pass
        elif self.block_right and window.keybind("left"):
            # Wall jump left
            self.apply_force(force * 2.6, 120, 1)
            self.block_right = 0
            sound.play(window, "player_hit_ground")
        elif self.block_left and window.keybind("right"):
            # Wall jump right
            self.apply_force(force * 2.6, 60, 1)
            self.block_left = 0
            sound.play(window, "player_hit_ground")

    def adjust_hitbox(self, world):
        """
        Swap states between normal and crouching and change hitbox size.
        """
        if self.state in ("crouch", "crouch_jump", "crawl"):
            if self.rect.size != self.rect_size_crouch:
                self.rect.x += (self.rect_size[0] - self.rect_size_crouch[0]) / 2
                self.rect.size = self.rect_size_crouch
            if self.get_collision(world):
                self.rect.x += (self.rect_size_crouch[0] - self.rect_size[0]) / 2
                self.rect.size = self.rect_size
                self.state = {
                    "crouch_jump": "fall",
                    "crawl": "walk"
                }.get(self.state, "idle")
        else:
            if self.rect.size != self.rect_size:
                self.rect.x += (self.rect_size_crouch[0] - self.rect_size[0]) / 2
                self.rect.size = self.rect_size
            if self.get_collision(world):
                self.rect.x += (self.rect_size[0] - self.rect_size_crouch[0]) / 2
                self.rect.size = self.rect_size_crouch
                self.state = {
                    "jump": "crouch_jump",
                    "jump_high": "crouch_jump",
                    "walk": "crawl",
                    "sprint": "crawl"
                }.get(self.state, "crouch")

    def move(self, world, window: Window):
        """
        Move player and play sounds and set animations.
        """
        # Set player direction
        if self.vel[0] > 0.2:
            self.direction = 0
        elif self.vel[0] < -0.2:
            self.direction = 1

        if self.underWater and not self.block_below:
            # Under water movement
            self.move_under_water(world, window)
            self.animation_under_water(world, window)
            self.sounds_under_water(world, window)
        else:
            if self.inWater:
                # Walk through water sounds
                self.sounds_under_water(world, window)

            # Try to climb
            self.move_climb(world, window)
            
            if not self.on_pole:
                # Normal movement
                self.animation_normal(world, window)
                self.move_normal(world, window)
                self.sounds_normal(world, window)
        
        # Resize hitbox if necessary
        self.adjust_hitbox(world)

    def mouse_inputs(self, world, window: Window):
        """
        Gather mouse inputs to place/break blocks.
        """

        # Mouse pull
        """
        if window.mouse_buttons[0] == 1: # left click: pull player to mouse
            def mouse_pull(strenght):
                mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            
                delta_x, delta_y = mouse_pos[0] - self.rect.centerx, mouse_pos[1] - self.rect.centery
                angle_to_mouse = math.degrees(math.atan2(delta_y, delta_x))

                force = min(math.dist(self.rect.center, mouse_pos), 3) / window.delta_time * strenght
                self.apply_force(force, angle_to_mouse, window.delta_time)
            mouse_pull(300) # constant activation balances out w/ gravity --> usable as rope
        """

        # Spawn particle
        """
        if window.mouse_buttons[1] == 1: # middle click: spawn particle
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            spawn_particle(mouse_pos)
        """

        # Place/break block
        """
        if window.mouse_buttons[2] == 1: # right click: place/break block
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            if world.get_block(math.floor(mouse_pos[0]), math.floor(mouse_pos[1])) > 0:
                world.set_block(math.floor(mouse_pos[0]), math.floor(mouse_pos[1]), 0)
            else:
                world.set_block(math.floor(mouse_pos[0]), math.floor(mouse_pos[1]), world.block_name["stone_block"])


        """
        if window.mouse_buttons[2] == 1: # right click: place/break block
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            world.add_entity(Slime(mouse_pos))
        """

        # Place water
        if window.mouse_buttons[2] == 1: # place water
            mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
            water_level = world.get_water(math.floor(mouse_pos[0]), math.floor(mouse_pos[1]))
            world.set_water(math.floor(mouse_pos[0]), math.floor(mouse_pos[1]), water_level + 1000)
        """

    def update(self, world, window: Window):
        self.move(world, window)
        super().update(world, window.delta_time)
        self.mouse_inputs(world, window)

        "Minecraft-like shifting (not working)"
        #last_position = self.rect.topleft if window.keybind("crouch") and not (world.get_block(math.floor(self.rect.left), int(self.rect.bottom - 1)) or world.get_block(math.ceil(self.rect.right), int(self.rect.bottom - 1))) else None
        #super().update(world, window.delta_time)
        #if (not last_position is None) and (self.rect.y < last_position[1] or world.get_block(math.floor(self.rect.left), int(self.rect.bottom - 1)) or world.get_block(math.ceil(self.rect.right), int(self.rect.bottom - 1))):
        #    self.rect.topleft = last_position
        # or
        #last_position = self.rect.topleft if self.state in ("crawl", "crouch") and (world.get_block(math.floor(self.rect.left), int(self.rect.top - 1)) and self.direction == 0 or world.get_block(math.ceil(self.rect.right) - 1, int(self.rect.top - 1)) and self.direction == 1) else None
        #super().update(world, window.delta_time)
        #if (not last_position is None) and (world.get_block(math.floor(self.rect.left), int(self.rect.top - 1)) == 0 and self.direction == 0 or world.get_block(math.ceil(self.rect.right) - 1, int(self.rect.top - 1)) == 0 and self.direction == 1):
        #    self.rect.topleft = last_position
        

        "Physics particles"
        #for particle in particle_list:
        #    particle.update(world, window.delta_time)
        #    tmp_draw_rect(window, particle.rect.topleft, [particle.rect.w, particle.rect.h], (0, 255, 255))

"Physics particles"
#def spawn_particle(pos: list[float, float]):
#    particle_list.append(PhysicsObject(10, pos, [0.5, 0.5]))
#def tmp_draw_rect(window: Window, pos: [float, float], size: [float, float], color: [int, int, int]):
#    rect = window.camera.map_coord((pos[0], pos[1], size[0], size[1]), from_world=True)
#    window.draw_rect(rect[:2], rect[2:], color)
#particle_list: list = []
