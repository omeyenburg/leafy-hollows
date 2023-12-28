extern crate sdl2;

use sdl2::TimerSubsystem;
use sdl2::event::Event;
use sdl2::keyboard::Keycode;
use sdl2::pixels::Color;

use crate::constants;

fn size_of<T>() -> usize {
    std::mem::size_of::<T>()
}
pub struct Window {
    sdl_context: sdl2::Sdl,
    window: sdl2::video::Window,
    gl_context: sdl2::video::GLContext,
    event_pump: sdl2::EventPump,
    clock: Clock,
    buffer: Buffer,
}

impl Window {
    // Initialisation method of window
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        // Create sdl context and return error when failing
        let sdl_context: sdl2::Sdl = sdl2::init()?;

        // Get video subsystem and return error on failure
        let video_subsystem: sdl2::VideoSubsystem = sdl_context.video()?;
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

        let display_size: sdl2::rect::Rect = video_subsystem.display_bounds(0)?;
        let title: &str = constants::PROJECT_NAME;
        let width: u32 = (display_size.w / 3 * 2) as u32;
        let height: u32 = (display_size.h / 5 * 3) as u32;

        // Create window and return error on failure
        let window: sdl2::video::Window = video_subsystem
            .window(title, width, height)
            .position_centered()
            .resizable()
            .allow_highdpi()
            .opengl()
            .build()?;

        // Create gl context and return error on failure
        let gl_context: sdl2::video::GLContext = window.gl_create_context()?;
        gl::load_with(|s| video_subsystem.gl_get_proc_address(s) as *const std::os::raw::c_void);

        // Set swap interval to vsync
        window
            .subsystem()
            .gl_set_swap_interval(sdl2::video::SwapInterval::VSync)?;

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
        let event_pump: sdl2::EventPump = sdl_context.event_pump()?;

        unsafe {
            gl::Viewport(0, 0, width as i32, height as i32);
            gl::ClearColor(0.0, 0.0, 0.0, 1.0);
            gl::Enable(gl::BLEND);
            gl::BlendFunc(gl::SRC_ALPHA, gl::ONE_MINUS_SRC_ALPHA);
        }

        // Create vertex array object
        let mut instance_vao = 0;
        unsafe {
            gl::GenVertexArrays(1, &mut instance_vao);
            gl::BindVertexArray(instance_vao);
        }

        let clock = Clock::new(&sdl_context);

        let buffer = Buffer::new();

        // Create and return Window instance
        Ok(Self {
            sdl_context,
            window,
            gl_context,
            event_pump,
            clock,
            buffer,
        })
    }

    pub fn update(mut self) {
        'running: loop {
            for event in self.event_pump.poll_iter() {
                match event {
                    Event::Quit { .. }
                    | Event::KeyDown {
                        keycode: Some(Keycode::Escape),
                        ..
                    } => break 'running,
                    _ => {}
                }
            }
            unsafe {
                gl::ClearColor(0.3, 0.6, 0.4, 1.0);
                gl::Clear(gl::COLOR_BUFFER_BIT);
            }
            self.window.gl_swap_window();
            // The rest of the game loop goes here...

            //::std::thread::sleep(std::time::Duration::new(0, 1_000_000_000u32 / 60));

            self.clock.update();
            //if self.clock.fps > 55.0 {
            println!("{}", self.clock.fps);
            //}
        }
    }
}

struct Clock {
    start: u64,
    timer: TimerSubsystem,
    time: u64,
    last: u64,
    delta_time: u64,
    fps: f32
}

impl Clock {
    fn new(sdl_context: &sdl2::Sdl) -> Self {
        let timer: TimerSubsystem = sdl_context.timer().unwrap();
        let start = timer.performance_counter();
        println!("{start}");

        Self {
            start,
            timer,
            time: 0,
            last: 0,
            delta_time: 1,
            fps: 1.0
        }
    }

    fn update(&mut self) {
        self.time = self.timer.performance_counter() - self.start;
        self.delta_time = self.time - self.last;
        self.last = self.time;
        if self.delta_time != 0 {
            self.fps = 1_000_000_000.0 / (self.delta_time as f32);
        }
    }
}

struct Buffer {
    size: u32,
    index: u32,
    ebo_vertices: gl::types::GLuint,
    vbo_vertices: gl::types::GLuint,
    vbo_dest: gl::types::GLuint,
    vbo_source_color: gl::types::GLuint,
    vbo_shape_transform: gl::types::GLuint,
}

impl Buffer {
    fn new() -> Self {
        let [ebo_vertices, vbo_vertices, vbo_dest, vbo_source_color, vbo_shape_transform] = {
            let mut vbos: [gl::types::GLuint; 5] = [0; 5];
            unsafe {
                gl::GenBuffers(5, vbos.as_mut_ptr());
            }
            vbos
        };

        // Vertices     /**/ Texcoords
        let vertices: Vec<f32> = vec![
            -1.0, -1.0, /**/ 0.0, 0.0, // bottom-left
            -1.0, 1.0, /**/ 0.0, 1.0, // top-left
            1.0, 1.0, /**/ 1.0, 1.0, // top-right
            1.0, -1.0, /**/ 1.0, 0.0, // bottom-right
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
            gl::BindBuffer(gl::ELEMENT_ARRAY_BUFFER, ebo_vertices);
            gl::BufferData(
                gl::ELEMENT_ARRAY_BUFFER,
                (indices.len() * size_of::<u32>()) as gl::types::GLsizeiptr,
                indices.as_ptr() as *const gl::types::GLvoid,
                gl::STATIC_DRAW,
            );

            // VBO: dest
            gl::EnableVertexAttribArray(2);
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_dest);
            gl::BufferData(gl::ARRAY_BUFFER, 0, std::ptr::null(), gl::STREAM_COPY);
            gl::VertexAttribPointer(2, 4, gl::FLOAT, gl::FALSE, 0, std::ptr::null());
            gl::VertexAttribDivisor(2, 1);

            // VBO: source / color
            gl::EnableVertexAttribArray(3);
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_source_color);
            gl::BufferData(gl::ARRAY_BUFFER, 0, std::ptr::null(), gl::STREAM_COPY);
            gl::VertexAttribPointer(3, 4, gl::FLOAT, gl::FALSE, 0, std::ptr::null());
            gl::VertexAttribDivisor(3, 1);

            // VBO: shape | flip (x) | flip (y) | rotation
            gl::EnableVertexAttribArray(4);
            gl::BindBuffer(gl::ARRAY_BUFFER, vbo_shape_transform);
            gl::BufferData(gl::ARRAY_BUFFER, 0, std::ptr::null(), gl::STREAM_COPY);
            gl::VertexAttribPointer(4, 4, gl::FLOAT, gl::FALSE, 0, std::ptr::null());
            gl::VertexAttribDivisor(4, 1);
        }

        Self {
            size: 0,
            index: 0,
            ebo_vertices,
            vbo_vertices,
            vbo_dest,
            vbo_source_color,
            vbo_shape_transform,
        }
    }

    fn add_instance(&self) {}
}
