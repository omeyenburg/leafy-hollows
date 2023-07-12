#version 330 core

in vec2 vertTexcoord;

out vec4 fragColor;

uniform sampler2D texBlocks;
uniform isampler2D texWorld;
uniform vec2 offset;
uniform int resolution;

int BLOCKSIZEDEST = 16 * resolution;
int BLOCKSIZESOURCE = 16;
vec2 BLOCKCOUNT = textureSize(texBlocks, 0) / BLOCKSIZESOURCE;

void main() {
    vec2 dest = vec2(gl_FragCoord.x / BLOCKSIZEDEST + offset.x, gl_FragCoord.y / BLOCKSIZEDEST + offset.y);
    int signed_block = texelFetch(texWorld, ivec2(dest), 0).r;
    int block = abs(signed_block);
    if (block == 0) {
        // background color
        fragColor = vec4(sin(vertTexcoord.x) / 2 + 0.5, cos(vertTexcoord.y) / 2 + 0.5, cos(vertTexcoord.x), 0.5);
        return;
    }
    //ivec2 source_offset = 16 * ivec2(mod(block - 1, BLOCKCOUNT.x), (block - 1) / BLOCKCOUNT.x);

    ivec2 source_offset = ivec2(mod(block - 1, BLOCKCOUNT.x), (block - 1) / BLOCKCOUNT.x) * BLOCKSIZESOURCE;

    ivec2 source = ivec2(mod(gl_FragCoord.x / resolution + offset.x * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + source_offset.x,
                         mod(gl_FragCoord.y / resolution + offset.y * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + source_offset.y);

    fragColor = texelFetch(texBlocks, source, 0);
    if (signed_block < 0) {
        fragColor.a *= 0.6;
    }
}