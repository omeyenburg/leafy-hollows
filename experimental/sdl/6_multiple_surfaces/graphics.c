#include <stdio.h>
#include "SDL2/SDL.h"
#include "SDL2/SDL_image.h"
#include "SDL2/SDL_ttf.h"
#include "glad/include/glad/glad.h"


// Window variables
SDL_DisplayMode monitor_size;
int window_size[2];
SDL_Window* sdl_window;
SDL_GLContext glContext;

// Clock variables
float last_tick_time, max_frame_time, current_time, delta_time, fps, delay = 0;
int vsync;

// Input variables
int mouseX, mouseY;

// Shader variables
GLuint vao, vbo, texture, program;
int timeLocation;

// Surface array
SDL_Surface** surfaces = NULL; // Dynamic array to store surfaces
int numSurfaces = 0;
int maxSurfaces = 0;

// Font array
TTF_Font** fonts = NULL; // Dynamic array to store fonts
int numFonts = 0;
int maxFonts = 0;

// Shader struct
typedef struct Shader {
    GLuint program;
    const char* variableNames;
    void* variableValues;
    int variableNum;
} Shader;

// Shader array
Shader* shaders = NULL;
int numShaders = 0;
int activeShader = -1;


// Vertices constants
GLfloat vertices[] = {
    0.0f, 1.0f, -1.0f, -1.0f,  // bottom-left
    0.0f, 0.0f, -1.0f, 1.0f,   // bottom-right
    1.0f, 0.0f, 1.0f, 1.0f,    // top-right
    1.0f, 1.0f, 1.0f, -1.0f    // top-left
};


// Add a new surface to the array
int store_surface(SDL_Surface* surface) {
    if (numSurfaces == maxSurfaces) {
        // If the array is full, resize it by doubling its capacity
        int newMaxSurfaces = (maxSurfaces == 0) ? 1 : (maxSurfaces * 2);
        SDL_Surface** newSurfaces = realloc(surfaces, newMaxSurfaces * sizeof(SDL_Surface));
        if (newSurfaces == NULL) {
            // Error handling if realloc fails
            printf("Failed to resize the surfaces array.\n");
            return -1;
        }
        surfaces = newSurfaces;
        maxSurfaces = newMaxSurfaces;
    }

    // Add the new SurfaceData to the array
    //SDL_FreeSurface(surfaces[numSurfaces]);
    surfaces[numSurfaces] = surface;
    numSurfaces++;
    return numSurfaces - 1;
}

// Add a new font to the array
int store_font(TTF_Font* font) {
    if (numFonts == maxFonts) {
        // If the array is full, resize it by doubling its capacity
        int newMaxFonts = (maxFonts == 0) ? 1 : (maxFonts * 2);
        TTF_Font** newFonts = realloc(fonts, newMaxFonts * sizeof(TTF_Font*));
        if (newFonts == NULL) {
            // Error handling if realloc fails
            printf("Failed to resize the fonts array.\n");
            return -1;
        }
        fonts = newFonts;
        maxFonts = newMaxFonts;
    }

    // Add the new font to the array
    fonts[numFonts] = font;
    numFonts++;
    return numFonts - 1;
}


// Add a new shader to the array
int store_shader(Shader shader) {
    Shader* newShaders = realloc(shaders, sizeof(shaders) + sizeof(shader));
    shaders = newShaders;
    shaders[numShaders] = shader;
    numShaders++;
    return numShaders - 1;
}


// Query the mouse position
void c_get_mousepos(int* x, int* y) {
    *x = mouseX;
    *y = mouseY;
}


// Query the fps
float get_fps() {
    return fps;
}


// Read the content of file
char* read_file(const char* fileName) {
    FILE* fp = fopen(fileName, "rb");
    if (fp == NULL) {
        return "";
    }

    fseek(fp, 0L, SEEK_END);
    long size = ftell(fp);
    rewind(fp);

    char* content = calloc(size + 1, sizeof(char));
    if (content == NULL) {
        fclose(fp);
        return "";
    }

    fread(content, sizeof(char), size, fp);
    fclose(fp);

    return content;
}


// Load and compile a vertex of fragment shader
void compile_shader(GLuint* shaderId, GLenum shaderType, const char* shaderFilePath) {
    GLint isCompiled = 0;
    const char* shaderSource = read_file(shaderFilePath); 

    *shaderId = glCreateShader(shaderType);
    if (*shaderId == 0) {
        printf("Could not load shader: %s!\n", shaderFilePath);
    }

    glShaderSource(*shaderId, 1, (const char**)&shaderSource, NULL);
    glCompileShader(*shaderId);
    glGetShaderiv(*shaderId, GL_COMPILE_STATUS, &isCompiled);
    free((void*)shaderSource);

    if (isCompiled == GL_FALSE) {
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


// Create display surface (surfaces[0])
void create_window_surface() {
	SDL_Surface* window_surface = SDL_CreateRGBSurfaceWithFormat(0, window_size[0], window_size[1], 32, SDL_PIXELFORMAT_RGBA32);
    if (numSurfaces) {
        free(surfaces[0]);
        surfaces[0] = window_surface;
    } else {
        store_surface(window_surface);
    }
}


// Load and store an image
int c_load_image(const char* image_path) {
    SDL_Surface* image = IMG_Load(image_path);
    if (image == NULL) {
        printf("Failed to load image: %s\n", IMG_GetError());
        return -1;
    }
    return store_surface(image);
}


// Blit a surface onto an other (target = 0 -> displayed surface)
void c_blit(int target, int image, int x, int y) {
    SDL_Rect dest_rect = {x, y, surfaces[image]->w, surfaces[image]->h};
    SDL_BlitSurface(surfaces[image], NULL, surfaces[target], &dest_rect);
}


// Draw a rectangle on a surface (target = 0 -> displayed surface)
void c_rect(int target, int r, int g, int b, int x, int y, int width, int height) {
    SDL_Rect rect = {x, y, width, height};
    Uint32 color = SDL_MapRGB(surfaces[target]->format, r, g, b);
    SDL_FillRect(surfaces[target], &rect, color);
}


void c_circle(int target, int r, int g, int b, int px, int py, int radius, int w) {
    Uint32 color = SDL_MapRGB(surfaces[target]->format, r, g, b);
    int sqrRadius = radius * radius;
    int sqrInnerRadius = (radius - w) * (radius - w);

    for (int x = -radius; x <= radius; x++) {
        for (int y = -radius; y <= radius; y++) {
            int distanceSq = (x * x) + (y * y);

            if (x + px >= 0 && x + px < surfaces[target]->w
                && y + py >= 0 && y + py < surfaces[target]->h
                && distanceSq <= sqrRadius && (w == 0 || distanceSq >= sqrInnerRadius)
            ) {
                Uint32* pixel = (Uint32*)surfaces[target]->pixels + (py + y) * surfaces[target]->pitch / sizeof(Uint32) + px + x;
                *pixel = color;
            }
        }
    }
}


void c_pixel(int target, int r, int g, int b, int x, int y) {
    Uint32 color = SDL_MapRGB(surfaces[target]->format, r, g, b);
    Uint32* pixel = (Uint32*)surfaces[target]->pixels + y * surfaces[target]->pitch / sizeof(Uint32) + x;
    *pixel = color; 
}


// Load and store a font from a file (.ttf)
int c_load_font(const char* path, int size) {
    return store_font(TTF_OpenFont(path, size));
}


// Write text onto a surface using a loaded font
void c_write(int target, int font, const char* text, int r, int g, int b, int x, int y) {
    SDL_Color color = {255, 100, 255};
    SDL_Surface* surf = TTF_RenderText_Blended(fonts[font], text, color);
    SDL_Rect dest_rect = {x, y, surf->w, surf->h};
    SDL_BlitSurface(surf, NULL, surfaces[target], &dest_rect);
    SDL_FreeSurface(surf);
}


// Create and store a shader program
int c_load_shader(const char* vertexPath, const char* fragmentPath, const char* variableNames, void* variableValues, int variableNum) {
    program = glCreateProgram();
	GLuint vertexShader, fragmentShader;
	compile_shader(&vertexShader, GL_VERTEX_SHADER, vertexPath);
	compile_shader(&fragmentShader, GL_FRAGMENT_SHADER, fragmentPath);
	link_shader(program, &vertexShader, &fragmentShader);
    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);
    Shader shader = {program, variableNames, variableValues, variableNum};
    return store_shader(shader);
}


// Activate a shader (-1 -> no shader)
void activate_shader(int shader) {
    glUseProgram(shader + 1);
    activeShader = shader + 1;
}


// Initialize the program and create a window
int c_window(const char* caption, int fps_limit) {
    vsync = (fps_limit == 0) ? 1 : 0;

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
    max_frame_time = (vsync == 0) ? 1000.0 / fps_limit : 0;
	
	// Create window
    sdl_window = SDL_CreateWindow(
        caption, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, window_size[0], window_size[1],
        SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE
    );
	glContext = SDL_GL_CreateContext(sdl_window);
	gladLoadGLLoader(SDL_GL_GetProcAddress);

    if (vsync && SDL_GL_SetSwapInterval(1) < 0) {
        printf("Warning: Unable to enable VSync! %s\n", SDL_GetError());
    }

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

    // Create window surface
    create_window_surface();

	// Create window texture
	glGenTextures(1, &texture);
	glBindTexture(GL_TEXTURE_2D, texture);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
	glBindTexture(GL_TEXTURE_2D, 0);

	// Send variables to shader
    timeLocation = glGetUniformLocation(program, "time");
    return 0;
}


// Quit the program
void quit() {
    for (int i = 0; i < numSurfaces; i++) {
        SDL_FreeSurface(surfaces[i]);
        surfaces[i] = NULL;
    }
    free(surfaces);
    for (int i = 0; i < numFonts; i++) {
        TTF_CloseFont(fonts[i]);
        fonts[i] = NULL;
    }
    free(fonts);
    for (int i = 0; i < numShaders; i++) {
        glDeleteProgram(shaders[i].program);
    }
    free(shaders);
    SDL_GL_DeleteContext(glContext);
    SDL_DestroyWindow(sdl_window);
    SDL_Quit();
}


// Update the window and query events
int update() {
    // Query events
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
    	switch (event.type) {
            case SDL_QUIT: 
                quit();
    	        return 0;
            case SDL_WINDOWEVENT:
                if (event.window.event == SDL_WINDOWEVENT_RESIZED) {
                    window_size[0] = event.window.data1;
                    window_size[1] = event.window.data2;
                    create_window_surface();
                    glViewport(0, 0, window_size[0], window_size[1]);
                }
                break;
            default:
                break;
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
 
    // Update shader
	glUniform1f(glGetUniformLocation(activeShader, "time"), current_time / 500.0);		
	glBindTexture(GL_TEXTURE_2D, texture);
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, window_size[0], window_size[1], 0,
                 GL_RGBA, GL_UNSIGNED_BYTE,
                 surfaces[0]->pixels);
	
    // Update display
	glClear(GL_COLOR_BUFFER_BIT);
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4);
    SDL_GL_SwapWindow(sdl_window);

    // Reset surface
	SDL_FillRect(surfaces[0], NULL, 0); // 0 == SDL_MapRGB(surface->format, 0, 0, 0));
    return 1;
}


// Main function for pure-C testing
int main(int argc, char* argv[]) {
    c_window("Test", 1000);

    int tree_image = c_load_image("tree.jpg");
    int player_image = c_load_image("player.png");
    int font = c_load_font("fonts/font.ttf", 50);

    for (int i = 0; i < 3; i++) {
        c_blit(tree_image, player_image, 5 + 20*i, 130 + 20*i);
    }

    int running = 1;
    while (running) {
        float fps = get_fps();
        char c[50];
        sprintf(c, "%g", fps);
        c_write(0, font, c, 0, 0, 255, 500, 100);
        c_blit(0, tree_image, 20, 40);
        for (int x = 0; x < 20; x++) {
            c_blit(0, player_image, 214 + x * 30, 320);
        }
        int x, y;
        c_get_mousepos(&x, &y);
        c_rect(0, 255, 0, 0, x, y, 110, 80);
        running = update();
    }

    quit();
}