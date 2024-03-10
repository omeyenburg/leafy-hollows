// Globals
pub const PROJECT_NAME: &str = "Leafy Hollows";
pub const PROJECT_DIRECTORY: &str = "LeafyHollows";
pub const OPENGL_VERSION: (u8, u8) = (3, 3);

// Macros #[macro_export]
macro_rules! load_str {
    ($expr:expr) => {
        include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/", $expr))
    };
}
macro_rules! load_bytes {
    ($expr:expr) => {
        include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/", $expr))
    };
}

// Shaders
pub const VERTEX_SHADER_SOURCE: &str = load_str!("resources/shader/vertex.glsl");
pub const FRAGMENT_SHADER_SOURCE: &str = load_str!("resources/shader/fragment.glsl");

// Sprites
pub const SPRITES_IMAGE: &[u8] = load_bytes!("resources/icon/icon.png");

// Font
pub const FONT_IMAGE: &[u8] = load_bytes!("resources/font/font.png"); 
pub const FONT_DATA: &str = load_str!("resources/font/font.txt");