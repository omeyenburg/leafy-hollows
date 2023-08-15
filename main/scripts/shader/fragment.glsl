#version 330 core

in vec2 vertTexcoord;
flat in vec4 vertSourceOrColor;
flat in float vertShape;

out vec4 fragColor;

uniform sampler2D texSprites;
uniform sampler2D texFont;
uniform sampler2D texBlocks;
uniform isampler2D texWorld;
uniform vec2 offset;
uniform vec2 camera;
uniform int resolution;
uniform float time;

vec2 BLOCK_COUNT;
int BLOCK_SIZE_DEST;
const int BLOCK_SIZE_SOURCE = 16;
const float BORDER_THRESHOLD = 0.0001;
const vec4 TRANSPARENCY = vec4(0, 0, 0, 0);
const vec4 WATER_COLOR = vec4(0.2, 0.6, 0.9, 1);
const float WAVE_AMPLITUDE = 0.05;
const float WAVE_FREQUENCY = 0.3;
const float WATER_PER_BLOCK = 1000.0;


int block = 0;
int adjacent_x, adjacent_y;
int animation_frames, image_id;
float animation_speed;
float amplitude, amplitude_left, amplitude_right = 0.0;
ivec2 source_offset;
ivec2 source;
vec2 animation_data;
vec4 block_color;


vec4 get_block_color(int block, vec2 source_pixel) {
    if (block != 0) {
        // Current frame
        animation_data = texelFetch(texBlocks, ivec2(block - 1, 0), 0).rg;
        animation_frames = int(animation_data.r * 255);
        animation_speed = animation_data.g * 2;
        image_id = block + int(mod(time / animation_speed / animation_frames, animation_frames)) - 1;

        // Source image coordinate in texture
        source_offset = ivec2(mod(image_id, BLOCK_COUNT.x), image_id / BLOCK_COUNT.x) * BLOCK_SIZE_SOURCE;
        source = ivec2(source_pixel.x + source_offset.x,
                       source_pixel.y + source_offset.y);

        // Get pixel color
        return texelFetch(texBlocks, source, 0);
    } else {
        return TRANSPARENCY;
    }
}


void main() {
    switch (int(floor(vertShape))) {
        case 0: // Image
            if (vertTexcoord.x < BORDER_THRESHOLD || vertTexcoord.y < BORDER_THRESHOLD || vertTexcoord.x > 1.0 - BORDER_THRESHOLD || vertTexcoord.y > 1.0 - BORDER_THRESHOLD) {
                fragColor = TRANSPARENCY;
            } else {
                fragColor = texture(texSprites, vertTexcoord * vertSourceOrColor.zw + vertSourceOrColor.xy);
            }
            break;

        case 1: // Rectangle
            fragColor = vertSourceOrColor;
            break;

        case 2: // Circle
            if (length(vertTexcoord - 0.5) <= 0.5) {
                fragColor = vertSourceOrColor;
            } else { // TRANSPARENCY
                fragColor = TRANSPARENCY;
            }
            break;

        case 3: // Text
            vec4 text_color = floor(vertSourceOrColor) / 255.0;
            vec4 text_source = fract(vertSourceOrColor);

            if (text_source.w == 0) {
                text_source.w = 1;
            }

            if (texture(texFont, vec2(vertTexcoord.x * text_source.z + text_source.x, vertTexcoord.y * text_source.w + text_source.y)) == vec4(1.0, 1.0, 1.0, 1.0)) {
                fragColor = text_color;
            } else { // TRANSPARENCY
                fragColor = TRANSPARENCY;
            }
            break;

        case 4: // World
            BLOCK_SIZE_DEST = 16 * resolution;
            BLOCK_COUNT = textureSize(texBlocks, 0) / BLOCK_SIZE_SOURCE;

            // Block in world
            vec2 dest = vec2(gl_FragCoord.x / BLOCK_SIZE_DEST + offset.x,
                             gl_FragCoord.y / BLOCK_SIZE_DEST + offset.y);
            
            // Block type (block < 0 --> alpha *= 0.6)
            int block = int(texelFetch(texWorld, ivec2(dest), 0).r);
            int block_left = int(texelFetch(texWorld, ivec2(dest.x - 1, dest.y), 0).r);
            int block_right = int(texelFetch(texWorld, ivec2(dest.x + 1, dest.y), 0).r);
            int block_top = int(texelFetch(texWorld, ivec2(dest.x, dest.y + 1), 0).r);
            int block_bottom = int(texelFetch(texWorld, ivec2(dest.x, dest.y - 1), 0).r);

            // Pixel within block
            ivec2 source_pixel = ivec2(
                mod(gl_FragCoord.x / resolution + offset.x * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE),
                mod(gl_FragCoord.y / resolution + offset.y * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE) + 1 // Row 0 is used to save animation data
            );
            ivec2 source_pixel_org = ivec2(source_pixel.x, source_pixel.y);

            // Source pixel offset
            ivec2 sub_block_pixel = ivec2(
                mod(gl_FragCoord.x / resolution + offset.x * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE / 2),
                mod(gl_FragCoord.y / resolution + offset.y * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE / 2) + 1 // Row 0 is used to save animation data
            );

            ivec2 quarter = ivec2(1, 1);
            if (source_pixel.x == sub_block_pixel.x) {
                quarter.x = -1;
                adjacent_x = block_left;
            } else {
                adjacent_x = block_right;
            }
            if (source_pixel.y == sub_block_pixel.y) {
                quarter.y = -1;
                adjacent_y = block_bottom;
            } else {
                adjacent_y = block_top;
            }

            if (block <= adjacent_x && block <= adjacent_y) {
                source_pixel = ivec2(8, 8);
            } else if (block <= adjacent_x) {
                source_pixel.x -= 4 * quarter.x;
            } else if (block <= adjacent_y) {
                source_pixel.y -= 4 * quarter.y;
            }

            // Background
            vec4 background = vec4(sin(vertTexcoord.x) / 2 + 0.5, cos(vertTexcoord.y) / 2 + 0.5, cos(vertTexcoord.x), 0.5);
            if (block == 0) {
                fragColor = background;
            }

            // Set pixel color
            block_color = get_block_color(block, source_pixel);

            // Mix with background and block
            if (block_color.a < 1.0) {
                if (block != 0) {
                    if (abs(source_pixel_org.x - (quarter.x + 1) * BLOCK_SIZE_SOURCE / 2) < abs(source_pixel_org.y - (quarter.y + 1) * BLOCK_SIZE_SOURCE / 2)) {
                        block_color = get_block_color(adjacent_x, ivec2(8, 8));
                    } else {
                        block_color = get_block_color(adjacent_y, ivec2(8, 8));
                    }
                }
                fragColor = block_color * block_color.a + background * (1 - block_color.a);
            } else {
                fragColor = block_color;
            }
            
            float water_level = texelFetch(texWorld, ivec2(dest), 0).a / WATER_PER_BLOCK;
            float water_level_top = abs(texelFetch(texWorld, ivec2(dest.x, dest.y + 1), 0).a / WATER_PER_BLOCK);
            float water_level_bottom = abs(texelFetch(texWorld, ivec2(dest.x, dest.y - 1), 0).a / WATER_PER_BLOCK);
            float water_level_left = abs(texelFetch(texWorld, ivec2(dest.x - 1, dest.y), 0).a / WATER_PER_BLOCK);
            float water_level_right = abs(texelFetch(texWorld, ivec2(dest.x + 1, dest.y), 0).a / WATER_PER_BLOCK);
            float water_level_top_left = abs(texelFetch(texWorld, ivec2(dest.x - 1, dest.y + 1), 0).a / WATER_PER_BLOCK);
            float water_level_top_right = abs(texelFetch(texWorld, ivec2(dest.x + 1, dest.y + 1), 0).a / WATER_PER_BLOCK);

            int water_side = 1;
            if (water_level < 0) {
                water_side = -1;
                water_level = abs(water_level);                
            }
            
            if (water_level < 0 || water_level_top < 0 || water_level_bottom < 0 || water_level_right < 0 || water_level_left < 0) {
                fragColor.r = 1;
                return;
            }

            vec2 fsource_pixel = vec2(source_pixel_org) / BLOCK_SIZE_SOURCE;

            if (water_level_top > BORDER_THRESHOLD && (water_level_left > 1.0 - BORDER_THRESHOLD || water_level_right > 1.0 - BORDER_THRESHOLD)) {
                water_level = 1.0;
            } else if (water_level_left > 1.0 - BORDER_THRESHOLD && water_level_right > 1.0 - BORDER_THRESHOLD) {
                water_level = 1.0;
            } else if (water_level_top > BORDER_THRESHOLD && water_level_top > water_level && block == 0) {
                water_level = water_level_top;
            }
            
            if (water_level > 0.1 && block == 0) {
                int draw_water, vertical, horizontal, covered, corner = 0;
                float width = min((water_level + water_level_top) * 0.5, 0.2);
                float height = 1.0;

                water_level = max(max(water_level, water_level_left), water_level_right);

                if (water_level_top > BORDER_THRESHOLD && water_level_top_left > 0.1 && water_level_top_right > 0.1) {
                    // covered water
                    horizontal = 1;
                    water_level = 1.0;
                } else if ((block_bottom != 0 || water_level_bottom > 0.9) && water_level_top > 0.1) {
                    // vertical & horizontal water
                    vertical = 1;
                    horizontal = 1;
                } else if (block_bottom == 0 && water_level_top > 0.1 && (water_level_left < BORDER_THRESHOLD || water_level_right < BORDER_THRESHOLD)) {
                    // vertical water
                    vertical = 1;
                } else if (block_bottom == 0 && water_level_top > 0.1 && (water_level_left > BORDER_THRESHOLD && water_level_right > BORDER_THRESHOLD)) {
                    // covered vertical water
                    horizontal = 1;
                    water_level = 1.0;
                } else if (block_bottom == 0 && water_level_top <= 0.1 && (water_level_left < BORDER_THRESHOLD && water_level_right < BORDER_THRESHOLD)) {
                    // top of vertical water
                    vertical = 1;
                    height = water_level;
                    width = min(water_level, 0.2);
                } else if (block_bottom == 0 && water_level_top < BORDER_THRESHOLD && water_level_bottom < 1.0 - BORDER_THRESHOLD && (water_level_left < BORDER_THRESHOLD && water_level_right > BORDER_THRESHOLD || water_level_right < BORDER_THRESHOLD && water_level_left > BORDER_THRESHOLD)) {
                    // corner of vertical water and horizontal on one side
                    corner = 1;
                    width = min(water_level, 0.2);
                } else {
                    // horizontal water
                    horizontal = 1;
                } 

                if (vertical == 1 && abs((water_side + 1) / 2 - fsource_pixel.x) <= width && fsource_pixel.y <= height) {
                    draw_water = 1;
                } else if (corner == 1 && water_side == -1) {
                    height = water_level_left;

                    if (fsource_pixel.x + fsource_pixel.y <= (width + height) / 2 && fsource_pixel.x <= width && fsource_pixel.y <= height) {
                        draw_water = 1;
                    }
                } else if (corner == 1 && water_side == 1) {
                    height = water_level_right;                    

                    if (abs((water_side + 1) / 2 - fsource_pixel.x) + fsource_pixel.y <= (width + height) / 2 && 1.0 - fsource_pixel.x <= width && fsource_pixel.y <= height) {
                        draw_water = 1;
                    }
                }

                if (horizontal == 1) {
                    if (false && water_level_top > BORDER_THRESHOLD && vertical == 0 || water_level > 1.0 - BORDER_THRESHOLD || water_level_top > 0.1 && water_level_top_left > 0.1 && water_level_left > 1.0 - BORDER_THRESHOLD * 10 || water_level_top > 0.1 && water_level_top_right > 0.1 && water_level_right > 1.0 - BORDER_THRESHOLD * 10) {
                        draw_water = 1;
                    } else {
                        // Wave amplitude
                        if (block_left == 0) {
                            amplitude_left = 1.0;
                        }
                        if (block_right == 0) {
                            amplitude_right = 1.0;
                        }
                        amplitude = mix(amplitude_left, amplitude_right, fsource_pixel.x);

                        // Wave offset
                        float wave_x = int(gl_FragCoord / resolution + camera.x * BLOCK_SIZE_SOURCE) * WAVE_FREQUENCY;
                        float wave_offset = amplitude * (WAVE_AMPLITUDE * sin(wave_x + time)
                                            + WAVE_AMPLITUDE * cos(wave_x * 0.5 - time) * 0.5
                                            + WAVE_AMPLITUDE * sin(wave_x * 0.25 - time) * 0.25);

                        if (block_left > 0) {
                            water_level_left = water_level;
                        }

                        if (block_right > 0) {
                            water_level_right = water_level;
                        }

                        // Interpolate final water level
                        float final_water_level = mix(mix(water_level, water_level_left, 0.5), mix(water_level, water_level_right, 0.5), fsource_pixel.x);

                        // Add wave offset
                        final_water_level += wave_offset;

                        if (source_pixel_org.y - 1 < final_water_level * BLOCK_SIZE_SOURCE) {
                            draw_water = 1;
                        }
                    }
                }

                if (draw_water == 1) {
                    fragColor = WATER_COLOR * 0.4 + fragColor * 0.6;
                }
            }

            /*
            // hell?
            if (camera.x > 5) {
                fragColor.g /= 2;
                fragColor.b /= 2;
                fragColor.r = fragColor.g + fragColor.b;
            }
            */

            break;

        case 5: // post processing

            // damage animation
            float red_spike = max(0, sin(2 * time) + sin(4 * time) + sin(8 * time) - 1.75) * 0.8 + 0.1;
            red_spike = 0.05;
            fragColor = vec4(red_spike, 0.05, 0, sqrt(pow((vertTexcoord.x - 0.5) * 5, 2) + pow((vertTexcoord.y - 0.5) * 5, 2)) / 5);
            break;
            
            BLOCK_SIZE_DEST = 16 * resolution;
            BLOCK_COUNT = textureSize(texBlocks, 0) / BLOCK_SIZE_SOURCE;

            vec2 p0 = BLOCK_COUNT / 2;
            vec2 p1 = vertTexcoord * BLOCK_SIZE_DEST;

            fragColor = TRANSPARENCY;

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
