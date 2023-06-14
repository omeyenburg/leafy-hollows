#version 330 core

in vec2 position;
in vec2 texCoord;

out vec2 fragCoord;

void main() {
    fragCoord = texCoord;
    gl_Position = vec4(position, 0.0, 1.0);
}
