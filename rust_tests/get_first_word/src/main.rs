use std::io;

fn main() {
    println!("Input some text:");
    let mut input = String::new();
    io::stdin()
        .read_line(&mut input)
        .expect("Failed to read line");

    let mut first_word = String::new();
    for char in input.chars() {
        if char == ' ' {
            break;
        }
        first_word.push_str(&String::from(char));
    }
    println!("The first word in your input was '{}'", first_word);
}
