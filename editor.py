import pygame, sys
from pygame.math import Vector2 as vector
from setting import *
from pygame.mouse import get_pressed as mouse_buttons
from pygame.mouse import get_pos as mouse_position
from pygame.key import get_pressed as key_pressed

from menu import Menu


class Editor:
    def __init__(self) -> None:
        
        # main setup
        self.display_surface = pygame.display.get_surface()

        #navigation
        self.origin = vector()
        self.pan_active = False
        self.pan_offset = vector()

        # support lines
        self.suport_line_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.suport_line_surf.set_colorkey('green')
        self.suport_line_surf.set_alpha(30)

        # selection
        self.selection_index = 2

        #menu
        self.menu = Menu()

    
    #INPUT
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            self.pan_input(event)
            self.selection_hotkeys(event)

    def pan_input(self, event):
        #middle mouse button pressed / released
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

        #panning update
        if self.pan_active:
            self.origin = vector(mouse_position()) - self.pan_offset

    def selection_hotkeys(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.selection_index += 1
            if event.key == pygame.K_LEFT:
                self.selection_index -= 1
        self.selection_index = max(2,min(self.selection_index, 18))

    # DRAWING GUIDE LINES
    def draw_tile_lines(self):
        cols = WINDOW_WIDTH // TILE_SIZE
        rows = WINDOW_HEIGHT // TILE_SIZE

        origin_offset = vector(
            x = self.origin.x - int(self.origin.x / TILE_SIZE) * TILE_SIZE,
            y = self.origin.y - int(self.origin.y / TILE_SIZE) * TILE_SIZE )
        
        self.suport_line_surf.fill('green')

        for col in range(cols + 1):
            x = origin_offset.x + col * TILE_SIZE
            pygame.draw.line(self.suport_line_surf, LINE_COLOR, (x,0), (x,WINDOW_HEIGHT))
       
        for row in range(rows + 1):
            y = origin_offset.y + row * TILE_SIZE
            pygame.draw.line(self.suport_line_surf, LINE_COLOR, (0,y), (WINDOW_WIDTH,y))
    
        self.display_surface.blit(self.suport_line_surf, (0,0))

    def run (self, dt):
        self.display_surface.fill('white')
        self.event_loop()

        #drawing
        self.draw_tile_lines()
        pygame.draw.circle(self.display_surface, 'red', self.origin, 10)

        #menu
        self.menu.display()
