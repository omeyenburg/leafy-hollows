#![allow(dead_code, unused_imports)]
use anyhow::{Context, Result};

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

    let mut r = 0.0;
    while window.running {
        r += window.clock.delta_time;
        window.draw_rectangle([0.0, 0.0, 0.5, 0.5], [0.7, 0.2, 0.3, 0.9], r);
        window.update();
    }
}
