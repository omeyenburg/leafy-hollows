#version 330 core

in vec2 fragTexCoord;
out vec4 fragColor;

uniform sampler2D tex;
uniform vec2 source;

void main() {
    vec4 color = texture(tex, vec2(fragTexCoord.x * source.y + source.x, fragTexCoord.y));
    if (color != vec4(1, 1, 1, 1)) {
        fragColor = vec4(0, 0, 0, 0);
    } else {
        fragColor = color;
    }
}