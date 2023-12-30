#![allow(dead_code, unused_imports)]
mod graphics;
mod utility;

use graphics::window;
use utility::constants;
use utility::file;

enum State {
    Menu,
    Game,
    // ...
}

fn game() {
    let var = "Hello, world!";
    println!("{}", var);
}

fn main() {
    // Directories used: config_dir for options; data_dir for other data (!!!paths are identical on macos!!!)
    println!("{:?}", file::get_config_directory());

    let state = State::Game;
    match state {
        State::Game => game(),
        State::Menu => (),
    }
    let mut window = window::Window::new();

    let mut r: f32 = 0.0;
    while window.running {
        r += window.clock.delta_time as f32;

        for i in 0..100 {
            window.draw_rectangle(
                [
                    (i as f32 / 50.0 + window.clock.time as f32).cos() * 0.2,
                    -0.25 + i as f32 / 200.0,
                    0.5,
                    0.5,
                ],
                [0.7 * i as f32 / 100.0, 0.2, 0.4, 0.9],
                r,
            );
        }
        window.update();
    }
}
