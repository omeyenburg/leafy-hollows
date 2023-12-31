use crate::window::Window;

impl Window {
    pub fn draw_rectangle(&mut self, rect: [f32; 4], color: [f32; 4], rotation: f32) {
        self.buffer.add_instance(rect, color, [0.0, 0.0, 0.0, rotation])
    }

    pub fn draw_image(&mut self, rect: [f32; 4], _image: u32, rotation: f32) {
        self.buffer.add_instance(rect, [0.0, 0.0, 1.0, 1.0], [1.0, 0.0, 0.0, rotation])
    }
}