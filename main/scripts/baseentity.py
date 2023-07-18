# -*- coding: utf-8 -*-
from scripts.geometry import angle
import scripts.physics as physics
import math; math.angle = angle


class Entity(physics.PhysicsObject): # Used for ropes etc.
    ...


class LivingEntity(physics.CollisionPhysicsObject):
    def __init__(self, *args, health: int=0, **kwargs):
        super().__init__(*args, *kwargs)
        self.health: int = health

    def damage(self, amount):
        self.health -= amount


class ChainedEntity(physics.CollisionPhysicsObject):
    def __init__(self, *args, parent=None, length: int=0, start: [float, float]=None,
                 end: [float, float]=None, element_radius: int=1, collision: bool=False, **kwargs):
        super().__init__(10, start, (element_radius, element_radius), *args, force_func=self.apply_force, **kwargs)
        self.fixed_point: [float] = None
        self.radius: int = element_radius
        self.length_index: int = length
        self.parent = parent

        if parent is None: # Element is start of chain
            self.fixed_point: [float] = start

        if length: # Add next chain element
            self.child = ChainedEntity(*args, parent=self, length=length - 1,
                                       start=(start[0] + (end[0] - start[0]) / length, start[1] + (end[1] - start[1]) / length,),
                                       end=end, element_radius=element_radius, collision=collision, **kwargs)
        else: # Element is end of chain
            self.child = None
            self.fixed_point: [float] = end

    def apply_force(self, force: float, angle: float, delta_time: float): # angle in degrees; 0 is right, counterclockwise
        if self.fixed_point:
            return
        r_angle = math.angle(math.radians(angle))

        self.vel[0] += math.cos(r_angle) * force / self.mass * delta_time
        self.vel[1] += math.sin(r_angle) * force / self.mass * delta_time

        """
        if not self.child is None:
            min_angle = math.angle(math.atan2(self.child.rect.x - self.rect.x, self.child.rect.y - self.rect.y) - 0.1)
            max_angle = math.angle(min_angle + math.pi / 2 + 0.2)
            if not min_angle < r_angle < max_angle:
                if abs(max_angle - r_angle) < abs(min_angle - r_angle):
                    #r_angle = max_angle
                    r_angle += force / self.radius
                else:
                    #r_angle = min_angle
                    r_angle -= force / self.radius
                #self.child.rect.centerx = self.rect.centerx + math.cos(r_angle) * self.radius
                #self.child.rect.centery = self.rect.centery + math.sin(r_angle) * self.radius
                #self.child.vel = [0, 0]
                self.rect.centerx = self.child.rect.centerx + math.cos(0) * self.child.radius * 0.9
                self.rect.centery = self.child.rect.centery + math.sin(0) * self.child.radius * 0.9
                self.vel = [0, 0]
        """
        
        if not self.parent is None:
            min_angle = math.angle(math.atan2(self.parent.rect.x - self.rect.x, self.parent.rect.y - self.rect.y) - 0.1)
            max_angle = math.angle(min_angle + math.pi / 2 + 0.2)
            if not min_angle < r_angle < max_angle:
                if abs(max_angle - r_angle) < abs(min_angle - r_angle):
                    #r_angle = max_angle
                    #r_angle += force / self.radius
                    r_angle += 0.1
                    #if abs(max_angle - r_angle) > abs(min_angle - r_angle):
                    #    r_angle -= 0.05
                else:
                    #r_angle = min_angle
                    #r_angle -= force / self.radius
                    #print(force / self.radius)
                    r_angle -= 0.1
                    #if abs(max_angle - r_angle) < abs(min_angle - r_angle):
                    #    r_angle += 0.05
                self.rect.centerx = self.parent.rect.centerx + math.cos(r_angle) * self.parent.radius
                self.rect.centery = self.parent.rect.centery + math.sin(r_angle) * self.parent.radius
                #self.vel = [0, 0]
        #"""

        

    def update(self, world, window):
        super().update(world, window.delta_time)
        if not self.child is None:
            self.child.update(world, window)
            #self.child.vel[0] += self.vel[0] * 0.05
            #self.child.vel[1] += self.vel[1] * 0.05
            """
            direction = (self.child.rect.x - self.rect.x, self.child.rect.y - self.rect.y)
            distance = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
            if distance > self.radius:
                direction = math.atan2(*direction)
                #self.apply_force(distance / 30 - radius, direction, window.delta_time)
                self.rect.x -= math.cos(direction) * (distance - self.radius) / 20
                self.rect.y -= math.sin(direction) * (distance - self.radius) / 20
                self.vel[0] *= 0.5
                self.vel[1] *= 0.5
                #self.vel = [0, 0]
            """
            #self.rect.x = (self.child.rect.x + self.rect.x * 2) / 3
            #self.rect.y = (self.child.rect.y + self.rect.y * 2) / 3
            velx = self.rect.x - self.child.rect.x
            if abs(velx) - self.radius > 0:
                velx = math.copysign(abs(velx) - self.radius, velx) / 4
                self.rect.x -= velx
                self.vel[0] = 0
            
            vely = self.rect.y - self.child.rect.y
            if abs(vely) - self.radius > 0:
                vely = math.copysign(abs(vely) - self.radius, vely) / 4
                self.rect.y -= vely
                self.vel[1] = 0

        if not self.parent is None:
            ...
            #self.parent.vel[0] += self.vel[1] * 0.05
            #self.parent.vel[1] += self.vel[1] * 0.05
            """
            direction = (self.parent.rect.x - self.rect.x, self.parent.rect.y - self.rect.y)
            distance = math.sqrt(direction[0] ** 2 + direction[1] ** 2)
            if distance > self.radius * 2:
                direction = math.atan2(*direction)
                #self.apply_force(distance / 30 - radius, direction, window.delta_time)
                #self.rect.x -= math.cos(direction) * (distance - self.radius) / 20
                #self.rect.y -= math.sin(direction) * (distance - self.radius) / 20
                self.rect.x = (self.parent.rect.x + self.rect.x * 2) / 3
                self.rect.y = (self.parent.rect.y + self.rect.y * 2) / 3
                #self.rect.x -= math.copysign(max(0, abs(self.parent.rect.x) - self.radius * 2), self.parent.rect.x)
                #self.rect.y -= math.copysign(max(0, abs(self.parent.rect.y) - self.radius * 2), self.parent.rect.y)
                self.vel[0] *= 0.5
                self.vel[1] *= 0.5
                self.vel = [0, 0]
            """

            #self.rect.x = (self.rect.x * 3 + math.copysign(max(0, abs(self.parent.rect.x) - self.radius), self.parent.rect.x)) / 4
            #self.rect.y = (self.rect.y * 3 + math.copysign(max(0, abs(self.parent.rect.y) - self.radius), self.parent.rect.y)) / 4

            velx = self.rect.x - self.parent.rect.x
            if abs(velx) - self.radius > 0:
                velx = math.copysign(abs(velx) - self.radius, velx) / 2
                self.rect.x -= velx
                self.vel[0] = 0
            
            vely = self.rect.y - self.parent.rect.y
            if abs(vely) - self.radius > 0:
                vely = math.copysign(abs(vely) - self.radius, vely) / 2
                self.rect.y -= vely
                self.vel[1] = 0

            #self.rect.x += (self.parent.rect.x - self.rect.x) / 2
            #self.rect.y += (self.parent.rect.y - self.rect.y) / 2

            #self.rect.x = (self.parent.rect.x + self.rect.x * 2) / 3
            #self.rect.y = (self.parent.rect.y + self.rect.y * 2) / 3
            

        self.draw(world, window)

        
        if not self.fixed_point is None:
            self.rect.topleft = self.fixed_point
            self.vel[0] *= 0.9
            self.vel[1] *= 0.9
        
    def draw(self, world, window):
        rect = window.camera.map_coord(self.rect, from_world=True)
        window.draw_rect(rect[:2], rect[2:], (0, 0, 255, 255))


class Particle(physics.PhysicsObject): # Does not collide
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CollisionParticle(physics.CollisionPhysicsObject):
    ...