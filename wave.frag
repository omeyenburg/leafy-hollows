#version 330 core

uniform sampler2D texWorld;
uniform sampler2D texUi;

in vec2 uv;
out vec4 fragColor;

void main() {
	int time = 0;
	vec4 uiColor = texture(texUi, uv);
	if (uiColor == vec4(0, 0, 0, 1)) {
    	vec2 world_uv = vec2(uv.x + sin(uv.y * 10 + time * 0.01) * 0.1, uv.y);
		fragColor = texture(texWorld, world_uv);
	} else {
		fragColor = uiColor;
	}
}