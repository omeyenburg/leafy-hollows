#version 330 core

in vec2 vertTexcoord;

out vec4 fragColor;

uniform sampler2D texBlocks;
uniform isampler2D texWorld;
uniform vec2 offset;
uniform int resolution;

int BLOCKSIZEDEST = 16 * resolution;
int BLOCKSIZESOURCE = 16;
vec2 BLOCKCOUNT = textureSize(texWorld, 0) / BLOCKSIZESOURCE;

void main() {
    vec2 dest = vec2(gl_FragCoord.x / BLOCKSIZEDEST + offset.x, gl_FragCoord.y / BLOCKSIZEDEST + offset.y);
    int block = texelFetch(texWorld, ivec2(dest), 0).r;
    if (block == 0) {
        fragColor = vec4(sin(vertTexcoord.x) / 2 + 0.5, cos(vertTexcoord.y) / 2 + 0.5, cos(vertTexcoord.x), 0.5);
        return;
    }
    ivec2 source_offset = 16 * ivec2(mod(block - 1, BLOCKCOUNT.x), (block - 1) / BLOCKCOUNT.x);
    ivec2 source = ivec2(mod(gl_FragCoord.x / (BLOCKSIZEDEST/BLOCKSIZESOURCE) + offset.x * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + source_offset.x, mod(gl_FragCoord.y / (BLOCKSIZEDEST/BLOCKSIZESOURCE) + offset.y * BLOCKSIZESOURCE, BLOCKSIZESOURCE) + source_offset.y);
    fragColor = texelFetch(texBlocks, ivec2(source), 0);
}