use gl::types::{GLenum, GLint, GLuint};
use std::ffi::CString;

pub struct Shader {
    program: GLuint,
    variables: Vec<u32>,
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

    pub fn apply(&self) {
        unsafe {
            gl::UseProgram(self.program);
        }
    }

    fn attach_shader(program: &GLuint, path: &str, shader_type: GLenum) -> GLenum {
        let source_code = CString::new(path).unwrap();
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
                eprint!("{}", log);
                panic!("Failed to compile shader!")
            }

            gl::AttachShader(*program, id);
        }
        return id;
    }
}

impl Drop for Shader {
    fn drop(&mut self) {
        unsafe {
            gl::DeleteProgram(self.program);
        }
    }
}
