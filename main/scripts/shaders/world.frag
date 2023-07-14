#version 330 core

in vec2 vertTexcoord;

out vec4 fragColor;

uniform sampler2D texBlocks;
uniform isampler2D texWorld;
uniform vec2 offset;
uniform int resolution;
uniform float time;

int BLOCKSIZEDEST = 16 * resolution;
int BLOCKSIZESOURCE = 16;
vec2 BLOCKCOUNT = textureSize(texBlocks, 0) / BLOCKSIZESOURCE;

void main() {
    // Block in world
    vec2 dest = vec2(gl_FragCoord.x / BLOCKSIZEDEST + offset.x,
                     gl_FragCoord.y / BLOCKSIZEDEST + offset.y);

    // Block type (signed_block < 0 --> alpha *= 0.6)
    int signed_block = texelFetch(texWorld, ivec2(dest), 0).r;
    int block = abs(signed_block);
    
    // Pixel within block
    ivec2 source_pixel = ivec2(mod(gl_FragCoord.x / resolution + offset.x * BLOCKSIZESOURCE, BLOCKSIZESOURCE),
                               mod(gl_FragCoord.y / resolution + offset.y * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + 1);
    
    // Round corners
    for (int xi = 0; xi < 2; xi++) {
        for (int yi = 0; yi < 2; yi++) {
            int xblock = texelFetch(texWorld, ivec2(dest.x + xi * 2 - 1, dest.y), 0).r;
            int yblock = texelFetch(texWorld, ivec2(dest.x, dest.y + yi * 2 - 1), 0).r;
            int cblock = texelFetch(texWorld, ivec2(dest.x + xi * 2 - 1, dest.y + yi * 2 - 1), 0).r;
            if (xblock != signed_block && yblock != signed_block && cblock != signed_block && xblock == yblock
            && abs(15.5 - xi * 16 - source_pixel.x) + abs(16.5 - yi * 16 - source_pixel.y) > 30) {
                source_pixel.y = 17 - source_pixel.y;
                signed_block = xblock;
                block = abs(signed_block);
            }
        }
    }

    // Background
    if (block == 0) {
        fragColor = vec4(sin(vertTexcoord.x) / 2 + 0.5, cos(vertTexcoord.y) / 2 + 0.5, cos(vertTexcoord.x), 0.5);
        return;
    }

    // Current frame
    int animation_frames = int(texelFetch(texBlocks, ivec2(block - 1, 0), 0).x * 255);
    int image_id = block + int(mod(time, animation_frames)) - 1;

    // Source image coordinate in texture
    ivec2 source_offset = ivec2(mod(image_id, BLOCKCOUNT.x), image_id / BLOCKCOUNT.x) * BLOCKSIZESOURCE;
    ivec2 source = ivec2(source_pixel.x + source_offset.x,
                         source_pixel.y + source_offset.y);

    // Set pixel color
    fragColor = texelFetch(texBlocks, source, 0);

    // Set alpha (signed_block < 0 --> alpha *= 0.6) 
    if (signed_block < 0) {
        fragColor.a *= 0.6;
    }
}
