#version 330 core

in vec2 vertTexcoord;
in vec4 vertSourceOrColor;
in float vertShape;

out vec4 fragColor;

uniform sampler2D texAtlas;
uniform sampler2D texFont;

void main() {
    // transparency
    fragColor = vec4(0.0, 0.0, 0.0, 0.0);

    switch (int(floor(vertShape))) {
        case 0: // image
            fragColor = texture(texAtlas, vertTexcoord * vertSourceOrColor.zw + vertSourceOrColor.xy);
            break;
        case 1: // rectangle
            fragColor = vertSourceOrColor;
            break;
        case 2: // circle
            if (length(vertTexcoord - 0.5) <= 0.5) {
                fragColor = vertSourceOrColor;
            }
            break;
        case 3: // text
            vec4 color = floor(vertSourceOrColor) / 255.0;
            vec4 source = fract(vertSourceOrColor);

            if (source.w == 0) {
                source.w = 1;
            }

            if (texture(texFont, vec2(vertTexcoord.x * source.z + source.x, vertTexcoord.y * source.w + source.y)) == vec4(1.0, 1.0, 1.0, 1.0)) {
                fragColor = color;
            }
            break;
    }
}
