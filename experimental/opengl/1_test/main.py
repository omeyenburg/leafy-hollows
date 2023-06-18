import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def load_texture(file_path):
    texture_surface = pygame.image.load(file_path).convert_alpha()
    texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
    width, height = texture_surface.get_width(), texture_surface.get_height()

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

    return texture_id

def render(texture_id):
    glClear(GL_COLOR_BUFFER_BIT)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(-0.5, -0.5)
    glTexCoord2f(1, 0); glVertex2f(0.5, -0.5)
    glTexCoord2f(1, 1); glVertex2f(0.5, 0.5)
    glTexCoord2f(0, 1); glVertex2f(-0.5, 0.5)
    glEnd()

    glDisable(GL_TEXTURE_2D)

    pygame.display.flip()

def main():
    # Initialize Pygame
    pygame.init()
    width, height = 800, 600
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)

    # Initialize OpenGL
    gluOrtho2D(-1, 1, -1, 1)

    # Load and bind texture
    texture_id = load_texture("player.png")

    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        
        render(texture_id)

if __name__ == "__main__":
    main()
