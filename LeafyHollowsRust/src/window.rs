pub const NUMBER: i32 = 6;

pub fn greet(x: i32) -> i32 {
    println!("Hello!");
    x * 2 // does not end with semicolon -> expression instead of statement -> will be returned
}

pub struct Window {

}

impl Window {
    pub fn new() -> Self {
        Self {

        }
    }
    pub fn update(self) {

    }
}