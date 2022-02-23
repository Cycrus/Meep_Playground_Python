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

SHADOW_HEIGHT = 6


class VectorEye():
    def __init__(self, pos, direction, fow, radius, grid_size):
        self.pos = pos
        self.fow = vec.deg_to_rad(fow)
        self.radius = radius
        self.grid_size = grid_size
        self.direction = direction
        self.calculate_position(pos, direction)
        self.vision_list = []
        
    def see(self, parent_pos, direction, world, debug):
        self.calculate_position(parent_pos, direction)
        self.get_vision_list(world, debug)
        
    def render_gaze(self, screen):
        first_ray = vec.calc_vector_from_angle(self.lower_bound) * self.radius
        last_ray = vec.calc_vector_from_angle(self.upper_bound) * self.radius
        pygame.draw.line(screen, (255, 0, 0), self.pos, (self.pos + first_ray))
        pygame.draw.line(screen, (255, 0, 0), self.pos, (self.pos + last_ray))
        for entity in self.vision_list:
            pygame.draw.line(screen, (0, 255, 0), self.pos, entity.pos)
            
    def calculate_position(self, parent_pos, direction):
        self.pos = parent_pos
        self.direction = direction
        self.dir_angle = vec.get_vector_rotation(self.direction)
        self.lower_bound = self.dir_angle - self.fow/2
        self.upper_bound = self.dir_angle + self.fow/2
        
    def step_wall(self, ray, max_distance, worldmap, pixel_coord, delta_x, delta_y, mode, x_dir, y_dir, debug, do_debug):
        is_wall = False
        map_value = 0
        
        while True:
            map_coord = pixel_coord / self.grid_size
            map_coord = map_coord.astype(int)
            
            if do_debug:
                debug_coord = map_coord * self.grid_size + (self.grid_size / 2)
                debug_coord = debug_coord.astype(int)
                debug_coord = pixel_coord
                box_size = 4
                pygame.draw.rect(debug, (0, 0, 255), [debug_coord[0] - box_size/2, debug_coord[1] - box_size/2,
                                                      box_size, box_size])
            
            try:
                map_value = worldmap[map_coord[0],map_coord[1]]
            except IndexError:
                is_wall = False
                break
            
            distance = np.linalg.norm(self.pos - pixel_coord)
            
            if distance > max_distance:
                is_wall = False
                break
                        
            if map_value != 0:
                is_wall = True
                break

            if mode == MODE_HORIZONTAL:
                pixel_coord[0] = pixel_coord[0] + delta_x * y_dir
            else:
                pixel_coord[0] = pixel_coord[0] + delta_x
            if mode == MODE_VERTICAL:
                pixel_coord[1] = pixel_coord[1] + delta_y * x_dir
            else:
                pixel_coord[1] = pixel_coord[1] + delta_y
                
        return is_wall
    
    def find_wall(self, ray_vector, ray_angle, ray_length, world, debug):
        # https://permadi.com/1996/05/ray-casting-tutorial-7/    
        pixel_coord_horizontal = np.zeros(2)
        pixel_coord_vertical = np.zeros(2)
        
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
        delta_x = self.grid_size / math.tan(ray_angle)
        if y_dir == UP:
            # direction -> up
            delta_y = -self.grid_size
            pixel_coord_horizontal[1] = int(self.pos[1]/self.grid_size) * self.grid_size - 1
        else:
            # direction -> down
            delta_y = self.grid_size
            pixel_coord_horizontal[1] = int(self.pos[1]/self.grid_size) * self.grid_size + self.grid_size
            
        pixel_coord_horizontal[0] = self.pos[0] + (self.pos[1] - pixel_coord_horizontal[1]) / math.tan(ray_angle)
        if x_dir == LEFT:
            pixel_coord_horizontal[0] = pixel_coord_horizontal[0] + 1
        
        is_wall = self.step_wall(ray_angle, ray_length, world.world_map, pixel_coord_horizontal,
                                 delta_x, delta_y, MODE_HORIZONTAL, x_dir, y_dir, debug, False)
        
        if not is_wall:
            ## Find vertical grid lines
            # Find first vertical point
            delta_y = self.grid_size * math.tan(ray_angle)
            if x_dir == LEFT:
                # direction -> left
                delta_x = -self.grid_size
                pixel_coord_vertical[0] = int(self.pos[0] / self.grid_size) * self.grid_size - 1
            else:
                # direction -> right
                delta_x = self.grid_size
                pixel_coord_vertical[0] = int(self.pos[0] / self.grid_size) * self.grid_size + self.grid_size
                
            pixel_coord_vertical[1] = self.pos[1] + (self.pos[0] - pixel_coord_vertical[0]) * math.tan(ray_angle)
            if y_dir == UP:
                pixel_coord_vertical[1] = pixel_coord_vertical[1] + 1
                
            is_wall = self.step_wall(ray_angle, ray_length, world.world_map, pixel_coord_vertical,
                                      delta_x, delta_y, MODE_VERTICAL, x_dir, y_dir, debug, False)
        
        return is_wall
        
    def get_vision_list(self, world, debug):
        def check_distance_angle(self, angle):
            can_see = False
            if vec.check_between_angle(angle, self.lower_bound, self.upper_bound):
                can_see = True
            else:
                angle = angle + vec.RAD_360
                if vec.check_between_angle(angle, self.lower_bound, self.upper_bound):
                    can_see = True
                else:
                    angle = angle - vec.RAD_720
                    if vec.check_between_angle(angle, self.lower_bound, self.upper_bound):
                        can_see = True
            return (can_see, angle)
        
        self.vision_list = []
        
        for idx, entity in enumerate(world.render_list):
            if self.pos[0] != entity.pos[0] and self.pos[1] != entity.pos[1]:
                distance_vector = entity.pos - self.pos
                angle = vec.get_vector_rotation(distance_vector)
                entity_distance = np.linalg.norm(distance_vector)
                if entity_distance < self.radius:
                    can_see, angle = check_distance_angle(self, angle)
                    if can_see:
                        if not self.find_wall(distance_vector, angle, entity_distance, world, debug):
                            self.vision_list.append(entity)
                    
        
class RayCastingEye():
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
        
    def render_gaze(self, screen):
        first_ray = vec.calc_vector_from_angle(self.vision_rays[0]) * self.depth
        last_ray = vec.calc_vector_from_angle(self.vision_rays[self.ray_n - 1]) * self.depth
        pygame.draw.line(screen, (0, 80, 255), self.pos, (self.pos + first_ray))
        pygame.draw.line(screen, (0, 80, 255), self.pos, (self.pos + last_ray))
        
    def calculate_position(self, parent_pos, direction):
        self.pos = parent_pos
        self.direction = direction
        self.dir_angle = vec.get_vector_rotation(self.direction)
        
    def project_sprites(self, entity_list, sun_intensity):
        def choose_sprite(self, entity, angle):
            entity_direction_angle = vec.get_vector_rotation(entity.direction)
            rel_entity_angle = entity_direction_angle - angle
            sprite_y = vec.get_rotated_sprite_offset(rel_entity_angle, entity.proj_sprite_dims[1])
            entity.proj_sprite.blit(entity.base_proj_sprite, (0, 0),
                                    (0, sprite_y, entity.proj_sprite_dims[0], entity.proj_sprite_dims[1]))
            
            sprite_height = (entity.height / sprite_distance) * self.projection_offset
            sprite_width = (entity.width / sprite_distance) * self.projection_offset
            
            return sprite_width, sprite_height
        
        def check_distance_angle(self, angle):
            can_see = False
            lower_bound = self.vision_rays[self.ray_n-1] - vec.RAD_45
            upper_bound = self.vision_rays[0] + vec.RAD_45
            
            if vec.check_between_angle(angle, lower_bound, upper_bound):
                can_see = True
            else:
                angle = angle + vec.RAD_360
                if vec.check_between_angle(angle, lower_bound, upper_bound):
                    can_see = True
                else:
                    angle = angle - vec.RAD_720
                    if vec.check_between_angle(angle, lower_bound, upper_bound):
                        can_see = True
            return (can_see, angle)
        
        def sort_sprites_by_distance(self):
            seen_sprites = []
            
            for entity in entity_list:
                if self.pos[0] != entity.pos[0] and self.pos[1] != entity.pos[1]:
                    distance_vector = entity.pos - self.pos
                    angle = vec.get_vector_rotation(distance_vector)
                    lens_correction = math.cos(self.dir_angle - angle)
                    sprite_distance = np.linalg.norm(distance_vector) * lens_correction
                    
                    if sprite_distance <= self.depth:
                        # Check of angle is not well structured
                        can_see, angle = check_distance_angle(self, angle)
                        if can_see:
                            seen_sprites.append([entity, angle, lens_correction, sprite_distance])
                        
            seen_sprites.sort(key=lambda x:x[3], reverse=True)
            return seen_sprites
            
        seen_sprites = sort_sprites_by_distance(self)
                        
        for entity_props in seen_sprites:
            entity = entity_props[0]
            angle = entity_props[1]
            lens_correction = entity_props[2]
            sprite_distance = entity_props[3]
            sprite_width, sprite_height = choose_sprite(self, entity, angle)
            
            self.grid_size / self.distance_map * self.projection_offset
            
            y_offset_by_size = ((self.grid_size - 2*entity.height - entity.z_pos) / sprite_distance * self.projection_offset) / 2
            x_offset_by_angle = ((angle - self.vision_rays[self.ray_n-1])/self.fow) * (self.ray_n-1)
            proj_pos_y = int(self.height/2 + y_offset_by_size)
            proj_pos_x = int((self.ray_n-1) - x_offset_by_angle - sprite_height/2)
            
            temp_proj_sprite = pygame.transform.scale(entity.proj_sprite, (sprite_width,
                                                        sprite_height))
            pixels_array = pygame.surfarray.pixels3d(temp_proj_sprite)
            alpha_array = pygame.surfarray.pixels_alpha(temp_proj_sprite)
            
            fog = (sprite_distance-1) / self.depth
            
            left_offset = int(proj_pos_x)
            if left_offset > 0:
                left_offset = 0
            else:
                left_offset = abs(left_offset)
                
            right_offset = int(proj_pos_x + sprite_width - self.ray_n)
            if right_offset < 0:
                right_offset = 0
                
            top_offset = int(proj_pos_y)
            if top_offset > 0:
                top_offset = 0
            else:
                top_offset = abs(top_offset)
                
            bottom_offset = int(proj_pos_y + sprite_height - self.height)
            if bottom_offset < 0:
                bottom_offset = 0
            inv_bottom_offset = pixels_array.shape[1] - bottom_offset
            
            lower_half = int(proj_pos_y + top_offset)
            upper_half = int(proj_pos_y + pixels_array.shape[1] - bottom_offset)
            
            
            shadow_height = (SHADOW_HEIGHT / sprite_distance) * self.projection_offset
            temp_shadow = pygame.transform.scale(entity.proj_shadow, (sprite_width, shadow_height))
            shadow_pixels = pygame.surfarray.pixels3d(temp_shadow)
            shadow_alpha = pygame.surfarray.pixels_alpha(temp_shadow)
            shadow_height = shadow_pixels.shape[1]
            
            shadow_y_offset = ((self.grid_size - 2*entity.height - 5) / sprite_distance * self.projection_offset) / 2
            shadow_pos_y = int(self.height / 2 + shadow_y_offset + sprite_height)
            
            top_shadow_offset = int(shadow_pos_y)
            if top_shadow_offset > 0:
                top_shadow_offset = 0
            else:
                top_shadow_offset = abs(top_shadow_offset)
            
            bottom_shadow_offset = int(shadow_pos_y + shadow_height - self.height)
            if bottom_shadow_offset < 0:
                bottom_shadow_offset = 0
            inv_bottom_shadow_offset = shadow_pixels.shape[1] - bottom_shadow_offset
            
            lower_shadow = shadow_pos_y
            upper_shadow = shadow_pos_y + shadow_height
            
            sprite_x = 0 + left_offset
            for img_x in range(int(proj_pos_x-1 + left_offset), int(proj_pos_x+sprite_width-1 - right_offset)):
                if self.distance_map[img_x] > sprite_distance:
                    try:
                        self.distance_map[img_x] = sprite_distance
                        
                        if shadow_pos_y < self.height:
                            shadow_alpha_slice = shadow_alpha[sprite_x, top_shadow_offset:inv_bottom_shadow_offset] / MAX_COLOR
                            shadow_pixel_slice = shadow_pixels[sprite_x, top_shadow_offset:inv_bottom_shadow_offset]
                            
                            self.perceived_image[lower_shadow:upper_shadow, img_x, 0] = shadow_alpha_slice * shadow_pixel_slice[:,2] + (1-shadow_alpha_slice) * self.perceived_image[lower_shadow:upper_shadow, img_x, 0]
                            self.perceived_image[lower_shadow:upper_shadow, img_x, 1] = shadow_alpha_slice * shadow_pixel_slice[:,1] + (1-shadow_alpha_slice) * self.perceived_image[lower_shadow:upper_shadow, img_x, 1]
                            self.perceived_image[lower_shadow:upper_shadow, img_x, 2] = shadow_alpha_slice * shadow_pixel_slice[:,0] + (1-shadow_alpha_slice) * self.perceived_image[lower_shadow:upper_shadow, img_x, 2]
                        
                        alpha_slice = alpha_array[sprite_x, top_offset:inv_bottom_offset] / MAX_COLOR
                        sprite_slice = pixels_array[sprite_x, top_offset:inv_bottom_offset]
                        sprite_slice[:,:] = (sprite_slice[:,:] - (sprite_slice[:,:] - COLOR_EMPTY[:]) * fog) * sun_intensity
                        sprite_slice = sprite_slice / MAX_COLOR
                        
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
                
            #if ray_idx % 5 == 0 or ray_idx == 0 or ray_idx == self.ray_n-1:
            #    pygame.draw.line(debug, (255, 0, 255), self.pos, self.pos + ray_vector * self.distance_map[ray_idx] / lens_correction)
            