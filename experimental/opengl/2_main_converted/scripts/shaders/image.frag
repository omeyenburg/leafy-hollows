#version 330 core

in vec2 fragTexCoord;
out vec4 fragColor;

uniform sampler2D tex;
uniform vec4 source_rect;

void main() {
    fragColor = texture(tex, fragTexCoord * source_rect.zw + source_rect.xy);
}