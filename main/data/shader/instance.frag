#version 330 core
#define WAVE_AMPLITUDE 0.05
#define WAVE_FREQUENCY 0.3
#define WATER_PER_BLOCK 1000.0
#define BLOCK_SIZE_SOURCE 16
#define BORDER_THRESHOLD 0.0001
#define TRANSPARENCY vec4(0, 0, 0, 0)
#define CORNER_COLOR vec4(0.05, 0, 0, 1.0)
#define FIRE_COLOR vec4(1.0, 0.6, 0.4, 0.8)

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
uniform sampler2D texShadow;
uniform vec2 offset;
uniform vec2 camera;
uniform float resolution;
uniform float shadow_resolution;
uniform float time;
uniform int gray_screen;

// Predefined values
float BLOCK_SIZE_DEST;
vec2 BLOCK_COUNT;
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
vec4 block_color = TRANSPARENCY;
vec4 water_color = TRANSPARENCY;
ivec2 block_texture_size;
int block_animation_rows;


// Image
void draw_image() {
    int border = int(
        step(BORDER_THRESHOLD, vertTexcoord.x) *
        step(BORDER_THRESHOLD, vertTexcoord.y) *
        step(vertTexcoord.x, 1.0 - BORDER_THRESHOLD) *
        step(vertTexcoord.y, 1.0 - BORDER_THRESHOLD)
    );
    vec4 color = texture(texSprites, vertTexcoord * vertSourceOrColor.zw + vertSourceOrColor.xy);
    fragColor = color * border, TRANSPARENCY * (1 - border);
}


// Circle
void draw_circle() {
    fragColor = mix(TRANSPARENCY, vertSourceOrColor, float(length(vertTexcoord - 0.5) <= 0.5));
}


// Text
void draw_text() {
    vec4 text_color = floor(vertSourceOrColor) / 255.0;
    vec4 text_source = fract(vertSourceOrColor);
    int draw = int(texture(texFont, vec2(
        vertTexcoord.x * text_source.z + text_source.x,
        vertTexcoord.y * text_source.w + text_source.y
    )).r);
    fragColor = text_color * draw + TRANSPARENCY * (1 - draw);
}


// background
ivec2 get_block_data_location(int block_type) {
    return ivec2(
        mod(block_type - 1, block_texture_size.x),
        block_animation_rows - (block_type - 1) / block_texture_size.x - 1
    );
}

ivec2 get_source_pixel() {
    return ivec2(
        mod(gl_FragCoord.x / resolution + offset.x * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE),
        mod(gl_FragCoord.y / resolution + offset.y * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE) + block_animation_rows // Row 0 is used to save animation data
    );
}

vec4 get_color_block(int block_type, vec2 source_pixel) {
    // Flip source_pixel for flipped blocks
    // (flipped blocks === even block_type && block_type != 0)
    if (block_type == 0) {
        return TRANSPARENCY;
    }

    source_pixel.x = mix(15 - source_pixel.x, source_pixel.x, block_type & 1);
    block_type = (block_type - 1) / 2 + 1;

    // Current frame
    animation_data = texelFetch(texBlocks, get_block_data_location(block_type), 0).rg;
    animation_frames = int(animation_data.r * 255);
    animation_speed = animation_data.g * 2;
    image_id = block_type + int(mod(time / animation_speed / animation_frames, animation_frames)) - 1;

    // Source image coordinate in texture
    source_offset = ivec2(
        mod(image_id, BLOCK_COUNT.x),
        image_id / BLOCK_COUNT.x
    ) * BLOCK_SIZE_SOURCE;
    source = ivec2(
        source_pixel.x + source_offset.x,
        source_pixel.y + source_offset.y
    );

    // Fetch and return pixel color
    return texelFetch(texBlocks, source, 0) * min(block_type, 1);
}

vec4 get_color_background() {
    return vec4(
        sin(vertTexcoord.x) / 2 + 0.5,
        cos(vertTexcoord.y) / 2 + 0.5,
        cos(vertTexcoord.x),
        0.5
    );

    return vec4(
        sin(vertTexcoord.x + time) / 2 + 0.5,
        cos(vertTexcoord.y + time * 0.4) / 2 + 0.5,
        cos(vertTexcoord.x + time * 0.2),
        0.5
    );
}

void draw_background() {
    BLOCK_SIZE_DEST = BLOCK_SIZE_SOURCE * resolution;
    block_texture_size = textureSize(texBlocks, 0);
    block_animation_rows = int(mod(block_texture_size.y, BLOCK_SIZE_SOURCE));
    BLOCK_COUNT = block_texture_size / BLOCK_SIZE_SOURCE;

    // block in world
    ivec2 block_coord = ivec2(
        gl_FragCoord.x / BLOCK_SIZE_DEST + offset.x,
        gl_FragCoord.y / BLOCK_SIZE_DEST + offset.y
    );

    // block data (foreground, plant, background, water level)
    ivec4 block_data = texelFetch(texWorld, block_coord, 0);
    
    // background block type
    int block_type = block_data.b;
    int foreground_block_type = block_data.r;

    // Pixel within block (y-offset by block_animation_rows)
    ivec2 source_pixel = get_source_pixel();
    int source_pixel_y_min = block_animation_rows;
    int source_pixel_y_max = block_animation_rows + 15;

    // Block color
    block_color = get_color_block(block_type, source_pixel);
    int return_block_color = int(block_color.a > 1.0 - BORDER_THRESHOLD);

    // Background color
    vec4 background_color = mix(get_color_background(), block_color, block_color.a);
    int return_background_color = int(return_block_color == 0 && (foreground_block_type == 0 || source_pixel.x != 0 && source_pixel.x != 15 && source_pixel.y != source_pixel_y_min && source_pixel.y != source_pixel_y_max));

    // Move source pixel at edge to next block
    int on_edge_left = int(source_pixel.x == 0);
    int on_edge_right = int(source_pixel.x == 15);
    int on_edge_bottom = int(source_pixel.y == source_pixel_y_min);
    int on_edge_top = int(source_pixel.y == source_pixel_y_max);
    
    source_pixel.x = on_edge_left * 15 + (1 - on_edge_left - on_edge_right) * source_pixel.x;
    block_coord.x += on_edge_right - on_edge_left;
    source_pixel.y = on_edge_bottom * source_pixel_y_max + on_edge_top * source_pixel_y_min + (1 - on_edge_bottom - on_edge_top) * source_pixel.y;
    block_coord.y += on_edge_top - on_edge_bottom;

    // Get adjacent block color
    block_type = texelFetch(texWorld, block_coord, 0).b;
    block_color = mix(get_color_block(block_type, source_pixel), block_color, block_color.a);
    block_color = mix(background_color, block_color, block_color.a);

    // Mix colors
    fragColor = background_color * return_background_color + block_color * (1 - return_background_color);
}


// Foreground
ivec4 get_next_closest_block(ivec2 source_pixel) {
    source_pixel.y -= block_animation_rows;
    int x_distance = int(min(source_pixel.x, BLOCK_SIZE_SOURCE - source_pixel.x));
    int y_distance = int(min(source_pixel.y, BLOCK_SIZE_SOURCE - source_pixel.y));

    /*
    if (x_distance <= y_distance) {
        // Block on x-axis
        if (x_distance == source_pixel.x) {
            // left
            return ivec4(15, source_pixel.y + block_animation_rows, -1, 0);
        }
        // right
        return ivec4(0, source_pixel.y + block_animation_rows, 1, 0);
    } else {
        // Block on y-axis
        if (y_distance == source_pixel.y) {
            // top
            return ivec4(source_pixel.x, 15 + block_animation_rows, 0, -1);
        }
        // bottom
        return ivec4(source_pixel.x, block_animation_rows, 0, 1);
    }*/

    int x_smaller_y = int(x_distance <= y_distance);
    int x_edge = int(x_distance == source_pixel.x);
    int y_edge = int(y_distance == source_pixel.y);

    return (
        x_smaller_y * (
            x_edge * ivec4(15, source_pixel.y + block_animation_rows, -1, 0) +
            (1 - x_edge) * ivec4(0, source_pixel.y + block_animation_rows, 1, 0)
        ) + (1 - x_smaller_y) * (
            y_edge * ivec4(source_pixel.x, 15 + block_animation_rows, 0, -1) +
            (1 - y_edge) * ivec4(source_pixel.x, block_animation_rows, 0, 1)
        )
    );
}

vec4 mix_overlay_color(vec4 block_color, vec4 overlay_color_add, vec4 overlay_color_sub) {
    float alpha = block_color.a + overlay_color_add.a + overlay_color_sub.a;
    vec4 out_color = mix(block_color + overlay_color_add, overlay_color_sub, overlay_color_sub.a);
    out_color.a = alpha;
    return out_color;
}

ivec2 get_source_pixel_wrapped(int block_type, ivec2 source_pixel_wrapped) {
    int block_family = int(texelFetch(texBlocks, get_block_data_location(block_type), 0).b * 255);
    int block_family_adjacent_x = int(texelFetch(texBlocks, get_block_data_location(adjacent_x), 0).b * 255);
    int block_family_adjacent_y = int(texelFetch(texBlocks, get_block_data_location(adjacent_y), 0).b * 255);

    int center = int(block_family <= block_family_adjacent_x && block_family <= block_family_adjacent_y && block_type <= adjacent_x && block_type <= adjacent_y);
    int x_edge = int(block_type <= adjacent_x);
    int y_edge = int(block_type <= adjacent_y);
    int left_edge = int(source_pixel_wrapped.x < BLOCK_SIZE_SOURCE / 2);
    int lower_edge = int(source_pixel_wrapped.y < BLOCK_SIZE_SOURCE / 2);

    return (
        center * ivec2(7, 7) +
        (1 - center) * (
            source_pixel_wrapped +
            x_edge * (
                left_edge * ivec2(4, 0) +
                (1 - left_edge) * ivec2(-4, 0)
            ) +
            (1 - x_edge) * y_edge * (
                lower_edge * ivec2(0, 4) +
                (1 - lower_edge) * ivec2(0, -4)
            )
        )
    );


    /*
    if (block_family <= block_family_adjacent_x && block_family <= block_family_adjacent_y && block_type <= adjacent_x && block_type <= adjacent_y) {
        source_pixel_wrapped = ivec2(7, 7);
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
    }*/
    return source_pixel_wrapped;
}

int unflip_block_type(int block_type) {
    return ((block_type - 1) & ~1) + 1;
}

vec4 get_color_foreground() {
    BLOCK_SIZE_DEST = BLOCK_SIZE_SOURCE * resolution;
    block_texture_size = textureSize(texBlocks, 0);
    block_animation_rows = int(mod(block_texture_size.y, BLOCK_SIZE_SOURCE));
    BLOCK_COUNT = block_texture_size / BLOCK_SIZE_SOURCE;

    // Block coord in world
    ivec2 block_coord = ivec2(gl_FragCoord.x / BLOCK_SIZE_DEST + offset.x,
                              gl_FragCoord.y / BLOCK_SIZE_DEST + offset.y);

    // Block data (foreground, plant, background, water level)
    ivec4 block_data = texelFetch(texWorld, ivec2(block_coord), 0);
    ivec4 block_data_left = texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y), 0);
    ivec4 block_data_right = texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y), 0);
    ivec4 block_data_top = texelFetch(texWorld, ivec2(block_coord.x, block_coord.y + 1), 0);
    ivec4 block_data_bottom = texelFetch(texWorld, ivec2(block_coord.x, block_coord.y - 1), 0);
    ivec4 block_data_top_left = texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y + 1), 0);
    ivec4 block_data_top_right = texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y + 1), 0);
    ivec4 block_data_bottom_left = texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y - 1), 0);
    ivec4 block_data_bottom_right = texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y - 1), 0);
    
    // Block type
    int block_type = block_data.r;
    int block_type_left = block_data_left.r;
    int block_type_right = block_data_right.r;
    int block_type_top = block_data_top.r;
    int block_type_bottom = block_data_bottom.r;

    // Pixel within block
    ivec2 source_pixel = get_source_pixel();
    vec2 fsource_pixel = vec2(source_pixel.x, source_pixel.y - block_animation_rows) / float(BLOCK_SIZE_SOURCE);
    ivec2 source_pixel_offset = ivec2(source_pixel.x, source_pixel.y - block_animation_rows);
    vec2 water_source_pixel = source_pixel;
    
    // Fire block distance
    float distance_fire = 2;
    float fire_x = sin(time / 11) / 2 + cos(time / 17) / 2 + 8.5;
    float fire_y = sin(time / 13) / 2 + cos(time / 19) / 2 + 8.5;
    if (unflip_block_type(block_data.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x, fire_y),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_top.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x, fire_y + BLOCK_SIZE_SOURCE),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_bottom.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x, fire_y - BLOCK_SIZE_SOURCE),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_left.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x - BLOCK_SIZE_SOURCE, fire_y),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_right.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x + BLOCK_SIZE_SOURCE, fire_y),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_top_left.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x - BLOCK_SIZE_SOURCE, fire_y + BLOCK_SIZE_SOURCE),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_top_right.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x + BLOCK_SIZE_SOURCE, fire_y + BLOCK_SIZE_SOURCE),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_bottom_left.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x - BLOCK_SIZE_SOURCE, fire_y - BLOCK_SIZE_SOURCE),
                source_pixel
            ) / 10
        );
    }
    if (unflip_block_type(block_data_bottom_right.g) == block.torch) {
        distance_fire = min(
            distance_fire,
            distance(
                vec2(fire_x + BLOCK_SIZE_SOURCE, fire_y - BLOCK_SIZE_SOURCE),
                source_pixel
            ) / 10
        );
    }

    if (distance_fire < 2) {
        distance_fire = min(2, distance_fire + (sin(time * 3) + 1) / 17 + (cos(time * 10) + 1) / 20);
    }

    // Fire color
    vec4 overlay_color_add = mix(FIRE_COLOR, TRANSPARENCY, distance_fire / 2);
    
    // Air block distance
    float distance_air = 3;
    for (int dx = -3; dx <= 3; dx += 1)
    for (int dy = -3; dy <= 3; dy += 1)
    if (texelFetch(texWorld, ivec2(block_coord.x + dx, block_coord.y + dy), 0).r == 0) {
        distance_air = min(distance_air, distance(vec2((dx + 0.5) * BLOCK_SIZE_SOURCE, (dy + 0.5) * BLOCK_SIZE_SOURCE), source_pixel) / 10);
    }
    vec4 overlay_color_sub = vec4(0, 0, 0, max(0, (distance_air - 1.5) / 1.5));

    if (overlay_color_sub.a >= 1.0) {
        return overlay_color_sub;
    }
    //vec4 overlay_color_sub = vec4(0);

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

    // Shadow position (changed for block gaps)
    vec2 shadow_position = vec2(vec2(gl_FragCoord.x + offset.x * BLOCK_SIZE_DEST - BLOCK_SIZE_DEST, gl_FragCoord.y + offset.y * BLOCK_SIZE_DEST - BLOCK_SIZE_DEST) * shadow_resolution / 16 / resolution);

    if (block_type != 0) {
        // Get wrapped source pixel of foreground blocks
        ivec2 source_pixel_wrapped = get_source_pixel_wrapped(block_type, source_pixel);

        // Get pixel color
        block_color = get_color_block(block_type, source_pixel_wrapped);

        if (block_color.a < 1.0) {
            if (block_type != 0) {
                if (abs(source_pixel_offset.x) < abs(source_pixel_offset.y)) {
                    block_color = get_color_block(adjacent_x, ivec2(7, 7));
                } else {
                    block_color = get_color_block(adjacent_y, ivec2(7, 7));
                }
                if (block_color.a > 0.0) {
                    return mix_overlay_color(block_color, overlay_color_add, overlay_color_sub);
                }
            }
        } else {
            return mix_overlay_color(block_color, overlay_color_add, overlay_color_sub);
        }
        
        // Set block to the closest other block -> let water flow into transparent gaps
        ivec4 next_closest_block = get_next_closest_block(source_pixel);
        source_pixel = next_closest_block.xy;
        block_coord += next_closest_block.zw;
        shadow_position += next_closest_block.zw;

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
    
    if (block_color.a < 1.0 - BORDER_THRESHOLD) {
        block_color = get_color_block(block_data.g, source_pixel);
    }

    vec2 fsource_pixel16 = vec2(
        mod(gl_FragCoord.x / resolution + offset.x * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE),
        mod(gl_FragCoord.y / resolution + offset.y * BLOCK_SIZE_SOURCE, BLOCK_SIZE_SOURCE) + block_animation_rows // Row 0 is used to save animation data
    );

    // Draw shadows
    if (shadow_resolution > 1.0 - BORDER_THRESHOLD && block_type < BORDER_THRESHOLD) {
        if (fsource_pixel16.x == 0) {
            shadow_position.x += 1;
        }
        if (fsource_pixel16.y == 0 || fsource_pixel16.y == 2) {
            shadow_position.y += 1;
        }
        float shadow_intensity = 0;
        float samples = 0;
        for (float x = -1; x < 2; x += 0.1)
        for (float y = -1; y < 2; y += 0.1) {
            //shadow_intensity += texelFetch(texShadow, shadow_position + ivec2(x, y), 0).r;
            shadow_intensity += texture(texShadow, (shadow_position + vec2(x, y)) / textureSize(texShadow, 0), 0).r;
            samples += 1;
        }
        block_color = mix(vec4(0.05, 0, 0.05, 0.6), block_color, 0.5 + shadow_intensity / samples);
    }
    
    // Skip water
    if (block_type == 0 && abs(block_data.a) < 1) {
        return mix_overlay_color(block_color, overlay_color_add, overlay_color_sub);
    }

    // Draw water
    float water_level = block_data.a / WATER_PER_BLOCK;
    float water_level_top = abs(block_data_top.a / WATER_PER_BLOCK);
    float water_level_bottom = abs(block_data_bottom.a / WATER_PER_BLOCK);
    float water_level_left = abs(block_data_left.a / WATER_PER_BLOCK);
    float water_level_right = abs(block_data_right.a / WATER_PER_BLOCK);
    float water_level_top_left = abs(texelFetch(texWorld, ivec2(block_coord.x - 1, block_coord.y + 1), 0).a / WATER_PER_BLOCK);
    float water_level_top_right = abs(texelFetch(texWorld, ivec2(block_coord.x + 1, block_coord.y + 1), 0).a / WATER_PER_BLOCK);

    water_color = get_color_block(block.water, water_source_pixel);
    water_color.a = 0.5;
    water_color = mix(mix(water_color, block_color, block_color.a * 0.6), overlay_color_add + overlay_color_sub, overlay_color_add.a + overlay_color_sub.a);

    fsource_pixel.y -= 1 / float(BLOCK_SIZE_SOURCE);

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

        // Get water state
        water_level = max(max(water_level, water_level_left), water_level_right);
        if (water_level_top > BORDER_THRESHOLD && water_level_top_left > 0.1 && water_level_top_right > 0.1) {
            // Covered water
            return water_color;
        } else if ((block_type_bottom != 0 || water_level_bottom > 0.9) && water_level_top > 0.1) {
            // Vertical & horizontal water
            vertical = 1;
            horizontal = 1;
        } else if (block_type_bottom == 0 && water_level_top > 0.1 && (water_level_left < BORDER_THRESHOLD || water_level_right < BORDER_THRESHOLD)) {
            // Vertical water
            vertical = 1;
        } else if (block_type_bottom == 0 && water_level_top > 0.1 && (water_level_left > BORDER_THRESHOLD && water_level_right > BORDER_THRESHOLD)) {
            // Covered vertical water
            return water_color;
        } else if (block_type_bottom == 0 && water_level_top <= 0.1 && (water_level_left < BORDER_THRESHOLD && water_level_right < BORDER_THRESHOLD)) {
            // Top of vertical water
            vertical = 1;
            height = water_level;
            width = min(water_level, 0.2);
        } else if (block_type_bottom == 0 && water_level_top < BORDER_THRESHOLD && water_level_bottom < 1.0 - BORDER_THRESHOLD && (water_level_left < BORDER_THRESHOLD && water_level_right > BORDER_THRESHOLD || water_level_right < BORDER_THRESHOLD && water_level_left > BORDER_THRESHOLD)) {
            // Corner of vertical water and horizontal on one side
            corner = 1;
            width = min(water_level, 0.2);
        } else {
            // Horizontal water
            horizontal = 1;
        }

        // Draw vertical water
        if (vertical == 1 && abs((water_side + 1) / 2 - fsource_pixel.x) <= width && fsource_pixel.y <= height) {
            return water_color;
        } else if (corner == 1 && water_side == -1) {
            height = water_level_left;

            if (fsource_pixel.x + fsource_pixel.y <= (width + height) / 2 && fsource_pixel.x <= width && fsource_pixel.y <= height) {
                return water_color;
            }
        } else if (corner == 1 && water_side == 1) {
            height = water_level_right;                    

            if (abs((water_side + 1) / 2 - fsource_pixel.x) + fsource_pixel.y <= (width + height) / 2 && 1.0 - fsource_pixel.x <= width && fsource_pixel.y <= height) {
                return water_color;
            }
        }

        // Draw horizontal water
        if (horizontal == 1) {
            if (false && water_level_top > BORDER_THRESHOLD && vertical == 0 || water_level > 1.0 - BORDER_THRESHOLD || water_level_top > 0.1 && water_level_top_left > 0.1 && water_level_left > 1.0 - BORDER_THRESHOLD * 10 || water_level_top > 0.1 && water_level_top_right > 0.1 && water_level_right > 1.0 - BORDER_THRESHOLD * 10) {
                return water_color;
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
                    return water_color;
                }
            }
        }
    }
    return mix_overlay_color(block_color, overlay_color_add, overlay_color_sub);
}

void draw_post_processing() {
    fragColor = mix((get_color_foreground() + vec4(0, 0, 0, gray_screen)) / (1 + gray_screen), CORNER_COLOR, sqrt(pow((vertTexcoord.x - 0.5) * 5, 2) + pow((vertTexcoord.y - 0.5) * 5, 2)) / 5 + 0.1);
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
    }
}
