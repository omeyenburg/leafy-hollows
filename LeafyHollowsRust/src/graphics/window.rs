use sdl2::event::Event;
use sdl2::keyboard::Keycode;
use sdl2::pixels::Color;

use crate::constants;
use crate::graphics::clock;
use crate::graphics::buffer;
use crate::graphics::input;


pub struct Window {
    sdl_context: sdl2::Sdl,
    window: sdl2::video::Window,
    gl_context: sdl2::video::GLContext,
    event_pump: sdl2::EventPump,
    clock: clock::Clock,
    buffer: buffer::Buffer,
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

        let clock = clock::Clock::new(&sdl_context);

        let buffer = buffer::Buffer::new();

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
            println!("{}", self.clock.get_delta_time());
            //}

            self.buffer.add_instance([0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]);
            self.buffer.update();
        }
    }
}
