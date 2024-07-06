#![allow(dead_code)]

struct Point(i32, i32);
impl Point {
    fn sum(&self) -> i32 {
        self.0 + self.1
    }
}

struct Rect {
    x: i32,
    y: i32,
    width: i32,
    height: i32
}
impl Rect {
    fn new(x: i32, y: i32, width: i32, height: i32) -> Self {
        Self {
            x,
            y,
            width,
            height
        }
    }
}

fn main() {
    let p = Point(3, 5);
    let r = Rect::new(0, 1, 3, 4);
    println!("Sum of point: {}", p.sum());
    println!("Size of rect: {}x{}", r.width, r.height);
}
