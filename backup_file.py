#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 16:01:12 2022

@author: cycrus
"""

import vector_tools as vec
from constants import COLOR_EMPTY, MAX_COLOR, COLOR_GROUND
from constants import MAP_GREY_WALL, MAPC_GREY_WALL
from constants import MAP_GREEN_WALL, MAPC_GREEN_WALL
import numpy as np
import math
import pygame

MODE_HORIZONTAL = 0
MODE_VERTICAL = 1

LEFT = 1
RIGHT = -1
UP = 1
DOWN = -1

class Eye():
    def __init__(self, pos, direction, fow, depth, ray_n, grid_size):
        self.pos = pos
        self.fow = vec.deg_to_rad(fow)
        self.depth = depth
        self.ray_n = ray_n
        self.grid_size = grid_size
        self.projection_offset = (self.ray_n/2) / math.tan(self.fow/2)
        self.max_step = self.depth // self.grid_size - 1
        self.height = int(self.ray_n / 2)
        self.origin_distance = 1
        self.direction = direction
        self.dir_angle = vec.get_vector_rotation(self.direction)
        self.vision_rays = np.zeros(self.ray_n)
        self.color_map = np.zeros([ray_n, 3])
        self.distance_map = np.zeros(ray_n)
        self.sunlight_map = np.zeros(ray_n)
        self.fog_map = np.zeros(ray_n)
        self.perceived_dims = [self.height, self.ray_n]
        self.perceived_image = np.zeros(self.perceived_dims + [3])
        self.proj_height = np.zeros(ray_n)
        self.proj_color = np.zeros(ray_n)
        
    def see(self, parent_pos, direction, world, debug):
        self.calculate_position(parent_pos, direction)
        self.calculate_vision_rays()
        self.calculate_vision_maps(world, debug)
        self.project_walls(world.sun_intensity, world.sun_color)
        self.project_sprites(world.render_list, world.sun_intensity)
        
    def calculate_position(self, parent_pos, direction):
        self.pos = parent_pos
        self.direction = direction
        self.dir_angle = vec.get_vector_rotation(self.direction)
        
    def project_sprites(self, entity_list, sun_intensity):
        for entity in entity_list:
            if self.pos[0] != entity.pos[0] and self.pos[1] != entity.pos[1]:
                distance_vector = entity.pos - self.pos
                angle = vec.get_vector_rotation(distance_vector)
                lens_correction = math.cos(self.dir_angle - angle)
                sprite_distance = np.linalg.norm(distance_vector) * lens_correction
                
                if sprite_distance <= self.depth:
                    if angle < self.vision_rays[0]+1 and angle > self.vision_rays[self.ray_n-1]-1:
                        entity_direction_angle = vec.get_vector_rotation(entity.direction)
                        rel_entity_angle = entity_direction_angle - angle
                        sprite_y = vec.get_rotated_sprite_offset(rel_entity_angle, entity.proj_sprite_dims[1])
                        entity.proj_sprite.blit(entity.base_proj_sprite, (0, 0),
                                                (0, sprite_y, entity.proj_sprite_dims[0], entity.proj_sprite_dims[1]))
                        
                        sprite_size = (entity.height / sprite_distance) * self.projection_offset
                        self.grid_size / self.distance_map * self.projection_offset
                        
                        y_offset_by_size = ((self.grid_size - 2*entity.height - entity.z_pos) / sprite_distance * self.projection_offset) / 2
                        x_offset_by_angle = ((angle - self.vision_rays[self.ray_n-1])/self.fow) * (self.ray_n-1)
                        proj_pos_y = int(self.height/2 + y_offset_by_size)
                        proj_pos_x = int((self.ray_n-1) - x_offset_by_angle - sprite_size/2)
                        
                        temp_proj_sprite = pygame.transform.scale(entity.proj_sprite, (sprite_size,
                                                                    sprite_size))
                        pixels_array = pygame.surfarray.pixels3d(temp_proj_sprite)
                        alpha_array = pygame.surfarray.pixels_alpha(temp_proj_sprite)
                        temp_shadow = pygame.transform.scale(entity.proj_shadow, (6, sprite_size))
                        shadow_pixels = pygame.surfarray.pixels3d(temp_shadow)
                        shadow_alpha = pygame.surfarray.pixels_alpha(temp_shadow)
                        shadow_height = temp_shadow.get_height()
                        
                        fog = (sprite_distance-1) / self.depth
                        
                        left_offset = int(proj_pos_x)
                        if left_offset > 0:
                            left_offset = 0
                        else:
                            left_offset = abs(left_offset)
                            
                        right_offset = int(proj_pos_x + sprite_size - self.ray_n)
                        if right_offset < 0:
                            right_offset = 0
                            
                        top_offset = int(proj_pos_y)
                        if top_offset > 0:
                            top_offset = 0
                        else:
                            top_offset = abs(top_offset)
                            
                        bottom_offset = int(proj_pos_y + sprite_size - self.height)
                        if bottom_offset < 0:
                            bottom_offset = 0
                        inv_bottom_offset = pixels_array.shape[1] - bottom_offset
                            
                        lower_half = int(proj_pos_y + top_offset)
                        upper_half = int(proj_pos_y + pixels_array.shape[1] - bottom_offset)
                        
                        sprite_x = 0 + left_offset
                        for img_x in range(int(proj_pos_x-1 + left_offset), int(proj_pos_x+sprite_size-1 - right_offset)):
                            if self.distance_map[img_x] > sprite_distance:
                                try:
                                    self.distance_map[img_x] = sprite_distance
                                    
                                    alpha_slice = alpha_array[sprite_x, top_offset:inv_bottom_offset] / MAX_COLOR
                                    sprite_slice = pixels_array[sprite_x, top_offset:inv_bottom_offset]
                                    sprite_slice[:,:] = (sprite_slice[:,:] - (sprite_slice[:,:] - COLOR_EMPTY[:]) * fog) * sun_intensity
                                    sprite_slice = sprite_slice / MAX_COLOR
                                    
                                    shadow_alpha_slice = shadow_alpha[sprite_x, :]
                                    shadow_pixel_slice = shadow_pixels[sprite_x, :]
                                    
                                    #self.perceived_image[0:shadow_height, img_x, 0] = shadow_alpha_slice * shadow_pixel_slice[:,2] + (1-shadow_alpha_slice) * self.perceived_image[0:shadow_height, img_x, 0]
                                    #self.perceived_image[0:shadow_height, img_x, 1] = shadow_alpha_slice * shadow_pixel_slice[:,1] + (1-shadow_alpha_slice) * self.perceived_image[0:shadow_height, img_x, 1]
                                    #self.perceived_image[0:shadow_height, img_x, 2] = shadow_alpha_slice * shadow_pixel_slice[:,0] + (1-shadow_alpha_slice) * self.perceived_image[0:shadow_height, img_x, 2]
                                    
                                    self.perceived_image[lower_half:upper_half, img_x, 0] = alpha_slice * sprite_slice[:,2] + (1-alpha_slice) * self.perceived_image[lower_half:upper_half, img_x, 0]
                                    self.perceived_image[lower_half:upper_half, img_x, 1] = alpha_slice * sprite_slice[:,1] + (1-alpha_slice) * self.perceived_image[lower_half:upper_half, img_x, 1]
                                    self.perceived_image[lower_half:upper_half, img_x, 2] = alpha_slice * sprite_slice[:,0] + (1-alpha_slice) * self.perceived_image[lower_half:upper_half, img_x, 2]
                                except:
                                    pass
                            sprite_x = sprite_x + 1
        
    def blit_ground_sky(self, half_height, half_col, sun_intensity, sun_color):
        self.perceived_image[:half_height,:,0] = np.ones(half_col) * COLOR_EMPTY[0] / MAX_COLOR * sun_intensity * sun_color[0]
        self.perceived_image[:half_height,:,1] = np.ones(half_col) * COLOR_EMPTY[1] / MAX_COLOR * sun_intensity * sun_color[1]
        self.perceived_image[:half_height,:,2] = np.ones(half_col) * COLOR_EMPTY[2] / MAX_COLOR * sun_intensity * sun_color[2]
        
        self.perceived_image[half_height:,:,0] = np.ones(half_col) * COLOR_GROUND[0] / MAX_COLOR * sun_intensity * sun_color[0]
        self.perceived_image[half_height:,:,1] = np.ones(half_col) * COLOR_GROUND[1] / MAX_COLOR * sun_intensity * sun_color[1]
        self.perceived_image[half_height:,:,2] = np.ones(half_col) * COLOR_GROUND[2] / MAX_COLOR * sun_intensity * sun_color[2]
        
    def project_walls(self, sun_intensity, sun_color):
        self.proj_height = self.grid_size / self.distance_map * self.projection_offset
        self.fog_map = (self.distance_map-1) / self.depth
        
        half_img_height = self.height // 2
        half_col = [self.height // 2, self.ray_n]
        extended_color_map = np.expand_dims(self.color_map, 1)
        
        self.perceived_image = np.zeros(self.perceived_dims + [3])
        
        self.blit_ground_sky(half_img_height, half_col, sun_intensity, sun_color)
        
        for x,col in enumerate(extended_color_map):
            col = col[0]
            invisible = vec.is_color(col, COLOR_EMPTY)
                        
            if not invisible:
                col[:] = (col[:] - (col[0] - COLOR_EMPTY[:]) * self.fog_map[x]) * sun_intensity * sun_color[:] * self.sunlight_map[x]
                
                if self.proj_height[x] >= self.height:
                    self.proj_height[x] = self.height - 1
                    
                half_slice_height = int(self.proj_height[x] // 2)
                lower_half = int(half_img_height - half_slice_height) + 1
                upper_half = int(half_img_height + half_slice_height) + 1
                slice_height = half_slice_height * 2
                
                self.perceived_image[lower_half:upper_half,x,0] = np.ones(slice_height) * col[2] / MAX_COLOR
                self.perceived_image[lower_half:upper_half,x,1] = np.ones(slice_height) * col[1] / MAX_COLOR
                self.perceived_image[lower_half:upper_half,x,2] = np.ones(slice_height) * col[0] / MAX_COLOR
        
    def calculate_vision_rays(self):
        ray_angle = self.fow / (self.ray_n - 1)
        
        for n in range(self.ray_n):
            self.vision_rays[n] = (self.dir_angle + self.fow / 2) - ray_angle * n
            
    def find_pixel(self, ray, worldmap, pixel_coord, delta_x, delta_y, lens_correction, mode,x_dir, y_dir, debug, show_debug):
        found_pixel = False
        step = 0
        map_value = 0
        
        while not found_pixel:
            map_coord = pixel_coord / self.grid_size
            map_coord = map_coord.astype(int)
            
            if show_debug:
                debug_coord = map_coord * self.grid_size + (self.grid_size / 2)
                debug_coord = debug_coord.astype(int)
                debug_coord = pixel_coord
                box_size = 4
                pygame.draw.rect(debug, (0, 0, 255), [debug_coord[0] - box_size/2, debug_coord[1] - box_size/2,
                                                      box_size, box_size])
            
            try:
                map_value = worldmap[map_coord[0],map_coord[1]]
            except IndexError:
                map_value = 0
                pixel_color = COLOR_EMPTY
                distance = self.depth
                found_pixel = True
                break
                
            distance = np.linalg.norm(self.pos - pixel_coord)
            
            if distance > self.depth:
                pixel_color = COLOR_EMPTY
                distance = self.depth
                found_pixel = True
                break
                        
            if map_value != 0:
                distance = distance * lens_correction
                if distance > self.depth:
                    pixel_color = COLOR_EMPTY
                    distance = self.depth
                else:
                    if map_value == MAP_GREY_WALL:
                        pixel_color = MAPC_GREY_WALL
                    elif map_value == MAP_GREEN_WALL:
                        pixel_color = MAPC_GREEN_WALL
                found_pixel = True
                break

            if mode == MODE_HORIZONTAL:
                pixel_coord[0] = pixel_coord[0] + delta_x * y_dir
            else:
                pixel_coord[0] = pixel_coord[0] + delta_x
            if mode == MODE_VERTICAL:
                pixel_coord[1] = pixel_coord[1] + delta_y * x_dir
            else:
                pixel_coord[1] = pixel_coord[1] + delta_y
                
            step = step + 1
                
        return pixel_color, distance
    
    def calculate_vision_maps(self, world, debug):
        # https://permadi.com/1996/05/ray-casting-tutorial-7/    
        pixel_coord_horizontal = np.zeros(2)
        pixel_coord_vertical = np.zeros(2)
        
        for ray_idx, ray in enumerate(self.vision_rays):
            ray_vector = vec.calc_vector_from_angle(ray)
            lens_correction = math.cos(self.dir_angle - ray)
            
            if ray_vector[1] > 0:
                y_dir = DOWN
            else:
                y_dir = UP
            if ray_vector[0] > 0:
                x_dir = RIGHT
            else:
                x_dir = LEFT
            
            ## Find horizontal grid lines
            # Find first horizontal point
            delta_x = self.grid_size / math.tan(ray)
            if y_dir == UP:
                # direction -> up
                delta_y = -self.grid_size
                pixel_coord_horizontal[1] = int(self.pos[1]/self.grid_size) * self.grid_size - 1
                light_shader_horizontal = 0.95
            else:
                # direction -> down
                delta_y = self.grid_size
                pixel_coord_horizontal[1] = int(self.pos[1]/self.grid_size) * self.grid_size + self.grid_size
                light_shader_horizontal = 0.90
                
            pixel_coord_horizontal[0] = self.pos[0] + (self.pos[1] - pixel_coord_horizontal[1]) / math.tan(ray)
            if x_dir == LEFT:
                pixel_coord_horizontal[0] = pixel_coord_horizontal[0] + 1
            
            pixel_color_horizontal, distance_horizontal = self.find_pixel(ray, world.world_map, pixel_coord_horizontal, delta_x, delta_y,
                                                                          lens_correction, MODE_HORIZONTAL, x_dir, y_dir, debug, False)
            
            ## Find vertical grid lines
            # Find first vertical point
            delta_y = self.grid_size * math.tan(ray)
            if x_dir == LEFT:
                # direction -> left
                delta_x = -self.grid_size
                pixel_coord_vertical[0] = int(self.pos[0] / self.grid_size) * self.grid_size - 1
                light_shader_vertical = world.west_side_light
            else:
                # direction -> right
                delta_x = self.grid_size
                pixel_coord_vertical[0] = int(self.pos[0] / self.grid_size) * self.grid_size + self.grid_size
                light_shader_vertical = world.east_side_light
                
            pixel_coord_vertical[1] = self.pos[1] + (self.pos[0] - pixel_coord_vertical[0]) * math.tan(ray)
            if y_dir == UP:
                pixel_coord_vertical[1] = pixel_coord_vertical[1] + 1
                
            pixel_color_vertical, distance_vertical = self.find_pixel(ray, world.world_map, pixel_coord_vertical, delta_x, delta_y,
                                                                      lens_correction, MODE_VERTICAL, x_dir, y_dir, debug, False)
            
            #box_size = 4
            
            if distance_vertical < distance_horizontal:
                #pygame.draw.rect(debug, (255,0,0), [pixel_coord_vertical[0] - box_size/2, pixel_coord_vertical[1] - box_size/2,
                #                                      box_size, box_size])
                self.color_map[ray_idx] = pixel_color_vertical[:3]
                self.distance_map[ray_idx] = distance_vertical
                self.sunlight_map[ray_idx] = light_shader_vertical
            else:
                #pygame.draw.rect(debug, (255,0,0), [pixel_coord_horizontal[0] - box_size/2, pixel_coord_horizontal[1] - box_size/2,
                #                                      box_size, box_size])
                self.color_map[ray_idx] = pixel_color_horizontal[:3]
                self.distance_map[ray_idx] = distance_horizontal
                self.sunlight_map[ray_idx] = light_shader_horizontal
                
            #pygame.draw.line(debug, (255, 0, 255), self.pos, self.pos + ray_vector * self.distance_map[ray_idx] / lens_correction)
            