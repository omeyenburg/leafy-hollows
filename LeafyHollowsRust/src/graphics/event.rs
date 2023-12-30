use sdl2::event::{Event, WindowEvent};
use sdl2::keyboard::Keycode;

use crate::window::Window;

impl Window {
    pub fn events(&mut self) {
        for event in self.event_pump.poll_iter() {
            match event {
                Event::Quit { .. }
                | Event::KeyDown {
                    keycode: Some(Keycode::Escape),
                    ..
                } => {self.running = false},
                Event::Window {
                    timestamp: _,
                    window_id: _,
                    win_event,
                } => match win_event {
                    WindowEvent::SizeChanged(width, height) => {
                        self.width = width;
                        self.height = height;
                    }
                    WindowEvent::FocusLost => println!("App lost focus -> pause game!"),
                    _ => {}
                },
                Event::KeyDown {
                    timestamp: _,
                    window_id: _,
                    keycode,
                    scancode: _,
                    keymod,
                    repeat,
                } => println!("Key down: {keycode:?}, Keymod: {keymod}, Repeat: {repeat}"),
                Event::KeyUp {
                    timestamp: _,
                    window_id: _,
                    keycode,
                    scancode: _,
                    keymod,
                    repeat,
                } => println!("Key up: {keycode:?}, Keymod: {keymod}, Repeat: {repeat}"),
                Event::TextInput {
                    timestamp: _,
                    window_id: _,
                    text,
                } => println!("Text input: {text}"),
                Event::MouseMotion {
                    timestamp: _,
                    window_id: _,
                    which: _,
                    mousestate: _,
                    x,
                    y,
                    xrel,
                    yrel,
                } => println!("Moved mouse: ({x}|{y}), Velocity: ({xrel}|{yrel})"),
                Event::MouseButtonDown {
                    timestamp: _,
                    window_id: _,
                    which: _,
                    mouse_btn,
                    clicks: _,
                    x: _,
                    y: _,
                } => println!("Pressed mouse button: {mouse_btn:?}"),
                Event::MouseButtonUp {
                    timestamp: _,
                    window_id: _,
                    which: _,
                    mouse_btn,
                    clicks: _,
                    x: _,
                    y: _,
                } => println!("Released mouse button: {mouse_btn:?}"),
                Event::MouseWheel {
                    timestamp: _,
                    window_id: _,
                    which: _,
                    x,
                    y,
                    direction,
                    precise_x,
                    precise_y,
                } => println!("Mouse wheel: {x}, {y}; Precise: {precise_x}, {precise_y}; Wheel direction: {direction:?}"),
                _ => {}
            }
        }
    }
}