import pygame, sys, numbers
from random import choice, randint
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_position
from pygame.key import get_pressed as key_pressed
from pygame.image import load as load_image
from setting import *
from support import *

from menu import Menu
from timery import Timer


class Editor:
    def __init__(self, land_tiles) -> None:
        # main setup
        self.display_surface = pygame.display.get_surface()
        self.canvas_data = {}

        # imports
        self.land_tiles = land_tiles
        self.imports()

        # clouds
        self.current_clouds = []
        self.cloud_surf = import_folder("./graphics/clouds")
        self.cloud_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.cloud_timer, 200)
        self.startup_clouds()

        # navigation
        self.origin = vector()
        self.pan_active = False
        self.pan_offset = vector()

        # support lines
        self.suport_line_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.suport_line_surf.set_colorkey("green")
        self.suport_line_surf.set_alpha(30)

        # selection
        self.selection_index = 2
        self.last_selected_cell = None

        # menu
        self.menu = Menu()

        # objects
        self.canvas_objects = pygame.sprite.Group()
        self.foreground = pygame.sprite.Group()
        self.background = pygame.sprite.Group()
        self.object_drag_active = False
        self.object_timer = Timer(400)

        # Player
        CanvasObject(
            pos=(200, WINDOW_HEIGHT / 2),
            frames=self.animations[0]["frames"],
            tile_id=0,
            origin=self.origin,
            group=[self.canvas_objects, self.foreground],
        )

        # sky
        pos = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)

        self.sky_handle = CanvasObject(
            pos=pos,
            frames=[self.sky_handle_surf],
            tile_id=1,
            origin=self.origin,
            group=[self.canvas_objects, self.background],
        )

    # SUPPORT
    def imports(self):
        self.water_bottom = load_image(
            "./graphics/terrain/water/water_bottom.png"
        ).convert_alpha()
        self.sky_handle_surf = load_image(
            "./graphics/cursors/handle.png"
        ).convert_alpha()

        # ANIMATIONS
        self.animations = {}
        for key, value in EDITOR_DATA.items():
            if value["graphics"]:
                graphics = import_folder(value["graphics"])
                self.animations[key] = {
                    "frame_index": 0,
                    "frames": graphics,
                    "lenght": len(graphics),
                }
        # preview
        self.preview_surfs = {
            key: load_image(value["preview"])
            for key, value in EDITOR_DATA.items()
            if value["preview"]
        }

    def get_current_cell(self, obj=None):
        distance_to_origin = (
            vector(mouse_position()) - self.origin
            if not obj
            else vector(obj.distance_to_origin) - self.origin
        )
        col = (
            int(distance_to_origin.x / TILE_SIZE)
            if distance_to_origin.x > 0
            else int(distance_to_origin.x / TILE_SIZE) - 1
        )
        row = (
            int(distance_to_origin.y / TILE_SIZE)
            if distance_to_origin.y > 0
            else int(distance_to_origin.y / TILE_SIZE) - 1
        )
        return col, row

    def check_neighbors(self, cell_position):
        # create a local cluster
        cluster_size = 3
        local_cluster = [
            (
                cell_position[0] + col - int(cluster_size / 2),
                cell_position[1] + row - int(cluster_size / 2),
            )
            for col in range(cluster_size)
            for row in range(cluster_size)
        ]

        # check Neighbors
        for cell in local_cluster:
            # continue if cell not in canvas data
            if not cell in self.canvas_data:
                continue

            self.canvas_data[cell].terrain_neighbors = []
            self.canvas_data[cell].water_on_top = False
            for name, side in NEIGHBOR_DIRECTIONS.items():
                neighbor_cell = (cell[0] + side[0], cell[1] + side[1])

                # continue if neighbor not in canvas data
                if not neighbor_cell in self.canvas_data:
                    continue

                # terrain neighbors
                if self.canvas_data[neighbor_cell].has_terrain:
                    self.canvas_data[cell].terrain_neighbors.append(name)
                # water neighbors
                if (
                    self.canvas_data[neighbor_cell].has_water
                    and self.canvas_data[cell].has_water
                    and name == "A"
                ):
                    self.canvas_data[cell].water_on_top = True

    def animations_update(self, dt):
        for value in self.animations.values():
            value["frame_index"] += ANIMATION_SPEED * dt
            if value["frame_index"] >= value["lenght"]:
                value["frame_index"] = 0

    def mouse_on_object(self):
        for sprite in self.canvas_objects:
            if sprite.rect.collidepoint(mouse_position()):
                return sprite

    def create_grid(self):
        for tile in self.canvas_data.values():
            tile.objects = []

        for obj in self.canvas_objects:
            current_cell = self.get_current_cell(obj)
            offset = vector(
                vector(obj.distance_to_origin) - (vector(current_cell) * TILE_SIZE)
            )

            if current_cell in self.canvas_data:
                self.canvas_data[current_cell].add_id(obj.tile_id, offset)
            else:
                self.canvas_data[current_cell] = CanvasTile(obj.tile_id, offset)

            # grid offset
            left = sorted(self.canvas_data.keys(), key=lambda tile: tile[0])[0][0]
            top = sorted(self.canvas_data.keys(), key=lambda tile: tile[1])[0][1]
        # create an empty grid
        layers = {
            "water": {},
            "bg_palms": {},
            "terrain": {},
            "enemies": {},
            "coins": {},
            "fg_objects": {},
        }

        # fil the grid
        for tile_pos, tile in self.canvas_data.items():
            col_adjusted = tile_pos[0] - left
            row_adjusted = tile_pos[1] - top
            x = col_adjusted * TILE_SIZE
            y = row_adjusted * TILE_SIZE
            if tile.has_water:
                layers["water"][(x, y)] = tile.get_water()
            if tile.has_terrain:
                layers["terrain"][(x, y)] = (
                    tile.get_terrain() if tile.get_terrain() in self.land_tiles else "X"
                )
            if tile.coin:
                layers["coins"][(x + TILE_SIZE // 2, y + TILE_SIZE // 2)] = tile.coin
            if tile.enemy:
                layers["enemies"][(x, y)] = tile.enemy
            if tile.objects:
                for obj, offset in tile.objects:
                    if obj in [
                        key
                        for key, value in EDITOR_DATA.items()
                        if value.style == "palm bg"
                    ]:
                        layers["bg_palms"][(int(x + offset.x), int(y + offset.y))] = obj
                    else:
                        layers["fg_objects"][(int(x + offset.x), int(y + offset.y))] = obj

        return layers 

    # INPUT
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.create_grid()

            self.pan_input(event)

            self.selection_hotkeys(event)

            self.menu_click(event)

            self.object_drag(event)

            self.canvas_add(event)

            self.create_clouds(event)

    def pan_input(self, event):
        # middle mouse button pressed / released
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[1]:
            self.pan_active = True
            self.pan_offset = vector(mouse_position()) - self.origin
        if not mouse_buttons()[1]:
            self.pan_active = False

        # mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            if key_pressed()[pygame.K_LCTRL]:
                self.origin.x -= event.y * 50
            else:
                self.origin.y -= event.y * 50

        # panning update
        if self.pan_active:
            self.origin = vector(mouse_position()) - self.pan_offset

    def selection_hotkeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.selection_index += 1
            if event.key == pygame.K_LEFT:
                self.selection_index -= 1
        self.selection_index = max(2, min(self.selection_index, 18))

    def menu_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.menu.buttons.sprites():
                if button.rect.collidepoint(mouse_position()):
                    self.selection_index = self.menu.click(
                        mouse_position(), mouse_buttons()
                    )

    def object_drag(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            for sprite in self.canvas_objects.sprites():
                if sprite.rect.collidepoint(event.pos):
                    sprite.start_drag()
                    self.object_drag_active = True
        if event.type == pygame.MOUSEBUTTONUP and self.object_drag_active:
            for sprite in self.canvas_objects.sprites():
                if sprite.selected:
                    sprite.end_drag(self.origin)
                    self.object_drag_active = False

    # DRAWING OBJECTS
    def canvas_add(self, event):
        if (
            mouse_buttons()[0]
            and not self.menu.rect.collidepoint(mouse_position())
            and not self.object_drag_active
        ):
            current_cell = self.get_current_cell()
            if EDITOR_DATA[self.selection_index]["type"] == "tile":
                if current_cell != self.last_selected_cell:
                    if current_cell in self.canvas_data:
                        self.canvas_data[current_cell].add_id(self.selection_index)
                    else:
                        self.canvas_data[current_cell] = CanvasTile(
                            self.selection_index
                        )
            else:
                if not self.object_timer.active:
                    groups = [self.canvas_objects, self.background] if EDITOR_DATA[self.selection_index]['style'] == 'palm_bg' else [self.canvas_objects, self.foreground]
                    CanvasObject(
                        pos=mouse_position(),
                        frames=self.animations[self.selection_index]["frames"],
                        tile_id=self.selection_index,
                        origin=self.origin,
                        group=groups,
                    )
                    self.object_timer.activate()
            self.check_neighbors(current_cell)
            self.last_selected_cell = current_cell

    def draw_level(self):
        self.background.draw(self.display_surface)
        for cell_pos, tile in self.canvas_data.items():
            pos = self.origin + vector(cell_pos) * TILE_SIZE
            # adding terrain
            if tile.has_terrain:
                terrain_string = "".join(tile.terrain_neighbors)
                terrain_style = (
                    terrain_string if terrain_string in self.land_tiles else "X"
                )
                self.display_surface.blit(self.land_tiles[terrain_style], pos)
            # adding water
            if tile.has_water:
                if tile.water_on_top:
                    self.display_surface.blit(self.water_bottom, pos)
                else:
                    frames = self.animations[3]["frames"]
                    index = int(self.animations[3]["frame_index"])
                    surf = frames[index]
                    self.display_surface.blit(surf, pos)
            # adding coins
            if tile.coin:
                frames = self.animations[tile.coin]["frames"]
                index = int(self.animations[tile.coin]["frame_index"])
                surf = frames[index]
                rect = surf.get_rect(
                    center=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2)
                )
                self.display_surface.blit(surf, rect)
            # adding enemys
            if tile.enemy:
                frames = self.animations[tile.enemy]["frames"]
                index = int(self.animations[tile.enemy]["frame_index"])
                surf = frames[index]
                rect = surf.get_rect(
                    midbottom=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE)
                )
                self.display_surface.blit(surf, rect)
            # adding palms
            # if tile.has_terrain:
            #     test_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            #     test_surf.fill('brown')
            #     self.display_surface.blit(test_surf, pos)
        self.foreground.draw(self.display_surface)

    def canvas_remove(self):
        if (
            mouse_buttons()[2]
            and not self.menu.rect.collidepoint(mouse_position())
            and self.canvas_data
        ):
            # delete tile
            selected_object = self.mouse_on_object()
            if selected_object and EDITOR_DATA[selected_object.tile_id][
                "style"
            ] not in ("player", "sky"):
                selected_object.kill()
            # delete object
            current_cell = self.get_current_cell()

            if current_cell in self.canvas_data:
                self.canvas_data[current_cell].remove_id(self.selection_index)

                if self.canvas_data[current_cell].is_empty:
                    del self.canvas_data[current_cell]

            self.check_neighbors(current_cell)

    def preview(self):
        if self.menu.rect.collidepoint(mouse_position()):
            return

        selected_object = self.mouse_on_object()

        if selected_object:
            rect = selected_object.rect.inflate(10, 10)
            color = "black"
            width = 3
            size = 15

            topleft = (
                (rect.left, rect.top + size),
                rect.topleft,
                (rect.left + size, rect.top),
            )
            topright = (
                (rect.right, rect.top + size),
                rect.topright,
                (rect.right - size, rect.top),
            )
            bottomleft = (
                (rect.left, rect.bottom - size),
                rect.bottomleft,
                (rect.left + size, rect.bottom),
            )
            bottomright = (
                (rect.right, rect.bottom - size),
                rect.bottomright,
                (rect.right - size, rect.bottom),
            )
            pygame.draw.lines(
                self.display_surface,
                color,
                False,
                topright,
                width,
            )
            pygame.draw.lines(
                self.display_surface,
                color,
                False,
                bottomleft,
                width,
            )
            pygame.draw.lines(
                self.display_surface,
                color,
                False,
                bottomright,
                width,
            )
            pygame.draw.lines(
                self.display_surface,
                color,
                False,
                topleft,
                width,
            )
            # draw lines around objects when selected

        else:
            type_dict = {key: value["type"] for key, value in EDITOR_DATA.items()}
            surf = self.preview_surfs[self.selection_index].copy()
            surf.set_alpha(200)
            # preview of the
            if type_dict[self.selection_index] == "tile":
                # tile
                current_cell = self.get_current_cell()
                rect = surf.get_rect(
                    topleft=self.origin + vector(current_cell) * TILE_SIZE
                )
            else:
                # object
                rect = surf.get_rect(center=mouse_position())
            self.display_surface.blit(surf, rect)

    def display_sky(self, dt):
        self.display_surface.fill(SKY_COLOR)
        y = self.sky_handle.rect.centery
        # horizon lines
        if y > 0:
            horizon_rect1 = pygame.Rect(0, y - 10, WINDOW_WIDTH, 10)
            horizon_rect2 = pygame.Rect(0, y - 16, WINDOW_WIDTH, 4)
            horizon_rect3 = pygame.Rect(0, y - 20, WINDOW_WIDTH, 2)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
            pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)

        self.display_clouds(dt, y)

        # sea
        if 0 < y < WINDOW_HEIGHT:
            sea_rect = pygame.Rect(0, y, WINDOW_WIDTH, WINDOW_HEIGHT)
            pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)
            pygame.draw.line(
                self.display_surface, HORIZON_COLOR, (0, y), (WINDOW_WIDTH, y), 3
            )
        if y < 0:
            self.display_surface.fill(SEA_COLOR)

    def display_clouds(self, dt, y):
        if not y > 0:
            return

        for cloud in self.current_clouds:
            cloud["pos"][0] -= cloud["speed"] * dt
            x = cloud["pos"][0]
            y = y - cloud["pos"][1]
            self.display_surface.blit(cloud["surf"], (x, y))

    def create_clouds(self, event):
        if event.type == self.cloud_timer:
            surf = choice(self.cloud_surf)
            surf = pygame.transform.scale2x(surf) if choice([False, True]) else surf
            pos = [WINDOW_WIDTH + randint(50, 100), randint(0, WINDOW_HEIGHT)]
            speed = randint(20, 50)
            self.current_clouds.append({"surf": surf, "pos": pos, "speed": speed})

            self.current_clouds = [
                cloud for cloud in self.current_clouds if cloud["pos"][0] > -400
            ]

    def startup_clouds(self):
        for i in range(20):
            surf = (
                pygame.transform.scale2x(choice(self.cloud_surf))
                if choice([True, False])
                else choice(self.cloud_surf)
            )
            pos = [randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT)]
            speed = randint(20, 50)
            self.current_clouds.append({"surf": surf, "pos": pos, "speed": speed})

    # DRAWING GUIDE LINES
    def draw_tile_lines(self):
        cols = WINDOW_WIDTH // TILE_SIZE
        rows = WINDOW_HEIGHT // TILE_SIZE

        origin_offset = vector(
            x=self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
            y=self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE,
        )

        self.suport_line_surf.fill("green")

        for col in range(cols + 1):
            x = origin_offset.x + col * TILE_SIZE
            pygame.draw.line(
                self.suport_line_surf, LINE_COLOR, (x, 0), (x, WINDOW_HEIGHT)
            )

        for row in range(rows + 1):
            y = origin_offset.y + row * TILE_SIZE
            pygame.draw.line(
                self.suport_line_surf, LINE_COLOR, (0, y), (WINDOW_WIDTH, y)
            )

        self.display_surface.blit(self.suport_line_surf, (0, 0))

    # RUNNING THE EDITOR
    def run(self, dt):
        self.event_loop()

        # drawing
        self.display_surface.fill("gray")
        self.display_sky(dt)
        self.draw_tile_lines()
        pygame.draw.circle(self.display_surface, "red", self.origin, 10)
        self.draw_level()
        self.canvas_remove()
        self.preview()

        # updating
        self.animations_update(dt)
        self.object_timer.update()

        # menu
        self.menu.display(self.selection_index)

        # objects update
        self.canvas_objects.update(dt, self.origin)


class CanvasTile:
    def __init__(self, tile_id, offset=vector()) -> None:
        # terrain
        self.has_terrain = False
        self.terrain_neighbors = []

        # water
        self.has_water = False
        self.water_on_top = False

        # coin
        self.coin = None

        # enemy
        self.enemy = None

        # objects
        self.objects = []

        self.add_id(tile_id, offset)

        self.is_empty = False

    def add_id(self, tile_id, offset=vector()):
        options = {key: value["style"] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case "terrain":
                self.has_terrain = True
            case "water":
                self.has_water = True
            case "coin":
                self.coin = tile_id
            case "enemy":
                self.enemy = tile_id
            case _:
                if (tile_id, offset) not in self.objects:
                    self.objects.append((tile_id, offset))

    def remove_id(self, tile_id):
        options = {key: value["style"] for key, value in EDITOR_DATA.items()}
        match options[tile_id]:
            case "terrain":
                self.has_terrain = False
            case "water":
                self.has_water = False
            case "coin":
                self.coin = None
            case "enemy":
                self.enemy = None
        self.check_content()

    def check_content(self):
        if (
            not self.has_terrain
            and not self.has_water
            and not self.coin
            and not self.enemy
        ):
            self.is_empty = True

    def get_water(self):
        return "bottom" if not self.water_on_top else "top"

    def get_terrain(self):
        return "".join(self.terrain_neighbors)


class CanvasObject(pygame.sprite.Sprite):
    def __init__(self, pos, frames, tile_id, origin, group):
        super().__init__(group)

        # setup
        self.tile_id = tile_id
        # animations
        self.frames = frames
        self.frames_index = 0

        self.image = self.frames[self.frames_index]
        self.rect = self.image.get_rect(center=pos)

        # movement
        self.distance_to_origin = vector(self.rect.topleft) - origin
        self.selected = False
        self.mouse_offset = vector()

    def start_drag(self):
        self.selected = True
        self.mouse_offset = vector(mouse_position()) - vector(self.rect.topleft)

    def end_drag(self, origin):
        self.selected = False
        self.distance_to_origin = vector(self.rect.topleft) - origin

    def drag(self):
        if self.selected:
            self.rect.topleft = mouse_position() - self.mouse_offset

    def animate(self, dt):
        self.frames_index += ANIMATION_SPEED * dt
        if self.frames_index >= len(self.frames):
            self.frames_index = 0
        self.image = self.frames[int(self.frames_index)]
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def pan_pos(self, origin):
        self.rect.topleft = origin + self.distance_to_origin

    def update(self, dt, origin):
        self.animate(dt)
        self.pan_pos(origin)
        self.drag()
