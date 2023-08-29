import math
import random
import pygame

from general_classes import * #functions and classes unrelated to the entity
from general_functions import *
import settings #global game variables
from entity_classes import * #entity components
from prefabs import * #premade entity bases

def play_sound(filename: str, volume=1):
    sound = pygame.mixer.Sound(filename)
    sound.set_volume(volume)
    sound.play()

#IMPORTING ALL FILES
