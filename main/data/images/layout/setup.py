from pathlib import Path
import rectpack as pack
import pygame
import sys
import os


cwd = os.path.dirname(__file__)
main_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, main_folder)
import scripts.utility.geometry as geometry
sys.path.insert(0, main_folder)


def fit(size_divider):
    data = ""
    images = {}
    image_paths = list(Path(os.path.join(os.path.dirname(__file__), "..", "sprites")).rglob("*.png"))
    rectangles = list()

    width = 0
    height = 0

    for path in image_paths:
        image = pygame.image.load(path)
        image_width = image.get_width()
        image_height = image.get_height()
        images[path] = (image_width, image_height)
        width = max(width + image_width / size_divider, image_width)
        height = max(height + image_height / size_divider, image_height)

    packer = pack.newPacker(bin_algo=pack.PackingBin.BBF, pack_algo=pack.GuillotineBafSas, rotation=False, sort_algo=pack.SORT_SSIDE)
    packer = pack.newPacker(rotation=False)
    for path, rectangle in images.items():
        packer.add_rect(*rectangle, rid=path)

    packer.add_bin(width, height)

    packer.pack()
    i = 0
    for rectangle in sorted(packer[0].rect_list(), key=lambda x: x[4]):
        data += rectangle[4].stem + ": " + str((rectangle[:4])) + "\n"
        images[rectangle[4]] = (rectangle[:2])
        rectangles.append(rectangle[:4])
        i += 1
    if i < len(image_paths):
        rectangles.append(rectangles[0])

    return rectangles, images, data


def main():
    size_divider = 20

    while size_divider > 0:
        rectangles, images, data = fit(size_divider)
        size_divider -= 0.5
        if not geometry.Rect.multi_intersection(rectangles):
            break
    
    with open(os.path.abspath(os.path.join(__file__, "..", "sprites.properties")), "w") as file:
        file.write(data)


if __name__ == "__main__":
    main()