#version 330 core

in vec2 vertTexcoord;
in vec2 vertSize;
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
            vec2 source = fract(vertSourceOrColor.xy);

            if (texture(texFont, vec2(vertTexcoord.x * source.y + source.x, vertTexcoord.y)) == vec4(1.0, 1.0, 1.0, 1.0)) {
                fragColor = color;
            }
            break;
    }
}
