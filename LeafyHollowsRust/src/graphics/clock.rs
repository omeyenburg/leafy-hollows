pub struct Clock {
    start: f64,
    timer: sdl2::TimerSubsystem,
    last: f64,
    pub time: f64,
    pub delta_time: f64,
    pub fps: f64,
}

impl Clock {
    pub fn new(sdl_context: &sdl2::Sdl) -> Self {
        let timer: sdl2::TimerSubsystem = sdl_context.timer().unwrap();
        let start: f64 = timer.performance_counter() as f64;

        Self {
            start,
            timer,
            last: 0.0,
            time: 0.0,
            delta_time: 1.0,
            fps: 1.0,
        }
    }

    pub fn update(&mut self) {
        self.time = (self.timer.performance_counter() as f64 - self.start) * 0.000000001;
        self.delta_time = self.time - self.last;
        self.last = self.time;
        if self.delta_time > 0.0 {
            self.fps = 1.0 / self.delta_time;
        }
    }
}
