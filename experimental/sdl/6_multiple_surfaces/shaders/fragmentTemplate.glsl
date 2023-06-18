#version 330 core

uniform sampler2D texWorld;
uniform sampler2D texUi;
uniform float time;

in vec2 fragCoord;
out vec4 fragColor;

void main() {
	vec4 uiColor = texture(texUi, fragCoord);
	if (uiColor == vec4(0, 0, 0, 0)) {
    	vec2 world_uv = vec2(fragCoord.x + sin(fragCoord.y * 10 + time * 0.01) * 0.01, fragCoord.y);
		fragColor = texture(texWorld, world_uv);
	} else {
		fragColor = uiColor;
	}
}