import pygame
from setting import *

class Menu:
    def __init__(self) -> None:
        self.display_surf = pygame.display.get_surface()
        self.create_data()
        self.create_buttons()
    
    def create_data(self):
        self.menu_surfaces = {}
        for key,value in EDITOR_DATA.items():
            if value['menu']:
                if not value['menu'] in self.menu_surfaces:
                    self.menu_surfaces[value['menu']]= ()
                

    def create_buttons(self):
        #menu area general
        size = 180
        margin = 6
        left = WINDOW_WIDTH - (size + margin)
        top = WINDOW_HEIGHT - (size + margin) 
        self.rect = pygame.Rect(left,top,size,size)

        #button areas
        generic_button_rect = pygame.Rect(self.rect.topleft, (self.rect.width / 2, self.rect.height / 2))
        button_margin = 10
        self.tile_button_rect = generic_button_rect.copy().inflate(-button_margin, -button_margin)
        self.coin_button_rect = generic_button_rect.move(self.rect.width / 2, 0).inflate(-button_margin, -button_margin)
        self.enemy_button_rect = generic_button_rect.move(self.rect.width/2, self.rect.height / 2).inflate(-button_margin, -button_margin)
        self.palm_button_rect = generic_button_rect.move(0,self.rect.width / 2).inflate(-button_margin, -button_margin)

    def display(self):
        # pygame.draw.rect(self.display_surf, 'red', self.rect)
        pygame.draw.rect(self.display_surf, 'green', self.tile_button_rect)
        pygame.draw.rect(self.display_surf, 'blue', self.coin_button_rect)
        pygame.draw.rect(self.display_surf, 'yellow', self.enemy_button_rect)
        pygame.draw.rect(self.display_surf, 'black', self.palm_button_rect)

class Button(pygame.sprite.Sprite):
    def __init__(self, rect, group, items, items_alt=None):
        super.__init__(group)
        self.image = pygame.Surface(rect.size)
        self.rect = rect

        #items
        self.items = {'main': items, 'alt': items_alt}
        self.index = 0
        self.main_active = True
        
