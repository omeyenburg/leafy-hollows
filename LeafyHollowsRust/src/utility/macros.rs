#[macro_export]
macro_rules! unwrap {
    [$expr:expr] => {
        match $expr {
            Ok(value) => value,
            Err(err) => {
                eprintln!("\nError: {:?}.", err);
                panic!("");
            }
        }
    };
}
