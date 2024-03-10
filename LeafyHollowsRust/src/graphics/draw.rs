use crate::window::Window;

impl Window {
    pub fn draw_rectangle(&mut self, rect: [f32; 4], color: [f32; 4], rotation: f32) {
        self.buffer.add_instance([0.0, rotation], rect, color)
    }

    pub fn draw_circle(&mut self, center: [f32; 2], color: [f32; 4], radius: f32) {
        self.buffer.add_instance([1.0, 0.0], [center[0] - radius, center[1] - radius, 2.0 * radius, 2.0 * radius], color)
    }

    pub fn draw_image(&mut self, rect: [f32; 4], _image: u32, rotation: f32) {
        self.buffer.add_instance([2.0, rotation], rect, [0.0, 0.0, 1.0, 1.0])
    }

    pub fn draw_text(&mut self, rect: [f32; 4], char: u32) {
        self.buffer.add_instance([3.0, char as f32], rect, [0.0, 0.0, 1.0, 1.0])
    }
}