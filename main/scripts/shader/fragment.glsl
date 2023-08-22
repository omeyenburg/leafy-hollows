#version 330 core

// Inputs from vertex shader
in vec2 vertTexcoord;
flat in vec4 vertSourceOrColor;
flat in float vertShape;

// Output pixel color
out vec4 fragColor;

// Uniform shader inputs
uniform sampler2D texSprites;
uniform sampler2D texFont;
uniform sampler2D texBlocks;
uniform isampler2D texWorld;
uniform vec2 offset;
uniform vec2 camera;
uniform float resolution;
uniform float time;

// Constants
vec2 BLOCK_COUNT;
const int BLOCK_SIZE_SOURCE = 16;
const float BORDER_THRESHOLD = 0.0001;
const vec4 TRANSPARENCY = vec4(0, 0, 0, 0);
const vec4 WATER_COLOR = vec4(0.2, 0.6, 0.9, 0.4);
const float WAVE_AMPLITUDE = 0.05;
const float WAVE_FREQUENCY = 0.3;
const float WATER_PER_BLOCK = 1000.0;
float BLOCK_SIZE_DEST = BLOCK_SIZE_SOURCE * resolution;

// Predefined values
int block_type = 0;
int adjacent_x;
int adjacent_y;
int animation_frames;
int image_id;
float animation_speed;
float amplitude = 0.0;
float amplitude_left = 0.0;
float amplitude_right = 0.0;
ivec2 source_offset;
ivec2 source;
vec2 animation_data;
vec4 block_color;


// Image
void draw_image() {
    if (vertTexcoord.x < BORDER_THRESHOLD || vertTexcoord.y < BORDER_THRESHOLD || vertTexcoord.x > 1.0 - BORDER_THRESHOLD || vertTexcoord.y > 1.0 - BORDER_THRESHOLD) {
        fragColor = TRANSPARENCY;
    } else {
        fragColor = texture(texSprites, vertTexcoord * vertSourceOrColor.zw + vertSourceOrColor.xy);
    }
}


// Circle
void draw_circle() {
    if (length(vertTexcoord - 0.5) <= 0.5) {
        fragColor = vertSourceOrColor;
    } else {
        // Pixel outside circle
        fragColor = TRANSPARENCY;
    }
}


// Text
void draw_text() {
    vec4 text_color = floor(vertSourceOrColor) / 255.0;
    vec4 text_source = fract(vertSourceOrColor);

    if (text_source.w == 0) {
        text_source.w = 1;
    }

    if (texture(texFont, vec2(vertTexcoord.x * text_source.z + text_source.x, vertTexcoord.y * text_source.w + text_source.y)) == vec4(1.0, 1.0, 1.0, 1.0)) {
        fragColor = text_color;
    } else {
        // Pixel outside letter
        fragColor = TRANSPARENCY;
    }
}


// World background
ivec2 get_source_pixel() {
    return ivec2(
        mod(gl_FragCoord.x / resolution + offset.x * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE),
        mod(gl_FragCoord.y / resolution + offset.y * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE) + 1 // Row 0 is used to save animation data
    );
}

ivec2 get_source_pixel_wrapped(int block_type, ivec2 source_pixel_wrapped) {
    int block_family = int(texelFetch(texBlocks, ivec2(block_type - 1, 0), 0).b * 255);
    int block_family_adjacent_x = int(texelFetch(texBlocks, ivec2(adjacent_x - 1, 0), 0).b * 255);
    int block_family_adjacent_y = int(texelFetch(texBlocks, ivec2(adjacent_y - 1, 0), 0).b * 255);
    if (block_family <= block_family_adjacent_x && block_family <= block_family_adjacent_y) {
        source_pixel_wrapped = ivec2(8, 8);
    } else if (block_type <= adjacent_x) {
        if (source_pixel_wrapped.x < BLOCK_SIZE_SOURCE / 2) {
            source_pixel_wrapped.x += 4;
        } else {
            source_pixel_wrapped.x -= 4;
        }
    } else if (block_type <= adjacent_y) {
        if (source_pixel_wrapped.y < BLOCK_SIZE_SOURCE / 2) {
            source_pixel_wrapped.y += 4;
        } else {
            source_pixel_wrapped.y -= 4;
        }
    }
    return source_pixel_wrapped;
}

vec4 get_color_block(int block_type, vec2 source_pixel) {
    if (block_type != 0) {
        // Current frame
        animation_data = texelFetch(texBlocks, ivec2(block_type - 1, 0), 0).rg;
        animation_frames = int(animation_data.r * 255);
        animation_speed = animation_data.g * 2;
        image_id = block_type + int(mod(time / animation_speed / animation_frames, animation_frames)) - 1;

        // Source image coordinate in texture
        source_offset = ivec2(mod(image_id, BLOCK_COUNT.x), image_id / BLOCK_COUNT.x) * BLOCK_SIZE_SOURCE;
        source = ivec2(source_pixel.x + source_offset.x,
                       source_pixel.y + source_offset.y);

        // Fetch and return pixel color
        return texelFetch(texBlocks, source, 0);
    } else {
        // Block is air
        return TRANSPARENCY;
    }
}

vec4 get_color_background() {
    return vec4(sin(vertTexcoord.x) / 2 + 0.5, cos(vertTexcoord.y) / 2 + 0.5, cos(vertTexcoord.x), 0.5);
}

void draw_background() {
    BLOCK_COUNT = textureSize(texBlocks, 0) / BLOCK_SIZE_SOURCE;

    // block in world
    vec2 block_coord = vec2(gl_FragCoord.x / BLOCK_SIZE_DEST + offset.x,
                            gl_FragCoord.y / BLOCK_SIZE_DEST + offset.y);

    // block data (foreground, plant, background, water level)
    ivec4 block_data = texelFetch(texWorld, ivec2(block_coord), 0);
    
    // background block type
    int block_type = block_data.g;
    //block_type = block.stone;

    // Pixel within block
    ivec2 source_pixel = get_source_pixel();
    
    // Background
    vec4 background = get_color_background();
    //fragColor = background;
    //return;

    // Set pixel color
    block_color = get_color_block(block_type, source_pixel);

    // Mix background and block
    if (block_color.a < 1.0) {
        fragColor = block_color * block_color.a + background * (1 - block_color.a);
    } else {
        fragColor = block_color;
    }
}


// Post processing
ivec4 get_next_closest_block(ivec2 source_pixel) {
    int x_distance = int(min(source_pixel.x, BLOCK_SIZE_SOURCE - source_pixel.x));
    int y_distance = int(min(source_pixel.y, BLOCK_SIZE_SOURCE - source_pixel.y));

    if (x_distance <= y_distance) {
        // Block on x-axis
        if (x_distance == source_pixel.x) {
            // left
            return ivec4(15, source_pixel.y, -1, 0);
        }
        // right
        return ivec4(0, source_pixel.y, 1, 0);
    } else {
        // Block on y-axis
        if (y_distance == source_pixel.y) {
            // top
            return ivec4(source_pixel.x, 15, 0, -1);
        }
        // bottom
        return ivec4(source_pixel.x, 0, 0, 1);
    }
}

vec4 get_color_foreground() {
    BLOCK_COUNT = textureSize(texBlocks, 0) / BLOCK_SIZE_SOURCE;

    // block in world
    ivec2 block_coord = ivec2(gl_FragCoord.x / BLOCK_SIZE_DEST + offset.x,
                              gl_FragCoord.y / BLOCK_SIZE_DEST + offset.y);

    // block data (foreground, plant, background, water level)
    ivec4 block_data = texelFetch(texWorld, ivec2(block_coord), 0);
    ivec4 block_data_left = texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y), 0);
    ivec4 block_data_right = texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y), 0);
    ivec4 block_data_top = texelFetch(texWorld, ivec2(block_coord.x, block_coord.y + 1), 0);
    ivec4 block_data_bottom = texelFetch(texWorld, ivec2(block_coord.x, block_coord.y - 1), 0);
    
    // block type
    int block_type = block_data.r;
    int block_type_left = block_data_left.r;
    int block_type_right = block_data_right.r;
    int block_type_top = block_data_top.r;
    int block_type_bottom = block_data_bottom.r;

    if (block_type == 0 && abs(block_data.a) < 1) {
        return TRANSPARENCY;
    }

    // Pixel within block
    ivec2 source_pixel = get_source_pixel();
    vec2 fsource_pixel = vec2(source_pixel) / float(BLOCK_SIZE_SOURCE);
    ivec2 source_pixel_offset = source_pixel;

    // Get adjacent blocks
    if (source_pixel.x < BLOCK_SIZE_SOURCE / 2) {
        adjacent_x = block_type_left;
    } else {
        adjacent_x = block_type_right;
        source_pixel_offset.x -= BLOCK_SIZE_SOURCE;
    }
    if (source_pixel.y < BLOCK_SIZE_SOURCE / 2) {
        adjacent_y = block_type_bottom;
    } else {
        adjacent_y = block_type_top;
        source_pixel_offset.y -= BLOCK_SIZE_SOURCE;
    }

    if (block_type > 0) {
        // Get wrapped source pixel of foreground blocks
        ivec2 source_pixel_wrapped = get_source_pixel_wrapped(block_type, source_pixel);

        // Get pixel color
        block_color = get_color_block(block_type, source_pixel_wrapped);

        if (block_color.a < 1.0) {
            if (block_type != 0) {
                if (abs(source_pixel_offset.x) < abs(source_pixel_offset.y)) {
                    block_color = get_color_block(adjacent_x, ivec2(8, 8));
                } else {
                    block_color = get_color_block(adjacent_y, ivec2(8, 8));
                }
                if (block_color.a > 0.0) {
                    return block_color;
                }
            }
        } else {
            return block_color;
        }
        
        // Set block to the closest other block -> let water flow into transparent gaps
        ivec4 next_closest_block = get_next_closest_block(source_pixel);
        source_pixel = next_closest_block.xy;
        block_coord += next_closest_block.zw;

        block_data = texelFetch(texWorld, ivec2(block_coord), 0);
        block_data_left = texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y), 0);
        block_data_right = texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y), 0);
        block_data_top = texelFetch(texWorld, ivec2(block_coord.x, block_coord.y + 1), 0);
        block_data_bottom = texelFetch(texWorld, ivec2(block_coord.x, block_coord.y - 1), 0);

        block_type = block_data.r;
        block_type_left = block_data_left.r;
        block_type_right = block_data_right.r;
        block_type_top = block_data_top.r;
        block_type_bottom = block_data_bottom.r;
        
    }

    float water_level = block_data.a / WATER_PER_BLOCK;
    float water_level_top = abs(block_data_top.a / WATER_PER_BLOCK);
    float water_level_bottom = abs(block_data_bottom.a / WATER_PER_BLOCK);
    float water_level_left = abs(block_data_left.a / WATER_PER_BLOCK);
    float water_level_right = abs(block_data_right.a / WATER_PER_BLOCK);
    float water_level_top_left = abs(texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y + 1), 0).a / WATER_PER_BLOCK);
    float water_level_top_right = abs(texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y + 1), 0).a / WATER_PER_BLOCK);

    int water_side = 1;
    if (water_level < 0) {
        water_side = -1;
        water_level = abs(water_level);                
    }

    if (water_level_top > BORDER_THRESHOLD && (water_level_left > 1.0 - BORDER_THRESHOLD || water_level_right > 1.0 - BORDER_THRESHOLD)) {
        water_level = 1.0;
    } else if (water_level_left > 1.0 - BORDER_THRESHOLD && water_level_right > 1.0 - BORDER_THRESHOLD) {
        water_level = 1.0;
    } else if (water_level_top > BORDER_THRESHOLD && water_level_top > water_level && block_type == 0) {
        water_level = water_level_top;
    }
    
    if (water_level > 0.1 && block_type == 0) {
        int draw_water = 0;
        int vertical = 0;
        int horizontal = 0;
        int covered = 0;
        int corner = 0;
        float width = min((water_level + water_level_top) * 0.5, 0.2);
        float height = 1.0;

        water_level = max(max(water_level, water_level_left), water_level_right);

        if (water_level_top > BORDER_THRESHOLD && water_level_top_left > 0.1 && water_level_top_right > 0.1) {
            // covered water
            return WATER_COLOR;
        } else if ((block_type_bottom != 0 || water_level_bottom > 0.9) && water_level_top > 0.1) {
            // vertical & horizontal water
            vertical = 1;
            horizontal = 1;
        } else if (block_type_bottom == 0 && water_level_top > 0.1 && (water_level_left < BORDER_THRESHOLD || water_level_right < BORDER_THRESHOLD)) {
            // vertical water
            vertical = 1;
        } else if (block_type_bottom == 0 && water_level_top > 0.1 && (water_level_left > BORDER_THRESHOLD && water_level_right > BORDER_THRESHOLD)) {
            // covered vertical water
            return WATER_COLOR;
        } else if (block_type_bottom == 0 && water_level_top <= 0.1 && (water_level_left < BORDER_THRESHOLD && water_level_right < BORDER_THRESHOLD)) {
            // top of vertical water
            vertical = 1;
            height = water_level;
            width = min(water_level, 0.2);
        } else if (block_type_bottom == 0 && water_level_top < BORDER_THRESHOLD && water_level_bottom < 1.0 - BORDER_THRESHOLD && (water_level_left < BORDER_THRESHOLD && water_level_right > BORDER_THRESHOLD || water_level_right < BORDER_THRESHOLD && water_level_left > BORDER_THRESHOLD)) {
            // corner of vertical water and horizontal on one side
            corner = 1;
            width = min(water_level, 0.2);
        } else {
            // horizontal water
            horizontal = 1;
        } 

        if (vertical == 1 && abs((water_side + 1) / 2 - fsource_pixel.x) <= width && fsource_pixel.y <= height) {
            return WATER_COLOR;
        } else if (corner == 1 && water_side == -1) {
            height = water_level_left;

            if (fsource_pixel.x + fsource_pixel.y <= (width + height) / 2 && fsource_pixel.x <= width && fsource_pixel.y <= height) {
                return WATER_COLOR;
            }
        } else if (corner == 1 && water_side == 1) {
            height = water_level_right;                    

            if (abs((water_side + 1) / 2 - fsource_pixel.x) + fsource_pixel.y <= (width + height) / 2 && 1.0 - fsource_pixel.x <= width && fsource_pixel.y <= height) {
                return WATER_COLOR;
            }
        }

        if (horizontal == 1) {
            if (false && water_level_top > BORDER_THRESHOLD && vertical == 0 || water_level > 1.0 - BORDER_THRESHOLD || water_level_top > 0.1 && water_level_top_left > 0.1 && water_level_left > 1.0 - BORDER_THRESHOLD * 10 || water_level_top > 0.1 && water_level_top_right > 0.1 && water_level_right > 1.0 - BORDER_THRESHOLD * 10) {
                return WATER_COLOR;
            } else {
                // Wave amplitude
                if (block_type_left == 0) {
                    amplitude_left = 1.0;
                }
                if (block_type_right == 0) {
                    amplitude_right = 1.0;
                }
                amplitude = mix(amplitude_left, amplitude_right, fsource_pixel.x);

                // Wave offset
                float wave_x = int(gl_FragCoord / resolution + camera.x * BLOCK_SIZE_SOURCE) * WAVE_FREQUENCY;
                float wave_offset = amplitude * (WAVE_AMPLITUDE * sin(wave_x)
                                    + WAVE_AMPLITUDE * cos(wave_x * 0.5 + 5.0) * 0.8
                                    + WAVE_AMPLITUDE * sin(wave_x * 0.25 + 10.0) * 0.5);

                // Interpolate final water level
                if (block_type_left > 0) {
                    water_level_left = water_level;
                }
                if (block_type_right > 0) {
                    water_level_right = water_level;
                }
                int final_water_level = int(mix(mix(water_level, water_level_left, 0.5), mix(water_level, water_level_right, 0.5), fsource_pixel.x) * BLOCK_SIZE_SOURCE);

                // Add wave offset
                if (wave_offset + sin(time) * 0.08 > 0.03) {
                    final_water_level += 1;
                } else if (wave_offset + sin(time) * 0.08 < -0.03) {
                    final_water_level -= 1;
                }

                if (source_pixel.y - 1 < final_water_level) {
                    return WATER_COLOR;
                }
            }
        }
    }
    return TRANSPARENCY;
}

void draw_post_processing() {
    // Water
    fragColor = get_color_foreground();
    
    /*
    // damage animation
    float red_spike = max(0, sin(2 * time) + sin(4 * time) + sin(8 * time) - 1.75) * 0.8 + 0.1;
    fragColor = vec4(red_spike, 0.05, 0, sqrt(pow((vertTexcoord.x - 0.5) * 5, 2) + pow((vertTexcoord.y - 0.5) * 5, 2)) / 5);
    */
}


void main() {
    switch (int(floor(vertShape))) {
        case 0: // Image
            draw_image();
            break;

        case 1: // Rectangle
            fragColor = vertSourceOrColor;
            break;

        case 2: // Circle
            draw_circle();
            break;

        case 3: // Text
            draw_text();
            break;

        case 4: // World (moved to post processing; now only background)
            draw_background();
            break;

        case 5: // Post processing
            draw_post_processing();
            break;

            /*
            for (int x = 0; x < BLOCK_COUNT.x; x++) {
                for (int y = 0; y < BLOCK_COUNT.y; y++) {
                    if (texelFetch(texWorld, ivec2(x, y), 0).r > 0) {
                        vec2 p2 = vec2(x, y);
                        vec2 p3 = vec2(x, (1+y));

                        float A1 = p1.y - p0.y;
                        float B1 = p0.x - p1.x;
                        float C1 = A1 * p0.x + B1 * p0.y;
                        float A2 = p3.y - p2.y;
                        float B2 = p2.x - p3.x;
                        float C2 = A2 * p2.x + B2 * p2.y;
                        float denominator = A1 * B2 - A2 * B1;
                    
                        //if (denominator == 0 || distance(p2, p0) + distance(p3, p0) == distance(p2, p3)) {
                        //	//gl_FragColor = vec4(1, 1, 1, 1);
                        //} else {
                        if (denominator != 0) {
                            vec2 p4 = vec2((B2 * C1 - B1 * C2) / denominator, (A1 * C2 - A2 * C1) / denominator);
                            float p0f = p0.x + p0.y;
                            float p1f = p1.x + p1.y;
                            float p2f = p2.x + p2.y;
                            float p3f = p3.x + p3.y;
                            float p4f = p4.x + p4.y;
                            float tef = p1.x + p1.y; // && (p0f < p4f && tef/160 < p4f ^^ p0f > p4f && tef/160 > p4f)
                            if (p4f <= max(p2f, p3f) && p4f >= min(p2f, p3f) && (p0.x <= p4.x && vertTexcoord.x >= p4.x || p0.x >= p4.x && vertTexcoord.x <= p4.x) && (p0.y <= p4.y && vertTexcoord.y >= p4.y || p0.y >= p4.y && vertTexcoord.y <= p4.y)) {
                                fragColor = vec4(0, 0, 0, 1);
                            //} else {
                            //	//gl_FragColor = vec4(1, 1, 1, 1);
                            }
                        }

                    }
                }
            }
            */
            break;
    }
}
