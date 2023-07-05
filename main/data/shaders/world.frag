#version 410 core

in vec2 vertTexcoord;
in vec4 vertOffset;

out vec4 fragColor;

uniform sampler2D texBlocks;
uniform sampler2D texWorld;

void main() {
    fragColor = vec4(0, 0, 0, 0);
}