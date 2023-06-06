import pygame
import sys

pygame.init()
pygame.mixer.init()

pygame.mixer.set_num_channels(16)

def play(sound, x):
    print(x, "\t", abs(0.5 - x), abs(-0.5 - x))
    channel = pygame.mixer.find_channel()
    channel.play(sound)
    channel.set_volume(abs(0.5 - x), abs(-0.5 - x))

window = pygame.display.set_mode((500, 200))
window.fill((255, 255, 255))
pygame.display.update()

sound = pygame.mixer.Sound("test.wav")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            play(sound, event.pos[0] / 500 - 0.5)

    
