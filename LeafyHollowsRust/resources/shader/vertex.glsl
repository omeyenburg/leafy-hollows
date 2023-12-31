#version 330 core
layout (location = 0) in vec2 vertex_position;
layout (location = 1) in vec2 vertex_texcoord;
layout (location = 2) in vec4 vertex_dest_rect;
layout (location = 3) in vec4 vertex_source_color;
layout (location = 4) in vec4 vertex_shape_transform;

uniform float window_size_relation;

out vec2 texcoord;
flat out vec4 source_color;
flat out int shape;


void main() {
    vec2 flip = vertex_shape_transform.gb;
    float angle = vertex_shape_transform.a;
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
        mat2 rotation_matrix = mat2(angle_cos, -angle_sin, angle_sin, angle_cos);
        vec2 rotated_position = position * rotation_matrix * vertex_dest_rect.zw; // vertex_dest_rect.zw
        /*vec2 rotated_position = vec2(
            angle_cos * position.x - angle_sin * position.y,
            angle_sin * position.x + angle_cos * position.y
        );*/
        gl_Position = vec4(rotated_position + vertex_dest_rect.xy, 0.0, 1.0);
    } else {
        gl_Position = vec4(position * vertex_dest_rect.zw + vertex_dest_rect.xy, 0.0, 1.0);
    }

    gl_Position.x *= window_size_relation;

    texcoord = vertex_texcoord;
    source_color = vertex_source_color;
    shape = int(round(vertex_shape_transform.r));
}