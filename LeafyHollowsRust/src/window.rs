use sdl2::pixels::Color;
use sdl2::event::Event;
use sdl2::keyboard::Keycode;
use sdl2::video::{GLContext, SwapInterval};
use std::time::Duration;

use crate::constants;


pub struct Window {
    sdl_context: sdl2::Sdl,
    window: sdl2::video::Window,
    gl_context: GLContext,
    gl: (),
    event_pump: sdl2::EventPump
}

impl Window {
    pub fn new() -> Self {
        let sdl_context = sdl2::init().unwrap();
        let video_subsystem = sdl_context.video().unwrap();
        let gl_attr = video_subsystem.gl_attr();
        gl_attr.set_context_profile(sdl2::video::GLProfile::Core);
        gl_attr.set_context_version(3, 3);

        let title = constants::PROJECT_NAME;
        let width = 500;
        let height = 500;

        let window = video_subsystem.window(title, width, height)
            .position_centered()
            .build()
            .unwrap();

        let gl_context = window.gl_create_context().unwrap();
        let gl = gl::load_with(|s| {
            video_subsystem.gl_get_proc_address(s) as *const std::os::raw::c_void
        });

        window.subsystem()
            .gl_set_swap_interval(SwapInterval::VSync)
            .unwrap();

        let event_pump = sdl_context.event_pump().unwrap();

        Self {
            sdl_context,
            window,
            gl_context,
            gl,
            event_pump
        } 
    }
    pub fn update(mut self) {
        'running: loop {
            for event in self.event_pump.poll_iter() {
                match event {
                    Event::Quit {..} |
                    Event::KeyDown { keycode: Some(Keycode::Escape), .. } => {
                        break 'running
                    },
                    _ => {}
                }
            }
            unsafe {
                gl::ClearColor(0.9, 0.1, 0.1, 1.0);
                gl::Clear(gl::COLOR_BUFFER_BIT);
            }
            self.window.gl_swap_window();
            // The rest of the game loop goes here...

            ::std::thread::sleep(Duration::new(0, 1_000_000_000u32 / 60));
        }
    }
}