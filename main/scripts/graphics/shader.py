# -*- coding: utf-8 -*-
from OpenGL.GL.shaders import compileProgram, compileShader
from scripts.utility import file
from OpenGL import GL


class Shader:
    active = None

    def __init__(self, vertex: str="", fragment: str="", variables={}, constants={}):
        # Create shader
        self._program = GL.glCreateProgram()
        
        # Read & compile vertex shader
        constants = sorted(constants.items(), key=lambda n: len(n[0]), reverse=True)
        content = file.load(vertex)
        for search, replacement in constants:
            content = content.replace(str(search), str(replacement))
        vertex_shader = compileShader(content, GL.GL_VERTEX_SHADER)
        GL.glAttachShader(self._program, vertex_shader)

        # Read & compile fragment shader
        content = file.load(fragment)
        for search, replacement in constants:
            content = content.replace(str(search), str(replacement))
        fragment_shader = compileShader(content, GL.GL_FRAGMENT_SHADER)
        GL.glAttachShader(self._program, fragment_shader)

        # For testing: print fragment shader code
        """
        c = content
        n = c.count("\n") + 1
        for i, s in reversed(list(enumerate(c))):
            if s == "\n":
                c = c[:i + 1] + str(n) + "\t" + c[i + 1:]
                n -= 1
        print(c)
        """

        # Clean up
        GL.glLinkProgram(self._program)
        GL.glValidateProgram(self._program)
        GL.glDeleteShader(vertex_shader)
        GL.glDeleteShader(fragment_shader)

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
        GL.glUseProgram(self._program)
        Shader.active = self

    def delete(self):
        """
        Delete the shader.
        """
        GL.glDeleteProgram(self._program)

    def get_uniform_loc(program, variable, data_type):
        """
        Returns variable location, glsl data type as a valid function and the variable value.
        """
        # OpenGL functions to send data to a shader and glsl data types
        """
        glUniform1f(location, value): Sets a single float value (float).
        glUniform1i(location, value): Sets a single integer value (int).
        glUniform1ui(location, value): Sets a single unsigned integer value (uint).
        glUniform2f(location, value1, value2): Sets a 2-component float vector (vec2).
        glUniform2i(location, value1, value2): Sets a 2-component integer vector (ivec2).
        glUniform2ui(location, value1, value2): Sets a 2-component unsigned integer vector (uvec2).
        glUniform3f(location, value1, value2, value3): Sets a 3-component float vector (vec3).
        glUniform3i(location, value1, value2, value3): Sets a 3-component integer vector (ivec3).
        glUniform3ui(location, value1, value2, value3): Sets a 3-component unsigned integer vector (uvec3).
        glUniform4f(location, value1, value2, value3, value4): Sets a 4-component float vector (vec4).
        glUniform4i(location, value1, value2, value3, value4): Sets a 4-component integer vector (ivec4).
        glUniform4ui(location, value1, value2, value3, value4): Sets a 4-component unsigned integer vector (uvec4).
        glUniformMatrix2fv(location, count, transpose, value): Sets a 2x2 matrix or an array of 2x2 matrices (mat2).
        glUniformMatrix3fv(location, count, transpose, value): Sets a 3x3 matrix or an array of 3x3 matrices (mat3).
        glUniformMatrix4fv(location, count, transpose, value): Sets a 4x4 matrix or an array of 4x4 matrices (mat4).
        """
        loc = GL.glGetUniformLocation(program, variable)
        func = data_type_map = {'int': GL.glUniform1i,
                                'uint': GL.glUniform1ui,
                                'float': GL.glUniform1f,
                                'vec2': GL.glUniform2f,
                                'vec3': GL.glUniform3f,
                                'vec4': GL.glUniform4f,
                                'bvec2': GL.glUniform2i,
                                'bvec3': GL.glUniform3i,
                                'bvec4': GL.glUniform4i,
                                'ivec2': GL.glUniform2i,
                                'ivec3': GL.glUniform3i,
                                'ivec4': GL.glUniform4i,
                                'uvec2': GL.glUniform2ui,
                                'uvec3': GL.glUniform3ui,
                                'uvec4': GL.glUniform4ui,
                                'mat2': GL.glUniformMatrix2fv,
                                'mat3': GL.glUniformMatrix3fv,
                                'mat4': GL.glUniformMatrix4fv}[data_type]
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
