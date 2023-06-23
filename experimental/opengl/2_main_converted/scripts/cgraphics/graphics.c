#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "glad/include/glad/glad.h"


// Shader struct
typedef struct Shader {
    GLuint program;
    int variableNum;
    const char* variableNames;
    const char* variableTypes;
    int* variableLocations;
    void (**variableFunctions)(int, void*);
    void** variableValues;
    int texLoc[2];
} Shader;

// Shader variables
GLuint vao, vbo, ebo;

// Shader array
Shader* shaders = NULL;
int numShaders = 0;
int activeShader = 0;

// Vertices
GLfloat vertices[] = {
    0.0f, 1.0f, -1.0f, -1.0f,  // bottom-left
    0.0f, 0.0f, -1.0f, 1.0f,   // bottom-right
    1.0f, 0.0f, 1.0f, 1.0f,    // top-right
    1.0f, 1.0f, 1.0f, -1.0f    // top-left
};

// Indices
GLuint indices[] = {
    0, 1, 2,   // triangle 1
    2, 3, 0    // triangle 2
};


// Add a new shader to the array
int store_shader(Shader shader) {
    Shader* newShaders = realloc(shaders, sizeof(shaders) + sizeof(shader));
    if (newShaders == NULL) {
        // Error handling if realloc fails
        printf("Failed to resize the fonts array.\n");
        free(shaders);
        return -1;
    }
    shaders = newShaders;
    shaders[numShaders] = shader;
    numShaders++;
    return numShaders - 1;
}


int c_info_max_tex_size() {
    GLint max_tex_size;
    glGetIntegerv(GL_MAX_TEXTURE_SIZE, &max_tex_size);
    return max_tex_size;
}


// Load and compile a vertex of fragment shader
void compile_shader(GLuint* shaderId, GLenum shaderType, const char* shader_content) {
    GLint isCompiled = 0;

    *shaderId = glCreateShader(shaderType);
    if (*shaderId == 0) {
        printf("Could not load shader\n");
    }

    glShaderSource(*shaderId, 1, (const char**)&shader_content, NULL);
    glCompileShader(*shaderId);
    glGetShaderiv(*shaderId, GL_COMPILE_STATUS, &isCompiled);
    free((void*)shader_content);

    if (isCompiled == GL_FALSE) {
        printf("Shader Compiler Error\n");
        glDeleteShader(*shaderId);
        return;
    }
}


// Attach shaders and link program
void link_shader(GLint program, GLuint* vertexShader, GLuint* fragmentShader) {
    glAttachShader(program, *vertexShader);
	glAttachShader(program, *fragmentShader);
    glLinkProgram(program);

    // Error handling
    GLint linkStatus;
    glGetProgramiv(program, GL_LINK_STATUS, &linkStatus);
    if (linkStatus == GL_FALSE) {
        GLint infoLogLength;
        glGetProgramiv(program, GL_INFO_LOG_LENGTH, &infoLogLength);
        GLchar* infoLog = (GLchar*)malloc(infoLogLength * sizeof(GLchar));
        glGetProgramInfoLog(program, infoLogLength, NULL, infoLog);
        printf("Program Linking Error: %s\n", infoLog);
        free(infoLog);
        return;
    }

    // Shader specific inputs
	glBindAttribLocation(program, 0, "position");
	glBindAttribLocation(program, 1, "texCoord");
}


// Cast types
void uniform1f(int location, void* value) {
    float typevar = *(float*)value;
    glUniform1f(location, typevar);
}
void uniform1i(int location, void* value) {
    int typevar = *(int*)value;
    glUniform1i(location, typevar);
}
void uniform1ui(int location, void* value) {
    int typevar = *(int*)value;
    glUniform1ui(location, typevar);
}
void uniform2f(int location, void* value) {
    const float* typevar = (float*)value;
    glUniform2f(location, typevar[0], typevar[1]);
}
void uniform2i(int location, void* value) {
    const int* typevar = (int*)value;
    glUniform2i(location, typevar[0], typevar[1]);
}
void uniform2ui(int location, void* value) {
    const int* typevar = (int*)value;
    glUniform2ui(location, typevar[0], typevar[1]);
}


// Create and store a shader program
int c_load_shader(const char* vertex, const char* fragment, const char** variableNames, const char** variableTypes, int variableNum) {
    GLuint program = glCreateProgram();
    GLuint vertexShader, fragmentShader;

    compile_shader(&vertexShader, GL_VERTEX_SHADER, vertex);
    compile_shader(&fragmentShader, GL_FRAGMENT_SHADER, fragment);
    link_shader(program, &vertexShader, &fragmentShader);

    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);

    int* variableLocations = malloc(variableNum * sizeof(int*));
    void (**variableFunctions)(int, void*) = malloc(variableNum * sizeof(void*));
    void** variableValues = malloc(variableNum * sizeof(void*));

    for (int i = 0; i < variableNum; i++) {
        variableLocations[i] = glGetUniformLocation(program, variableNames[i]);
        if (strcmp(variableTypes[i], "float") == 0) {
            variableFunctions[i] = uniform1f;
            variableValues[i] = malloc(sizeof(float));
            *(int*)(variableValues[i]) = 0.0f;
        } else if (strcmp(variableTypes[i], "int") == 0) {
            variableFunctions[i] = uniform1i;
            variableValues[i] = malloc(sizeof(int));
            *(int*)(variableValues[i]) = 0;
        } else if (strcmp(variableTypes[i], "uint") == 0) {
            variableFunctions[i] = uniform1ui;
        } else if (strcmp(variableTypes[i], "vec2") == 0) {  // currently unsupported
            variableFunctions[i] = uniform2f;
        } else if (strcmp(variableTypes[i], "ivec2") == 0) { // currently unsupported
            variableFunctions[i] = uniform2i;
        } else if (strcmp(variableTypes[i], "uvec2") == 0) { // currently unsupported
            variableFunctions[i] = uniform1ui;
        }
    }

    int texLoc[2] = {glGetUniformLocation(program, "texWorld"),
                     glGetUniformLocation(program, "texUi")};

    Shader shader = {program, variableNum, *variableNames, *variableTypes, variableLocations,
                     variableFunctions, variableValues, {texLoc[0], texLoc[1]}};
    return store_shader(shader);
}


// Overwrite a variable value with it's index
void c_update_shader_value(int shader, int index, void* value) {
    *(int*)(shaders[shader].variableValues[index]) = *(int*)value;
}


// Activate a shader (-1 -> no shader)
void activate_shader(int shader) {
    glUseProgram(shader + 1);
    activeShader = shader;
}


GLuint c_create_texture(int width, int height, const char* data) {
    GLuint texture;
    glGenTextures(1, &texture);
	glBindTexture(GL_TEXTURE_2D, texture);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);  // pixel
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, data);
    glBindTexture(GL_TEXTURE_2D, 0);
    return texture;
}


// Initialize the program and create a window
int c_init(int width, int height) {
	// Set up OpenGL
    printf("A\n");
    //glViewport(0, 0, width, height);
	glClearColor(0.0, 0.0, 0.0, 0.0);
    printf("D\n");
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_BLEND);
	glDisable(GL_CULL_FACE);

    printf("B\n");

    // Create VAO and VBO
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);

    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    glGenBuffers(1, &ebo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);

    // Specify vertex attributes
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), 0);
    glEnableVertexAttribArray(0);

    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), (GLvoid*)(2 * sizeof(GLfloat)));
    glEnableVertexAttribArray(1);

    // Unbind VAO and buffers
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
    /*
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, texture_world);
    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, texture_ui);
    */
    printf("C\n");
    return 0;
}


void resize_window(int width, int height) {
    glViewport(0, 0, width, height);
}


// Quit the program
void c_quit() {
    for (int i = 0; i < numShaders; i++) {
        glDeleteProgram(shaders[i].program);
    }
    free(shaders);
    //glDeleteTextures(2, &texture_world);
    glDeleteBuffers(1, &vbo);
    glDeleteVertexArrays(1, &vao);
}


// Update the window and query events
void c_update() {
    // Update shader variables
    glUniform1i(shaders[activeShader].texLoc[0], 0);
    glUniform1i(shaders[activeShader].texLoc[1], 1);
    for (int i = 0; i < shaders[activeShader].variableNum; i++) {
        shaders[activeShader].variableFunctions[i](shaders[activeShader].variableLocations[i],
                                                   shaders[activeShader].variableValues[i]);
    }

    // Update display
	glClear(GL_COLOR_BUFFER_BIT);
    glBindVertexArray(vao);
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4);
    glBindVertexArray(0);
    return;
}

int main() {}