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

#[macro_export]
macro_rules! read {
    ($expr:expr) => {
        include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/", $expr))
    };
}
