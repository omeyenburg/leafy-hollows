use crate::utility::file;
use core::panic;
use gl::types::{GLenum, GLint, GLuint};
use gl::GetBooleani_v;
use std::ffi::CString;

pub struct Shader {
    program: GLuint,
    variables: Vec<UniformVariable>,
}

struct UniformVariable {
    loc: i32,
    value: UniformValue,
    update: bool,
}

pub enum UniformValue {
    Int(i32),
    UInt(u32),
    Float(f32),
    Vec2([f32; 2]),
    Vec3([f32; 3]),
    Vec4([f32; 4]),
    IVec2([i32; 2]),
    IVec3([i32; 3]),
    IVec4([i32; 4]),
    UVec2([u32; 2]),
    UVec3([u32; 3]),
    UVec4([u32; 4]),
}

impl Shader {
    pub fn new(vertex: &str, fragment: &str) -> Self {
        let program: GLuint;
        let mut success: GLint = 0;

        unsafe {
            program = gl::CreateProgram();
            let vertex_shader = Shader::attach_shader(&program, vertex, gl::VERTEX_SHADER);
            let fragment_shader = Shader::attach_shader(&program, fragment, gl::FRAGMENT_SHADER);

            gl::LinkProgram(program);
            gl::DeleteShader(vertex_shader);
            gl::DeleteShader(fragment_shader);
            gl::GetProgramiv(program, gl::LINK_STATUS, &mut success);

            if success != 1 {
                let mut error_log_size: GLint = 0;
                gl::GetProgramiv(program, gl::INFO_LOG_LENGTH, &mut error_log_size);
                let mut error_log: Vec<u8> = Vec::with_capacity(error_log_size as usize);
                gl::GetProgramInfoLog(
                    program,
                    error_log_size,
                    &mut error_log_size,
                    error_log.as_mut_ptr() as *mut _,
                );

                error_log.set_len(error_log_size as usize);
                let log = String::from_utf8(error_log).unwrap();
                eprint!("{}", log);
                panic!("Failed to compile shader!")
            }
        }

        Self {
            program,
            variables: Vec::new(),
        }
    }

    pub fn update(&self) {
        unsafe {
            gl::UseProgram(self.program);

            for var in &self.variables {
                if !var.update {
                    continue;
                }
                match var.value {
                    UniformValue::Int(value) => gl::Uniform1i(var.loc, value),
                    UniformValue::UInt(value) => gl::Uniform1ui(var.loc, value),
                    UniformValue::Float(value) => gl::Uniform1f(var.loc, value),
                    UniformValue::Vec2(value) => gl::Uniform2f(var.loc, value[0], value[1]),
                    UniformValue::Vec3(value) => {
                        gl::Uniform3f(var.loc, value[0], value[1], value[2])
                    }
                    UniformValue::Vec4(value) => {
                        gl::Uniform4f(var.loc, value[0], value[1], value[2], value[3])
                    }
                    UniformValue::IVec2(value) => gl::Uniform2i(var.loc, value[0], value[1]),
                    UniformValue::IVec3(value) => {
                        gl::Uniform3i(var.loc, value[0], value[1], value[2])
                    }
                    UniformValue::IVec4(value) => {
                        gl::Uniform4i(var.loc, value[0], value[1], value[2], value[3])
                    }
                    UniformValue::UVec2(value) => gl::Uniform2ui(var.loc, value[0], value[1]),
                    UniformValue::UVec3(value) => {
                        gl::Uniform3ui(var.loc, value[0], value[1], value[2])
                    }
                    UniformValue::UVec4(value) => {
                        gl::Uniform4ui(var.loc, value[0], value[1], value[2], value[3])
                    }
                }
            }
        }
    }

    fn attach_shader(program: &GLuint, source_code: &str, shader_type: GLenum) -> GLenum {
        let source_code = CString::new(source_code).unwrap();
        let mut success: GLint = 0;
        let id: GLuint;

        unsafe {
            id = gl::CreateShader(shader_type);
            gl::ShaderSource(id, 1, &source_code.as_ptr(), std::ptr::null());
            gl::CompileShader(id);
            gl::GetShaderiv(id, gl::COMPILE_STATUS, &mut success);

            if success != 1 {
                let mut error_log_size: GLint = 0;
                gl::GetShaderiv(id, gl::INFO_LOG_LENGTH, &mut error_log_size);
                let mut error_log: Vec<u8> = Vec::with_capacity(error_log_size as usize);
                gl::GetShaderInfoLog(
                    id,
                    error_log_size,
                    &mut error_log_size,
                    error_log.as_mut_ptr() as *mut _,
                );

                error_log.set_len(error_log_size as usize);
                let log = String::from_utf8(error_log).unwrap();

                let mut file_path = String::from("");
                match shader_type {
                    gl::VERTEX_SHADER => file_path += "vertex.glsl",
                    gl::GEOMETRY_SHADER => file_path += "geometry.glsl",
                    gl::FRAGMENT_SHADER => file_path += "fragment.glsl",
                    _ => panic!("Unkown shader type: {}", shader_type),
                };
                panic!("\nShader Error: {}{}", file_path, &log[8..]);
            }

            gl::AttachShader(*program, id);
        }
        return id;
    }

    pub fn add_var(&mut self, name: &str, value: UniformValue, send: bool) {
        let loc;
        let name = CString::new(name).unwrap();
        unsafe {
            loc = gl::GetUniformLocation(self.program, name.as_ptr() as *const i8);
        }
        let variable = UniformVariable {
            loc,
            value,
            update: send,
        };
        self.variables.push(variable)
    }

    pub fn set_var(&mut self, index: usize, value: UniformValue) {
        self.variables[index].value = value;
    }
}

impl Drop for Shader {
    fn drop(&mut self) {
        unsafe {
            gl::DeleteProgram(self.program);
        }
    }
}
