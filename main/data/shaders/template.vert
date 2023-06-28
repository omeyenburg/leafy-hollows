#version 330 core

layout (location = 0) in vec2 position;
layout (location = 1) in vec2 texcoord;
layout (location = 2) in vec4 dest_rect;
layout (location = 3) in vec4 source_or_color;
layout (location = 4) in float shape;

out vec2 vertTexcoord;
out vec2 vertSize;
out vec4 vertSourceOrColor;
out float vertShape;

void main() {
    gl_Position = vec4(position * dest_rect.zw + dest_rect.xy, 0.0, 1.0);
    
    vertTexcoord = texcoord;
    vertSize = dest_rect.wz;
    vertSourceOrColor = source_or_color;
    vertShape = shape;
}