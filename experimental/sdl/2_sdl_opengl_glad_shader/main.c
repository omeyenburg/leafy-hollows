/*

Compile with:
gcc main.c ./glad/src/glad.c -I/Library/Frameworks/SDL2.framework/Headers -I./glad/include -F/Library/Frameworks -L/usr/local/Cellar/sdl2/2.26.2/lib -Wl,-rpath,/usr/local/Cellar/sdl2/2.26.2/lib -lSDL2

*/

#include <SDL2/SDL.h>
#include <glad/glad.h>
#include <stdio.h>

#define W 1000
#define H 600


const GLchar* shader_vertex[] = {
    "#version 330 core\n"
    "in vec2 position;\n"
    "in vec2 texCoord;\n"
    "out vec2 fragTexCoord;\n"
    "void main() {\n"
    "    gl_Position = vec4(position, 0.0, 1.0);\n"
    "    fragTexCoord = texCoord;\n"
    "}\n"
};

const GLchar* shader_fragment[] = {
    "#version 330 core\n"
    "uniform float time;\n"
    "uniform vec2 resolution;\n"
    "out vec4 FragColor;\n"
    "void main() {\n"
    "    vec2 uv = gl_FragCoord.xy / resolution.xy;\n"
    "    vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0, 2, 4));\n"
    "    FragColor = vec4(col, 1.0);\n"
    "    if (uv.x < 0.5 && uv.y < 0.5) {FragColor = vec4(1.0, 0.0, 0.0, 1.0);}\n"
    "}\n"
};

GLfloat vertices[] = {
    0.0f, 0.0f, -1.0f, -1.0f,  // bottom-left
    0.0f, 1.0f, -1.0f, 1.0f,  // bottom-right
    1.0f, 1.0f, 1.0f, 1.0f,  // top-right
    1.0f, 0.0f, 1.0f, -1.0f   // top-left
};


int main(int argc, char* argv[]) {
    SDL_Init(SDL_INIT_VIDEO);
	
	// OpenGL 3.3 core
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
	
	// Create window
    SDL_Window* screen = SDL_CreateWindow("Shaders", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, W, H, SDL_WINDOW_OPENGL);
    SDL_GLContext glContext = SDL_GL_CreateContext(screen);
    gladLoadGLLoader(SDL_GL_GetProcAddress);

	// Set up OpenGL
    glViewport(0, 0, W, H);
	glClearColor(0.0, 0.0, 0.0, 0.0);
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_BLEND);
	glDisable(GL_CULL_FACE);
	
	// Create VAO and VBO
	GLuint vao, vbo;
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);

    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), 0);
	glEnableVertexAttribArray(0);
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * sizeof(GLfloat), (GLvoid*)(2 * sizeof(GLfloat)));
	glEnableVertexAttribArray(1);

	// Create texture
	GLuint texture;
	glGenTextures(1, &texture);
	glBindTexture(GL_TEXTURE_2D, texture);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
	glBindTexture(GL_TEXTURE_2D, 0);

	// Create shader program
    int p = glCreateProgram();
	
	// Compile fragment shader
	int fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, shader_fragment, NULL);
    glCompileShader(fragmentShader);
	GLint fragmentCompileStatus;
    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &fragmentCompileStatus);
    if (fragmentCompileStatus == GL_FALSE) {
        return -1;
    }

	// Compile vertex shader
	GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);
	glShaderSource(vertexShader, 1, shader_vertex, NULL);
	glCompileShader(vertexShader);
	GLint vertexCompileStatus;
	glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &vertexCompileStatus);
	if (vertexCompileStatus == GL_FALSE) {
	    return -1;
	}

	// Attach shaders and link program
    glAttachShader(p, vertexShader);
	glAttachShader(p, fragmentShader);
    glLinkProgram(p);

    GLint linkStatus;
    glGetProgramiv(p, GL_LINK_STATUS, &linkStatus);
    if (linkStatus == GL_FALSE) {
        GLint infoLogLength;
        glGetProgramiv(p, GL_INFO_LOG_LENGTH, &infoLogLength);
        GLchar* infoLog = (GLchar*)malloc(infoLogLength * sizeof(GLchar));
        glGetProgramInfoLog(p, infoLogLength, NULL, infoLog);
        printf("Program Linking Error: %s\n", infoLog);
        free(infoLog);
        return -1;
    }

	glBindAttribLocation(p, 0, "position");
	glBindAttribLocation(p, 1, "texCoord");

	// Use program
    glUseProgram(p);

	// Send variables to shader
    int timeLocation = glGetUniformLocation(p, "time");
    int resolutionLocation = glGetUniformLocation(p, "resolution");
    glUniform2f(resolutionLocation, W, H);

	// Main loop
    SDL_Event event;
	int running = 1;
    while (running) {
		// Query events
        while (SDL_PollEvent(&event)) {
        	if(event.type == SDL_QUIT){
        	    running = 0;
        	}
		}
        float t = SDL_GetTicks() / 500.0;
        glUniform1f(timeLocation, t);

		/*
		glBindTexture(GL_TEXTURE_2D, texture);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, W, H, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     texture);
		*/
		
		glClear(GL_COLOR_BUFFER_BIT);
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4);

        SDL_GL_SwapWindow(screen);
    }

	// Cleanup
    SDL_GL_DeleteContext(glContext);
    SDL_DestroyWindow(screen);
    SDL_Quit();

    return 0;
}