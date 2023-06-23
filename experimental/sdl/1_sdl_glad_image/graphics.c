#include <stdio.h>   // printf
#include <stdbool.h> // bool
#include <stdlib.h>  // files
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <glad/glad.h>

// Define the surface and texture variables
SDL_Surface* surface = NULL;
SDL_Texture* texture = NULL;

typedef struct Window {
    SDL_Window* sdl_window;
    SDL_GLContext context;
    SDL_Renderer* renderer;
	int width;
	int height;
} Window;

// Function to create a surface and texture
void create_surface_and_texture(Window w) {
    // Get the window's renderer
    SDL_Renderer* renderer = w.renderer;

    // Create a surface compatible with the renderer's target
    surface = SDL_CreateRGBSurfaceWithFormat(0, w.width, w.height, 32, SDL_PIXELFORMAT_RGBA32);

    // Create a texture from the surface
    texture = SDL_CreateTextureFromSurface(renderer, surface);
}

// Function to draw a rectangle onto the surface
void draw_rect_to_surface(int r, int g, int b, int x, int y, int width, int height) {
    // Set the color for drawing the rectangle
    SDL_Rect rect = { x, y, width, height };
    Uint32 color = SDL_MapRGB(surface->format, r, g, b);
    SDL_FillRect(surface, &rect, color);
}

// Function to blit an image onto the surface
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

char* get_shader_content(const char* fileName) {
    FILE *fp;
    long size = 0;
    char* content;
    
    // Read file size
    fp = fopen(fileName, "rb");
    if(fp == NULL) {
        return "";
    }
    fseek(fp, 0L, SEEK_END);
    size = ftell(fp)+1;
    fclose(fp);

    // Read file content
    fp = fopen(fileName, "r");
    content = memset(malloc(size), '\0', size);
    fread(content, 1, size-1, fp);
    fclose(fp);

    return content;
}

Window window(const char* caption) {
	SDL_Init(SDL_INIT_VIDEO);

    // OpenGL 3.3 core
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);

    // Get screen size
    SDL_DisplayMode screen_size;
    SDL_GetCurrentDisplayMode(0, &screen_size);

    // Set window size and position
    int window_w = screen_size.w / 3 * 2;
    int window_h = screen_size.h / 5 * 3;
    int window_x = screen_size.w / 2 - window_w / 2;
    int window_y = screen_size.h / 2 - window_h / 2;

    // Create window
	SDL_Window* sdl_window = SDL_CreateWindow(caption, window_x, window_y, window_w, window_h,
                                              SDL_WINDOW_SHOWN | SDL_WINDOW_OPENGL);

    // Create OpenGL context
	SDL_GLContext context;
    context = SDL_GL_CreateContext(sdl_window);
	gladLoadGLLoader(SDL_GL_GetProcAddress);

    // Create SDL renderer
	SDL_Renderer* renderer = SDL_CreateRenderer(sdl_window, -1, SDL_RENDERER_ACCELERATED);

    // Set up OpenGL
    glViewport(0, 0, window_w, window_h);
    glClearColor(0.0, 0.0, 0.0, 0.0);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_BLEND);
    glDisable(GL_CULL_FACE);

    // Set up texture 1
    GLuint texture = 1;
    glGenTextures(1, &texture); // i, 1 = tex1
    glBindTexture(GL_TEXTURE_2D, 1); // 1 = tex1
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

    // Unbind texture 1
    glBindTexture(GL_TEXTURE_2D, 0);

    /*////////// SHADER */
    char* vertexSource = get_shader_content("shaders/template.vert");
    char* fragmentSource = get_shader_content("shaders/template.frag");

    GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);

    const GLchar *source = (const GLchar *)vertexSource;//.c_str();
    glShaderSource(vertexShader, 1, &source, 0);

    glCompileShader(vertexShader);

    GLint isCompiled = 0;
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &isCompiled);
    if (isCompiled == GL_FALSE)
    {
        GLint maxLength = 0;
        glGetShaderiv(vertexShader, GL_INFO_LOG_LENGTH, &maxLength);

        GLchar *infoLog = (GLchar *)malloc(maxLength * sizeof(GLchar));
        glGetShaderInfoLog(vertexShader, maxLength, &maxLength, infoLog);

        glDeleteShader(vertexShader);

        free(infoLog);
        //return;
    }

    GLuint fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);

    source = (const GLchar *)fragmentSource;//.c_str();
    glShaderSource(fragmentShader, 1, &source, 0);

    glCompileShader(fragmentShader);

    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &isCompiled);
    if (isCompiled == GL_FALSE)
    {
        GLint maxLength = 0;
        glGetShaderiv(fragmentShader, GL_INFO_LOG_LENGTH, &maxLength);

        GLchar *infoLog = (GLchar *)malloc(maxLength * sizeof(GLchar));
        glGetShaderInfoLog(fragmentShader, maxLength, &maxLength, infoLog);

        glDeleteShader(fragmentShader);
        glDeleteShader(vertexShader);

        free(infoLog);
        //return;
    }

    GLuint program = glCreateProgram();

    glAttachShader(program, vertexShader);
    glAttachShader(program, fragmentShader);

    glLinkProgram(program);

    GLint isLinked = 0;
    glGetProgramiv(program, GL_LINK_STATUS, (int *)&isLinked);
    if (isLinked == GL_FALSE)
    {
        GLint maxLength = 0;
        glGetProgramiv(program, GL_INFO_LOG_LENGTH, &maxLength);

        GLchar *infoLog = (GLchar *)malloc(maxLength * sizeof(GLchar));
        glGetProgramInfoLog(program, maxLength, &maxLength, infoLog);

        glDeleteProgram(program);
        glDeleteShader(vertexShader);
        glDeleteShader(fragmentShader);

        free(infoLog);
        //return;
    }

    glDetachShader(program, vertexShader);
    glDetachShader(program, fragmentShader);

    glUseProgram(program);

    /* SHADER //////////*/

    Window w = {sdl_window, context, renderer, window_w, window_h};
    return w;
}

void quit(Window w) {
    GLuint texture = 1;
    glDeleteTextures(1, &texture);
    SDL_DestroyWindow(w.sdl_window);
	SDL_Quit();
}

int update(Window w) {
    bool running = true;

    SDL_Event event;
	while (SDL_PollEvent(&event)) {
        if(event.type == SDL_QUIT){
            running = false;
        }
	}
	/*
    glClear(GL_COLOR_BUFFER_BIT);

    
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4);

	SDL_RenderPresent(w.renderer);
    SDL_SetRenderDrawColor(w.renderer, 0, 0, 0, SDL_ALPHA_OPAQUE);
    SDL_RenderClear(w.renderer);


    // Update the texture with the modified surface
    SDL_UpdateTexture(texture, NULL, surface->pixels, surface->pitch);

    // Render the texture onto the renderer
    SDL_RenderCopy(w.renderer, texture, NULL, NULL);

    // Present the renderer to the window
    SDL_RenderPresent(w.renderer);


    SDL_Delay(16);
	*/
	glClear(GL_COLOR_BUFFER_BIT);

    // Render your OpenGL objects here

    // Update the texture with the modified surface
    SDL_UpdateTexture(texture, NULL, surface->pixels, surface->pitch);

    // Render the texture onto the renderer
    SDL_RenderCopy(w.renderer, texture, NULL, NULL);

    // Present the renderer to the window
    SDL_RenderPresent(w.renderer);

    SDL_Delay(16);
    return running;
}
/*
void draw_rect(Window w, int r, int g, int b, int x, int y, int width, int height) {
	SDL_Rect rectangle;
    rectangle.x = x;
    rectangle.y = y;
    rectangle.w = width;
    rectangle.h = height;
	
    SDL_SetRenderDrawColor(w.renderer, r, g, b, SDL_ALPHA_OPAQUE);
	SDL_RenderFillRect(w.renderer, &rectangle);
}*/