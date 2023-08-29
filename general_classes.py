import pygame
import math
import random
import threading
from enum import Enum


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def get(self):
        return (self.x, self.y)

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            return Vector(self.x + other.x, self.y + other.y)
        else:
            return Vector(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            return Vector(self.x - other.x, self.y - other.y)
        else:
            return Vector(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            return Vector(self.x * other.x, self.y * other.y)
        else:
            return Vector(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, self.__class__):
            return Vector(self.x / other.x, self.y / other.y)
        else:
            return Vector(self.x / other, self.y / other)

    def __rmul__(self, other):
        self.__mul__(other)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.x == other.x and self.y == other.y:
                return True
            else:
                return False
        else:
            return False

    def round_by_factor(self, factor=1): #round by a factor
        return Vector(round(self.x / factor) * factor, round(self.y / factor) * factor)

    def __round__(self):
        return Vector(round(self.x), round(self.y))

    def __abs__(self):
        return Vector(abs(self.x), abs(self.y))

    def normalize(self):
        # to normalize a vector, the magnitude of as vector (its length, must be divided by each of its values (x, y))]
        # the magniude represents its length and can be found using pythagarus

        magnitude = math.sqrt((self.x * self.x) + (self.y * self.y))

        try:
            self.x /= magnitude
            self.y /= magnitude
        except ZeroDivisionError:
            print("Could not divide by zero, normalize ignored")





    @staticmethod
    def distance(a, b):
        dv = abs(a - b) # using pythagarus
        squaredDistance = (dv.x*dv.x) + (dv.y*dv.y)

        if squaredDistance != 0:
            return math.sqrt(abs(squaredDistance))
        else:
            return 0


    @staticmethod
    def up():
        return Vector(0, -1)
    @staticmethod
    def down():
        return Vector(0, 1)
    @staticmethod
    def left():
        return Vector(-1, 0)
    @staticmethod
    def right():
        return Vector(1, 0)

    @staticmethod
    def random(scale=1):
        x = random.uniform(-scale, scale)
        y = random.uniform(-scale, scale)

        return Vector(x,y)

class Spritesheet:
    def __init__(self, file: str, cellsize):
        self.surface = pygame.image.load(file).convert()
        self.surface.set_colorkey((0,0,0))
        if isinstance(cellsize, Vector):
            self.cellsize = cellsize
        else:
            self.cellsize = Vector(cellsize, cellsize)

    @staticmethod
    def clip_surface(surface, position: Vector, dimensions: Vector, scaler=1):
        handle_surface = surface.copy()
        rect = pygame.Rect(position.x, position.y, dimensions.x, dimensions.y)
        handle_surface.set_clip(rect)
        image = surface.subsurface(handle_surface.get_clip())
        return pygame.transform.scale(image, (dimensions.x * scaler, dimensions.y * scaler))

    def get_sprite(self, position: Vector, scaler=1):
        return Spritesheet.clip_surface(self.surface, position * self.cellsize, self.cellsize, scaler)

class Colour:
    def __init__(self, r, g, b, a=1):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @staticmethod
    def random_between(a, b):
        if(a.r < b.r):
            r = random.randint(a.r, b.r)
        else:
            r = random.randint(b.r, a.r)

        if(a.g < b.g):
            g = random.randint(a.g, b.g)
        else:
            g = random.randint(b.g, a.g)

        if(a.b < b.b):
            b = random.randint(a.b, b.b)
        else:
            b = random.randint(b.b, a.b)

        return Colour(r,g,b)

    def get(self):
        return(self.r * self.a, self.g * self.a, self.b * self.a)

    def __add__(self, other):
        if isinstance(other, self.__class__):
            col =  Colour(self.r + other.r, self.g + other.g, self.b + other.b)
        else:
            col =  Colour(self.r + other, self.g + other, self.b + other)

        col.clamp()
        return col

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            col = Colour(self.r - other.r, self.g - other.g, self.b - other.b)
        else:
            col = Colour(self.r - other, self.g - other, self.b - other)

        col.clamp()
        return col

    def __mul__(self, other):
        if isinstance(other, self.__class__):
            col =  Colour(self.r * other.r, self.g * other.g, self.b * other.b)
        else:
            col =  Colour(self.r * other, self.g * other, self.b * other)

        col.clamp()
        return col
        
    def __rmul__(self, other):
        self.__mul__(other)

    def clamp(self):

        if self.r > 255:
            self.r = 255
        elif self.r < 0:
            self.r = 0

        if self.g > 255:
            self.g = 255
        elif self.g < 0:
            self.g = 0

        if self.b > 255:
            self.b = 255
        elif self.b < 0:
            self.b = 0 # prevents values exceeding colour range 0-255

class Camera:

    class ShakeStream():
        def __init__(self, stream_array, magnitude, duration):
            self.stream_array = stream_array
            self.duration = duration
            self.duration_tracked = duration
            self.magnitude = magnitude
            self.offset = Vector(0,0)

            self.stream_array.append(self)

        def do_shake(self):
            self.offset = Vector.random(self.magnitude * self.duration_tracked/self.duration * 10)

        def run(self):
            if self.duration_tracked > 0:
                self.do_shake()
                self.duration_tracked -= 1
            else:
                self.stream_array.remove(self)

    def __init__(self):
        self.offset_global = Vector(0,0) #global offset, addeded to all positions when drawing

        self.shake_offset = Vector(0,0)
        self.position = Vector(0,0)
        self.background_colour = Colour(10,10,30)
        self.background_image = None #will use instead of background colour is present
        self.duration_tracked = 0 #is multiplied by position to give screenshake position tracked
        self.shake_streams = [] #to allow multiple screenshakes to overlape
        self.freeze_frames = 0
        self.temporary_delta_time = 1

    def freeze(self, freeze_frames: int, freeze_speed):
        self.freeze_frames = freeze_frames
        self.temporary_delta_time = freeze_speed

    def shake(self, magnitude, duration=15):
        thread = threading.Thread(target=self.shake_thread, args=(magnitude/2,duration))
        thread.start()

    def shake_thread(self, magnitude, duration):
        stream = self.ShakeStream(self.shake_streams, magnitude, duration)
        self.shake_streams.append(stream)

    def update(self):
        self.shake_offset = Vector(0,0)
        for shake in self.shake_streams:
            shake.run()
            self.shake_offset += shake.offset

        self.offset_global = self.position + self.shake_offset
