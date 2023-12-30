#version 330 core
in vec2 texcoord;
flat in vec4 source_color;
flat in float shape;

out vec4 fragColor;

void main() {
    fragColor = vec4(source_color);
}