# -*- coding: utf-8 -*-
from scripts.utility.noise_functions import pnoise1
from scripts.utility.language import translate
from scripts.utility.geometry import *
from scripts.utility.const import *
from scripts.graphics import sound
from scripts.game.weapon import *
from scripts.utility import file
import copy


class Inventory:
    def __init__(self):
        self.weapons = [Stick(1)]
        self.selected = self.weapons[0]
        self.marked_weapons = set()
        self.arrows = 0
        self.max_arrows = 64

    def save(self, world):
        self.selected = world.player.holding
        file.save("data/user/inventory.data", self, file_format="pickle")

    @staticmethod
    def load():
        if file.exists("data/user/inventory.data"):
            return file.load("data/user/inventory.data", file_format="pickle")
        else:
            return Inventory()

    def update(self, window, menu, world):
        if menu.inventory_page.fusing != 0:
            menu.inventory_page.fusing = min(int(menu.inventory_page.fusing >= 0), menu.inventory_page.fusing + window.delta_time)
        if menu.inventory_page.fusing:
            self.update_fuse(window, menu, world)
        else:
            menu.inventory_page.secondary_fuse_item = None
            self.update_inventory(window, menu, world)

    def update_inventory(self, window, menu, world):
        # Search bar
        window.draw_rect((-0.88, -0.98), (0.8, 0.16), (27, 21, 39))
        window.draw_image("search_icon", (-0.98, -0.98), (0.09, 0.09 / window.height * window.width))

        if 1 in window.mouse_buttons:
            menu.inventory_page.search_selected = window.mouse_pos[0] < 0 and window.mouse_pos[1] / window.height * 2 < -0.8
            sound.play(window, "click")

        if menu.inventory_page.search_selected:
            search_text_length = len(menu.inventory_page.search_text)
            if "\x08" in window.unicode:
                if search_text_length:
                    menu.inventory_page.search_text = menu.inventory_page.search_text[:search_text_length - 1]
            elif search_text_length < 20:
                menu.inventory_page.search_text += window.unicode

        if menu.inventory_page.search_text:
            search_text_width = window.draw_text((-0.85, -0.9), menu.inventory_page.search_text, (255, 255, 255), 0.2)[0]
        else:
            window.draw_text((-0.85, -0.9), "Search...", (100, 100, 100), 0.2)
            search_text_width = -0.025

        if menu.inventory_page.search_selected and window.time % 1 < 0.5:
            window.draw_rect((-0.85 + search_text_width, -0.97), (0.005, 0.14), (255, 255, 255))

        # Filter weapon list with search parameters
        if menu.inventory_page.sort_key == "Level":
            weapon_sort_function = lambda i: (not i is world.player.holding) * 99999999 + (not i.uuid in world.player.inventory.marked_weapons) * 9999999 - max(i.attributes.values()) - 0.1 * min(i.attributes.values())
        elif menu.inventory_page.sort_key == "Type":
            weapon_sort_function = lambda i: (not i.uuid in world.player.inventory.marked_weapons) * 9999999 + sum(map(lambda j: ord(j), i.image))
        elif menu.inventory_page.sort_key == "Age":
            weapon_sort_function = lambda i: (not i is world.player.holding) * 99999999 + (not i.uuid in world.player.inventory.marked_weapons) * 9999999 + i.uuid

        search_text = menu.inventory_page.search_text.lower()
        inventory = sorted(
            filter(
                lambda i:
                search_text in translate(window.options["language"], i.image) or
                any([
                    search_text in translate(window.options["language"], attribute).lower() or
                    search_text in translate(window.options["language"], ATTRIBUTE_DESCRIPTIONS[attribute]).lower()
                    for attribute in i.attributes
                ]),
                world.player.inventory.weapons
            ),
            key=weapon_sort_function
        )

        if not len(inventory):
            window.draw_text((0.2, 0.7), "Could not find\nany matching item.", (255, 255, 255), 0.2)
            return
        
        window.draw_text((-0.95, 0), "Sort by:", (255, 255, 255), 0.2)

        for i, key in enumerate(("Level", "Type", "Age")):
            if key == menu.inventory_page.sort_key:
                sort_image = "button_dark_selected"
            else:
                sort_image = "button_dark_unselected"

            rect = Rect(-0.95, -i * 0.2 - 0.05 / window.height * window.width - 0.2, 0.5, 0.1 / window.height * window.width)
            if 1 in window.mouse_buttons and rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)):
                menu.inventory_page.sort_key = key
                sound.play(window, "click")

            window.draw_image(sort_image, rect[:2], rect[2:])
            window.draw_text((-0.9, -i * 0.2 - 0.2), key, (255, 255, 255), 0.17)

        # Get mouse scroll
        scroll_speed = -20
        window.mouse_wheel[1] = max(min(window.mouse_wheel[1], 0), len(inventory) * scroll_speed - scroll_speed)
        scroll_position = window.mouse_wheel[1] / scroll_speed
        if not window.mouse_wheel[3]:
            window.mouse_wheel[1] += (round(scroll_position) - scroll_position) * scroll_speed * 0.02

        # Get weapon positions
        weapon_y = 0.5
        weapon_positions = []
        for i, weapon in enumerate(inventory):
            weapon_size = Vec(0.4, 0.4 / window.height * window.width) * max(0.5, 1 / ((i - scroll_position) ** 2 + 1))
            weapon_y -= weapon_size[1]
            weapon_positions.append(weapon_y)

        distance = abs(floor(scroll_position) - scroll_position)
        weapon_center_y = (1 - distance) * weapon_positions[floor(scroll_position)] + distance * weapon_positions[ceil(scroll_position)]

        # Draw weapon list
        for i, weapon in enumerate(inventory):
            weapon_size = Vec(0.4, 0.4 / window.height * window.width) * max(0, 1 / ((i - scroll_position) ** 4 + 1))
            weapon_pos = Vec(-0.2 - weapon_size[0] / 2, weapon_positions[i] - weapon_center_y)

            if weapon_pos[1] < -0.8:
                continue

            weapon_rect = Rect(*weapon_pos, *weapon_size)
            star_rect = Rect(-0.2 -weapon_size[0] * 0.55, weapon_positions[i] - weapon_center_y + weapon_size[1] * 0.9, *(weapon_size * 0.2))

            if (1 in window.mouse_buttons and
            weapon_rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)) and
            abs(round(scroll_position) - i) == 1):
                if scroll_position < i:
                    window.mouse_wheel[1] = (ceil(round(window.mouse_wheel[1] / scroll_speed) + 0.1) - 0.3) * scroll_speed
                else:
                    window.mouse_wheel[1] = (floor(round(window.mouse_wheel[1] / scroll_speed) - 0.1) + 0.3) * scroll_speed
                sound.play(window, "click")

            if (1 in window.mouse_buttons and
            star_rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)) and
            round(scroll_position) == i):
                if weapon.uuid in world.player.inventory.marked_weapons:
                    world.player.inventory.marked_weapons.remove(weapon.uuid)
                else:
                    world.player.inventory.marked_weapons.add(weapon.uuid)
                sorted_inventory = sorted(inventory, key=weapon_sort_function)
                window.mouse_wheel[1] = scroll_speed * sorted_inventory.index(weapon)
                sound.play(window, "click")

            # Draw highlight circle
            if i == round(scroll_position):
                radius = weapon_size[0] * 0.5 + pnoise1(window.time * 0.1, octaves=2) * 0.1
                if weapon is world.player.holding:
                    color = (168, 202, 88, 50)
                else:
                    color = (162, 62, 140, 50)
                window.draw_circle(weapon_pos + weapon_size / 2, radius, color)

            if weapon.uuid in world.player.inventory.marked_weapons:
                star_image = "star_marked_icon"
            else:
                star_image = "star_unmarked_icon"

            window.draw_image(star_image, star_rect[:2], star_rect[2:])
            window.draw_image(weapon.image, weapon_pos, weapon_size, angle=weapon.angle)

        # Write weapon's stats/attributes
        weapon = inventory[round(scroll_position)]
        if weapon is None:
            return

        name = weapon.image.title()
        name_width = window.draw_text((0, 0.8), name, (255, 255, 255), 0.3)[0]
        if weapon is world.player.holding:
            window.draw_text((name_width + name_width / len(name), 0.8), "(equipped)", (255, 255, 255), 0.3)[0]

        weapon_base_stats = (weapon.damage, weapon.attack_speed, weapon.range, weapon.crit_chance)
        attribute_stat_increase = weapon.get_weapon_stat_increase(world)
        
        for i, stat in enumerate(("damage", "attack_speed", "range", "crit_chance")):
            stat_name = stat.title().replace("_", " ")
            stat_size = window.draw_text((0, -i * 0.1 + 0.6), f"{stat_name}: {weapon_base_stats[i]}", (164, 221, 219), 0.17)

            stat_increase = round(attribute_stat_increase[i] - weapon_base_stats[i], 2)
            if stat_increase:
                window.draw_text((stat_size[0] + 0.05, -i * 0.1 + 0.6), f"(+{stat_increase})", (223, 132, 165), 0.17)

        for i, (attribute, level) in enumerate(weapon.attributes.items()):
            description_y = -0.6 * i + 0.1
            modifier = ATTRIBUTE_BASE_MODIFIERS[attribute] * level
            if attribute == "paralysis":
                modifier = min(100, modifier)

            name = translate(window.options["language"], attribute).title()
            description = translate(window.options["language"], ATTRIBUTE_DESCRIPTIONS[attribute]) % modifier
            window.draw_text((0, description_y), f"{name} {INT_TO_ROMAN.get(level, level)}: {description}", (223, 132, 165), 0.17, wrap=1)

        matching_items_text = translate(window.options['language'], "%s matching item" + "s" * int(len(inventory) != 1)) % str(len(inventory))
        window.draw_text((-0.92, -0.75), matching_items_text, (255, 255, 255), 0.17)

        if len(world.player.inventory.weapons) == 1:
            return
        
        # Weapon actions
        window.draw_text((-0.95, 0.9), "Action:", (255, 255, 255), 0.2)
        destroy_health_gain = sum(weapon.attributes.values())

        for i, key in enumerate(("Equip", "Fuse", "Destroy")):
            rect = Rect(-0.95, -i * 0.2 - 0.05 / window.height * window.width + 0.7, 0.5, 0.1 / window.height * window.width)
            sort_image = "button_dark_unselected"

            if rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)):
                if 1 in window.mouse_buttons:
                    if key == "Equip":
                        world.player.holding = weapon
                        window.mouse_wheel[1] = 0
                    elif key == "Fuse":
                        menu.inventory_page.fuse_item = weapon
                        menu.inventory_page.fusing = window.delta_time
                        window.mouse_wheel[1] = 0
                    elif key == "Destroy":
                        world.player.inventory.weapons.remove(weapon)
                        inventory.remove(weapon)
                        if world.player.holding is weapon:
                            if len(inventory):
                                world.player.holding = inventory[0]
                            else:
                                world.player.holding = None
                        world.player.heal(window, destroy_health_gain)
                    sound.play(window, "click")

                if any(window.mouse_buttons):
                    sort_image = "button_dark_selected"

            window.draw_image(sort_image, rect[:2], rect[2:])

            button_text = key
            button_image_size = 0.2
            if key == "Equip":
                button_image = "equip_icon"
            elif key == "Fuse":
                button_image = "fuse_icon"
            else:
                button_image = "heart"
                button_image_size = 0.1

            action_width = window.draw_text((-0.9, -i * 0.2 + 0.7), button_text, (255, 255, 255), 0.17)[0]
            if key == "Destroy":
                window.draw_text((-0.85 + action_width, -i * 0.2 + 0.7), "+" + str(destroy_health_gain), (255, 255, 255), 0.17)
            window.draw_image(button_image, (-0.53 - button_image_size * 0.2, -i * 0.2 + 0.7  - button_image_size / 2), (button_image_size * window.height / window.width, button_image_size))

    def update_fuse(self, window, menu, world):
        # Main fusion weapon
        weapon = menu.inventory_page.fuse_item
        weapon_size = Vec(1, 1 / window.height * window.width) * (0.4 - 0.1 * (max(0, min(menu.inventory_page.fusing, 0.5)) + 0.5 * (menu.inventory_page.fusing < 0)))
        weapon_pos = Vec(-0.2 - 1.2 * (max(0, min(menu.inventory_page.fusing, 0.5)) + 0.5 * (menu.inventory_page.fusing < 0)) - weapon_size[0] / 2, 0)
        window.draw_image(weapon.image, weapon_pos, weapon_size, angle=weapon.angle)

        # Back button
        rect = Rect(-0.98, -0.98, 0.5, 0.1 / window.height * window.width)
        fuse_button_image = "button_dark_unselected"
        if rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)):
            if 1 in window.mouse_buttons:
                menu.inventory_page.fusing = 0
                window.mouse_wheel[1] = 0
            if any(window.mouse_buttons):
                fuse_button_image = "button_dark_selected"
            
        window.draw_image(fuse_button_image, rect[:2], rect[2:])
        window.draw_text((-0.93, -0.98 + 0.1 / window.height * window.width / 2), "Back", (255, 255, 255), 0.17)

        if 0 < menu.inventory_page.fusing < 0.5:
            return

        name = weapon.image.title()
        window.draw_text((-0.6, 0.7), name, (255, 255, 255), 0.3)

        for i, (attribute, level) in enumerate(weapon.attributes.items()):
            description_y = -0.15 * i + 0.5
            attribute_name = translate(window.options['language'], attribute).title()
            window.draw_text((-0.6, description_y), f"{attribute_name} {INT_TO_ROMAN[level]}", (223, 132, 165), 0.17, wrap=1)
        
        # Search bar
        window.draw_rect((0.12, -0.98), (0.8, 0.16), (27, 21, 39))
        window.draw_image("search_icon", (0.02, -0.98), (0.09, 0.09 / window.height * window.width))

        if 1 in window.mouse_buttons:
            menu.inventory_page.search_selected = window.mouse_pos[0] > 0 and window.mouse_pos[1] / window.height * 2 < -0.8

        if menu.inventory_page.search_selected:
            search_text_length = len(menu.inventory_page.search_text)
            if "\x08" in window.unicode:
                if search_text_length:
                    menu.inventory_page.search_text = menu.inventory_page.search_text[:search_text_length - 1]
            elif search_text_length < 20:
                menu.inventory_page.search_text += window.unicode

        if menu.inventory_page.search_text:
            search_text_width = window.draw_text((0.15, -0.9), menu.inventory_page.search_text, (255, 255, 255), 0.2)[0]
        else:
            window.draw_text((0.15, -0.9), "Search...", (100, 100, 100), 0.2)
            search_text_width = -0.025

        if menu.inventory_page.search_selected and window.time % 1 < 0.5:
            window.draw_rect((0.15 + search_text_width, -0.97), (0.005, 0.14), (255, 255, 255))

        search_text = menu.inventory_page.search_text.lower()
        inventory = sorted(
            filter(
                lambda i:
                (search_text in translate(window.options["language"], i.image) or any([
                    search_text in translate(window.options["language"], attribute).lower() or
                    search_text in translate(window.options["language"], ATTRIBUTE_DESCRIPTIONS[attribute]).lower()
                    for attribute in i.attributes
                ])) and not i is menu.inventory_page.fuse_item and
                any([
                    i.attributes.get(attribute, 0) >= level
                    for attribute, level in weapon.attributes.items()
                ]),
                world.player.inventory.weapons
            ),
            key=lambda i: not i.uuid in world.player.inventory.marked_weapons
        )

        if not len(inventory):
            window.draw_text((0.2, 0.7), "Could not find\nany matching item.", (255, 255, 255), 0.2)
            return

        if menu.inventory_page.secondary_fuse_item is None:
            # Get mouse scroll
            scroll_speed = -20
            window.mouse_wheel[1] = max(min(window.mouse_wheel[1], 0), len(inventory) * scroll_speed - scroll_speed)
            scroll_position = window.mouse_wheel[1] / scroll_speed
            if not window.mouse_wheel[3]:
                window.mouse_wheel[1] += (round(scroll_position) - scroll_position) * scroll_speed * 0.02

            # Get weapon positions
            weapon_y = 0.5
            weapon_positions = []
            for i, weapon in enumerate(inventory):
                weapon_size = Vec(0.4, 0.4 / window.height * window.width) * max(0.5, 1 / ((i - scroll_position) ** 2 + 1))
                weapon_y -= weapon_size[1]
                weapon_positions.append(weapon_y)

            distance = abs(floor(scroll_position) - scroll_position)
            weapon_center_y = (1 - distance) * weapon_positions[floor(scroll_position)] + distance * weapon_positions[ceil(scroll_position)]

            # Draw weapon list
            for i, weapon in enumerate(inventory):
                weapon_size = Vec(0.3, 0.3 / window.height * window.width) * max(0, 1 / ((i - scroll_position) ** 4 + 1))
                weapon_pos = Vec(0.8 - weapon_size[0] / 2, weapon_positions[i] - weapon_center_y)

                if weapon_pos[1] < -0.8:
                    continue

                weapon_rect = Rect(*weapon_pos, *weapon_size)

                if (1 in window.mouse_buttons and
                weapon_rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)) and
                abs(round(scroll_position) - i) == 1):
                    if scroll_position < i:
                        window.mouse_wheel[1] = (ceil(round(window.mouse_wheel[1] / scroll_speed) + 0.1) - 0.3) * scroll_speed
                    else:
                        window.mouse_wheel[1] = (floor(round(window.mouse_wheel[1] / scroll_speed) - 0.1) + 0.3) * scroll_speed

                # Draw highlight circle
                if i == round(scroll_position):
                    radius = weapon_size[0] * 0.5 + pnoise1(window.time * 0.1, octaves=2) * 0.1
                    if weapon is world.player.holding:
                        color = (168, 202, 88, 50)
                    else:
                        color = (162, 62, 140, 50)
                    window.draw_circle(weapon_pos + weapon_size / 2, radius, color)

                window.draw_image(weapon.image, weapon_pos, weapon_size, angle=weapon.angle)

            # Write weapon's attributes
            secondary_weapon = inventory[round(scroll_position)]
            if secondary_weapon is None:
                return
        else:
            secondary_weapon = menu.inventory_page.secondary_fuse_item
            weapon_size = Vec(1, 1 / window.height * window.width) * 0.3
            weapon_pos = Vec(0.8 - weapon_size[0] / 2, 0)
            window.draw_image(secondary_weapon.image, weapon_pos, weapon_size, angle=secondary_weapon.angle)

        matching_items_text = (translate(window.options['language'], "%s matching item" + "s" * int(len(inventory) != 1)) % str(len(inventory))) + ":"
        window.draw_text((0.2, 0.9), matching_items_text, (255, 255, 255), 0.17)

        name = secondary_weapon.image.title()
        window.draw_text((0.3, 0.7), name, (255, 255, 255), 0.3)

        for i, (attribute, level) in enumerate(secondary_weapon.attributes.items()):
            description_y = -0.15 * i + 0.5
            attribute_name = translate(window.options['language'], attribute).title()
            window.draw_text((0.3, description_y), f"{attribute_name} {INT_TO_ROMAN[level]}", (223, 132, 165), 0.17, wrap=1)

        fusion_attributes = {
            attribute:
            max(level + (level == secondary_weapon.attributes.get(attribute, 0)), secondary_weapon.attributes.get(attribute, 0))
            for attribute, level in menu.inventory_page.fuse_item.attributes.items()
        }

        for i, (attribute, level) in enumerate(fusion_attributes.items()):
            description_y = -0.15 * i - 0.3
            attribute_name = translate(window.options['language'], attribute).title()
            window.draw_text((-0.12, description_y), f"{attribute_name} {INT_TO_ROMAN[level]}", (223, 132, 165), 0.17, wrap=1)

        # Fuse button
        rect = Rect(-0.25, -0.1 / window.height * window.width / 2, 0.5, 0.1 / window.height * window.width)
        fuse_button_image = "button_dark_unselected"
        if rect.collide_point((window.mouse_pos[0] / window.width * 2, window.mouse_pos[1] / window.height * 2)):
            if 1 in window.mouse_buttons and menu.inventory_page.fusing > 0:
                menu.inventory_page.fusing = -1.5
                previous_fuse_item = copy.deepcopy(menu.inventory_page.fuse_item)
                menu.inventory_page.fuse_item.attributes = fusion_attributes
                menu.inventory_page.fuse_item = previous_fuse_item
                menu.inventory_page.secondary_fuse_item = secondary_weapon
                if world.player.holding == secondary_weapon:
                    world.player.holding = menu.inventory_page.fuse_item
                world.player.inventory.weapons.remove(secondary_weapon)
                sound.play(window, "fuse")
            if any(window.mouse_buttons):
                fuse_button_image = "button_dark_selected"
            
        window.draw_image(fuse_button_image, rect[:2], rect[2:])
        window.draw_text((0, 0), "Fuse", (255, 255, 255), 0.17, centered=True)

        # Fuse bar
        if menu.inventory_page.fusing > 0:
            fuse_bar_image = "fuse_bar_a"
        else:
            fuse_bar_image = "fuse_bar_" + chr(ord("a") + round(6 + menu.inventory_page.fusing * 4))
        
        window.draw_image(fuse_bar_image, (-0.5, -0.4), (0.3, 0.3 / window.height * window.width))
        window.draw_image(fuse_bar_image, (0.2, -0.4), (0.3, 0.3 / window.height * window.width), flip=(1, 0))
