from pathlib import Path
from rectpack import newPacker
import rectpack as pack
import pygame
import os


def main():
    data = ""

    images = {}
    image_paths = list(Path(os.path.dirname(__file__)).rglob("*.png"))

    width = 0
    height = 0

    for path in image_paths:
        image = pygame.image.load(path)
        image_width = image.get_width()
        image_height = image.get_height()
        images[path] = (image_width, image_height)
        width = max(width + image_width / 2, image_width)
        height = max(height + image_height / 2, image_height)

    packer = pack.newPacker(bin_algo=pack.PackingBin.BBF, pack_algo=pack.GuillotineBafSas, rotation=False, sort_algo=pack.SORT_SSIDE)
    packer = pack.newPacker(rotation=False)
    for path, rectangle in images.items():
        packer.add_rect(*rectangle, rid=path)

    packer.add_bin(width, height)

    packer.pack()
    for rectangle in sorted(packer[0].rect_list(), key=lambda x: x[4]):
        data += rectangle[4].stem + ": " + str((rectangle[:4])) + "\n"
        images[rectangle[4]] = (rectangle[:2])

    with open(os.path.abspath(os.path.join(__file__, "..", "images.properties")), "w") as file:
        file.write(data)

    """
    pygame.init()
    window = pygame.display.set_mode((width * 2, height * 2))
    screen = pygame.Surface((width, height))
    pygame.display.set_caption("Packed Images")

    for path, rectangle in images.items():
        image = pygame.image.load(path)
        image_width, image_height = rectangle
        image_rect = image.get_rect()
        image_rect.topleft = rectangle[:2]
        screen.blit(image, image_rect)

    window.blit(pygame.transform.scale2x(screen), (0, 0))
    pygame.display.flip()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                break
    """


if __name__ == "__main__":
    main()