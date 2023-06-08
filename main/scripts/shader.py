from platform import system as get_system
import numpy
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from pygame.locals import *

try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    OPENGL_SUPPORTED = True
except:
    OPENGL_SUPPORTED = False


def init(use_opengl):
    global OPENGL_SUPPORTED
    pygame.init()

    if not use_opengl:
        OPENGL_SUPPORTED = False
        print("OpenGL is disabled")
        return

    try:
        # Explicitly use OpenGL 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                        pygame.GL_CONTEXT_PROFILE_CORE)
        # MacOS support
        if get_system() == "Darwin":
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True) 
    except:
        OPENGL_SUPPORTED = False
        print("OpenGL is not installed")


def window(width, height):
    global OPENGL_SUPPORTED

    # Test, if OpenGL is available
    try:
        # Set up OpenGL
        glViewport(0, 0, width, height)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glDisable(GL_CULL_FACE)

        # Vertex data
        Shader.vertices = numpy.array((0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0), dtype=numpy.float32)
        Shader.texcoords = numpy.array((-1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0, -1.0), dtype=numpy.float32)

        # Create Vertex Array Object
        Shader.vao = glGenVertexArrays(1)
        glBindVertexArray(Shader.vao)

        # Create Vertex Buffer Object
        Shader.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, Shader.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, Shader.vertices.nbytes, Shader.vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)

        Shader.vbo_texcoords = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, Shader.vbo_texcoords)
        glBufferData(GL_ARRAY_BUFFER, Shader.texcoords.nbytes, Shader.texcoords, GL_STATIC_DRAW)
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
        
    except:
        OPENGL_SUPPORTED = False
        print("OpenGL is not available")


def quit():
    if not OPENGL_SUPPORTED:
        return
    for shader in Shader.shaders:
        shader.delete()
    glDeleteTextures(2, (Shader.world_texture, Shader.ui_texture))
    glDeleteBuffers(2, (Shader.vbo_vertices, Shader.vbo_texcoords))
    glDeleteVertexArrays(1, (Shader.vao,))


def modify(width, height):
    glViewport(0, 0, width, height)


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
        if not OPENGL_SUPPORTED:
            return
        Shader.shaders.append(self)
        self.vertex = load_vertex(vertex)
        self.fragment = load_fragment(fragment)
        self.program = glCreateProgram()
        
        glAttachShader(self.program, self.vertex)
        glAttachShader(self.program, self.fragment)
        glLinkProgram(self.program)
        glValidateProgram(self.program)

        # Dict containing all variables which should be send to the fragment shader {variable1: (uniformLoc, glUniformFunc, value)}
        self.variables = {variable: get_uniform(self.program, variable, variables[variable]) for variable in variables}
        self.worldLoc = glGetUniformLocation(self.program, "texWorld")
        self.uiLoc = glGetUniformLocation(self.program, "texUi")

    def setvar(self, variable, value):
        if not OPENGL_SUPPORTED:
            return
        self.variables[variable][2] = value

    def activate(self):
        if not OPENGL_SUPPORTED:
            return
        glUseProgram(self.program)
        Shader.active = self

    def delete(self):
        if not OPENGL_SUPPORTED:
            return
        glDetachShader(self.program, self.vertex)
        glDetachShader(self.program, self.fragment)
        glDeleteProgram(self.program)


def load_vertex(path):
    if not OPENGL_SUPPORTED:
        return
    with open(path, "r") as file:
        vertex = compileShader(file.read(), GL_VERTEX_SHADER)
    return vertex


def load_fragment(path):
    if not OPENGL_SUPPORTED:
        return
    with open(path, "r") as file:
        fragment = compileShader(file.read(), GL_FRAGMENT_SHADER)
    return fragment


def get_uniform(program, variable, data_type):
    # Get location and convert glsl data type to valid function
    loc = glGetUniformLocation(program, variable)
    func = data_type_map = {'int': glUniform1i,
                            'uint': glUniform1ui,
                            'float': glUniform1f,
                            'vec2': glUniform2f,
                            'vec3': glUniform3f,
                            'vec4': glUniform4f,
                            'bvec2': glUniform2i,
                            'bvec3': glUniform3i,
                            'bvec4': glUniform4i,
                            'ivec2': glUniform2i,
                            'ivec3': glUniform3i,
                            'ivec4': glUniform4i,
                            'uvec2': glUniform2ui,
                            'uvec3': glUniform3ui,
                            'uvec4': glUniform4ui,
                            'mat2': glUniformMatrix2fv,
                            'mat3': glUniformMatrix3fv,
                            'mat4': glUniformMatrix4fv}[data_type]
    return [loc, func, None]

def update(world_surface, ui_surface):
    if OPENGL_SUPPORTED:
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
        for loc, func, value in Shader.active.variables.values():
            if value is None:
                continue
            func(loc, value)
        
        # Update window
        glBindVertexArray(Shader.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
    else:
        ui_surface.set_colorkey((0, 0, 0))
        pygame.display.get_surface().blits(((world_surface, (0, 0)), (ui_surface, (0, 0))))
        
    pygame.display.flip()