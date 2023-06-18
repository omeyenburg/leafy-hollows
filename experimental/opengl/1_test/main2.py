import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
from platform import system as get_system

# Initialize Pygame
pygame.init()

pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                        pygame.GL_CONTEXT_PROFILE_CORE)
# MacOS support
if get_system() == "Darwin":
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True) 

# Create the Pygame window
width, height = 800, 600
pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)

VAO = glGenVertexArrays(1)
glBindVertexArray(VAO)

print(glGenVertexArrays)

# Create a vertex buffer object (VBO)
VBO = glGenBuffers(1)

# Define the vertices and texture coordinates for a single sprite
vertices = np.array([-0.5, -0.5, 0.0, 0.0,
                     0.5, -0.5, 1.0, 0.0,
                     0.5, 0.5, 1.0, 1.0,
                    -0.5, 0.5, 0.0, 1.0], dtype=np.float32)

# Upload the vertex data to the VBO
glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

# Bind the vertex attribute pointers directly to the VBO if VAO is not supported
if not glGenVertexArrays:
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
    glEnableVertexAttribArray(1)

# Compile shaders
vertex_shader = compileShader("""
#version 330 core
in vec2 position;
in vec2 texcoord;
out vec2 fragTexCoord;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
    fragTexCoord = texcoord;
}
""", GL_VERTEX_SHADER)

fragment_shader = compileShader("""
#version 330 core
in vec2 fragTexCoord;
uniform sampler2D tex;
out vec4 fragColor;
void main()
{
    fragColor = texture(tex, fragTexCoord);
}
""", GL_FRAGMENT_SHADER)

shader_program = compileProgram(vertex_shader, fragment_shader)

# Load the sprite texture
image = pygame.image.load("player.png")
image_data = pygame.image.tostring(image, "RGBA", 1)
image_width, image_height = image.get_width(), image.get_height()

texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
glGenerateMipmap(GL_TEXTURE_2D)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# Activate the shader program and set the texture uniform
glUseProgram(shader_program)
glUniform1i(glGetUniformLocation(shader_program, "tex"), 0)

# Main game loop
while True:
    # Process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    # Clear the screen
    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    # Render multiple sprites
    sprite_positions = [(100, 100), (200, 200), (300, 300)]

    for pos in sprite_positions:
        # Calculate the model matrix for each sprite
        model_matrix = np.array([[1.0, 0.0, pos[0]],
                                 [0.0, 1.0, pos[1]],
                                 [0.0, 0.0, 1.0]], dtype=np.float32)

        # Upload the model matrix to the shader
        model_loc = glGetUniformLocation(shader_program, "model")
        glUniformMatrix3fv(model_loc, 1, GL_FALSE, model_matrix)

        # Render the sprite
        if glGenVertexArrays:
            VAO = glGenVertexArrays(1)
            glBindVertexArray(VAO)
            glBindBuffer(GL_ARRAY_BUFFER, VBO)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
            glEnableVertexAttribArray(1)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)
            glBindVertexArray(VAO)
        else:
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
            glEnableVertexAttribArray(1)

        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

    # Update the display
    pygame.display.flip()