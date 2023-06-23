#version 330 core

uniform float time;
uniform sampler2D sdl_tex;

in vec2 FragCoord;
out vec4 FragColor;

void main() {
	vec4 texCol = texture(sdl_tex, FragCoord.xy);
	vec3 col = 0.5 + 0.5 * cos(time + FragCoord.xyx + vec3(0, 2, 4));
	FragColor = vec4((texCol.rgb + col) / 2, 1.0);
}