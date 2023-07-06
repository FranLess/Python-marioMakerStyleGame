import pygame, sys
from pygame.math import Vector2 as vector

from setting import *
from support import *

from sprites import Generic, Player, Animated, Coin, Particle

class Level:
    def __init__(self, grid, switch, asset_dict) -> None:
        self.display_surface = pygame.display.get_surface()
        self.switch = switch

        # groups
        self.all_sprites = pygame.sprite.Group()
        self.coin_sprites = pygame.sprite.Group()

        #additional stuff
        self.particle_surf = asset_dict['particle']

        self.build_level(grid, asset_dict)

    def build_level(self, grid, asset_dict):
        for layer_name, layer in grid.items():
            for pos, data in layer.items():
                if layer_name == 'terrain':
                    Generic(pos, asset_dict['land'][data], self.all_sprites)
                
                if layer_name == 'water':
                    if data == 'top':
                        Animated(asset_dict['water_top'], pos, self.all_sprites)
                    else:
                        Generic(pos, asset_dict['water_bottom'], self.all_sprites)

                match data:
                    case 0: self.player = Player(pos, self.all_sprites)
                    # case 1:
                    case 4: Coin('gold', asset_dict['gold'], pos, [self.all_sprites, self.coin_sprites])
                    case 5: Coin('silver', asset_dict['silver'], pos, [self.all_sprites, self.coin_sprites])
                    case 6: Coin('diamond', asset_dict['diamond'], pos, [self.all_sprites, self.coin_sprites])
    
    def get_coins(self):
        collided_coins:pygame.sprite.Group = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
        for sprite in collided_coins:
            pos = sprite.rect.center
            Particle(self.particle_surf, pos, self.all_sprites)

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.switch()

    def run(self, dt):
        self.event_loop()
        self.display_surface.fill('red')
        self.all_sprites.update(dt)
        self.all_sprites.draw(self.display_surface)
        self.get_coins()