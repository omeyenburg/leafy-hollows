from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import platform
import numpy
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from pygame.locals import *

if not pygame.display.get_init():
    pygame.init()

# Explicitly use OpenGL 3.3 core
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                pygame.GL_CONTEXT_PROFILE_CORE)

# MacOS support
if platform.system() == "Darwin":
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG,
                                    True)


def init(width, height, vsync):
    # Create pygame window
    window = pygame.display.set_mode((width, height),
                                     flags=DOUBLEBUF | OPENGL | RESIZABLE,
                                     vsync=vsync)

    # Set up OpenGL
    glViewport(0, 0, width, height)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_BLEND)
    glDisable(GL_CULL_FACE)

    # Vertex data
    Shader.vertices = numpy.array((0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0),
                                  dtype=numpy.float32)
    Shader.texcoords = numpy.array(
        (-1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0, -1.0), dtype=numpy.float32)

    # Create Vertex Array Object
    Shader.vao = glGenVertexArrays(1)
    glBindVertexArray(Shader.vao)

    # Create Vertex Buffer Object
    Shader.vbo_vertices = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, Shader.vbo_vertices)
    glBufferData(GL_ARRAY_BUFFER, Shader.vertices.nbytes, Shader.vertices,
                 GL_STATIC_DRAW)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(0)

    Shader.vbo_texcoords = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, Shader.vbo_texcoords)
    glBufferData(GL_ARRAY_BUFFER, Shader.texcoords.nbytes, Shader.texcoords,
                 GL_STATIC_DRAW)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(1)

    # Load textures
    # GL_LINEAR (smooth) or GL_NEAREST (pixelated)
    Shader.world_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, Shader.world_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    Shader.ui_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, Shader.ui_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    glBindTexture(GL_TEXTURE_2D, 0)
    return window


def quit():
    for shader in Shader.shaders:
        shader.delete()
    glDeleteTextures(Shader.world_texture)
    glDeleteTextures(Shader.ui_texture)
    glDeleteBuffers(2, (Shader.vbo_vertices, Shader.vbo_texcoords))
    glDeleteVertexArrays(1, (Shader.vao, ))


def modify_window(width, height, vsync):
    window = pygame.display.set_mode((width, height),
                                     flags=DOUBLEBUF | OPENGL | RESIZABLE,
                                     vsync=vsync)
    glViewport(0, 0, width, height)
    return window


class Shader:
    vertices = None
    texcoords = None
    vao = None
    vbo_vertices = None
    vbo_texcoords = None
    world_texture = None
    ui_texture = None
    shaders = []
    program = None
    active = None

    def __init__(self, vertex, fragment, **variables):
        self.vertex = load_vertex(vertex)
        self.fragment = load_fragment(fragment)
        self.variables = variables
        self.program = glCreateProgram()
        glAttachShader(self.program, self.vertex)
        glAttachShader(self.program, self.fragment)
        glLinkProgram(self.program)
        glValidateProgram(self.program)
        self.worldLoc = glGetUniformLocation(self.program, "texWorld")
        self.uiLoc = glGetUniformLocation(self.program, "texUi")
        Shader.shaders.append(self)

    def activate(self):
        glUseProgram(self.program)
        Shader.active = self

    def delete(self):
        glDetachShader(self.program, self.vertex)
        glDetachShader(self.program, self.fragment)
        glDeleteProgram(self.program)


def load_vertex(path):
    with open(path, "r") as file:
        vertex = compileShader(file.read(), GL_VERTEX_SHADER)
    return vertex


def load_fragment(path):
    with open(path, "r") as file:
        fragment = compileShader(file.read(), GL_FRAGMENT_SHADER)
    return fragment


def update(world_surface, ui_surface):
    glClear(GL_COLOR_BUFFER_BIT)

    # Update world texture
    glBindTexture(GL_TEXTURE_2D, Shader.world_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *world_surface.get_size(), 0,
                 GL_RGBA, GL_UNSIGNED_BYTE,
                 pygame.image.tostring(world_surface, "RGBA", 1))

    # Update UI texture
    glBindTexture(GL_TEXTURE_2D, Shader.ui_texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *ui_surface.get_size(), 0,
                 GL_RGBA, GL_UNSIGNED_BYTE,
                 pygame.image.tostring(ui_surface, "RGBA", 1))

    # Bind textures to texture units
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, Shader.world_texture)
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, Shader.ui_texture)

    # Set texture uniforms in shader
    glUniform1i(Shader.active.worldLoc, 0)
    glUniform1i(Shader.active.uiLoc, 1)

    glUniform1f(glGetUniformLocation(Shader.active.program, "player0"), 0.5)
    glUniform1f(glGetUniformLocation(Shader.active.program, "player1"), 0.5)

    # Update window
    glBindVertexArray(Shader.vao)
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
    pygame.display.flip()
