// https://www.youtube.com/watch?v=CpvzeyzgQdw
use std::path::{Path, PathBuf};
use std::fs;

fn main() {
    let dir = Path::new("./");
    let mut full_path = PathBuf::from(dir);
    let file_name = "Cargo.toml";
    full_path.push(file_name);
    let content = fs::read_to_string(full_path).expect("Couldn't read file.");

    println!("{}", content);
}
