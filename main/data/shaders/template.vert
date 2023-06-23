#version 330 core

layout (location = 0) in vec2 position;
layout (location = 1) in vec2 texcoord;
layout (location = 2) in vec4 dest_rect;
layout (location = 3) in vec4 source_rect;
layout (location = 4) in vec4 color;
layout (location = 5) in float shape;

out vec2 vertTexcoord;
out vec2 vertSize;
out vec4 vertSource_rect;
out vec4 vertColor;
out float vertShape;

void main() {
    gl_Position = vec4(position * dest_rect.zw + dest_rect.xy, 0.0, 1.0);
    
    vertTexcoord = texcoord;
    vertSize = dest_rect.wz;
    vertSource_rect = source_rect;
    vertColor = color;
    vertShape = shape;
}