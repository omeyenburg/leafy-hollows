/*

Compile with:
gcc main.c ./glad/src/glad.c -I/Library/Frameworks/SDL2.framework/Headers -I./glad/include -F/Library/Frameworks -L/usr/local/Cellar/sdl2/2.26.2/lib -Wl,-rpath,/usr/local/Cellar/sdl2/2.26.2/lib -lSDL2 -lSDL2_image

*/

#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <glad/glad.h>
#include <stdio.h>

#define W 1000
#define H 600

SDL_Surface* surface;


char* get_shader_content(const char* fileName) {
    FILE *fp;
    long size = 0;
    char* shaderContent;
    
    /* Read File to get size */
    fp = fopen(fileName, "rb");
    if(fp == NULL) {
        return "";
    }
    fseek(fp, 0L, SEEK_END);
    size = ftell(fp)+1;
    fclose(fp);

    /* Read File for Content */
    fp = fopen(fileName, "r");
    shaderContent = memset(malloc(size), '\0', size);
    fread(shaderContent, 1, size-1, fp);
    fclose(fp);

    return shaderContent;
}

void compile_shader(GLuint* shaderId, GLenum shaderType, const char* shaderFilePath) {
    GLint isCompiled = 0;
    /* Calls the Function that loads the Shader source code from a file */
    const char* shaderSource = get_shader_content(shaderFilePath); 

    *shaderId = glCreateShader(shaderType);
    if(*shaderId == 0) {
        printf("COULD NOT LOAD SHADER: %s!\n", shaderFilePath);
    }

    glShaderSource(*shaderId, 1, (const char**)&shaderSource, NULL);
    glCompileShader(*shaderId);
    glGetShaderiv(*shaderId, GL_COMPILE_STATUS, &isCompiled);

    if(isCompiled == GL_FALSE) { /* Here You should provide more error details to the User*/
        printf("Shader Compiler Error: %s\n", shaderFilePath);
        glDeleteShader(*shaderId);
        return;
    }
}

void link_shader(GLint program, GLuint* vertexShader, GLuint* fragmentShader) {
	// Attach shaders and link program
    glAttachShader(program, *vertexShader);
	glAttachShader(program, *fragmentShader);
    glLinkProgram(program);

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

	glBindAttribLocation(program, 0, "position");
	glBindAttribLocation(program, 1, "texCoord");

	// Use program
    glUseProgram(program);
}


void blit_image_to_surface(const char* image_path, int x, int y) {
    // Load the image using SDL_image
    SDL_Surface* image = IMG_Load(image_path);
    if (image == NULL) {
        printf("Failed to load image: %s\n", IMG_GetError());
        return;
    }

    // Set the destination rectangle for blitting
    SDL_Rect dest_rect = { x, y, image->w, image->h };

    // Blit the image onto the surface
    SDL_BlitSurface(image, NULL, surface, &dest_rect);

    // Free the loaded image
    SDL_FreeSurface(image);
}

void draw_rect_to_surface(int r, int g, int b, int x, int y, int width, int height) {
    // Set the color for drawing the rectangle
    SDL_Rect rect = {x, y, width, height};
    Uint32 color = SDL_MapRGB(surface->format, r, g, b);
    SDL_FillRect(surface, &rect, color);
}


GLfloat vertices[] = {
    0.0f, 1.0f, -1.0f, -1.0f,  // bottom-left
    0.0f, 0.0f, -1.0f, 1.0f,   // bottom-right
    1.0f, 0.0f, 1.0f, 1.0f,    // top-right
    1.0f, 1.0f, 1.0f, -1.0f    // top-left
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
	float last_tick_time = SDL_GetTicks();
	float current_time, delta_time, fps, delay = 0;
	float max_frame_time = 1000.0 / 60.0;

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
	
	// Create surface
	surface = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);

	// Create texture
	GLuint texture;
	glGenTextures(1, &texture);
	glBindTexture(GL_TEXTURE_2D, texture);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
	glBindTexture(GL_TEXTURE_2D, 0);

	// Create shader program
    GLint program = glCreateProgram();

	GLuint vertexShader, fragmentShader;
	compile_shader(&vertexShader, GL_VERTEX_SHADER, "vertexShader.glsl");
	compile_shader(&fragmentShader, GL_FRAGMENT_SHADER, "fragmentShader.glsl");
	link_shader(program, &vertexShader, &fragmentShader);

	// Send variables to shader
    int timeLocation = glGetUniformLocation(program, "time");
    //int resolutionLocation = glGetUniformLocation(program, "resolution");
    //glUniform2f(resolutionLocation, W, H);

	// Main loop
	int mouseX, mouseY;

    SDL_Event event;
	int running = 1;
    while (running) {
		// Query events
        while (SDL_PollEvent(&event)) {
        	if(event.type == SDL_QUIT){
        	    running = 0;
        	}
		}
		
		// Reset surface
		SDL_FillRect(surface, NULL, 0); // 0 == SDL_MapRGB(surface->format, 0, 0, 0));

		// Get mouse pos
		SDL_GetMouseState(&mouseX, &mouseY);

		// Get ticks
        current_time = SDL_GetTicks();
		delta_time = (current_time - last_tick_time + delta_time * 9) / 10.0;
		if (delta_time != 0) {
			fps =  1000.0 / delta_time;
		}
		printf("%f\n", fps);
		
		if (delta_time < max_frame_time) {
			//printf("%f\n", max_frame_time - delta_time);
			SDL_Delay(max_frame_time - delta_time);
			last_tick_time = current_time;
		} else {
			//printf("none\n");
		}
		//delay = (1000.0 / (fps - 60.0) + delay) / 2.0;
		//printf("%f\n", delay);

		glUniform1f(timeLocation, current_time / 500.0);

		// Draw
		blit_image_to_surface("tree.jpg", 30, 50);
		draw_rect_to_surface(255, 0, 0, mouseX, mouseY, 120, 80);

		
		glBindTexture(GL_TEXTURE_2D, texture);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, W, H, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     surface->pixels);
		
		
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