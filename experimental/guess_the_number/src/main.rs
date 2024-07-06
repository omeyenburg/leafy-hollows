use rand::Rng;
use std::{io, cmp::Ordering};

fn main() {
    println!("Guess the number!");

    let secret_number = rand::thread_rng().gen_range(1..=100);

    loop {
        println!("Please enter your guess!");

        let mut guess = String::new();
        io::stdin()
            .read_line(&mut guess)
            .expect("Failed to read line");
        
        let guess: u32 = match guess.trim().parse() {
            Ok(num) => num,
            Err(_) => {
                println!("This is no valid number!");
                continue;
            },
        };

        println!("You guessed: {guess}");
        match guess.cmp(&secret_number) {
            Ordering::Less => println!("The secret number is larger."),
            Ordering::Greater => println!("The secret number is smaller."),
            Ordering::Equal => {
                println!("This guess was correct.");
                break;
            },
        }
    }
}