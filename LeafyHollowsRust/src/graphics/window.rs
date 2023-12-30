use sdl2::pixels::Color;

use crate::graphics::buffer;
use crate::graphics::clock;
use crate::graphics::input;
use crate::graphics::shader;

use crate::unwrap;
use crate::utility::constants;
use crate::utility::file;

pub struct Window {
    pub running: bool,
    pub width: i32,
    pub height: i32,
    sdl_context: sdl2::Sdl,
    window: sdl2::video::Window,
    gl_context: sdl2::video::GLContext,
    pub event_pump: sdl2::EventPump,
    pub clock: clock::Clock,
    pub buffer: buffer::Buffer,
    shader: shader::Shader,
}

impl Window {
    // Initialisation method of window
    pub fn new() -> Self {
        // Create sdl context and return error when failing
        let sdl_context: sdl2::Sdl = unwrap![sdl2::init()];

        // Get video subsystem and return error on failure
        let video_subsystem: sdl2::VideoSubsystem = unwrap![sdl_context.video()];
        println!("Display bounds: {:?}", video_subsystem.display_bounds(0));
        println!(
            "Usable display bounds: {:?}",
            video_subsystem.display_usable_bounds(0)
        );
        println!(
            "Default display mode: {:?}",
            video_subsystem.current_display_mode(0)
        );
        println!("Video driver: {:?}", video_subsystem.current_video_driver());
        let gl_attr: sdl2::video::gl_attr::GLAttr<'_> = video_subsystem.gl_attr();
        gl_attr.set_context_profile(sdl2::video::GLProfile::Core);
        gl_attr.set_context_version(constants::OPENGL_VERSION.0, constants::OPENGL_VERSION.1);

        let display_size: sdl2::rect::Rect = unwrap![video_subsystem.display_bounds(0)];
        let title: &str = constants::PROJECT_NAME;
        let width: i32 = display_size.w / 3 * 2;
        let height: i32 = display_size.h / 5 * 3;

        // Create window and return error on failure
        let window = video_subsystem
            .window(title, width as u32, height as u32)
            .position_centered()
            .resizable()
            .allow_highdpi()
            .opengl()
            .build();
        let window = unwrap![window];

        // Create gl context and return error on failure
        let gl_context: sdl2::video::GLContext = unwrap![window.gl_create_context()];
        gl::load_with(|s| video_subsystem.gl_get_proc_address(s) as *const std::os::raw::c_void);

        // Set swap interval to vsync
        //window.subsystem().gl_set_swap_interval(sdl2::video::SwapInterval::VSync);

        // Depth size
        println!("Default depth size: {:?}", gl_attr.depth_size());

        // OpenGL version
        let version = unsafe {
            let data = gl::GetString(gl::VERSION) as *const i8;
            std::ffi::CStr::from_ptr(data).to_str().unwrap().to_owned()
        };
        println!("OpenGL version: {}", version);

        // Antialiasing
        println!("Multisample buffers: {:?}", gl_attr.multisample_buffers());
        println!("Multisample samples: {:?}", gl_attr.multisample_samples());
        unsafe {
            gl::Enable(gl::MULTISAMPLE);
            //GL.glDisable(GL.GL_MULTISAMPLE)
        }

        // Create event pump and return error on failure
        let event_pump: sdl2::EventPump = unwrap![sdl_context.event_pump()];

        unsafe {
            //gl::Viewport(0, 0, width, height);
            gl::ClearColor(0.0, 0.0, 0.0, 1.0);
            gl::Enable(gl::BLEND);
            gl::BlendFunc(gl::SRC_ALPHA, gl::ONE_MINUS_SRC_ALPHA);
        }

        let clock = clock::Clock::new(&sdl_context);
        let buffer = buffer::Buffer::new();

        let vertex = unwrap![file::read("ressources/shader/vertex.glsl")];
        let fragment = unwrap![file::read("ressources/shader/fragment.glsl")];
        let mut shader = shader::Shader::new(&vertex, &fragment);

        shader.add_var(
            "window_size_relation",
            shader::UniformValue::Float(height as f32 / width as f32),
            true,
        );

        unsafe {
            gl::BindVertexArray(buffer.vao);
            gl::ClearColor(0.3, 0.6, 0.4, 1.0);
        }

        // Create and return Window instance
        Self {
            running: true,
            width,
            height,
            sdl_context,
            window,
            gl_context,
            event_pump,
            clock,
            buffer,
            shader,
        }
    }

    pub fn update(&mut self) {
        self.events();
        self.shader.set_var(
            0,
            shader::UniformValue::Float(self.height as f32 / self.width as f32),
        );
        self.shader.update();

        unsafe {
            gl::Clear(gl::COLOR_BUFFER_BIT);
            gl::DrawElementsInstanced(
                gl::TRIANGLES,
                6,
                gl::UNSIGNED_INT,
                std::ptr::null(),
                self.buffer.index as i32,
            );
        }

        self.window.gl_swap_window();
        self.clock.update();
        self.buffer.index = 0;
    }
}
