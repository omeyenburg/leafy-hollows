#version 330 core
/*const SHAPE_RECTANGLE = 0;
const SHAPE_CIRCLE = 1;
const SHAPE_IMAGE = 2;
const SHAPE_TEXT = 3;
*/
in vec2 texcoord;
flat in vec4 source_color;
flat in int shape;

uniform ivec2 window_size;

uniform sampler2D texSprites;

out vec4 fragColor;

void draw_rectangle() {
    fragColor = vec4(source_color);
}

void draw_circle() {
    float d = distance(texcoord, vec2(0.5, 0.5)) * 1.01;
    float smoothness = 2.0 / window_size.y;
    float inside = 1 - smoothstep(0.5 - smoothness, 0.5 + smoothness, d);
    fragColor = source_color;
    fragColor.a *= inside;
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
