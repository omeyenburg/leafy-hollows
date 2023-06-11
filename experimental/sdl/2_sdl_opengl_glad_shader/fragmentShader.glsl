#version 330 core

uniform float time;
uniform vec2 resolution;

out vec4 FragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec3 col = 0.5 + 0.5 * cos(time + uv.xyx + vec3(0, 2, 4));
    FragColor = vec4(col, 1.0);
}