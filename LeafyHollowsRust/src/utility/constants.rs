use crate::read;

pub const PROJECT_NAME: &str = "Leafy Hollows";
pub const PROJECT_DIRECTORY: &str = "LeafyHollows";
pub const OPENGL_VERSION: (u8, u8) = (3, 3);

pub const VERTEX_SHADER_SOURCE: &str = read!("resources/shader/vertex.glsl");
pub const FRAGMENT_SHADER_SOURCE: &str = read!("resources/shader/fragment.glsl");