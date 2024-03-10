#version 330 core
const int SHAPE_RECTANGLE = 0;
const int SHAPE_CIRCLE = 1;
const int SHAPE_IMAGE = 2;
const int SHAPE_TEXT = 3;
const float FLOAT_THRESHOLD_ZERO = 0.000001;
const float FLOAT_THRESHOLD_ONE = 0.999999;
const vec4 TRANSPARENCY = vec4(0.0, 0.0, 0.0, 0.0);

out vec4 fragColor;
in vec2 texcoord;
flat in vec2 shape;
flat in vec4 color;

uniform sampler2D texSprites;
uniform sampler2D texFont;
uniform ivec2 window_size;

void draw_rectangle() {
    fragColor = vec4(color);
}

void draw_circle() {
    float d = distance(texcoord, vec2(0.5, 0.5)) * 1.01;
    float smoothness = 2.0 / window_size.y;
    float inside = 1 - smoothstep(0.5 - smoothness, 0.5 + smoothness, d);
    fragColor = color;
    fragColor.a *= inside;
}

void draw_image() {
    ivec2 sprites_size = textureSize(texSprites, 0);

    int image_id = int(shape.y);
    fragColor = texture(texSprites, texcoord);
}

void draw_text() {
    int char_id = int(shape.y);
    ivec2 source = ivec2(char_id % 26 * 5 + 5 * texcoord.x, char_id / 26 * 10 + 10 * texcoord.y);
    vec4 pixel = texelFetch(texFont, source, 0);
    if (pixel.r > FLOAT_THRESHOLD_ZERO) {
        fragColor = color;
    } else {
        fragColor = TRANSPARENCY;
    }
}

void main() {
    switch (int(shape.x)) {
    case SHAPE_RECTANGLE:
        draw_rectangle();
        break;
    case SHAPE_CIRCLE:
        draw_circle();
        break;
    case SHAPE_IMAGE:
        draw_image();
        break;
    case SHAPE_TEXT:
        draw_text();
        break;
    }
}
