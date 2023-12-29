pub struct Clock {
    start: u64,
    timer: sdl2::TimerSubsystem,
    last: u64,
    delta_time: u64,
    pub time: u64,
    pub fps: f32,
}

impl Clock {
    pub fn new(sdl_context: &sdl2::Sdl) -> Self {
        let timer: sdl2::TimerSubsystem = sdl_context.timer().unwrap();
        let start = timer.performance_counter();
        println!("{start}");

        Self {
            start,
            timer,
            last: 0,
            delta_time: 1,
            time: 0,
            fps: 1.0,
        }
    }

    pub fn update(&mut self) {
        self.time = self.timer.performance_counter() - self.start;
        self.delta_time = self.time - self.last;
        self.last = self.time;
        if self.delta_time != 0 {
            self.fps = 1_000_000_000.0 / (self.delta_time as f32);
        }
    }

    pub fn get_delta_time(&self) -> f32 {
        (self.delta_time as f32) / 1_000_000_000.0
    }
}