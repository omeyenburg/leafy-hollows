#version 330 core

in vec2 vertTexcoord;
in vec2 vertSize;
in vec4 vertSource_rect;
in vec4 vertColor;
in float vertShape;

out vec4 fragColor;

uniform sampler2D texAtlas;
uniform sampler2D texFont;

void main() {
    float shape = floor(vertShape);
    if (shape == 0) {
        // image
        fragColor = texture(texAtlas, vertTexcoord * vertSource_rect.zw + vertSource_rect.xy);
    } else if (shape == 1) {
        // rectangle
        fragColor = vertColor;
    } else if (shape == 2 && length(vertTexcoord - 0.5) <= 0.5) {
        // circle
        fragColor = vertColor;
    } else if (shape == 3 && texture(texFont, vertTexcoord * vertSource_rect.zw + vertSource_rect.xy) == vec4(1.0, 1.0, 1.0, 1.0)) {
        // text
        fragColor = vertColor;
    } else {
        // transparency
        fragColor = vec4(0.0, 0.0, 0.0, 0.0);
    }
}
