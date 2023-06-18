#version 330 core

layout (location = 0) in vec2 position;
layout (location = 1) in vec2 texcoord;
out vec2 fragTexCoord;

uniform vec4 dest_rect;

void main() {
    gl_Position = vec4(position * dest_rect.zw + dest_rect.xy, 0.0, 1.0);
    fragTexCoord = texcoord;
}