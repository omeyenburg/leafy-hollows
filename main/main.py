# -*- coding: utf-8 -*-

# Apple: signing bundle
# https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
# https://gist.github.com/txoof/0636835d3cc65245c6288b2374799c43
# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-OSX-Code-Signing
# https://support.apple.com/en-us/HT204397
# xattr -d com.apple.quarantine "title.app"

from scripts.utility.thread import threaded
from scripts.graphics.window import Window
from scripts.menu.menu import Menu
from scripts.game.world import World
from scripts.utility.const import *
import math


# Create window
window: Window = Window("Title")
menu: Menu = Menu(window)
world: World = None


def save_world():
    if not world is None:
        world.save()


def generate():
    global world

    # Wait for world generation thread
    while True:
        menu.update()
        window.update()

        world = threaded(World.load, window, wait=True)
        if not world is None:
            break

        # Open menu
        if window.keybind("return") == 1:
            menu.main_page.open()
            menu.game_state = "menu"
            return

        # Write fps
        if window.options["show fps"]:
            window.draw_text(
                (-0.98, 0.95),
                str(round(window.fps, 3)),
                (250, 250, 250, 200),
                size=TEXT_SIZE_DESCRIPTION
            )

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

    # Write fps & debug info
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
            "Mouse Pos: " + str((math.floor(mouse_pos[0]),
            math.floor(mouse_pos[1]))),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.75 - y_offset),
            "Seed: " + str(world.seed),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )
        window.draw_text(
            (-0.98, 0.65 - y_offset),
            "Mouse Block: " + str(world.get(
                (math.floor(mouse_pos[0]), math.floor(mouse_pos[1])),
                0
            )),
            (250, 250, 250, 200),
            size=TEXT_SIZE_DESCRIPTION
        )


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
    if window.keybind("jump") == 1 and 0.05 < intro_text_position < 0.95:
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
    if world.player.onGround:
        window.camera.zoom(CAMERA_RESOLUTION_GAME, 100.0)
        menu.game_state = "game"
        world.player.can_move = True


def main():
    window.callback_quit = save_world
    window.camera.set_zoom(CAMERA_RESOLUTION_GAME)
    while True:
        if menu.game_state == "generate":
            window.camera.reset()
            generate()

        elif menu.game_state == "intro":
            window.camera.set_zoom(CAMERA_RESOLUTION_INTRO)
            world.update(window)
            draw_game()
            draw_intro()
            update_intro()

        elif menu.game_state == "game":
            # Update and draw the game
            world.update(window)
            draw_game()

            # Update and draw the menu
            window.update()
            window.camera.update()

            # Move camera
            camera_pos = (
                world.player.rect.centerx - world.player.vel[0] / 100,
                world.player.rect.centery - world.player.vel[0] / 100
            )
            window.camera.move(camera_pos)

            # Pause
            if window.keybind("return") == 1:
                menu.pause_page.open()
                menu.game_state = "pause"
                window.effects["gray_screen"] = 1

        elif menu.game_state == "pause":
            # Draw world
            draw_game()

            # Draw menu
            if menu.game_intro:
                draw_intro()

            # Save world
            menu.save_world = world.save

            # Update and draw the menu
            menu.update()

            # Update window + shader
            window.effects["gray_screen"] = 1
            window.update()
            window.effects["gray_screen"] = 0

            # Game
            if window.keybind("return") == 1:
                if menu.game_intro:
                    menu.game_state = "intro"
                    menu.game_intro = False
                else:
                    menu.game_state = "game"

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
