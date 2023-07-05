import pygame
from pygame.image import load as load_image
from os import walk


def import_folder(path):
    surface_list = []
    for folder_name, sub_folders, files in walk(path):
        for file_name in files:
            full_path = f"{folder_name}/{file_name}"
            image_surf = load_image(full_path).convert_alpha()
            surface_list.append(image_surf)

    return surface_list


def import_folder_dict(path):
    surface_dict = {}
    for folder_name, sub_folders, files in walk(path):
        for file_name in files:
            full_path = f"{folder_name}/{file_name}"
            image_surf = load_image(full_path).convert_alpha()
            surface_dict[file_name.split(".")[0]] = image_surf

    return surface_dict
