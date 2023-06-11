#include <stdio.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <SDL2/SDL_ttf.h>
#include <glad/glad.h> // Valid path


SDL_DisplayMode monitor_size;
uint window_size[2];
SDL_Window* sdl_window;
SDL_GLContext glContext;

float last_tick_time, max_frame_time, current_time, delta_time, fps, delay = 0;
int mouseX, mouseY;

GLuint vao, vbo, texture, program;
SDL_Surface* surface;
SDL_Surface* image;

TTF_Font* font;

int timeLocation;


GLfloat vertices[] = {
    0.0f, 1.0f, -1.0f, -1.0f,  // bottom-left
    0.0f, 0.0f, -1.0f, 1.0f,   // bottom-right
    1.0f, 0.0f, 1.0f, 1.0f,    // top-right
    1.0f, 1.0f, 1.0f, -1.0f    // top-left
};

void c_get_mousepos(int* x, int* y) {
    *x = mouseX;
    *y = mouseY;
}

char* get_shader_content(const char* fileName) {
    FILE* fp = fopen(fileName, "rb");
    if (fp == NULL) {
        return "";
    }

    fseek(fp, 0L, SEEK_END);
    long size = ftell(fp);
    rewind(fp);

    char* shaderContent = calloc(size + 1, sizeof(char));
    if (shaderContent == NULL) {
        fclose(fp);
        return "";
    }

    fread(shaderContent, sizeof(char), size, fp);
    fclose(fp);

    return shaderContent;
}

void compile_shader(GLuint* shaderId, GLenum shaderType, const char* shaderFilePath) {
    GLint isCompiled = 0;
    const char* shaderSource = get_shader_content(shaderFilePath); 

    *shaderId = glCreateShader(shaderType);
    if(*shaderId == 0) {
        printf("COULD NOT LOAD SHADER: %s!\n", shaderFilePath);
    }

    glShaderSource(*shaderId, 1, (const char**)&shaderSource, NULL);
    glCompileShader(*shaderId);
    glGetShaderiv(*shaderId, GL_COMPILE_STATUS, &isCompiled);

    if(isCompiled == GL_FALSE) {
        printf("Shader Compiler Error: %s\n", shaderFilePath);
        glDeleteShader(*shaderId);
        return;
    }
}

// Attach shaders and link program
void link_shader(GLint program, GLuint* vertexShader, GLuint* fragmentShader) {
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

    // Shader specific inputs
	glBindAttribLocation(program, 0, "position");
	glBindAttribLocation(program, 1, "texCoord");

	// Use program
    glUseProgram(program);
}


int c_load_image(const char* image_path) {
    image = IMG_Load(image_path);
    if (image == NULL) {
        printf("Failed to load image: %s\n", IMG_GetError());
        return -1;
    }
    return 0;
}


void c_blit(int image_id, int x, int y) {
    //image = IMG_Load(image_path);
    // Set the destination rectangle for blitting
    SDL_Rect dest_rect = { x, y, image->w, image->h };

    // Blit the image onto the surface
    SDL_BlitSurface(image, NULL, surface, &dest_rect);

    // Free the loaded image
}

void c_rect(int r, int g, int b, int x, int y, int width, int height) {
    SDL_Rect rect = {x, y, width, height};
    Uint32 color = SDL_MapRGB(surface->format, r, g, b);
    SDL_FillRect(surface, &rect, color);
}

int c_window(char* caption, int fps_limit) {
    // Init SDL
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        printf("Could not initailize SDL2, error: %s\n", SDL_GetError());
        return 1;
    }
    
    // Init SDL Font
    if (TTF_Init() != 0) {
        printf("Could not initailize SDL2_ttf, error: %s\n", TTF_GetError());
        SDL_Quit();
        return 1;
    }
	
	// OpenGL 3.3 core
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);

    // Get screen size
    if (SDL_GetCurrentDisplayMode(0, &monitor_size) != 0) {
        printf("Failed to get display mode: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    // Set window size and position
    window_size[0] = monitor_size.w / 3 * 2;
    window_size[1] = monitor_size.h / 5 * 3;

    last_tick_time = SDL_GetTicks();
    max_frame_time = 1000.0 / fps_limit;
	
	// Create window
    sdl_window = SDL_CreateWindow(caption, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, window_size[0], window_size[1], SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE);
	
	glContext = SDL_GL_CreateContext(sdl_window);
	gladLoadGLLoader(SDL_GL_GetProcAddress);

	// Set up OpenGL
    glViewport(0, 0, window_size[0], window_size[1]);
	glClearColor(0.0, 0.0, 0.0, 0.0);
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_BLEND);
	glDisable(GL_CULL_FACE);
	
	// Create VAO and VBO
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
	surface = SDL_CreateRGBSurfaceWithFormat(0, window_size[0], window_size[1], 32, SDL_PIXELFORMAT_RGBA32);

	// Create texture
	glGenTextures(1, &texture);
	glBindTexture(GL_TEXTURE_2D, texture);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
	glBindTexture(GL_TEXTURE_2D, 0);

	// Create shader program
    program = glCreateProgram();
	GLuint vertexShader, fragmentShader;
	compile_shader(&vertexShader, GL_VERTEX_SHADER, "shaders/vertexTemplate.glsl");
	compile_shader(&fragmentShader, GL_FRAGMENT_SHADER, "shaders/fragmentTemplate.glsl");
	link_shader(program, &vertexShader, &fragmentShader);

	// Send variables to shader
    timeLocation = glGetUniformLocation(program, "time");
    //int resolutionLocation = glGetUniformLocation(program, "resolution");
    //glUniform2f(resolutionLocation, W, H);	

    font = TTF_OpenFont("fonts/font.ttf", 32);

    SDL_Color textColor = {255, 100, 255};
    image = TTF_RenderText_Blended(font, "Mike SDL2 Series", textColor);


    return 0;
}

int update() {
        SDL_Event event;
        int running = 1;
        while (SDL_PollEvent(&event)) {
        	if(event.type == SDL_QUIT){
        	    running = 0;
        	}
        }
		

		// Get mouse pos
		SDL_GetMouseState(&mouseX, &mouseY);

		// Get ticks
        current_time = SDL_GetTicks();
		delta_time = (current_time - last_tick_time + delta_time * 9.0) / 10.0;
        last_tick_time = current_time;
		if (delta_time != 0) {
			fps =  1000.0 / delta_time;
		}
		//printf("%f\n", fps);
 
		glUniform1f(timeLocation, current_time / 500.0);		

		
		glBindTexture(GL_TEXTURE_2D, texture);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, window_size[0], window_size[1], 0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     surface->pixels);
		
		
		glClear(GL_COLOR_BUFFER_BIT);
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4);

        SDL_GL_SwapWindow(sdl_window);

        // Reset surface
		SDL_FillRect(surface, NULL, 0); // 0 == SDL_MapRGB(surface->format, 0, 0, 0));

        SDL_Color textColor = {255, 100, 255};
        static char buffer[32];
        snprintf(buffer, sizeof(buffer), "%.2f", fps);
        image = TTF_RenderText_Blended(font, buffer, textColor);

        return running;
}

void quit() {
    TTF_CloseFont(font);
    SDL_FreeSurface(image);
    SDL_GL_DeleteContext(glContext);
    SDL_DestroyWindow(sdl_window);
    SDL_Quit();
}