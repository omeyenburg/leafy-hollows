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
    let window = window::Window::new();
    window.update();
}
