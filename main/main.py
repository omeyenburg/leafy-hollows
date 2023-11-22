# -*- coding: utf-8 -*-
from scripts.graphics.image import load_blocks
from scripts.utility.thread import threaded
from scripts.graphics.window import Window
from scripts.utility.geometry import *
from scripts.game.world import World
from scripts.utility.const import *
from scripts.menu.menu import Menu
from scripts.utility import file
import math


# Setup
caption = "Title"
*block_data, block_atlas_image = load_blocks()
window: Window = Window(caption, block_data[0], block_atlas_image)
menu: Menu = Menu(window)
world: World = None
menu.load_threaded("Title", "menu", window.setup)
menu.main_page.open()


def save_world():
    global world
    window.clear_world()
    
    if menu.game_state in ("game", "intro", "pause", "inventory", "fuse") and not world is None:
        menu.load_threaded("Saving world", "save_world", world.save, window)
        del world


def load_world():
    global world

    world = menu.load_threaded("Loading world", "load_world", World.load, window, block_data, wait=True)

    if world.player.rect.x == 0:
        menu.game_state = "intro"
        window.camera.pos[1] = 50
        world.player.vel[1] = 5
        window.camera.set_zoom(CAMERA_RESOLUTION_INTRO)
    else:
        menu.game_state = "game"
        window.camera.dest = list(world.player.rect.center)
        window.camera.pos = list(world.player.rect.center)
        window.camera.set_zoom(CAMERA_RESOLUTION_GAME)


def draw_game():
    # Draw all world objects
    world.draw(window)

    # Draw foreground blocks & post processing
    window.draw_post_processing()

    # Write fps
    if window.options["show fps"]:
        window.draw_text(
            (-0.98, 0.95),
            "FPS: " + str(round(window.fps, 3)),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        y_offset = 0.1
    else:
        y_offset = 0

    # Write debug info
    if window.options["show debug"]:
        mouse_pos = window.camera.map_coord(window.mouse_pos[:2], from_pixel=1, world=1)
        window.draw_text(
            (-0.98, 0.95 - y_offset),
            "Player Pos: " + str((round(world.player.rect.centerx, 1),
            round(world.player.rect.centery, 1))),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.85 - y_offset),
            "Player Speed: " + str(tuple(map(lambda n: round(n, 1), world.player.vel))),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.75 - y_offset),
            "Mouse Pos: " + str((math.floor(mouse_pos[0]),
            math.floor(mouse_pos[1]))),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.65 - y_offset),
            "Seed: " + str(world.seed),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.55 - y_offset),
            "Mouse Block: " + str(world.get_block(
                math.floor(mouse_pos[0]),
                math.floor(mouse_pos[1]),
                layer=slice(None) 
            )),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.45 - y_offset),
            "Below Player: " + str(world.player.block_below),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.35 - y_offset),
            "Player State: " + world.player.state,
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.25 - y_offset),
            "Left to Player: " + str(world.player.block_left),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.15 - y_offset),
            "Right to Player: " + str(world.player.block_right),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.05 - y_offset),
            "Entity count: " + str(len(world.entities)),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, -0.05 - y_offset),
            "Loaded entity count: " + str(len(world.loaded_entities)),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )

    if menu.game_state != "intro" and not (world.player.rect.x == 0 and menu.game_state == "pause"):
        # Draw player health bar
        health_percentage = world.player.health / world.player.max_health
        heart_center = Vec(-0.9, -0.9)
        heart_width = 0.1
        heart_size = Vec(heart_width, heart_width / window.height * window.width / 7 * 6)
        health_bar_size = Vec(0.5, 0.05)

        window.draw_image("heart", heart_center - heart_size / 2, heart_size)
        window.draw_rect(heart_center + Vec(heart_size.x * 0.8, -health_bar_size.y / 2), (0.5 * health_percentage, 0.05), (165, 48, 48, 255))
        window.draw_rect(heart_center + Vec(heart_size.x * 0.8 + 0.5 * health_percentage, -health_bar_size.y / 2), (0.5 * (1 - health_percentage), 0.05), (56, 29, 49, 255))

        # Draw weapon
        weapon = world.player.holding
        if not weapon is None:
            weapon = weapon.image

            weapon_pos = (0.8, -0.9)
            weapon_size = Vec(0.2, 0.2 / window.height * window.width)
            window.draw_image(weapon, weapon_pos, weapon_size, angle=30)


def draw_intro():
    # Draw intro text
    intro_texts = menu.get_intro_texts()

    intro_text_position = (-world.player.rect.centery / INTRO_LENGTH - 0.01) * 1.12
    if 0 < intro_text_position < 1:
        skip_text = menu.translate("Press [%s] to skip intro")
        window.draw_text(
            (-0.95, -0.9),
            skip_text % window.options['key.jump'].title(),
            (255, 255, 255),
            0.14
        )

        intro_text_index = int(intro_text_position * len(intro_texts))
        intro_text_fract = (intro_text_position * len(intro_texts)) % 1
        intro_text_size = 0.5 if intro_text_index == 0 else 0.16
        text_y = 2 * (2 * intro_text_fract - 1) ** 21
        intro_text = intro_texts[intro_text_index].split("\n")
        for i, text in enumerate(intro_text):
            window.draw_text(
                (0.6, text_y - (i - len(intro_text) / 2) * 0.1),
                text,
                (255, 255, 255),
                intro_text_size,
                centered=True
            )


def update_intro():
    # Move camera
    camera_move_pos = (0, world.player.rect.centery - world.player.vel[0] / 100)
    window.camera.move(camera_move_pos)

    # Update window + shader
    window.update()
    window.camera.update()

    # Skip intro
    intro_text_position = (-world.player.rect.centery / INTRO_LENGTH - 0.01) * 1.12
    if window.keybind("jump") == 1 and intro_text_position < 0.95:
        original = world.player.rect.y
        world.player.rect.y = min(
            world.player.rect.y,
            -INTRO_LENGTH + INTRO_REPEAT + world.player.rect.y % INTRO_REPEAT
        )
        window.camera.pos[1] += world.player.rect.y - original

    # Pause
    if window.keybind("return") == 1:
        menu.pause_page.open()
        menu.game_state = "pause"
        menu.game_intro = True
        window.effects["gray_screen"] = 1

    # End intro
    if world.player.block_below:
        window.camera.zoom(CAMERA_RESOLUTION_GAME, 100.0)
        menu.game_state = "game"
        world.player.can_move = True


def update_inventory():
    window.draw_text((-0.95, -0.55), "Sort by:\nAge      Level      Type", (255, 255, 255), 0.2)
    if "\x08" in window.unicode and len(menu.inventory_page.search_text):
        menu.inventory_page.search_text = menu.inventory_page.search_text[:len(menu.inventory_page.search_text) - 1]
    else:
        menu.inventory_page.search_text += window.unicode
    
    if menu.inventory_page.search_text:
        window.draw_text((-0.95, -0.85), menu.inventory_page.search_text, (255, 255, 255), 0.2)
    else:
        window.draw_text((-0.95, -0.85), "Search...", (100, 100, 100), 0.2)


    inventory = list(filter(
        lambda i:
        menu.inventory_page.search_text.lower() in i.image or
        any([
            menu.inventory_page.search_text in attribute or
            menu.inventory_page.search_text in ATTRIBUTE_DESCRIPTIONS[attribute]
            for attribute in i.attributes
        ]),
        world.player.inventory
    ))

    if not len(inventory):
        return

    scroll_speed = 20
    window.mouse_wheel[1] = min(max(window.mouse_wheel[1], 0), len(inventory) * scroll_speed - scroll_speed)
    scroll_position = window.mouse_wheel[1] / scroll_speed
    if not window.mouse_wheel[3]:
        window.mouse_wheel[1] += (round(scroll_position) - scroll_position) * scroll_speed * 0.02

    weapon_y = 0.5
    weapon_positions = []
    for i, weapon in enumerate(inventory):
        weapon_size = Vec(0.4, 0.4 / window.height * window.width) * max(0.5, 1 / ((i - scroll_position) ** 2 + 1))
        weapon_y -= weapon_size[1]
        weapon_positions.append(weapon_y)

    distance = abs(math.floor(scroll_position) - scroll_position)
    weapon_center_y = (1 - distance) * weapon_positions[math.floor(scroll_position)] + distance * weapon_positions[math.ceil(scroll_position)]

    for i, weapon in enumerate(inventory):
        weapon_size = Vec(0.4, 0.4 / window.height * window.width) * max(0, 1 / ((i - scroll_position) ** 4 + 1))
        weapon_pos = (-0.2 - weapon_size[0] / 2, weapon_positions[i] - weapon_center_y)
        window.draw_image(weapon.image, weapon_pos, weapon_size, angle=30)

    weapon = inventory[round(scroll_position)]
    if not weapon is None:

        description_y = 0.8
        description_y += window.draw_text((0, description_y), weapon.image.title(), (255, 255, 255), 0.3)[1]
        
        for stat in ("damage", "attack_speed", "range", "crit_chance"):
            stat_name = stat.title().replace("_", " ")
            description_y -= abs(window.draw_text((0, description_y), f"{stat_name}: {weapon.__dict__[stat]}", (164, 221, 219), 0.17, wrap=1)[1]) * 6

        for i, (attribute, level) in enumerate(weapon.attributes.items()):
            description_y = -0.6 * i + 0.1
            description = ATTRIBUTE_DESCRIPTIONS[attribute] % (ATTRIBUTE_BASE_MODIFIERS[attribute] * level)
            window.draw_text((0, description_y), f"{attribute.title()} {INT_TO_ROMAN[level]}: {description}", (223, 132, 165), 0.17, wrap=1)

        window.draw_text((0.75, 0.85), "Equip", (255, 255, 255), 0.2)
        window.draw_text((0.75, 0.7), "Fuse", (255, 255, 255), 0.2)
        window.draw_text((0.75, 0.55), "Destroy", (255, 255, 255), 0.2)


def main():
    menu.save_world = save_world
    window.callback_quit = save_world
    window.camera.set_zoom(CAMERA_RESOLUTION_GAME)

    while True:
        if menu.game_state == "load_world":
            window.camera.reset()
            load_world()

        elif menu.game_state == "intro":
            window.camera.set_zoom(CAMERA_RESOLUTION_INTRO)
            world.update(window)
            draw_game()
            draw_intro()
            update_intro()

        elif menu.game_state == "game":
            # Draw and update the game
            draw_game()
            world.update(window)

            # Update and draw the menu
            window.update()
            window.camera.update()

            # Move camera
            camera_pos = (
                world.player.rect.centerx + world.player.vel[0] * 0.1,
                world.player.rect.centery + world.player.vel[1] * 0.1
            )

            if not window.options["reduce camera movement"]:
                mouse_pos = window.camera.map_coord(window.mouse_pos[:2], world=True)
                camera_pos = (
                    (camera_pos[0] * 0.8 + mouse_pos[0] * 0.2),
                    (camera_pos[1] * 0.8 + mouse_pos[1] * 0.2)
                )
                window.camera.shift_x((-world.player.direction + 0.5) * 50)
            window.camera.move(camera_pos)

            # Pause
            if window.keybind("return") == 1:
                menu.pause_page.open()
                menu.game_state = "pause"

            # Inventory
            if window.keybind("inventory") == 1:
                menu.inventory_page.open()
                menu.game_state = "inventory"

            # Death
            if world.player.health <= 0:
                file.delete("data/user/world.data")
                menu.death_page.open()
                menu.game_state = "death"

        elif menu.game_state in ("pause", "death", "inventory"):
            # Draw world
            draw_game()

            # Draw menu
            if menu.game_intro:
                draw_intro()
            window.draw_rect((-1, -1), (2, 2), (0, 0, 0, 200))

            # Update and draw the menu
            menu.update()
            if menu.game_state == "inventory":
                update_inventory()

            # Update window + shader
            window.update()

            # Game
            if window.keybind("return") == 1 or window.keybind("inventory") == 1:
                if menu.game_state in ("pause", "inventory"):
                    if menu.game_intro:
                        menu.game_state = "intro"
                        menu.game_intro = False
                    else:
                        menu.game_state = "game"
                else:
                    menu.main_page.open()
                    menu.game_state = "menu"

        else:
            # Update and draw the menu
            window.clear_world()
            menu.update()

            # Write fps
            if window.options["show fps"]:
                window.draw_text(
                    (-0.98, 0.95),
                    str(round(window.fps, 3)),
                    (250, 250, 250, 200),
                    size=TEXT_SIZE_DESCRIPTION
                )

            # Update window + shader
            window.update()


if __name__ == "__main__":
    main()

    # Profiler
    #import cProfile
    #cProfile.run('main()')
