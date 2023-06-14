#include <stdio.h>
#include <stdlib.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <SDL2/SDL_ttf.h>
#include <glad/glad.h>


// Shader struct
typedef struct Shader {
    GLuint program;
    int variableNum;
    const char* variableNames;
    const char* variableTypes;
    int* variableLocations;
    void (**variableFunctions)(int, void*);
    void** variableValues;
} Shader;


// Window variables
SDL_DisplayMode monitor_size;
int window_size[2], res_window_size[2], resolution;
int fullscreen = 0;
Uint32 windowFlags = SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE;
Uint32 windowFullscreenFlags = SDL_WINDOW_OPENGL | SDL_WINDOW_FULLSCREEN_DESKTOP; // ? SDL_FULLSCREEN
SDL_Window* sdl_window;
SDL_GLContext glContext;

// Clock variables
float last_tick_time, max_frame_time, current_time, delta_time, update_fps, delay = 0;
int vsync;

// Input variables
int mouse_buttons[3] = {0, 0, 0};

// Shader variables
GLuint vao, vbo, ebo, texture_world, texture_ui;

// Surface array
SDL_Surface** surfaces = NULL; // Dynamic array to store surfaces
int numSurfaces = 0;
int maxSurfaces = 0;

// Font array
TTF_Font** fonts = NULL; // Dynamic array to store fonts
int numFonts = 0;
int maxFonts = 0;

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


// Add a new surface to the array
int store_surface(SDL_Surface* surface) {
    if (numSurfaces == maxSurfaces) {
        // If the array is full, resize it by doubling its capacity
        int newMaxSurfaces = (maxSurfaces == 0) ? 1 : (maxSurfaces * 2);
        SDL_Surface** newSurfaces = realloc(surfaces, newMaxSurfaces * sizeof(SDL_Surface*));
        if (newSurfaces == NULL) {
            // Error handling if realloc fails
            printf("Failed to resize the surfaces array.\n");
            free(surfaces);
            return -1;
        }
        surfaces = newSurfaces;
        maxSurfaces = newMaxSurfaces;
    }

    // Add the new SurfaceData to the array
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
            free(fonts);
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
	SDL_Surface* surface_world = SDL_CreateRGBSurfaceWithFormat(0, res_window_size[0], res_window_size[1], 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Surface* surface_ui = SDL_CreateRGBSurfaceWithFormat(0, res_window_size[0], res_window_size[1], 32, SDL_PIXELFORMAT_RGBA32);
    if (numSurfaces) {
        free(surfaces[0]);
        free(surfaces[1]);
        surfaces[0] = surface_world;
        surfaces[1] = surface_ui;
    } else {
        store_surface(surface_world);
        store_surface(surface_ui);
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


// raw a circle on a surface (target = 0 -> displayed surface)
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


// Set a pixel on a surface (target = 0 -> displayed surface)
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
int c_load_shader(const char* vertexPath, const char* fragmentPath, const char** variableNames, const char** variableTypes, int variableNum) {
    GLuint program = glCreateProgram();
    GLuint vertexShader, fragmentShader;

    compile_shader(&vertexShader, GL_VERTEX_SHADER, vertexPath);
    compile_shader(&fragmentShader, GL_FRAGMENT_SHADER, fragmentPath);
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
        } else if (strcmp(variableTypes[i], "vec2") == 0) {  // unsupported
            variableFunctions[i] = uniform2f;
        } else if (strcmp(variableTypes[i], "ivec2") == 0) { // unsupported
            variableFunctions[i] = uniform2i;
        } else if (strcmp(variableTypes[i], "uvec2") == 0) { // unsupported
            variableFunctions[i] = uniform1ui;
        }
    }

    Shader shader = {program, variableNum, *variableNames, *variableTypes, variableLocations, variableFunctions, variableValues};
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


// Generate the SDL_Scancode from a key name
int c_key_identifier(const char* name) {
    return SDL_GetScancodeFromName(name);
}


// Set fps limit
void fps_limit(int max_fps) {
    vsync = (max_fps == 0) ? 1 : 0;
    max_frame_time = (vsync == 0) ? 1000.0 / max_fps : 0;
    if (SDL_GL_SetSwapInterval(vsync) < 0) {
        printf("Warning: Unable to enable VSync! %s\n", SDL_GetError());
    }
}


// Toggle fullscreen mode
void toggle_fullscreen() {
    fullscreen = !fullscreen;
    if (fullscreen) {
        SDL_SetWindowFullscreen(sdl_window, windowFullscreenFlags);
    } else {
        SDL_SetWindowFullscreen(sdl_window, windowFlags);
    }
}


// Initialize the program and create a window
int c_window(const char* caption, int max_fps, int screen_resolution) {
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
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 1);

    // Get screen size
    if (SDL_GetCurrentDisplayMode(0, &monitor_size) != 0) {
        printf("Failed to get display mode: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    // Set window size and resolution
    resolution = screen_resolution;
    window_size[0] = monitor_size.w / 3 * 2;
    window_size[1] = monitor_size.h / 5 * 3;
    res_window_size[0] = window_size[0] / resolution;
    res_window_size[1] = window_size[1] / resolution;
    

	// Create window
    sdl_window = SDL_CreateWindow(caption, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, window_size[0], window_size[1], windowFlags);

	glContext = SDL_GL_CreateContext(sdl_window);
	gladLoadGLLoader(SDL_GL_GetProcAddress);
    fps_limit(max_fps);
    last_tick_time = SDL_GetTicks();

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

    // Create world and ui surface
    create_window_surface();

	// Create world and ui texture
    glGenTextures(1, &texture_world);
	glBindTexture(GL_TEXTURE_2D, texture_world);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);  // pixel
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    //glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); // blur
	//glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glBindTexture(GL_TEXTURE_2D, 0);

	glGenTextures(1, &texture_ui);
	glBindTexture(GL_TEXTURE_2D, texture_ui);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);  // pixel
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    //glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); // blur
	//glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glBindTexture(GL_TEXTURE_2D, 0);

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
    glDeleteTextures(2, &texture_world);
    glDeleteBuffers(1, &vbo);
    glDeleteVertexArrays(1, &vao);
    SDL_GL_DeleteContext(glContext);
    SDL_DestroyWindow(sdl_window);
    TTF_Quit();
    IMG_Quit();
    SDL_Quit();
}


// Update the window and query events
const Uint8* c_update(int* p_running, float* p_fps, int* p_mouse_x, int* p_mouse_y, float* p_mouse_wx, float* p_mouse_wy, int* p_mouse_b1, int* p_mouse_b2, int* p_mouse_b3) {
    // Update mouse
    for (int i = 0; i < 3; i++) {
        if (mouse_buttons[i] == 1) {
            mouse_buttons[i] = 2;
        }
    }
    *p_mouse_wx = 0.0;
    *p_mouse_wy = 0.0;

    // Query events
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
    	switch (event.type) {
            case SDL_QUIT:
                quit();
                *p_running = 0;
                return (const Uint8*)p_running;
            case SDL_WINDOWEVENT:
                if (event.window.event == SDL_WINDOWEVENT_RESIZED) {
                    window_size[0] = event.window.data1;
                    window_size[1] = event.window.data2;
                    res_window_size[0] = window_size[0] / resolution;
                    res_window_size[1] = window_size[1] / resolution;
                    create_window_surface();
                    glViewport(0, 0, window_size[0], window_size[1]);
                }
                break;
            case SDL_MOUSEBUTTONDOWN:
                mouse_buttons[event.button.button - 1] = 1;
                break;
            case SDL_MOUSEBUTTONUP:
                mouse_buttons[event.button.button - 1] = 0;
                break;
            case SDL_MOUSEMOTION:
                *p_mouse_x = event.motion.x / resolution;
                *p_mouse_y = event.motion.y / resolution;
                break;
            case SDL_MOUSEWHEEL:
                *p_mouse_wx = event.wheel.preciseX;
                *p_mouse_wy = event.wheel.preciseY;
                break; // wheel
            default:
                break;
        }
    }
    *p_mouse_b1 = mouse_buttons[0];
    *p_mouse_b2 = mouse_buttons[1];
    *p_mouse_b3 = mouse_buttons[2];
    
	// Get ticks
    current_time = SDL_GetTicks();
	delta_time = (current_time - last_tick_time + delta_time) / 2.0;
    last_tick_time = current_time;
    update_fps += delta_time;
    if (vsync == 0 && current_time - last_tick_time + 3 < max_frame_time) {
        SDL_Delay(max_frame_time - current_time + last_tick_time - 3);
    }
	if (delta_time != 0) {
        if (update_fps > 100) {
            *p_fps = 1000.0 / delta_time;
            update_fps = 0;
        }
	}
 
    // Update textures
    glClear(GL_COLOR_BUFFER_BIT);

    glBindTexture(GL_TEXTURE_2D, texture_world);
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, res_window_size[0], res_window_size[1], 0,
                 GL_RGBA, GL_UNSIGNED_BYTE,
                 surfaces[0]->pixels);

    glBindTexture(GL_TEXTURE_2D, texture_ui);
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, res_window_size[0], res_window_size[1], 0,
                 GL_RGBA, GL_UNSIGNED_BYTE,
                 surfaces[1]->pixels);

    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, texture_world);
    glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, texture_ui);

    // Update shader variables
    glUniform1i(glGetUniformLocation(shaders[activeShader].program, "texWorld"), 0);
    glUniform1i(glGetUniformLocation(shaders[activeShader].program, "texUi"), 1);
    for (int i = 0; i < shaders[activeShader].variableNum; i++) {
        shaders[activeShader].variableFunctions[i](shaders[activeShader].variableLocations[i],
                                                   shaders[activeShader].variableValues[i]);
    }

    // Update display
	glClear(GL_COLOR_BUFFER_BIT);
    glBindVertexArray(vao);
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4);
    glBindVertexArray(0);
    SDL_GL_SwapWindow(sdl_window);

    // Reset surface (0 => SDL_MapRGB(surface->format, 0, 0, 0));)
	SDL_FillRect(surfaces[0], NULL, 0);

    // Return array of keys (SDL_Scancode)
    return SDL_GetKeyboardState(NULL);
}