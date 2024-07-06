use crate::constants::*;
use std::collections::HashMap;

pub struct Font {
    hashmap: HashMap<char, i32>,
}

impl Font {
    pub fn new() -> Self {
        let mut hashmap: HashMap<char, i32> = HashMap::new();
        for (i, c) in FONT_DATA.chars().enumerate() {
            hashmap.entry(c).or_insert(i as i32);
        }

        Self { hashmap }
    }

    pub fn supports_char(&self, c: char) -> bool {
        self.hashmap.contains_key(&c)
    }

    pub fn get_index(&self, c: char) -> i32 {
        match self.hashmap.get(&c) {
            Some(index) => *index,
            None => 74, // 74 == "?"
        }
    }
}
