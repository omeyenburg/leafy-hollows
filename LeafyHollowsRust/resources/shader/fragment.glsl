#version 330 core
in vec2 texcoord;
flat in vec4 source_color;
flat in int shape;

uniform sampler2D texSprites;

out vec4 fragColor;

void draw_rectangle() {
    fragColor = vec4(source_color);
}

void draw_image() {
    fragColor = texture(texSprites, texcoord);
}

void main() {
    switch (shape) {
        case 0:
            draw_rectangle();
        case 1:
            draw_image();
    }
}