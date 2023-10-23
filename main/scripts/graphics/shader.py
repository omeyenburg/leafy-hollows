# -*- coding: utf-8 -*-
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL import GL
from scripts.utility import file


class Shader:
    active = None

    def __init__(self, vertex: str="", fragment: str="", variables={}, constants={}):
        # Create shader
        self._program = GL.glCreateProgram()
        
        # Read & compile vertex shader
        constants = sorted(constants.items(), key=lambda n: len(n[0]), reverse=True)
        content = file.read(vertex)
        for search, replacement in constants:
            content = content.replace(str(search), str(replacement))
        vertex_shader = compileShader(content, GL.GL_VERTEX_SHADER)
        GL.glAttachShader(self._program, vertex_shader)

        # Read & compile fragment shader
        content = file.read(fragment)
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
