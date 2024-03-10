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
        r += window.clock.delta_time as f32 * 0.3;

        for i in 0..100 {
            window.draw_image(
                [
                    (i as f32 / 50.0 + window.clock.time as f32).cos() * 0.2,
                    -0.25 + i as f32 / 200.0,
                    0.5,
                    0.5,
                ],
                1,
                r,
            );
        }

        window.draw_circle([1.0, 0.3], [0.6, 0.2, 0.9, 0.7], 0.2);
        //window.draw_text([0.0, 0.0, 1.0, 1.0], 4);

        window.update();
    }
}
