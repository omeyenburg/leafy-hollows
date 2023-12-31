#version 330 core
in vec2 texcoord;
flat in vec4 source_color;
flat in int shape;

uniform sampler2D texSprites;

out vec4 fragColor;

void draw_rectangle() {
    fragColor = vec4(source_color);
}

void draw_circle() {
    int inside = int(pow(texcoord.x - 0.5, 2) + pow(texcoord.y - 0.5, 2) < pow(0.5, 2));
    fragColor = vec4(source_color) * inside;
}

void draw_image() {
    fragColor = texture(texSprites, texcoord);
}

void main() {
    switch (shape) {
        case 0:
            draw_rectangle();
            break;
        case 1:
            draw_circle();
            break;
        case 2:
            draw_image();
            break;
    }
}