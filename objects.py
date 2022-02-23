#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 00:19:11 2022

@author: cycrus
"""

import numpy as np
import pygame
import vector_tools as vec
from helper_functions import make_noise
import copy
import math
import random

TYPE_FOOD = 0
TYPE_WALL = 1
TYPE_ORGANISM = 2
TYPE_ENVIRONMENT = 3

PROP_EDIBLE = 0
PROP_SOLID = 1
PROP_INVISIBLE = 2
PROP_LIVING = 3
PROP_FRUIT = 4
PROP_MEAT = 5
PROP_HOME = 6
PROP_CARRIABLE = 7
PROP_IS_CARRIED = 8

SHADOW_STRENGTH = 100

NOISE_RADIUS = 100


class Entity(object):
    def __init__(self, pos, height, topdown_sprite, texture_sprite, proj_sprite_dims, obj_type, property_list):
        self.pos = pos
        self.prev_pos = self.pos
        self.width = 0
        self.z_pos = 0
        self.base_height = height
        self.height = self.base_height
        self.sides = np.zeros(4)
        self.base_sprite = pygame.image.load(topdown_sprite)
        self.base_proj_sprite = pygame.image.load(texture_sprite)
        self.proj_sprite_dims = proj_sprite_dims
        self.sprite = self.base_sprite
        self.proj_sprite = pygame.Surface(self.proj_sprite_dims,
                                          flags=pygame.SRCALPHA)
        self.proj_sprite.blit(self.base_proj_sprite, (0, 0),
                              (0, 0, self.proj_sprite_dims[0], self.proj_sprite_dims[1]))
        self.proj_shadow = pygame.Surface((self.proj_sprite_dims[1], 10),
                                          flags=pygame.SRCALPHA)
        pygame.draw.ellipse(self.proj_shadow, (0, 0, 0, SHADOW_STRENGTH),
                            (0, 0, self.proj_sprite_dims[1], 6))
        
        self.size = np.array(self.sprite.get_size())
        self.proj_sprite_size = self.base_proj_sprite.get_size()[1]
        self.type = obj_type
        self.properties = property_list
        self.direction = np.array([0, -1])
        self.calc_sides()
        self.calc_proj_sprite_width()
        self.prev_sides = copy.copy(self.sides)
        self.save_prev_state()
        
    def exist(self, world):
        pass
        
    def calc_proj_sprite_width(self):
         self.width = self.proj_sprite_dims[0] / self.proj_sprite_dims[1] * self.height
        
    def calc_sides(self):
        self.sides[0] = self.pos[0] - self.size[0] / 2
        self.sides[1] = self.pos[1] - self.size[1] / 2
        self.sides[2] = self.pos[0] + self.size[0] / 2
        self.sides[3] = self.pos[1] + self.size[1] / 2
        
    def save_prev_state(self):
        self.prev_pos = self.pos
        self.prev_size = self.size
        self.prev_sides = copy.copy(self.sides)
        
    def change_position(self, delta, axis=None):
        if axis is None:
            self.pos = self.pos + delta
        elif axis == 0 or axis == 1:
            self.pos[axis] = self.pos[axis] + delta
        else:
            print("[WARNING] Wrong axis given to Entity.change_position.")
        self.calc_sides()
        
        
class Tree(Entity):
    def __init__(self, pos, makes_fruit=True):
        super().__init__(pos, 40, "img/tree.png", "img/tree_proj.png",
                         (40, 40), TYPE_ENVIRONMENT, [PROP_SOLID])
        self.makes_fruit = makes_fruit
        self.spawn_interval = 0
        self.spawn_timer = 0
        self.food_size = np.array([12, 12])
        spawn_distance = self.size * 0.75
        self.spawn_areas = np.array([[self.pos[0]-spawn_distance[0], self.pos[1]],
                                     [self.pos[0], self.pos[1]-spawn_distance[1]],
                                     [self.pos[0]+spawn_distance[0], self.pos[1]],
                                     [self.pos[0], self.pos[1]+spawn_distance[1]]])
        self.checked_blocked_areas = False
        
        if self.makes_fruit:
            self.spawn_interval = 30 * 60
            
    def check_spawn_areas(self, wall_list):
        if not self.checked_blocked_areas:
            deleted_areas = []
            for idx, spawn_area in enumerate(self.spawn_areas): 
                for wall in wall_list:
                    is_occupied = vec.basic_collision(spawn_area, self.food_size,
                                                      wall.pos, wall.size)
                    if is_occupied:
                        deleted_areas.append(idx)
                        break
                    
            for del_area in reversed(deleted_areas):
                np.delete(self.spawn_areas, del_area)
                
            self.checked_blocked_areas = True
        
    def spawn_fruit(self, entity_list):
        if self.spawn_interval > 0 and self.spawn_areas.shape[0] > 0:
            if self.spawn_timer >= self.spawn_interval:
                direction = random.randint(0, self.spawn_areas.shape[0]-1)
                spawn_area = self.spawn_areas[direction]
                
                is_occupied = False
                for entity in entity_list:
                    if entity is not self:
                        if PROP_EDIBLE in entity.properties or PROP_SOLID in entity.properties:
                            is_occupied = vec.basic_collision(spawn_area, self.food_size,
                                                              entity.pos, entity.size)
                            if is_occupied:
                                break
                        
                if not is_occupied:
                    new_food = Food(spawn_area, PROP_FRUIT)
                    entity_list.append(new_food)

                self.spawn_timer = 0
            
            self.spawn_timer = self.spawn_timer + 1
            
            
    def exist(self, world):
        if self.makes_fruit:
            self.check_spawn_areas(world.walls)
            self.spawn_fruit(world.entities)
    
        
class Cave(Entity):
    def __init__(self, pos, inhabitant=None, waketime=0, bedtime=100):
        super().__init__(pos, 40, "img/cave_top.png", "img/cave_proj.png",
                         (40, 40), TYPE_ENVIRONMENT,  [PROP_HOME, PROP_SOLID])
        self.direction = np.array([0, 1])
        self.inhabitant = inhabitant
        self.spawn_pos = self.pos + self.direction * self.size[0]
        if self.inhabitant is not None:
            self.inhabitant.pos = self.spawn_pos
            self.inhabitant.home_cave = self
            temp_angle = vec.get_vector_rotation(self.direction)
            temp_angle = temp_angle * 180/math.pi - 90
            self.inhabitant.init_rotation(temp_angle)
            self.inhabitant.perform_rotation()
        self.waketime = waketime
        self.bedtime = bedtime
        self.is_awake = False
        self.is_dead = False
        
    def wake_up(self, time, organism_list):
        if not self.is_awake:
            organism_list.append(copy.copy(self.inhabitant))
            self.is_awake = True
                
    def go_to_sleep(self, time, organism_list):
        if self.is_awake:
            for organism in organism_list:
                if organism.home_cave == self:
                    is_at_home = vec.basic_collision(organism.pos, organism.size, self.spawn_pos, organism.size)
                    if is_at_home:
                        organism_list.remove(organism)
                        self.is_awake = False
    
    def exist(self, world):
        if self.inhabitant is not None and not self.is_dead:
            waketime_active = False
            if self.waketime < self.bedtime:
                waketime_active = world.time > self.waketime and world.time < self.bedtime
            else:
                waketime_active = world.time > self.waketime or world.time < self.bedtime
                
            if waketime_active:
                self.wake_up(world.time, world.organisms)
            else:
                self.go_to_sleep(world.time, world.organisms)
                

class Food(Entity):
    def __init__(self, pos, food_type=PROP_FRUIT):
        if food_type == PROP_FRUIT:
            top_sprite = "img/food_fruit.png"
            proj_sprite = "img/food_fruit_proj_sprite.png"
        elif food_type == PROP_MEAT:
            top_sprite = "img/food_meat.png"
            proj_sprite = "img/food_meat_proj_sprite.png"
            
        super().__init__(pos, 4, top_sprite, proj_sprite, (40,40), TYPE_FOOD, [PROP_EDIBLE, PROP_CARRIABLE, food_type])
        
        if food_type == PROP_FRUIT:
            self.max_portions = 3
        elif food_type == PROP_MEAT:
            self.max_portions = 2
            
        self.portions = self.max_portions
        self.portion_energy = 50
        self.z_pos = 20
        
        self.calc_sides()
        self.change_image_size()
        
    def exist(self, world):
        pass
        #make_noise(self.pos, 300, 3, 0.6, world)
        
    def change_image_size(self):
        self.sprite = pygame.transform.scale(self.base_sprite, (self.base_sprite.get_width() * self.portions,
                                                                self.base_sprite.get_height() * self.portions))
        self.size = np.array(self.sprite.get_size())
        self.proj_sprite_size = self.base_proj_sprite.get_size()[1] * self.portions
        self.height = self.base_height * self.portions
        self.calc_proj_sprite_width()
        
    def shrink(self):
        if self.portions > 0:
            self.portions = self.portions - 1
            self.change_image_size()
        
    def grow(self):
        if self.portions < self.max_portions:
            self.portions = self.portions + 1
            self.change_image_size()
        
        
class Rock(Entity):
    def __init__(self, pos):
        super().__init__(pos, 30, "img/rock.png", "img/rock_proj_sprite.png",
                         (40, 40), TYPE_ENVIRONMENT, [PROP_SOLID, PROP_CARRIABLE])
        

class Wall(Entity):
    def __init__(self, pos, symbol, color):
        if symbol == 1:
            sprite_file = "img/grey_wall.png"
        elif symbol == 2:
            sprite_file = "img/green_wall.png"
            
        super().__init__(pos, 40, sprite_file, "img/wood_wall_texture.png", (40,40), TYPE_WALL, [PROP_SOLID])
        self.calc_sides()
        