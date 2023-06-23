import pygame
import math

PIXELS_PER_METER = 50
GRAVITY_CONSTANT = 20 # reality: 9.81 
FRICTION = 1.5

class Physics_Object:
    def __init__(self, mass, position, size):
        self.mass = mass

        self.pos = list(position) # pos used for writing, rect used for reading
        self.vel = [0.0, 0.0]
        self.rect = pygame.Rect(*self.posInt, *size)

        self.collision_flags = [False] * 4 # counterclockwise, 0 is right

        self.collision_frames_skipped = [0] * 4 # collsions aren't detected every frame because of sub-pixel movements
        self.collision_frame_duration = 25 # collisions are held for x frames

        self.onGround = 0

    @property
    def posInt(self):
        return (round(self.pos[0]), round(self.pos[1]))

    def apply_force(self, force, angle): # angle in degrees; 0 is right, counterclockwise
        r_angle = math.radians(angle)

        self.vel[0] += ((math.cos(r_angle) * force) / self.mass) * delta_time
        self.vel[1] += ((math.sin(r_angle) * force) / self.mass) * delta_time
    
    def apply_velocity(self):
        self.pos[0] += self.vel[0] * delta_time
        self.rect.centerx = round(self.pos[0])
        self.x_collide()
        self.rect.centerx = round(self.pos[0])
    
        self.pos[1] += self.vel[1] * delta_time
        self.rect.centery = round(self.pos[1])
        self.y_collide()
        self.rect.centery = round(self.pos[1])

        if self.rect.collidelist(terrain) > 0 and delta_time != 0:
            print("unresolved", delta_time)

    def gravity(self):
        self.apply_force((GRAVITY_CONSTANT * PIXELS_PER_METER) * self.mass, 90)
    
    def x_collide(self):
        for i in self.rect.collidelistall(terrain):
            rect = terrain[i]
            if self.vel[0] < 0:
                self.collision_flags[2] = True
                self.collision_frames_skipped[2] = 0

                self.pos[0] = rect.right + (self.rect.size[0] / 2)
                self.vel[0] = 0

                self.vel[1] /= FRICTION

            if self.vel[0] > 0:
                self.collision_flags[0] = True
                self.collision_frames_skipped[0] = 0

                self.pos[0] = rect.left - (self.rect.size[0] / 2)
                self.vel[0] = 0

                self.vel[1] /= FRICTION
    
    def y_collide(self):
        for i in self.rect.collidelistall(terrain):
            rect = terrain[i]
            if self.vel[1] > 0:
                self.collision_flags[3] = True
                self.collision_frames_skipped[3] = 0

                self.pos[1] = rect.top - (self.rect.size[1] / 2)
                self.vel[1] = 0

                self.vel[0] /= FRICTION
                self.onGround = 3

            if self.vel[1] < 0:
                self.collision_flags[1] = True
                self.collision_frames_skipped[1] = 0

                self.pos[1] = rect.bottom + (self.rect.size[1] / 2)
                self.vel[1] = 0


    def check_collision_skipping(self):
        for i in range(4):
            if self.collision_flags[i]:
                self.collision_frames_skipped[i] += 1
                if self.collision_frames_skipped[i] > self.collision_frame_duration:
                    self.collision_flags[i] = False

    def update(self):
        self.gravity()
        if self.onGround: # onGround (0 - 3)
            self.onGround -= 1

        self.check_collision_skipping()
        self.apply_velocity()

pygame.init()

window = pygame.display.set_mode((300, 300))
clock = pygame.time.Clock()

p = Physics_Object(10, (100, 100), (50, 50))
delta_time = 0

terrain = [pygame.Rect(20, 250, 300, 10), pygame.Rect(20, 230, 10, 10), pygame.Rect(250, 200, 10, 10)]

while True:
    window.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_d]:
        p.apply_force(8000, 0)
    if keys[pygame.K_a]:
        p.apply_force(8000, 180)
    if keys[pygame.K_SPACE] and p.onGround:
        p.apply_force(30000, 270)

    p.update()
    
    fps = clock.get_fps()
    delta_time = (1 / fps) if fps > 0 else delta_time
    pygame.draw.rect(window, (255, 0, 0), p.rect)

    for rect in terrain:
        pygame.draw.rect(window, (255, 255, 0), rect)

    pygame.display.flip()
    clock.tick(30)
