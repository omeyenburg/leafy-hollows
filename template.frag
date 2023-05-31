#version 330 core

uniform sampler2D texWorld;
uniform sampler2D texUi;

in vec2 uv;
out vec4 fragColor;

void main() {
	vec4 uiColor = texture(texUi, uv);
	if (uiColor == vec4(0, 0, 0, 1)) {
		fragColor = texture(texWorld, uv);
	} else {
		fragColor = uiColor;
	}
}
