use crate::constants::*;
use std::collections::HashMap;

fn load() {
    let mut font_hashmap: HashMap<char, i32> = HashMap::new();
    for (i, c) in FONT_DATA.chars().enumerate() {
        font_hashmap.entry(c).or_insert(i as i32);
    }
}
