#include <stdio.h>   // printf
#include <stdbool.h> // bool
#include <stdlib.h>  // files
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <glad/glad.h>

SDL_DisplayMode screen_size;
int window_w, window_h, window_x, window_y;
SDL_Window* window;
SDL_GLContext context;
SDL_Renderer* renderer;
GLuint program;

SDL_Surface* render_surf;
SDL_Texture* render_tex;

GLuint texture = 0;
GLuint vao = 1;
GLuint vbo_vertices = 2;
GLuint vbo_texcoords = 3;


char* get_shader_content(const char* fileName) {
    FILE* fp;
    long size = 0;
    char* content;

    // Read file size
    fp = fopen(fileName, "rb");
    if (fp == NULL) {
        printf("Failed to open file: %s\n", fileName);
        return NULL;
    }
    fseek(fp, 0L, SEEK_END);
    size = ftell(fp) + 1;
    fclose(fp);

    // Read file content
    fp = fopen(fileName, "r");
    content = memset(malloc(size), '\0', size);
    fread(content, 1, size - 1, fp);
    fclose(fp);

    return content;
}

int create_window(const char* caption) {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL initialization failed: %s\n", SDL_GetError());
        return 1;
    }

    // OpenGL 3.3 core
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    //SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    //SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);

    // Get screen size
    if (SDL_GetCurrentDisplayMode(0, &screen_size) != 0) {
        printf("Failed to get display mode: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    // Set window size and position
    window_w = screen_size.w / 3 * 2;
    window_h = screen_size.h / 5 * 3;
    window_x = screen_size.w / 2 - window_w / 2;
    window_y = screen_size.h / 2 - window_h / 2;

    // Create window
    window = SDL_CreateWindow(caption, window_x, window_y, window_w, window_h,
                              SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE);
    if (window == NULL) {
        printf("Failed to create SDL window: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    // Create OpenGL context
    context = SDL_GL_CreateContext(window);
    if (context == NULL) {
        printf("Failed to create OpenGL context: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    // Initialize GLAD
    if (!gladLoadGLLoader(SDL_GL_GetProcAddress)) {
        printf("Failed to initialize GLAD\n");
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    // Set up SDL renderer
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (renderer == NULL) {
        printf("Failed to create SDL renderer: %s\n", SDL_GetError());
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    // Set up OpenGL
    glViewport(0, 0, window_w, window_h);
    glClearColor(0.0, 0.0, 0.0, 0.0);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_BLEND);
    glDisable(GL_CULL_FACE);

    // Vertex data
    float vertices[] = {
        0.0, 0.0,
        0.0, 1.0,
        1.0, 1.0,
        1.0, 0.0
    };

    float texcoords[] = {
        -1.0, -1.0,
        -1.0, 1.0,
        1.0, 1.0,
        1.0, -1.0
    };

    // Create VAO
    glGenVertexArrays(1, &vao);
    glBindVertexArray(vao);

    // Create VBOs
    glGenBuffers(1, &vbo_vertices);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_vertices);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, NULL);
    glEnableVertexAttribArray(0);

    glGenBuffers(1, &vbo_texcoords);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_texcoords);
    glBufferData(GL_ARRAY_BUFFER, sizeof(texcoords), texcoords, GL_STATIC_DRAW);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, NULL);
    glEnableVertexAttribArray(1);

    // Set up texture
    glGenTextures(1, &texture);
    glBindTexture(GL_TEXTURE_2D, texture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    // Unbind texture
    glBindTexture(GL_TEXTURE_2D, 0);

    /*////////// SHADER */
    char* vertexSource = get_shader_content("shaders/template.vert");
    if (vertexSource == NULL) {
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    char* fragmentSource = get_shader_content("shaders/template.frag");
    if (fragmentSource == NULL) {
        free(vertexSource);
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, (const GLchar**)&vertexSource, NULL);
    glCompileShader(vertexShader);

    GLint isCompiled = 0;
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &isCompiled);
    if (isCompiled == GL_FALSE) {
        GLint maxLength = 0;
        glGetShaderiv(vertexShader, GL_INFO_LOG_LENGTH, &maxLength);

        GLchar* infoLog = (GLchar*)malloc(maxLength * sizeof(GLchar));
        glGetShaderInfoLog(vertexShader, maxLength, &maxLength, infoLog);

        printf("Vertex shader compilation failed: %s\n", infoLog);

        glDeleteShader(vertexShader);
        free(infoLog);
        free(vertexSource);
        free(fragmentSource);
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    GLuint fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, (const GLchar**)&fragmentSource, NULL);
    glCompileShader(fragmentShader);

    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &isCompiled);
    if (isCompiled == GL_FALSE) {
        GLint maxLength = 0;
        glGetShaderiv(fragmentShader, GL_INFO_LOG_LENGTH, &maxLength);

        GLchar* infoLog = (GLchar*)malloc(maxLength * sizeof(GLchar));
        glGetShaderInfoLog(fragmentShader, maxLength, &maxLength, infoLog);

        printf("Fragment shader compilation failed: %s\n", infoLog);

        glDeleteShader(fragmentShader);
        glDeleteShader(vertexShader);
        free(infoLog);
        free(vertexSource);
        free(fragmentSource);
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    program = glCreateProgram();
    glAttachShader(program, vertexShader);
    glAttachShader(program, fragmentShader);
    glLinkProgram(program);

    
    

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, vertices);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, texcoords);
    glEnableVertexAttribArray(0);
    glEnableVertexAttribArray(1);

    GLint isLinked = 0;
    glGetProgramiv(program, GL_LINK_STATUS, &isLinked);
    if (isLinked == GL_FALSE) {
        GLint maxLength = 0;
        glGetProgramiv(program, GL_INFO_LOG_LENGTH, &maxLength);

        GLchar* infoLog = (GLchar*)malloc(maxLength * sizeof(GLchar));
        glGetProgramInfoLog(program, maxLength, &maxLength, infoLog);

        printf("Program linking failed: %s\n", infoLog);

        glDeleteProgram(program);
        glDeleteShader(fragmentShader);
        glDeleteShader(vertexShader);
        free(infoLog);
        free(vertexSource);
        free(fragmentSource);
        SDL_GL_DeleteContext(context);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    glDetachShader(program, vertexShader);
    glDetachShader(program, fragmentShader);

    glUseProgram(program);

    free(vertexSource);
    free(fragmentSource);

    /* SHADER //////////*/

    return 0;
}

void quit() {
    SDL_GL_DeleteContext(context);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
}

int update() {
    bool running = true;

    SDL_Event event;
	while (SDL_PollEvent(&event)) {
        if(event.type == SDL_QUIT){
            running = false;
        }
	}

    glBindTexture(GL_TEXTURE_2D, texture);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, window_w, window_h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     render_surf->pixels);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, texture);

    glUniform1i(glGetUniformLocation(program, "texWorld"), 0);

    glBindVertexArray(vao);

    glDrawArrays(GL_TRIANGLE_FAN, 0, 4);
    
    //glDrawArrays(GL_QUADS, 0, 4);

    SDL_UpdateWindowSurface(window);
	SDL_RenderPresent(renderer);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, SDL_ALPHA_OPAQUE);
    SDL_RenderClear(renderer);
    SDL_GL_SwapWindow(window);
    SDL_Delay(16);

    glClear(GL_COLOR_BUFFER_BIT);

    return running;
}

// Function to create a surface and texture
void create_surface_and_texture() {

    // Create a surface compatible with the renderer's target
    render_surf = SDL_CreateRGBSurfaceWithFormat(0, window_w, window_h, 32, SDL_PIXELFORMAT_RGBA32);

    // Create a texture from the surface
    render_tex = SDL_CreateTextureFromSurface(renderer, render_surf);
}

// Function to draw a rectangle onto the surface
void draw_rect_to_surface(int r, int g, int b, int x, int y, int width, int height) {
    // Set the color for drawing the rectangle
    SDL_Rect rect = {x, y, width, height};
    Uint32 color = SDL_MapRGB(render_surf->format, r, g, b);
    SDL_FillRect(render_surf, &rect, color);
}

// Function to blit an image onto the surface
void blit_image_to_surface(const char* image_path, int x, int y) {
    // Load the image using SDL_image
    SDL_Surface* image = IMG_Load(image_path);
    // faster: IMG_LoadTexture
    if (image == NULL) {
        printf("Failed to load image: %s\n", IMG_GetError());
        return;
    }

    // Set the destination rectangle for blitting
    SDL_Rect dest_rect = { x, y, image->w, image->h };

    // Blit the image onto the surface
    SDL_BlitSurface(image, NULL, render_surf, &dest_rect);

    // Free the loaded image
    SDL_FreeSurface(image);
}