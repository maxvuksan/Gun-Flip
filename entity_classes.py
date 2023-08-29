from general_classes import *
from general_functions import *
import settings
import pickle


class Font:
    def __init__(self, path: str, colour=Colour(255,255,255)):
        #settings.FONT ORDER:
        self.character_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'Y', 'X', 'Z', '.', '-', ',', ':', '+', """'""", '!', '?', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '(', ')', '/', '_', '=', '/', '[', ']', '*', '"', '<', '>', ';']
        self.characters = { } #the sub surface of each character
        self.spacing = 1
        font_img = pygame.image.load(path)

        pixel_array = pygame.PixelArray(font_img)
        pixel_array.replace((255,255,255), colour.get())

        current_char_width = 0
        char_count = 0

        for x in range(font_img.get_width()):
            col = font_img.get_at((x, 0))
            if col[0] == 43: #the dividers red value, loop has hit divided
                char_image = Spritesheet.clip_surface(font_img, Vector(x - current_char_width,0), Vector(current_char_width, font_img.get_height()))
                self.characters[self.character_order[char_count]] = char_image.copy()
                self.characters[self.character_order[char_count]].set_colorkey((0,0,0))
                char_count += 1
                current_char_width = 0
            else:
                current_char_width += 1

            if char_count == 56: # last character
                break

        self.space_char_width = self.characters["A"].get_width()

    def render(self, surface: pygame.Surface, text: str, position: Vector,alignment="center",scaler=1, world_space=False):

        if world_space:
            position -= settings.CAMERA.offset_global
        else:
            position -= settings.CAMERA.shake_offset

        text = text.upper()
        x_offset = 1 #how far we have moved along
        y_offset = 0
        match alignment:
            case "center":
                text_width = 0
                for char in text:
                    if char != " ":
                        text_width += (self.characters[char].get_width() + self.spacing) * scaler
                    else:
                        text_width += (self.space_char_width + self.spacing) * scaler
                x_offset -= text_width/2
                y_offset = (self.characters['A'].get_height() * scaler) /2

        for char in text:
            if char != " ":
                img = pygame.transform.scale(self.characters[char], (self.characters[char].get_width() * scaler, self.characters[char].get_height() * scaler))
                img.set_colorkey((0,0,0))
                surface.blit(img, (position.x + x_offset, position.y - y_offset))
                x_offset += (self.characters[char].get_width() + self.spacing) * scaler
            else:
                x_offset += (self.space_char_width + self.spacing) * scaler


class Entity:
    def __init__(self):
        self.tag = "default"
        self.components = []
        self.children = [] #destroys all of these aswell on destroy
        self.transform = Transform()
        self.layer = 0 #allows excluded collisions between layers
        settings.ENTITIES.append(self)
        self.change_priority(0)

    def change_priority(self, priority):

        self.priority = priority #the position this entity updates in relation to the entire list
        match_found = False

        for i in range(len(settings.UPDATE_LAYERS)):
            if priority == settings.UPDATE_LAYERS[i]:
                match_found = True
                break

        if not match_found:
            settings.UPDATE_LAYERS.append(priority)

        settings.UPDATE_LAYERS.sort()

    @staticmethod
    def update_entities():
        settings.ALL_COLLIDERS = []

        for e in settings.ENTITIES:
            for c in e.components:
                if isinstance(c, Collider):
                    settings.ALL_COLLIDERS.append(c)
                elif isinstance(c, Tilemap) and c.collisions: #collisions are enabled on said tilemap
                    Tilemap.add_colliders_to_list(c)

        for i in range(len(settings.UPDATE_LAYERS)):
            for e in settings.ENTITIES:
                if e.priority == settings.UPDATE_LAYERS[i]:
                    e.update()

    def destroy_in(self, seconds):
        thread = threading.Thread(target=self.destroy, args=(seconds,))
        thread.start()
    def destroy(self, seconds=0):
        if(seconds > 0):
            time.sleep(seconds)

        for child in self.children:
            child.destroy()

        try:
            settings.ENTITIES.remove(self)
            self.on_destroy()

        except ValueError:
            pass #has already been removed from list


    def remove_in(self, component: str, seconds):
        thread = threading.Thread(target=self.remove, args=(component,seconds))
        thread.start()
    def remove(self, component: str, seconds=0):
        if(seconds > 0):
            time.sleep(seconds)
        for c in self.components:
            if isinstance(c, eval(component)):
                self.components.remove(c)
    def add(self, component: str):
        self.components.append(eval(component+"(self)"))
        return self.get(component)
    def get(self, component: str):
        for c in self.components:
            if isinstance(c, eval(component)):
                return c
        return None

    def update(self):
        self.transform.update()
        for c in self.components:
            c.update()

        self.update_extension()
        self.update_extension2()

        if settings.DEBUG_MODE:
            pygame.draw.circle(settings.DISPLAY, (0,255,0), self.transform.position_final.get(), 1)
    def update_extension(self):
        pass #can be defined in children to extend upon method
    def update_extension2(self):
        pass #can be defined in children to extend upon method
    def on_event(self, event):
        pass
    def on_destroy(self):
        pass
    def on_collision(self, collider_entity):
        pass
    def on_trigger(self, trigger_entity):
        pass

class Transform:
    class Mode(Enum):
        Absolute = "absolute"
        Relative = "relative" #in relation to the parent

    def __init__(self):
        self.position = Vector(0,0) #position relative to any parent
        self.position_global = Vector(0,0)
        self.position_final = Vector(0,0) #position after parent offsets are applied

        self.position_mode = self.Mode.Relative
        self.parent = None

        self.scale = Vector(1,1)
        self.rotation = 0
        self.rotation_mode = self.Mode.Relative
        self.rotation_final = self.rotation

    def update(self):

        if self.position_mode == self.Mode.Relative and self.parent is not None:
            if self.parent.transform.rotation == 0:
                self.position_global = self.position + self.parent.transform.position_global
            else: # use trig to calc new position

                distance = distance_between(self.parent.transform.position_global, self.position + self.parent.transform.position_global)

                origin = self.parent.transform.position_global
                radians = math.radians(self.parent.transform.rotation_final)

                x = (math.cos(radians)) * distance
                y = (math.sin(radians)) * distance

                position = Vector(x, y)
                self.position_global = position + self.parent.transform.position_global
        else:
            self.position_global = self.position

        self.position_final = self.position_global - settings.CAMERA.offset_global

        if self.rotation_mode == self.Mode.Relative and self.parent is not None:
            self.rotation_final = self.rotation + self.parent.transform.rotation_final
        else:
            self.rotation_final = self.rotation

        self.rotation_final %= 360 #stops rotation exceeding 360

    @staticmethod
    def centre(position: Vector, dimensions: Vector):
        return Vector(position.x - dimensions.x/2, position.y - dimensions.y/2)

    @staticmethod
    def centre_revert(position: Vector, dimensions: Vector):
        return Vector(position.x + dimensions.x/2, position.y + dimensions.y/2)

    def scale_dimensions(self, dimensions: Vector):
        return Vector(dimensions.x * self.scale.x, dimensions.y * self.scale.y)


    def up(self,offset=0):
        vec = angle_to_vector(self.rotation_final + offset)
        return vec

    def down(self):
        return self.up(180)

    def left(self):
        return self.up(-90)

    def right(self):
        return self.up(90)

class BlitMode(Enum):
    Subtract = "subtract" #subtracts glow colour from pixels
    Add = "add" #adds glow colour to pixels
    Overlay = "overlay"
class Shape(Enum):
    Rect = "rect"
    Circle = "circle"
    Diamond = "diamond"

class ParticleSource:

    class Mode(Enum):
        Default = "default"
        Overtime = "overtime" #changes from colour 1 -> colour 2
        Between = "between" #random value between given values
        Random = "random" #random one of the colours

    class Particle:
        def __init__(self, source, angle: int, variance: Vector, speed, radius: int, colour: Colour):
            self.source = source
            self.angle = angle
            self.position = source.parent.transform.position_global + variance
            self.radius = radius
            self.radius_final = self.radius
            self.colour = colour
            self.colour_final = self.colour
            self.duration = 0
            self.lifetime_factor = 0
            self.speed = speed
            #for diamond shapes
            self.points = []

        def update(self):

            direction = angle_to_vector(self.angle)

            if self.duration > self.source.lifetime:
                self.source.kill_particle(self)

            self.lifetime_factor = self.duration/self.source.lifetime
            speed_multipler = 1

            if self.source.speed_curve == -1:
                speed_multipler = 1 - self.lifetime_factor
            elif self.source.speed_curve == 1:
                speed_multipler = self.lifetime_factor

            self.position += (direction * self.speed * speed_multipler * settings.DELTA_TIME)


            if self.source.shrink_overtime:
                self.radius_final = self.radius * (1 - self.lifetime_factor)
            else:
                self.radius_final = self.radius

            if self.source.colour_mode == self.source.Mode.Overtime and isinstance(self.source.colour, list):
                col1 = self.source.colour[1] * self.lifetime_factor
                col2 = self.source.colour[0] * (1 - self.lifetime_factor)

                self.colour_final = col1 + col2
                self.colour_final.clamp()
            else:
                self.colour_final = self.colour
            if self.source.glow and self.radius_final > 0:

                glow_radius = self.radius_final + self.source.glow_radius
                glow = get_circle_surface(glow_radius, self.source.glow_colour)
                glow_position = self.position - glow_radius - settings.CAMERA.offset_global

                if self.source.glow_mode == BlitMode.Add:
                    settings.DISPLAY.blit(glow, glow_position.get(), special_flags=pygame.BLEND_RGB_ADD)
                elif self.source.glow_mode == BlitMode.Subtract:
                    settings.DISPLAY.blit(glow, glow_position.get(), special_flags=pygame.BLEND_RGB_SUB)
                elif self.source.glow_mode == BlitMode.Overlay:
                    settings.DISPLAY.blit(glow, glow_position.get())
                else:
                    raise ValueError("glow_colour has an invalid ParticleSource.Mode")

            self.duration += settings.DELTA_TIME
            self.angle += self.source.angle_overtime * settings.DELTA_TIME

        def draw(self):

            pos = self.position - settings.CAMERA.offset_global

            match self.source.shape:
                case Shape.Circle:
                    pygame.draw.circle(settings.DISPLAY, self.colour_final.get(), pos.get(), self.radius_final)

                case Shape.Diamond:

                    angle = math.radians(self.angle)

                    top = Vector(pos.x + math.cos(angle) * self.radius, pos.y + math.sin(angle) * self.radius)
                    bottom = Vector(pos.x - math.cos(angle) * self.radius * self.source.diamond_trail, pos.y - math.sin(angle) * self.radius * self.source.diamond_trail)

                    bottom_final = bottom
                    top_final = top
                    if self.source.shrink_overtime:
                        bottom_final = (pos * self.lifetime_factor) + (bottom_final * (1 - self.lifetime_factor))
                        top_final = (pos * self.lifetime_factor) + (top_final * (1 - self.lifetime_factor))

                    left = Vector(pos.x - math.cos(angle + 90) * self.radius  * self.source.diamond_width/10, pos.y - math.sin(angle + 90) * self.radius * self.source.diamond_width/10)
                    right = Vector(pos.x + math.cos(angle + 90) * self.radius * self.source.diamond_width/10, pos.y + math.sin(angle + 90) * self.radius * self.source.diamond_width/10)

                    points = (top_final.get(), left.get(), bottom_final.get(), right.get())
                    pygame.draw.polygon(settings.DISPLAY, self.colour_final.get(), points)



    def __init__(self, parent: Entity):
        self.parent = parent

        self.shape = Shape.Circle
        #valid shapes are:
        #Circle, Diamond
        self.diamond_width = 1
        self.diamond_trail = 1

        self.particles = []
        self.count = 1 #per frame
        self.delay = 0 #frames skipped per particle
        self.delay_tracked = self.delay #tracking that skipped amount
        self.emit = True
        self.burst = False

        self.glow = False
        self.glow_colour = Colour(255,255,255,0.4)
        self.glow_radius = 2
        self.glow_mode = BlitMode.Add

        self.gravity = 1
        self.angle = [0, 360]
        self.angle_overtime = 0
        self.variance = 0.2
        self.speed = 2

        self.lifetime = 50

        self.radius = [8, 4]
        self.shrink_overtime = True
        self.speed_curve = 0
        #should be set to 1 for increase over time, -1 for decrease over time

        self.colour_mode = self.Mode.Overtime
        self.colour = Colour(255,255,255)

    def update(self):

        if self.emit:
            if self.delay_tracked <= 0:
                self.delay_tracked = self.delay #reseting the delay timer

                for i in range(self.count):
                    variance = Vector(random.uniform(-self.variance, self.variance), random.uniform(-self.variance, self.variance))

                    if isinstance(self.angle, list):
                        angle = random.uniform(self.angle[0], self.angle[1])
                        direction = self.angle
                    else:
                        angle = self.angle

                    if isinstance(self.radius, list):
                        radius = random.uniform(self.radius[0], self.radius[1])
                    else:
                        radius = self.radius

                    colour = Colour(255,255,255)
                    if isinstance(self.colour, list):
                        index = 0
                        if self.colour_mode == self.Mode.Random:
                            index = random.randint(0, len(self.colour) - 1)
                            colour = self.colour[index]
                        elif self.colour_mode == self.Mode.Between:
                            colour = Colour.random_between(self.colour[0], self.colour[1])

                    else:
                        colour = self.colour

                    new_particle = self.Particle(self, angle, variance, self.speed, radius, colour)
                    self.particles.append(new_particle)

                if self.burst:
                    self.emit = False

            else:
                self.delay_tracked -= settings.DELTA_TIME


        for p in self.particles:
            p.update()
        for p in self.particles:
            p.draw()

    def stop_in(self, seconds):
        thread = threading.Thread(target=ParticleSource.stop_thread, args=(self,seconds))
        thread.start()

    @staticmethod
    def stop_thread(source,seconds):
        time.sleep(seconds)
        source.emit = False


    def kill_particle(self, particle: Particle):
        self.particles.remove(particle)

class TilemapSaveData:
    def __init__(self, layer_count, origin, grids, sprite_file, cellsize):
        self.layer_count = layer_count
        self.origin = origin
        self.sprite_file = sprite_file
        self.grids = grids
        self.cellsize = cellsize
class TilemapGroup:
    def __init__(self, filename, position=Vector(0,0)):
        f = open(filename, 'rb')
        data = pickle.load(f)
        f.close()

        self.tilemaps = {}
        for layer in data.grids:
            e = Entity()
            e.add("Tilemap").assign(settings.DISPLAY, Vector(100,100), data.cellsize, Spritesheet(data.sprite_file, data.cellsize))
            e.get("Tilemap").origin = data.origin - (position/8)
            e.get("Tilemap").grid = data.grids[layer]
            e.change_priority(layer)
            self.tilemaps[layer] = e.get("Tilemap")
class TilemapEditor:

    def __init__(self, surface, sprite_file: str, save_file: str, cellsize, window_size, display_size):

        self.transform = Transform()
        self.surface = surface
        self.save_file = save_file
        self.sprite_file = sprite_file
        self.window_size = window_size
        self.display_size = display_size
        self.ui_size = Vector(100, window_size.y)

        self.cellsize = cellsize
        self.spritesheet = Spritesheet(sprite_file, cellsize)
        self.tile_count = round(self.spritesheet.surface.get_width()/self.cellsize)
        # which tile is going to be placed
        self.selected_tile = 0

        self.tilemaps = {}
        self.surfaces = {}
        self.current_layer = 0
        self.dimensions = Vector(20 * self.cellsize,20 * self.cellsize)
        self.reset()

        self.origin = Vector(0,0)

        self.macros = { "ctrl": False, "remove": False, "place": False}

    def save(self):
        grids = {}
        for layer in self.tilemaps:
            grids[layer] = self.tilemaps[layer].grid

        print(self.sprite_file)
        data = TilemapSaveData(len(self.tilemaps), self.origin, grids, self.sprite_file, self.cellsize)
        f = open(self.save_file, 'wb')
        pickle.dump(data, f)
        f.close()
        print(f"saved in {self.save_file}")

    def open(self):

        f = open(self.save_file, 'rb')
        data = pickle.load(f)
        f.close()

        self.sprite_file = data.sprite_file
        self.cellsize = data.cellsize
        self.spritesheet = Spritesheet(self.sprite_file, self.cellsize)
        self.tile_count = round(self.spritesheet.surface.get_width()/self.cellsize)
        self.origin = data.origin
        self.current_layer = 0
        self.tilemaps = {}
        self.surfaces = {}
        for layer in data.grids:
            self.create_new_layer(layer)
            self.tilemaps[layer].grid = data.grids[layer]


    def draw_ui(self, window):
        color = (60, 30, 80)

        rect = pygame.Rect(0,0, self.ui_size.x, self.ui_size.y) #ui pannel
        pygame.draw.rect(window, color, rect)

        rect2 = pygame.Rect(self.ui_size.x + 2,0, 2, self.ui_size.y) # accent line
        pygame.draw.rect(window, color, rect2)

        settings.FONT.render(window, f"layer: {self.current_layer}", Vector(8,8), scaler = 2, alignment = "left")

        for i in range(self.tile_count):
            scaler = 3
            space = 1
            position = Vector(8, 8 + i * scaler * (self.cellsize + space) + 24)

            if i == self.selected_tile:
                rect = pygame.Rect(position.x - 3, position.y - 3, self.cellsize * scaler + 6, self.cellsize * scaler + 6)
                pygame.draw.rect(window, (255,255,255), rect, 3)

            window.blit(self.spritesheet.get_sprite(Vector(i,0), scaler), (position.x, position.y))

    def reset(self):
        self.tilemaps = {}
        self.current_layer = 0
        self.create_new_layer(0)

    def create_new_layer(self, layer):
        self.tilemaps[layer] = Tilemap(self)
        self.surfaces[layer] = pygame.Surface((self.display_size.x, self.display_size.y))
        self.surfaces[layer].set_colorkey((0,0,0))
        self.tilemaps[layer].assign(self.surfaces[layer], self.dimensions, self.cellsize, self.spritesheet)

    def change_layer(self, direction):
        self.current_layer += direction

        if not(self.current_layer in self.tilemaps):
            self.create_new_layer(self.current_layer)
    def change_tile(self, direction):
        new_value = self.selected_tile + direction

        if(new_value > self.tile_count - 1):
            new_value = 0
        elif(new_value < 0):
            new_value = self.tile_count - 1

        self.selected_tile = new_value

    def update(self):
        for layer in self.tilemaps:
            self.tilemaps[layer].surface.fill((0,0,0))
            if layer != self.current_layer:

                self.tilemaps[layer].surface.set_alpha(80)
                self.tilemaps[layer].update()
                self.surface.blit(self.tilemaps[layer].surface, (0,0))

        self.tilemaps[self.current_layer].surface.set_alpha(255)
        self.tilemaps[self.current_layer].update()
        self.surface.blit(self.tilemaps[self.current_layer].surface, (0,0))
        #draw this layer on top

        mouse_pos_raw = pygame.mouse.get_pos()
        mouse_pos_raw = Vector((self.display_size.x/(self.window_size.x - self.window_size.x/4)) * (mouse_pos_raw[0] - self.cellsize/2), (self.display_size.y/(self.window_size.y - self.window_size.y/4)) * (mouse_pos_raw[1] - self.cellsize/2))
        mouse_pos_raw -= Vector(self.window_size.x/16 + self.ui_size.x/4 + 4, self.window_size.y/16)
        mouse_pos = mouse_pos_raw.round_by_factor(self.cellsize)
        #which tile is currently being hovered
        self.focused_tile = round(mouse_pos / self.cellsize)

        cursor_rect = pygame.Rect(mouse_pos.x, mouse_pos.y, self.cellsize, self.cellsize)

        cursor_colour = (255,255,255)
        origin_colour = (255,255,0)

        if self.macros["ctrl"]:
            cursor_colour = origin_colour

        pygame.draw.rect(self.surface, cursor_colour, cursor_rect, 1)

        cursor_rect.x = self.origin.x * self.cellsize
        cursor_rect.y = self.origin.y * self.cellsize
        pygame.draw.rect(self.surface, origin_colour, cursor_rect, 1)


        #detecting change of cursor state
        if self.macros["remove"]:
            self.remove()
        elif self.macros["place"]:
            self.place()

    def place(self):
        if self.macros["ctrl"]: #place origin if holding control
            self.origin = self.focused_tile
        else: #place block instead
            tile = Tile(self.selected_tile)
            self.tilemaps[self.current_layer].set_at(self.focused_tile, tile)

    def remove(self):
        self.tilemaps[self.current_layer].set_at(self.focused_tile, 0)

class ColliderType(Enum):
    Solid = "solid"
    Platform = "platform" #different collider behaviour (solid, platform, etc...)
class Tilemap:
    def create_grid(self):
        self.grid = []
        for x in range(self.dimensions.x):
            column = []
            for y in range(self.dimensions.y):
                column.append(0); #0 represents no tile
            self.grid.append(column)
    def __init__(self, parent: Entity):
        self.origin = Vector(0,0)
        self.parent = parent
        self.collisions = False
    def assign(self, surface, dimensions: Vector, cellsize: int, spritesheet: Spritesheet):
        self.surface = surface
        self.dimensions = dimensions
        self.cellsize = cellsize
        self.spritesheet = spritesheet
        self.create_grid()
    def enable_colliders(self, collider_type=ColliderType.Solid):
        self.collisions = True
        for x in range(self.dimensions.x):
            for y in range(self.dimensions.y):
                if self.grid[x][y] != 0:
                    pos = self.parent.transform.position_final - (self.origin * self.cellsize)
                    if collider_type == ColliderType.Platform:
                        dimensions = Vector(self.cellsize, 2)
                    else:
                        dimensions = Vector(self.cellsize, self.cellsize)
                    col = TileCollider(self.parent, pos + (Vector(x, y) * self.cellsize), dimensions)
                    col.collider_type = collider_type
                    self.grid[x][y].collider = col
    @staticmethod
    def add_colliders_to_list(tilemap):
        for x in range(len(tilemap.grid)):
            for y in range(len(tilemap.grid[x])):
                if tilemap.grid[x][y] != 0:
                    settings.ALL_COLLIDERS.append(tilemap.grid[x][y].collider)

    def set_at(self, position: Vector, tile=0): #defaults to empty space
        self.grid[position.x][position.y] = tile

    def update(self):
        for x in range(self.dimensions.x):
            for y in range(self.dimensions.y):

                if self.grid[x][y] != 0:
                    pos = self.parent.transform.position_final - (self.origin * self.cellsize )
                    self.surface.blit(self.spritesheet.get_sprite(Vector(self.grid[x][y].index, 0)), (pos.x + (x * self.cellsize), pos.y + (y * self.cellsize)))
                    if self.collisions:
                        self.grid[x][y].collider.update()
class Tile:
    def __init__(self, index: int):
        self.index = index
        self.collider = None

class Collider:

    def __init__(self, parent: Entity):
        self.parent = parent
        self.dimensions = Vector(0,0)
        self.rect = pygame.Rect(0,0,0,0) #init a default rect
        self.scaled_dimensions = Vector(0,0)
        self.collider_type = ColliderType.Solid
        self.exclusion_layers = []
        self.bounce = 0
        self.bounce_share = True #are other colliders effected / bounced off this collided
        self.friction = 1

    def update(self):
        dim = self.dimensions
        if self.dimensions == Vector(0,0):
            if self.parent.get("ImageRenderer") != None: #use the image dimensions (allows colliders ease of use with sprites)
                image = self.parent.get("ImageRenderer").image
                dim = Vector(image.get_width(), image.get_height())

        self.scaled_dimensions = self.parent.transform.scale_dimensions(dim)
        centre_position = Transform.centre(self.parent.transform.position_global, self.scaled_dimensions) #+ settings.CAMERA.position
        self.rect = pygame.Rect(centre_position.get(), self.scaled_dimensions.get())

        if settings.DEBUG_MODE:
            pos = Transform.centre(self.parent.transform.position_final, self.scaled_dimensions)
            draw_rect = pygame.Rect(pos.get(), self.scaled_dimensions.get())
            pygame.draw.rect(settings.DISPLAY, (0,255,0), draw_rect, 1)

    @staticmethod
    def collision_test(self, colliders: list, exclusion_layers=[]):
        collisions = []
        bounce = 0
        friction = 0

        for c in colliders:

            exclude = False
            for layer in exclusion_layers:
                if c.parent.layer == layer:
                    exclude = True

            if not exclude and self is not c:
                if self.rect.colliderect(c.rect):
                    collisions.append(c)

                    if c.bounce_share:
                        bounce = c.bounce
                    if c.friction > 0:
                        if c.friction > friction:
                            friction = c.friction


        return collisions, bounce, friction

    @staticmethod
    def point_in_collider(point: Vector, colliders: list, exclusion_layers=[]):
        for c in colliders:
            exclude = False
            for layer in exclusion_layers:
                if c.parent.layer == layer:
                    exclude = True

            if not exclude:
                if c.rect.collidepoint(point.get()):
                    return True
        return False

    @staticmethod
    def on_collision_entity_calls(entity, collisions_x, collisions_y=[]):
        cols = []
        for c in collisions_y:
            cols.append(c)

        for c in collisions_x:
            added = False
            for exisiting_collider in cols:
                if c == exisiting_collider:
                    added = True
                    break
            if not added:
                cols.append(c)

        for c in cols:
            c.parent.on_collision(entity)
            entity.on_collision(c.parent)

    def move(self, movement: Vector):
        #when a movement is made, it tackles each dimension seperately
        collision_check = {"x": False, "y": False}
        self.rect.y += movement.y

        friction = Vector(0,0)
        bounce = Vector(0,0)

        collisions_y, bounce.y, friction.y = Collider.collision_test(self, settings.ALL_COLLIDERS, self.exclusion_layers)

        for c in collisions_y:
            if movement.y > 0:
                self.rect.bottom = c.rect.top
                collision_check["y"] = True
                self.grounded = True
            elif movement.y < 0 and c.collider_type != ColliderType.Platform:
                self.rect.top =  c.rect.bottom
                collision_check["y"] = True

        self.rect.x += movement.x
        collisions_x, bounce.x, friction.x = Collider.collision_test(self, settings.ALL_COLLIDERS, self.exclusion_layers)

        for c in collisions_x:
            if c.collider_type != ColliderType.Platform:
                if movement.x > 0:
                    self.rect.right = c.rect.left
                    collision_check["x"] = True
                elif movement.x < 0:
                    self.rect.left = c.rect.right
                    collision_check["x"] = True

        Collider.on_collision_entity_calls(self.parent, collisions_x, collisions_y)

        self.parent.transform.position = Transform.centre_revert(self.rect, self.scaled_dimensions)

        return collision_check["x"], collision_check["y"], bounce + self.bounce, friction
class Trigger:
    def __init__(self, parent: Entity):
        self.parent = parent
        self.offset = Vector(0,0)
        self.dimensions = Vector(1,1)
        self.triggered = False
        self.exclusion_layers = []

    def check_if_triggered(self):
        collisions, bounce, frictioon = Collider.collision_test(self, settings.ALL_COLLIDERS, self.exclusion_layers)
        if collisions != []: #not an empty array
            self.triggered = True
            Trigger.on_trigger_entity_calls(self.parent, collisions)
        else:
            self.triggered = False

    def on_trigger_entity_calls(entity, collisions):
        for c in collisions:
            c.parent.on_trigger(entity)
            entity.on_trigger(c.parent)


    def update(self):
        scaled_dimensions = self.parent.transform.scale_dimensions(self.dimensions)
        pos = Transform.centre(self.parent.transform.position_global + (self.offset * self.parent.transform.scale), scaled_dimensions)

        self.rect = pygame.Rect(pos.get(), scaled_dimensions.get())

        self.check_if_triggered()

        if settings.DEBUG_MODE:
            colour = (255,255,0)
            if self.triggered:
                colour = (255,0,0)

            pos = Transform.centre(self.parent.transform.position_final + (self.offset * self.parent.transform.scale), scaled_dimensions)
            rect = pygame.Rect(pos.get(), scaled_dimensions.get())

            pygame.draw.rect(settings.DISPLAY, colour, rect, 1)
class TileCollider(Collider): # collider which never moves #SHOULD NOT BE ADDED TO COMPONENTS, ONLY FOR TILEMAPS
    def __init__(self, parent: Entity, position_offset: Vector, dimensions: Vector):
        self.parent = parent

        self.position_offset = position_offset
        self.dimensions = dimensions

        pos = self.parent.transform.position_global + self.position_offset
        self.rect = pygame.Rect(pos.get(), self.dimensions.get())

        self.exclusion_layers = []
        self.bounce = 0
        self.bounce_share = True #are other colliders effected
        self.friction = 1

    def update(self): #overrides the original collider update

        pos = self.parent.transform.position_global + self.position_offset
        self.rect = pygame.Rect(pos.get(), self.dimensions.get())

        if settings.DEBUG_MODE:
            pos = self.parent.transform.position_final + self.position_offset
            draw_rect = pygame.Rect(pos.get(), self.dimensions.get())
            pygame.draw.rect(settings.DISPLAY, (0,255,0), draw_rect, 1)

    def move(*args):
        print("can not move a static collider!")

class Rigidbody:
    def __init__(self, parent: Entity):
        self.parent = parent

        self.gravity_inital = 1
        self.gravity_increment = 0.15
        self.gravity = 2
        self.bounce = 0
        self.bounce_count = 0
        self.destroy_on_collision = False

        self.use_torque = False
        self.torque = 0
        self.torque_strength = 1
        self.torque_drag = 1
        self.velocity = Vector(0,0)
        self.drag = Vector(0,0) #constant opposing force on velocity
        self.max_velocity = Vector(10,10)

    def update(self):
        if self.gravity != 0:
            if self.velocity.y < self.max_velocity.y * self.gravity:
                self.velocity.y += self.gravity_increment * self.gravity * settings.DELTA_TIME

        #capping the velocity
        if(abs(self.velocity.x) > self.max_velocity.x):
            self.velocity.x = self.max_velocity.x * self.velocity.x/abs(self.velocity.x)
        if(abs(self.velocity.y) > self.max_velocity.y):
            self.velocity.y = self.max_velocity.y * self.velocity.y/abs(self.velocity.y)


        colX, colY = False, False
        if self.parent.get("Collider"): #move via the colliders
            colX, colY, bounce, friction = self.parent.get("Collider").move(self.velocity * settings.DELTA_TIME)

            if colX or colY:
                potential_rebound = Vector(0,0)

                if self.destroy_on_collision:
                    self.parent.destroy()
                    return

                if colX:
                    if bounce.x > 0:
                        potential_rebound.x = -self.velocity.x * bounce.y
                        if abs(potential_rebound.x) < 0.1:
                            potential_rebound.x = 0


                    self.velocity.x = 0

                if colY:
                    if bounce.y > 0:
                        potential_rebound.y = -self.velocity.y * bounce.y
                        if abs(potential_rebound.y) < 0.1:
                            potential_rebound.y = 0

                    self.velocity.y = 0



                if potential_rebound.x != 0 or potential_rebound.y != 0:
                    self.velocity += potential_rebound
                    self.bounce_count += 1


        else:
            self.parent.transform.position += self.velocity #* settings.DELTA_TIME


        # DRAG ######################################
        if self.velocity.x > self.drag.x:
            self.velocity.x -= self.drag.x * settings.DELTA_TIME
        elif self.velocity.x < -self.drag.x:
            self.velocity.x += self.drag.x * settings.DELTA_TIME
        else:
            self.velocity.x = 0

        if self.velocity.y > self.drag.y:
            self.velocity.y -= self.drag.y * settings.DELTA_TIME
        elif self.velocity.y < -self.drag.y:
            self.velocity.y += self.drag.y * settings.DELTA_TIME
        else:
            self.velocity.y = 0

        # TORQUE ######################################


        if self.torque != 0:
            self.parent.transform.rotation += self.torque * settings.DELTA_TIME
            new_torque = self.torque * (1/(1 + (self.torque_drag/100)))
            dif = new_torque - self.torque
            self.torque = self.torque + (dif * settings.DELTA_TIME)

            if abs(self.torque) < 0.001:
                self.torque = 0




    def add_force(self, force):
        self.velocity += force

        if self.use_torque:
            if self.velocity.x > 0:
                self.torque = self.torque_strength
            else:
                self.torque = -self.torque_strength

class ImageRenderer:
    def __init__(self, parent: Entity):
        self.parent = parent

        self.outline = False
        self.outline_colour = Colour(255,255,255)
        self.fill = False
        self.fill_tracked = 0
        self.fill_colour = Colour(255,255,255)

        self.flip_x = False
        self.flip_y = False
        self.glow = False
        self.glow_radius = 2
        self.glow_colour = Colour(255,255,255,0.2)
        self.glow_shape = Shape.Rect
        self.glow_mode = BlitMode.Add
        self.glow_offset = Vector(0,0)
        self.show_image = True
        self.image = None

    def assign(self, image): #Accepts a surface or filename
        if isinstance(image, str):
            self.image = pygame.image.load(image)
        else:
            self.image = image
            self.image.set_colorkey((0,0,0))

    @staticmethod
    def get_rotated_surface(surf, rotation, position):
        angle = -rotation
        image = pygame.transform.rotate(surf, angle)
        image_rect = image.get_rect(center = position.get())

        return image, image_rect

    def flash(self, time):
        self.fill_tracked = time

    def update(self):

        if self.image != None:
            dimensions = self.parent.transform.scale_dimensions( Vector(self.image.get_width(), self.image.get_height()) )
            image = pygame.transform.scale(self.image, dimensions.get())
            centre_position = Transform.centre(self.parent.transform.position_final, dimensions)

            if self.glow:
                rect = pygame.Rect(0, 0, dimensions.x + self.glow_radius * 2, dimensions.y + self.glow_radius * 2)

                glow = None
                if self.glow_shape == Shape.Rect:
                    glow = get_rect_surface(rect, self.glow_colour)
                else:
                    glow = get_circle_surface(rect.width/2 + self.glow_radius, self.glow_colour)

                glow, position_rect = ImageRenderer.get_rotated_surface(glow, self.parent.transform.rotation_final,  self.parent.transform.position_final + self.glow_offset)

                if self.glow_mode == BlitMode.Subtract:
                    settings.DISPLAY.blit(glow, position_rect, special_flags=pygame.BLEND_RGB_SUB)
                elif self.glow_mode == BlitMode.Add:
                    settings.DISPLAY.blit(glow, position_rect, special_flags=pygame.BLEND_RGB_ADD)
                else:
                    settings.DISPLAY.blit(glow, position_rect)

            if self.show_image:
                if self.parent.transform.rotation_final > 0: #the image needs to be rotated

                    image = ImageRenderer.flip_surface(image, self.flip_x, self.flip_y)
                    image, position_rect = ImageRenderer.get_rotated_surface(image, self.parent.transform.rotation_final, self.parent.transform.position_final)

                    if self.outline:
                        self.draw_outline(Vector(position_rect.left, position_rect.top), image)

                    settings.DISPLAY.blit(image, position_rect)

                    if self.fill or self.fill_tracked > 0:
                        self.fill_surf(Vector(position_rect.left, position_rect.top), image)
                else:
                    image = ImageRenderer.flip_surface(image, self.flip_x, self.flip_y)

                    if self.outline:
                        self.draw_outline(centre_position, image)
                    settings.DISPLAY.blit(image, centre_position.get())

                    if self.fill or self.fill_tracked > 0:
                        self.fill_surf(centre_position, image)





    @staticmethod
    def get_mask_surf(image):
        mask = pygame.mask.from_surface(image)
        mask_surface = mask.to_surface()
        return mask_surface


    def fill_surf(self, position: Vector, image):
        mask_surface = ImageRenderer.get_mask_surf(image)
        mask_surface.set_colorkey((0,0,0))

        pixel_array = pygame.PixelArray(mask_surface)
        pixel_array.replace((255,255,255), self.fill_colour.get())
        del pixel_array

        settings.DISPLAY.blit(mask_surface, position.get())

    def draw_outline(self, position: Vector, image):
        mask_surface = ImageRenderer.get_mask_surf(image)
        mask_surface.set_colorkey((0,0,0))

        pixel_array = pygame.PixelArray(mask_surface)
        pixel_array.replace((255,255,255), self.outline_colour.get())
        del pixel_array

        offsets = [Vector(-1, 0), Vector(1, 0), Vector(0, -1), Vector(0, 1)]
        for offset in offsets:
            pos = round(offset + position)
            settings.DISPLAY.blit(mask_surface, pos.get())

    @staticmethod
    def flip_surface(surf, flip_x, flip_y):
        return pygame.transform.flip(surf, flip_x, flip_y)

class ImageAnimator:
    def __init__(self, parent):
        self.parent = parent
        if parent.get("ImageRenderer") == None:
            self.parent.add("ImageRenderer")

        self.ir = self.parent.get("ImageRenderer")
        self.ir.assign(pygame.Surface( (1,1)) )

        self.state = ""
        self.previous_state = ""
        self.clips = []
        self.current_clip = None

        self.current_frame = 0

        self.current_frame_lifetime = 0 #how long the frame has been held for

    def update(self):
        if self.previous_state != self.state:

            self.current_frame = 0

            for clip in self.clips:
                if clip.state == self.state:
                    self.current_clip = clip
                    self.current_frame_lifetime = clip.frame_and_duration[0][1]
                    self.ir.assign(clip.frame_and_duration[0][0]) #[0] is the image
                    break

        if self.current_clip != None:

            if self.current_frame_lifetime >= self.current_clip.frame_and_duration[self.current_frame - 1][1]: #[1] is the image hold duration

                self.ir.assign(self.current_clip.frame_and_duration[self.current_frame][0]) #[0] is the image

                if self.current_frame < self.current_clip.count - 1:
                    self.current_frame += 1
                    self.current_frame_lifetime = 0
                else:
                    self.current_frame = 0
                    self.current_frame_lifetime = 0

            self.current_frame_lifetime += settings.DELTA_TIME

        self.previous_state = self.state
class ImageAnimationClip:
    def __init__(self, state_name, frame_durations, sprite_sheet: Spritesheet, frame_count=-1, row_number=0):
        self.state = state_name

        self.count = frame_count
        if frame_count == -1: #assuming all animations on spritesheet are same nubmer of frames
            self.count = round(sprite_sheet.surface.get_width()/sprite_sheet.cellsize.x)

        self.frame_and_duration = [] #structured as so [frame/image, duration]
        for i in range(self.count):
            duration = frame_durations
            if isinstance(frame_durations, list):
                try:
                    duration = frame_durations[i]
                except IndexError:
                    print("the number of animation frames must be equal to the frame duration list!")

            self.frame_and_duration.append([sprite_sheet.get_sprite(Vector(i, row_number)), duration])


        #check how many frames in spritesheet

        #assign

class LineRenderer:
    def __init__(self, parent):
        self.parent = parent

        self.direction = Vector(1,1)
        self.max_length = 400
        self.check_multiple = 10 #how often does the line check for collisions
        self.collision = False
        self.colour = Colour(255,255,255)
        self.exclusion_layers = []
        self.blit_mode = BlitMode.Overlay
        self.width = 1
        self.origin = Vector(0,0)

    def update(self):
        current_position = self.origin
        end_position = Vector(0,0)
        steps_taken = 0
        while steps_taken < self.max_length:

            if self.collision and steps_taken % self.check_multiple == 0:
                if Collider.point_in_collider(current_position, settings.ALL_COLLIDERS, self.exclusion_layers):
                    break

            round_pos = round(current_position)
            #settings.DISPLAY.set_at(round_pos.get(), self.colour.get())
            current_position += self.direction
            steps_taken += 1
        pygame.draw.line(settings.DISPLAY, self.colour.get(), self.parent.transform.position_final.get(), current_position.get(), width=self.width)
class Slider:
    def __init__(self, parent: Entity):
        self.parent = parent
        self.value = 0.5
        self.width = 16
        self.height = 4
        self.alignment = "center"
        self.full_colour = Colour(255,255,255)
        self.empty_colour = Colour(150,150,150)
        self.rect = None

    def assign(self, width, height):
        self.width = width
        self.height = height

    def update(self):

        offset_x = 0
        if self.alignment == "center":
            offset_x = self.width/2

        full_rect = pygame.Rect(self.parent.transform.position_final.x - offset_x, self.parent.transform.position_final.y, self.width * self.value, self.height)
        empty_rect = pygame.Rect(self.parent.transform.position_final.x - offset_x, self.parent.transform.position_final.y, self.width, self.height)

        pygame.draw.rect(settings.DISPLAY, self.empty_colour.get(), empty_rect)
        pygame.draw.rect(settings.DISPLAY, self.full_colour.get(), full_rect)

class Interactable:
    def __init__(self, parent: Entity):
        self.parent = parent
        self.radius = 23
        self.buffer_time = 8
        self.target = None #takes an entity to track
        self.time_within_focus = 0
        self.targets_in_range = []
        self.debug_colour = Colour(200,50,200)


    def update(self):
        if self.target is not None:
            distance = 9999
            self.targets_in_range = []
            if isinstance(self.target, list):
                self.focus_function(self.target)
            else:

                self.focus_function([self.target])


    def focus_function(self, targets=[]):

        in_range = False
        for target in targets:
            distance = Vector.distance(target.transform.position_final, self.parent.transform.position_final)
            if distance < self.radius:

                self.time_within_focus += 1
                in_range = True
                if self.time_within_focus > self.buffer_time: #gives the interactable a buffer when entering
                    self.targets_in_range.append(target)
                    self.debug_colour = Colour(200,50,200)
                else:
                    self.debug_colour = Colour(255,50,50)

                if settings.DEBUG_MODE:
                    pygame.draw.line(settings.DISPLAY, self.debug_colour.get(), target.transform.position_final.get(), self.parent.transform.position_final.get())

        if not in_range:
            self.time_within_focus = 0

#must be declared after because uses these components
from prefabs import *
