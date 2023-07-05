#version 410 core

layout (location = 0) in vec2 position;
layout (location = 1) in vec2 texcoord;
layout (location = 2) in vec4 offset; // x, y of offset | w, h of single block

out vec2 vertTexcoord;
out vec4 vertOffset;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    vertTexcoord = texcoord;
}