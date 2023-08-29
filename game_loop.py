import math
from general_classes import *
import settings
from game import *


FONT_SMALL = Font("fonts/font_small.png") #custom font object, for rendering text (use FONT.render() )


def update_setting_parameters():
    mouse_pos_raw = pygame.mouse.get_pos()
    settings.MOUSE_POSITION = Vector(mouse_pos_raw[0] * settings.DISPLAY_SIZE.x/settings.WINDOW_SIZE.x, mouse_pos_raw[1] * settings.DISPLAY_SIZE.y/settings.WINDOW_SIZE.y)

    #without delta_time
    #settings.CLOCK.tick(settings.TARGET_FPS)
    #with delta_time
    delta_time = settings.CLOCK.tick(settings.TARGET_FPS) * 0.001 * 60

    if settings.CAMERA.freeze_frames > 0:
        settings.DELTA_TIME = settings.CAMERA.temporary_delta_time
        settings.CAMERA.freeze_frames -= 1
    else:
        settings.DELTA_TIME = delta_time

    if settings.DEBUG_MODE:
        pygame.draw.circle(settings.UI_DISPLAY, (255,255,255), settings.MOUSE_POSITION.get(), 2, 1)

        fps = settings.CLOCK.get_fps()
        FONT_SMALL.render(settings.UI_DISPLAY, "FPS: "+str(round(fps)), Vector(5, 15), "left")

while(settings.RUNNING):


    settings.DISPLAY.fill(settings.CAMERA.background_colour.get())
    settings.UI_DISPLAY.fill((0,0,0))
    settings.UI_DISPLAY.set_colorkey((0,0,0))

    if settings.CAMERA.background_image != None:
        settings.DISPLAY.blit(settings.CAMERA.background_image, (0,0))

    update()
    update_setting_parameters()
    Entity.update_entities()
    settings.CAMERA.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            settings.RUNNING = False;

        manage_events(event)
        for e in settings.ENTITIES:
            e.on_event(event)

    scaled_display = pygame.transform.scale(settings.DISPLAY, settings.WINDOW_SIZE.get())
    settings.WINDOW.fill(settings.CAMERA.background_colour.get())

    scaled_ui_display = pygame.transform.scale(settings.UI_DISPLAY, settings.WINDOW_SIZE.get())

    settings.WINDOW.blit(scaled_display, (0,0))
    settings.WINDOW.blit(scaled_ui_display, (0,0))

    pygame.display.update()
