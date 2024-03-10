fn size_of<T>() -> usize {
    std::mem::size_of::<T>()
}

/*
-- New buffer layout --

In total: 10*f32 (= 40 bytes)
Values:   [shape, a, dest_x, dest_y, dest_w, dest_h, b, c, d, e]

Rectangle:
[shape, rotation]: vec2
dest: vec4
color: vec4

Image
[shape, image]: vec2
dest: vec4
[flipX, flipY, rotation, _]: vec4

Text
[shape, char]: vec2
dest: vec4
color: vec4

*/

pub struct Buffer {
    size: isize,
    pub index: isize,
    pub vao: gl::types::GLuint,
    ebo_indices: gl::types::GLuint,
    vbo_vertices: gl::types::GLuint,
    vbo_shape: gl::types::GLuint,
    vbo_dest: gl::types::GLuint,
    vbo_color: gl::types::GLuint,
}

impl Buffer {
    pub fn new() -> Self {
        // Create vertex array object
        let mut vao: gl::types::GLuint = 0;
        unsafe {
            gl::GenVertexArrays(1, &mut vao);
            gl::BindVertexArray(vao);
        }

        let [ebo_indices, vbo_vertices, vbo_dest, vbo_color, vbo_shape] = {
            let mut vbos: [gl::types::GLuint; 5] = [0; 5];
            unsafe {
                gl::GenBuffers(5, vbos.as_mut_ptr());
            }
            vbos
        };

        // Vertices        |   Texcoords
        let vertices: Vec<f32> = vec![
            -1.0, -1.0, /* | */ 0.0, 0.0, // bottom-left
            -1.0, 1.0, /*  | */ 0.0, 1.0, // top-left
            1.0, 1.0, /*   | */ 1.0, 1.0, // top-right
            1.0, -1.0, /*  | */ 1.0, 0.0, // bottom-right
        ];

        // Indices to lines in vertices
        let indices: Vec<u32> = vec![
            0, 1, 2, // First triangle
            0, 2, 3, // Second triangle
        ];

        unsafe {
            // VBO: vertices
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_vertices);
            gl::BufferData(
                gl::ARRAY_BUFFER,
                (vertices.len() * size_of::<f32>()) as gl::types::GLsizeiptr,
                vertices.as_ptr() as *const gl::types::GLvoid,
                gl::STATIC_DRAW,
            );

            // Vertices
            gl::EnableVertexAttribArray(0);
            gl::VertexAttribPointer(
                0,
                2,
                gl::FLOAT,
                gl::FALSE,
                (4 * size_of::<f32>()) as gl::types::GLint,
                std::ptr::null(),
            );

            // Texcoords
            gl::EnableVertexAttribArray(1);
            gl::VertexAttribPointer(
                1,
                2,
                gl::FLOAT,
                gl::FALSE,
                (4 * size_of::<f32>()) as gl::types::GLint,
                (2 * size_of::<f32>()) as *const gl::types::GLvoid,
            );

            // EBO: indices
            gl::BindBuffer(gl::ELEMENT_ARRAY_BUFFER, ebo_indices);
            gl::BufferData(
                gl::ELEMENT_ARRAY_BUFFER,
                (indices.len() * size_of::<u32>()) as gl::types::GLsizeiptr,
                indices.as_ptr() as *const gl::types::GLvoid,
                gl::STATIC_DRAW,
            );

            // VBO: shape
            gl::EnableVertexAttribArray(2);
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_shape);
            gl::BufferData(gl::ARRAY_BUFFER, 0, std::ptr::null(), gl::STREAM_COPY);
            gl::VertexAttribPointer(2, 2, gl::FLOAT, gl::FALSE, 0, std::ptr::null());
            gl::VertexAttribDivisor(2, 1);

            // VBO: dest
            gl::EnableVertexAttribArray(3);
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_dest);
            gl::BufferData(gl::ARRAY_BUFFER, 0, std::ptr::null(), gl::STREAM_COPY);
            gl::VertexAttribPointer(3, 4, gl::FLOAT, gl::FALSE, 0, std::ptr::null());
            gl::VertexAttribDivisor(3, 1);

            // VBO: color
            gl::EnableVertexAttribArray(4);
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_color);
            gl::BufferData(gl::ARRAY_BUFFER, 0, std::ptr::null(), gl::STREAM_COPY);
            gl::VertexAttribPointer(4, 4, gl::FLOAT, gl::FALSE, 0, std::ptr::null());
            gl::VertexAttribDivisor(4, 1);
        }

        Self {
            size: 0,
            index: 0,
            vao,
            ebo_indices,
            vbo_vertices,
            vbo_shape,
            vbo_dest,
            vbo_color,
        }
    }

    pub fn add_instance(&mut self, shape: [f32; 2], dest: [f32; 4], color: [f32; 4]) {
        let f32_size: isize = std::mem::size_of::<f32>() as isize;

        if self.index >= self.size {
            // Resize buffers
            let new_size: isize = self.size + 10;
            let new_buffer_size: isize = new_size * f32_size;
            //let old_buffer_size: isize = self.size * f32_size;

            unsafe {
                // Shape
                gl::BindBuffer(gl::ARRAY_BUFFER, self.vbo_shape);
                gl::BufferData(
                    gl::ARRAY_BUFFER,
                    new_buffer_size * 2,
                    std::ptr::null(),
                    gl::STREAM_COPY,
                );
                //gl::CopyBufferSubData(gl::ARRAY_BUFFER, gl::ARRAY_BUFFER, 0, 0, old_buffer_size * 2);

                // Dest
                gl::BindBuffer(gl::ARRAY_BUFFER, self.vbo_dest);
                gl::BufferData(
                    gl::ARRAY_BUFFER,
                    new_buffer_size * 4,
                    std::ptr::null(),
                    gl::STREAM_COPY,
                );
                //gl::CopyBufferSubData(gl::ARRAY_BUFFER, gl::ARRAY_BUFFER, 0, 0, old_buffer_size * 4);

                // Color
                gl::BindBuffer(gl::ARRAY_BUFFER, self.vbo_color);
                gl::BufferData(
                    gl::ARRAY_BUFFER,
                    new_buffer_size * 4,
                    std::ptr::null(),
                    gl::STREAM_COPY,
                );
                //gl::CopyBufferSubData(gl::ARRAY_BUFFER, gl::ARRAY_BUFFER, 0, 0, old_buffer_size * 4);
            }

            self.size = new_size;
        }

        let data_offset: isize = self.index * f32_size;
        let data_size: isize = f32_size;
        unsafe {
            // Shape
            gl::BindBuffer(gl::ARRAY_BUFFER, self.vbo_shape);
            gl::BufferSubData(
                gl::ARRAY_BUFFER,
                2 * data_offset,
                2 * data_size,
                shape.as_ptr() as *const gl::types::GLvoid,
            );

            // Dest
            gl::BindBuffer(gl::ARRAY_BUFFER, self.vbo_dest);
            gl::BufferSubData(
                gl::ARRAY_BUFFER,
                4 * data_offset,
                4 * data_size,
                dest.as_ptr() as *const gl::types::GLvoid,
            );

            // Color
            gl::BindBuffer(gl::ARRAY_BUFFER, self.vbo_color);
            gl::BufferSubData(
                gl::ARRAY_BUFFER,
                4 * data_offset,
                4 * data_size,
                color.as_ptr() as *const gl::types::GLvoid,
            );
        }
        self.index += 1;
    }
}
