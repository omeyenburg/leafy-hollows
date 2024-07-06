#version 330 core
const int SHAPE_RECTANGLE = 0;
const int SHAPE_CIRCLE = 1;
const int SHAPE_IMAGE = 2;
const int SHAPE_TEXT = 3;
const float FLOAT_THRESHOLD_ZERO = 0.000001;
const float FLOAT_THRESHOLD_ONE = 0.999999;

layout(location = 0) in vec2 vertex_position;
layout(location = 1) in vec2 vertex_texcoord;
layout(location = 2) in vec2 vertex_shape;
layout(location = 3) in vec4 vertex_dest;
layout(location = 4) in vec4 vertex_color;

uniform float window_size_relation;

out vec2 texcoord;
flat out vec2 shape;
flat out vec4 color;

void main() {
    vec2 position = vertex_position;
    float angle;

    switch (int(vertex_shape.x)) {
    case SHAPE_RECTANGLE:
        angle = vertex_shape.y;
        break;
    case SHAPE_IMAGE:
        angle = vertex_color.z;
        if (vertex_color.x > FLOAT_THRESHOLD_ONE) {
            position.x *= -1;
        }
        if (vertex_color.y > FLOAT_THRESHOLD_ONE) {
            position.y *= -1;
        }
        break;
    default:
        angle = 0.0;
        break;
    }
    position.y *= -1;

    if (angle != 0.0) {
        float angle_sin = sin(angle);
        float angle_cos = cos(angle);
        mat2 rotation_matrix = mat2(angle_cos, -angle_sin, angle_sin, angle_cos);
        vec2 rotated_position = position * rotation_matrix * vertex_dest.zw; // vertex_dest.zw
        /*vec2 rotated_position = vec2(
            angle_cos * position.x - angle_sin * position.y,
            angle_sin * position.x + angle_cos * position.y
        );*/
        gl_Position = vec4(rotated_position + vertex_dest.xy, 0.0, 1.0);
    } else {
        gl_Position = vec4(position * vertex_dest.zw + vertex_dest.xy, 0.0, 1.0);
    }
    gl_Position.x *= window_size_relation;

    texcoord = vertex_texcoord;
    color = vertex_color;
    shape = vertex_shape;
}