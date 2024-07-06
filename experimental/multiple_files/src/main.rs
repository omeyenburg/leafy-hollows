use hello::*; // Used for "NUMBER" without "hello::"
mod hello;    // Used for "hello::greet"

fn main() {
    let x: i32 = hello::greet(NUMBER);
    println!("{x}");
}
