# -*- coding: utf-8 -*-
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL import *
import scripts.utility.file as file


class Shader:
    active = None

    def __init__(self, vertex, fragment, replace={}, **variables):
        self._program = glCreateProgram()
        
        # Read & compile vertex shader
        content = file.read(vertex)
        for search, replacement in replace.items():
            content = content.replace(str(search), str(replacement))
        vertex_shader = compileShader(content, GL_VERTEX_SHADER)
        glAttachShader(self._program, vertex_shader)

        # Read & compile fragment shader
        content = file.read(fragment)
        for search, replacement in replace.items():
            content = content.replace(str(search), str(replacement))
        fragment_shader = compileShader(content, GL_FRAGMENT_SHADER)
        glAttachShader(self._program, fragment_shader)

        glLinkProgram(self._program)
        glValidateProgram(self._program)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        # Dict containing all variables which should be send to the fragment shader {variable1: (uniformLoc, glUniformFunc, value)}
        self._variables = {variable: Shader.get_uniform_loc(self._program, variable, variables[variable]) for variable in variables}

    def setvar(self, variable, *value):
        """
        Set the value of a variable, which is send to the shader by update
        """
        self._variables[variable][2] = value

    def activate(self):
        """
        Activate the shader.
        """
        glUseProgram(self._program)
        Shader.active = self

    def delete(self):
        """
        Delete the shader.
        """
        glDeleteProgram(self._program)

    def get_uniform_loc(program, variable, data_type): # Get location and convert glsl data type to valid function
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

    def update(self):
        """
        Update all variables.
        """
        for index, (loc, func, value) in self._variables.items():
            if value is None:
                continue
            func(loc, *value)
            self._variables[index][2] = None