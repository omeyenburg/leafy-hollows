#version 330 core

in vec2 vertTexcoord;
in vec4 vertSourceOrColor;
in float vertShape;

out vec4 fragColor;

uniform sampler2D texAtlas;
uniform sampler2D texFont;
uniform sampler2D texBlocks;
uniform isampler2D texWorld;
uniform vec2 offset;
uniform int resolution;
uniform float time;

vec2 BLOCKCOUNT;
int BLOCKSIZEDEST;
const int BLOCKSIZESOURCE = 16;
const float BORDERTHRESHOLD = 0.0001;
const vec4 TRANSPARENCY = vec4(0, 0, 0, 0);

int block = 0;
int animation_frames;
int image_id;
float animation_speed;
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
        source_offset = ivec2(mod(image_id, BLOCKCOUNT.x), image_id / BLOCKCOUNT.x) * BLOCKSIZESOURCE;
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
            if (vertTexcoord.x < BORDERTHRESHOLD || vertTexcoord.y < BORDERTHRESHOLD || vertTexcoord.x > 1.0 - BORDERTHRESHOLD || vertTexcoord.y > 1.0 - BORDERTHRESHOLD) {
                fragColor = TRANSPARENCY;
            } else {
                fragColor = texture(texAtlas, vertTexcoord * vertSourceOrColor.zw + vertSourceOrColor.xy);
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
            BLOCKSIZEDEST = 16 * resolution;
            BLOCKCOUNT = textureSize(texBlocks, 0) / BLOCKSIZESOURCE;

            // Block in world
            vec2 dest = vec2(gl_FragCoord.x / BLOCKSIZEDEST + offset.x,
                             gl_FragCoord.y / BLOCKSIZEDEST + offset.y);
            
            // Block type (block < 0 --> alpha *= 0.6)
            int block = int(texelFetch(texWorld, ivec2(dest), 0).r);

            // Pixel within block
            ivec2 source_pixel = ivec2(
                mod(gl_FragCoord.x / resolution + offset.x * BLOCKSIZESOURCE, BLOCKSIZESOURCE),
                mod(gl_FragCoord.y / resolution + offset.y * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + 1 // Row 0 is used to save animation data
            );
            ivec2 source_pixel_org = ivec2(source_pixel.x, source_pixel.y);

            // Source pixel offset
            ivec2 sub_block_pixel = ivec2(
                mod(gl_FragCoord.x / resolution + offset.x * BLOCKSIZESOURCE, BLOCKSIZESOURCE / 2),
                mod(gl_FragCoord.y / resolution + offset.y * BLOCKSIZESOURCE, BLOCKSIZESOURCE / 2) + 1 // Row 0 is used to save animation data
            );

            ivec2 quarter = ivec2(1, 1);
            if (source_pixel.x == sub_block_pixel.x) {
                quarter.x = -1;
            }
            if (source_pixel.y == sub_block_pixel.y) {
                quarter.y = -1;
            }

            int adjacent_x = int(texelFetch(texWorld, ivec2(dest.x + quarter.x, dest.y), 0).r);
            int adjacent_y = int(texelFetch(texWorld, ivec2(dest.x, dest.y + quarter.y), 0).r);

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
                return;
            }

            // Set pixel color
            block_color = get_block_color(block, source_pixel);

            // Mix with background and block
            if (block_color.a < 1.0) {
                if (abs(source_pixel_org.x - (quarter.x + 1) * BLOCKSIZESOURCE / 2) < abs(source_pixel_org.y - (quarter.y + 1) * BLOCKSIZESOURCE / 2)) {
                    block_color = get_block_color(adjacent_x, ivec2(8, 8));
                } else {
                    block_color = get_block_color(adjacent_y, ivec2(8, 8));
                }
                fragColor = block_color * block_color.a + background * (1 - block_color.a);
            } else {
                fragColor = block_color;
            }
            break;

        case 5: // post processing
            fragColor = vec4(0.1, 0.1, 0, sqrt(pow((vertTexcoord.x - 0.5) * 5, 2) + pow((vertTexcoord.y - 0.5) * 5, 2)) / 5);
            break;
            
            BLOCKSIZEDEST = 16 * resolution;
            BLOCKCOUNT = textureSize(texBlocks, 0) / BLOCKSIZESOURCE;

            vec2 p0 = BLOCKCOUNT / 2;
            vec2 p1 = vertTexcoord * BLOCKSIZEDEST;

            fragColor = TRANSPARENCY;

            /*
            for (int x = 0; x < BLOCKCOUNT.x; x++) {
                for (int y = 0; y < BLOCKCOUNT.y; y++) {
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
