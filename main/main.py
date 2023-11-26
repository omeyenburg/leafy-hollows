# -*- coding: utf-8 -*-
from scripts.utility.noise_functions import pnoise1, snoise2
from scripts.graphics.image import load_blocks
from scripts.utility.thread import threaded
from scripts.graphics.window import Window
from scripts.utility.geometry import *
from scripts.game.world import World
from scripts.utility.const import *
from scripts.menu.menu import Menu
from scripts.utility import file
import pprint


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
            "FPS: " + str(round(window.average_fps, 3)),
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
            weapon_pos = (0.8, -0.9)
            weapon_size = Vec(0.2, 0.2 / window.height * window.width)
            window.draw_image(weapon.image, weapon_pos, weapon_size, angle=weapon.angle)
            
            if weapon.image == "bow":
                arrow_text = f"{world.player.inventory.arrows}/{world.player.inventory.max_arrows}"
                window.draw_text((0.75, -0.42), arrow_text, (255, 255, 255), 0.17)
                window.draw_image("arrow_item", (0.9, -0.5), (0.1, 0.1 / window.height * window.width), angle=0)
                

        if world.player.recent_drop[0] > 0:
            world.player.recent_drop[0] -= window.delta_time
            drop_y = max(0.8, 1 - world.player.recent_drop[0])
            if world.player.recent_drop[1] == "arrows":
                window.draw_text((0.8, drop_y + 0.05 / window.height * window.width), "+" + str(world.player.recent_drop[2]), (255, 255, 255), 0.25)
                window.draw_image("arrow_item", (0.9, drop_y), (0.1, 0.1 / window.height * window.width), angle=0)
            else:
                window.draw_text((0.85, drop_y + 0.05 / window.height * window.width), "+", (255, 255, 255), 0.25)
                window.draw_image(world.player.recent_drop[1].image, (0.9, drop_y), (0.1, 0.1 / window.height * window.width), angle=world.player.recent_drop[1].angle)
                

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
    window.update(world.player.rect.center)
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


def update_game_camera():
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
    window.camera.update()


def main():
    menu.save_world = save_world
    window.callback_quit = save_world
    window.camera.set_zoom(CAMERA_RESOLUTION_GAME)
    #menu.game_state = "testing"

    if menu.game_state == "testing":
        time_paused = False
        flip_direction = False
        unique_stepping = False
        entity = "goblin"
        state = "walk"
        image = entity + "_" + state
        frames, speed = window.sprites[image]

        animation_path = file.find("data/images/sprites", image + "_.json", True, True)
        animation_data = file.load(animation_path, file_format="json")
        frame_names = animation_data["frames"]
        unique_frames = sorted(set(frame_names), key=lambda i: (len(i), i))
        unique_frame_indices = [frame_names.index(f) for f in unique_frames]
        current_unique_frame_index = 0

        item_positions = [[0, 0, 0] for _ in unique_frames]
        item_selected = False
        item_image = "sword"
        item_shown = False

    while True:
        if menu.game_state == "testing":
            if "p" in window.unicode:
                time_paused = not time_paused
                unique_stepping = False
            if "d" in window.unicode:
                flip_direction = not flip_direction
            if "0" in window.unicode:
                window.time = 0
            if "u" in window.unicode:
                unique_stepping = not unique_stepping
                time_paused = False
            if "+" in window.unicode:
                current_unique_frame_index = (current_unique_frame_index + 1) % len(unique_frames)
            if "-" in window.unicode:
                current_unique_frame_index = (current_unique_frame_index - 1) % len(unique_frames)
            if "i" in window.unicode:
                item_shown = not item_shown
            if "o" in window.unicode:
                print_positions = []
                pre_print_positions = []

                for p_frame_name in frame_names:
                    p_unique_index = unique_frames.index(p_frame_name)
                    pre_print_positions.append(item_positions[p_unique_index])

                last_position = pre_print_positions[-1]

                for i, current_position in enumerate(pre_print_positions):
                    previous_position = pre_print_positions[i - 1]
                    next_position = pre_print_positions[(i + 1) % len(pre_print_positions)]

                    interpolated_x = round((previous_position[0] + current_position[0] * 10 + next_position[0]) / 12, 4)
                    interpolated_y = round((previous_position[1] + current_position[1] * 10 + next_position[1]) / 12, 4)
                    interpolated_a = round((previous_position[2] + current_position[2] * 10 + next_position[2]) / 12, 4)

                    last_position = [interpolated_x, interpolated_y, interpolated_a]
                    print_positions.append([interpolated_x, interpolated_y, interpolated_a])
                
                pprint.pprint(print_positions)

            if unique_stepping:
                window.time = (unique_frame_indices[current_unique_frame_index] + 0.01) * speed

            rect = window.camera.map_coord((-1, -1, 2, 2), from_world=True)
            window.draw_image(image, rect[:2], rect[2:], flip=(flip_direction, 0))

            if item_shown:
                rect = Rect(*window.camera.map_coord((item_positions[current_unique_frame_index][0] - 0.3, item_positions[current_unique_frame_index][1] - 0.3, 0.6, 0.6), from_world=True))
                if unique_stepping and rect.collide_point(Vec(window.mouse_pos[0] / window.width, window.mouse_pos[1] / window.height) * 2) and (2 in window.mouse_buttons or any(window.mouse_buttons) and item_selected):
                    item_selected = True
                    item_positions[current_unique_frame_index][0] += window.mouse_pos[2] / WORLD_BLOCK_SIZE / 2
                    item_positions[current_unique_frame_index][1] += window.mouse_pos[3] / WORLD_BLOCK_SIZE / 2
                else:
                    item_selected = False
                window.draw_image(item_image, rect[:2], rect[2:], flip=(not flip_direction, 0), angle=item_positions[current_unique_frame_index][2])
                if "q" in window.unicode:
                    item_positions[current_unique_frame_index][2] = (item_positions[current_unique_frame_index][2] + 1) % 360
                if "e" in window.unicode:
                    item_positions[current_unique_frame_index][2] = (item_positions[current_unique_frame_index][2] - 1) % 360
                if "Q" in window.unicode:
                    item_positions[current_unique_frame_index][2] = (item_positions[current_unique_frame_index][2] + 10) % 360
                if "E" in window.unicode:
                    item_positions[current_unique_frame_index][2] = (item_positions[current_unique_frame_index][2] - 10) % 360

            if unique_stepping:
                window.draw_text((-0.98, 0.9), str(current_unique_frame_index), (255, 255, 255), 0.2)
                window.draw_text((-0.98, 0.75), str(unique_frames[current_unique_frame_index]), (255, 255, 255), 0.2)
            else:
                if speed != 0 and len(frames) >= 0:
                    index = int(window.time // speed % len(frames))
                else:
                    index = 0
                window.draw_text((-0.98, 0.9), str(index), (255, 255, 255), 0.2)
                window.draw_text((-0.98, 0.75), str(frames[index]), (255, 255, 255), 0.2)
                window.draw_text((-0.98, 0.6), frame_names[index], (255, 255, 255), 0.2)

            last_time = window.time
            window.mouse_pos = (*window.mouse_pos[:2], 0, 0)
            window.update()
            if time_paused:
                window.time = last_time

        elif menu.game_state == "load_world":
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
            window.update(world.player.rect.center)

            # Move camera
            update_game_camera()

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
                world.player.inventory.save()
                file.delete("data/user/world.data")
                menu.death_page.open()
                menu.game_state = "death"

        elif menu.game_state in ("pause", "death", "inventory"):
            # Draw world
            draw_game()

            if menu.game_state == "inventory":
                world.player.can_move = False
                world.update(window)
                world.player.can_move = True
                update_game_camera()

            # Draw menu
            if menu.game_intro:
                draw_intro()
            window.draw_rect((-1, -1), (2, 2), (0, 0, 0, 200))

            # Update and draw the menu
            menu.update()
            if menu.game_state == "inventory":
                world.player.inventory.update(window, menu, world)

            # Update window + shader
            window.update()

            # Game
            if window.keybind("return") == 1 or (window.keybind("inventory") == 1 and not menu.inventory_page.search_selected):
                if menu.game_state in ("pause", "inventory"):
                    window.mouse_wheel[1] = 0
                    menu.inventory_page.search_selected = False
                    menu.inventory_page.fusing = 0

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
                    str(round(window.average_fps, 3)),
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
