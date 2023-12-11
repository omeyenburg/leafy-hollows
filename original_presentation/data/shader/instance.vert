#version 330 core

layout (location = 0) in vec2 vertex_position;
layout (location = 1) in vec2 texcoord;
layout (location = 2) in vec4 dest_rect;
layout (location = 3) in vec4 source_or_color;
layout (location = 4) in vec4 shape_transform;

out vec2 vertTexcoord;
flat out vec4 vertSourceOrColor;
flat out float vertShape;

void main() {
    vec2 flip = shape_transform.gb;
    float angle = shape_transform.a;
    vec2 position = vertex_position;
    if (flip.x == 1) {
        position.x *= -1;
    }
    if (flip.y == 1) {
        position.y *= -1;
    }
    if (angle != 0.0) {
        float angle_sin = sin(angle);
        float angle_cos = cos(angle);
        mat2 rotationMatrix = mat2(angle_cos, -angle_sin, angle_sin, angle_cos);
        vec2 rotatedPosition = (position * rotationMatrix);
        gl_Position = vec4(rotatedPosition * dest_rect.zw + dest_rect.xy, 0.0, 1.0);
    } else {
        gl_Position = vec4(position * dest_rect.zw + dest_rect.xy, 0.0, 1.0);
    }
    vertTexcoord = texcoord;
    vertSourceOrColor = source_or_color;
    vertShape = shape_transform.x;
}
