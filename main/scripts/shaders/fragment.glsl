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

int BLOCKSIZEDEST;
int BLOCKSIZESOURCE;
vec2 BLOCKCOUNT;

const float border_theshold = 0.0001;
const vec4 transparency = vec4(0.0, 0.0, 0.0, 0.0);

int block = 0;
int xblock;
int yblock;
int cblock;
int depth_block = 0;
int depth_xblock;
int depth_yblock;
int depth_cblock;
int animation_frames;
int image_id;
ivec2 source_offset;
ivec2 source;
vec4 block_color = transparency;
vec4 depth_block_color = transparency;


void main() {
    switch (int(floor(vertShape))) {
        case 0: // Image
            if (vertTexcoord.x < border_theshold || vertTexcoord.y < border_theshold || vertTexcoord.x > 1.0 - border_theshold || vertTexcoord.y > 1.0 - border_theshold) {
                fragColor = transparency;
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
            } else { // Transparency
                fragColor = transparency;
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
            } else { // Transparency
                fragColor = transparency;
            }
            break;
        case 4: // World
            /*

            3 Layers:
            - block
            - depth block if block is transparent
            - fluid if block and depth block are transparent

            */
            
            int BLOCKSIZEDEST = 16 * resolution;
            int BLOCKSIZESOURCE = 16;
            vec2 BLOCKCOUNT = textureSize(texBlocks, 0) / BLOCKSIZESOURCE;

            // Block in world
            vec2 dest = vec2(gl_FragCoord.x / BLOCKSIZEDEST + offset.x,
                             gl_FragCoord.y / BLOCKSIZEDEST + offset.y);
            
            // Block type (block < 0 --> alpha *= 0.6)
            int raw_block = texelFetch(texWorld, ivec2(dest), 0).r;
            if (raw_block > 999) {
                depth_block = int(floor(raw_block / 1000.0));
                block = raw_block - depth_block * 1000;
            } else {
                block = raw_block;
            }

            // Pixel within block
            ivec2 source_pixel = ivec2(
                mod(gl_FragCoord.x / resolution + offset.x * BLOCKSIZESOURCE, BLOCKSIZESOURCE),
                mod(gl_FragCoord.y / resolution + offset.y * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + 1 // Row 0 is used to save animation data
            );

            // Round corners
            for (int xi = 0; xi < 2; xi++)
            for (int yi = 0; yi < 2; yi++)
            if (abs(15.5 - xi * 16 - source_pixel.x) + abs(16.5 - yi * 16 - source_pixel.y) > 30) {
                // X-axis block
                xblock = texelFetch(texWorld, ivec2(dest.x + xi * 2 - 1, dest.y), 0).r;
                if (xblock > 999) {
                    depth_xblock = int(floor(xblock / 1000.0));
                } else {
                    depth_xblock = 0;
                }

                // Y-axis block
                yblock = texelFetch(texWorld, ivec2(dest.x, dest.y + yi * 2 - 1), 0).r;
                if (yblock > 999) {
                    depth_yblock = int(floor(yblock / 1000.0));
                } else {
                    depth_yblock = 0;
                }

                // Corner block
                cblock = texelFetch(texWorld, ivec2(dest.x + xi * 2 - 1, dest.y + yi * 2 - 1), 0).r;
                if (cblock > 999) {
                    depth_cblock = int(floor(cblock / 1000.0));
                } else {
                    depth_cblock = 0;
                }

                if (xblock != block && yblock != block && cblock != block && xblock == yblock) {
                    source_pixel.y = 17 - source_pixel.y;
                    block = xblock;
                }

                if (depth_xblock != depth_block && depth_yblock != depth_block && depth_cblock != depth_block && depth_xblock == depth_yblock) {
                    source_pixel.y = 17 - source_pixel.y;
                    depth_block = 0;
                }
            }

            // Background
            vec4 background = vec4(sin(vertTexcoord.x) / 2 + 0.5, cos(vertTexcoord.y) / 2 + 0.5, cos(vertTexcoord.x), 0.5);
            if (block == 0 && depth_block == 0) {
                fragColor = background;
                return;
            }

            if (block != 0) {
                // Current frame
                animation_frames = int(texelFetch(texBlocks, ivec2(block - 1, 0), 0).x * 255);
                image_id = block + int(mod(time, animation_frames)) - 1;

                // Source image coordinate in texture
                source_offset = ivec2(mod(image_id, BLOCKCOUNT.x), image_id / BLOCKCOUNT.x) * BLOCKSIZESOURCE;
                source = ivec2(source_pixel.x + source_offset.x,
                                    source_pixel.y + source_offset.y);

                // Set pixel color
                block_color = texelFetch(texBlocks, source, 0);
            }

            // Depth block
            if (depth_block != 0 && block_color.a < 1.0) {
                // Current frame
                animation_frames = int(texelFetch(texBlocks, ivec2(depth_block - 1, 0), 0).x * 255);
                image_id = depth_block + int(mod(time, animation_frames)) - 1;

                // Source image coordinate in texture
                source_offset = ivec2(mod(image_id, BLOCKCOUNT.x), image_id / BLOCKCOUNT.x) * BLOCKSIZESOURCE;
                source = ivec2(source_pixel.x + source_offset.x,
                                    source_pixel.y + source_offset.y);
                
                // Set pixel color
                depth_block_color = texelFetch(texBlocks, source, 0);
                depth_block_color.a *= 0.6;
                
                // Mix depth block and block
                block_color = block_color * block_color.a + depth_block_color * (1 - block_color.a);
            }

            /*
            // Shadow
            int dist = 4;
            for (int x = -3; x <= 3; x++) {
                xblock = int(texelFetch(texWorld, ivec2(dest.x + x, dest.y), 0).r % 1000);
                if (xblock == 0) {
                    dist = min(dist, abs(x));
                }
            }
            for (int y = -3; y <= 3; y++) {
                yblock = int(texelFetch(texWorld, ivec2(dest.x, dest.y + y), 0).r % 1000);
                if (yblock == 0) {
                    dist = min(dist, abs(y));
                }
            }
            block_color *= 4 - dist;
            block_color.a = 1;
            */

            // Mix with background and block
            if (block_color.a < 1.0) {
                fragColor = block_color * block_color.a + background * (1 - block_color.a);
            } else {
                fragColor = block_color;
            }
            break;
        case 5: // post processing
            fragColor = vec4(0.1, 0.1, 0, sqrt(pow((vertTexcoord.x - 0.5) * 5, 2) + pow((vertTexcoord.y - 0.5) * 5, 2)) / 5);
            break;
            
            BLOCKSIZEDEST = 16 * resolution;
            BLOCKSIZESOURCE = 16;
            BLOCKCOUNT = textureSize(texBlocks, 0) / BLOCKSIZESOURCE;

            vec2 p0 = BLOCKCOUNT / 2;
            vec2 p1 = vertTexcoord * BLOCKSIZEDEST;

            fragColor = transparency;

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
