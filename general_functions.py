import math
import threading
import time
import pygame
from general_classes import *

def clamp(x, minimum, maximum):
    if(x > maximum):
        x = maximum
    elif(x < minimum):
        x = minimum

    return x #clamps value within range
def clamp_and_tell(x, minimum, maximum): #clamps value and returns IF the value was clamped
    clamped = False
    new_x = clamp(x, minimum, maximum)
    if(new_x != x):
        clamped = True

    return new_x, clamped #clamps value within range

def vector_between(a: Vector, b: Vector, offset: Vector = Vector(0,0)): #returns the vector direction from one to another
    w, h = b.x - a.x + offset.x, b.y - a.y + offset.y
    vector = Vector(w, h)
    vector.normalize()

    return vector
def distance_between(a: Vector, b: Vector):
    return math.sqrt((b.x - a.x)**2 + (b.y-a.y)**2)
def angle_between(a: Vector, b: Vector, degree_offset=0): #returns the angle between two vectors

    direction = vector_between(a, b) #direction vector, to be converted to an angle

    # the direction vector tells us the position on the unit cicle which we can then find calculate the desired angle with
    # (x, y) = (cos0, sin0)
    angle = math.atan2(direction.y, direction.x)
    angle = math.degrees(angle) - degree_offset

    return angle
def angle_to_vector(deg, degree_offset=0):
    rot = math.radians(deg)

    x = math.cos(rot)
    y = math.sin(rot)

    return Vector(x,y)
def vector_to_angle(a: Vector, degree_offset=0):

    direction = a
    direction.normalize

    angle = math.atan2(a.y, a.x)
    angle = math.degrees(angle) - degree_offset

    return angle





def get_circle_surface(radius, colour):
    radius = round(radius)
    surf = pygame.Surface((radius*2, radius*2))
    pygame.draw.circle(surf, colour.get(), (radius, radius), radius)
    surf.set_colorkey((0,0,0))
    return surf
def get_rect_surface(rect, colour):
    surf = pygame.Surface((rect.width, rect.height))
    pygame.draw.rect(surf, colour.get(), rect, 0)
    surf.set_colorkey((0,0,0))
    return surf
