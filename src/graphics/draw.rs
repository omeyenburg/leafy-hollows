use crate::window::Window;

impl Window {
    pub fn draw_rectangle(&mut self, rect: [f32; 4], color: [f32; 4], rotation: f32) {
        self.buffer.add_instance([0.0, rotation], rect, color)
    }

    pub fn draw_circle(&mut self, center: [f32; 2], color: [f32; 4], radius: f32) {
        self.buffer.add_instance(
            [1.0, 0.0],
            [
                center[0] - radius,
                center[1] - radius,
                2.0 * radius,
                2.0 * radius,
            ],
            color,
        )
    }

    pub fn draw_image(
        &mut self,
        rect: [f32; 4],
        image: u32,
        rotation: f32,
        flip_x: i32,
        flip_y: i32,
    ) {
        self.buffer.add_instance(
            [2.0, image as f32],
            rect,
            [flip_x as f32, flip_y as f32, rotation, 0.0],
        )
    }

    pub fn draw_char(&mut self, rect: [f32; 4], c: char, color: [f32; 4]) {
        let char_id: f32 = self.font.get_index(c) as f32;
        self.buffer
            .add_instance([3.0, char_id], rect, color)
    }

    pub fn draw_text(&mut self, center: [f32; 2], text: &str, size: f32, color: [f32; 4]) {
        let length = text.len();
        for (i, c) in text.chars().enumerate() {
            let x = center[0] + (i as f32 - length as f32 * 0.5 + 1.0 / 5.0 * i as f32) * size;
            self.draw_char([x, center[1], size * 0.5, size], c, color)
        }
    }
}
