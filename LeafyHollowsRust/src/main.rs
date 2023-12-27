#![allow(dead_code, unused_imports)]
mod window;    // Used A) to introduce window into scope and B) to allow the path "window::greet"
use window::*; // Used for "NUMBER" without "hello::"

extern crate directories;
use directories::ProjectDirs;

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
    if let Some(proj_dirs) = ProjectDirs::from("", "",  "LeafyHollows") {
        println!("Config dir: {:?}", proj_dirs.config_dir());
        println!("Data dir: {:?}", proj_dirs.data_dir());
    }

    let state = State::Game;
    match state {
        State::Game => game(),
        State::Menu => ()
    }
}
