#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 18:50:03 2022

@author: cycrus
"""

import os
import math
from PIL import Image
import numpy as np
import itertools
from vector_tools import is_color
from organism import Organism, HERBIVORE, CARNIVORE, OMNIVORE
from objects import Food, Cave, Wall, Tree, Rock, PROP_FRUIT, PROP_MEAT
import constants as con

class World(object):
    def __init__(self, worldname=None, size=[0,0]):
        self.organisms = []
        self.entities = []
        self.render_list = []
        self.walls = []
        self.background_color = con.COLOR_GROUND
        self.grid_size = 40
        self.time = 500
        self.max_time = 1300
        self.sun_angle = 0
        self.sun_intensity = 0
        self.sun_color = np.array([1.0, 1.0, 1.0])
        self.min_sun_intensity = 0.04
        self.update_time()
        if worldname:
            self.load_worldfile(worldname)
        else:
            self.size = size
            self.world_map = np.zeros(size // self.grid_size)
            
    def sort_entites_by_size(self):
        self.render_list = self.organisms + self.entities
        
    def spawn_food(self, pos, food_type):
        new_food = Food(pos, food_type)
        self.entities.append(new_food)
        
    def spawn_wall(self, pos, symbol, color):
        new_wall = Wall(pos, symbol, color)
        self.walls.append(new_wall)
        wall_pos = pos / self.grid_size
        wall_pos = wall_pos.astype(int)
        self.world_map[wall_pos[0], wall_pos[1]] = symbol
        
    def spawn_organism(self, init_pos, food_source, is_controlled):
        init_rotation = np.random.rand(1) * 360
        new_organism = Organism(init_pos, init_rotation[0], food_source,
                                is_controlled, self.grid_size)
        self.organisms.append(new_organism)
    
    def spawn_npc(self, init_pos, food_source):
        self.spawn_organism(init_pos, food_source, False)
        
    def spawn_player(self, init_pos, food_source):
        for idx, organism in enumerate(self.organisms):
            if organism.is_controlled:
                self.organisms.pop(idx)
                break
                
        self.spawn_organism(init_pos, food_source, True)
        
    def spawn_cave(self, init_pos, food_source):
        cave_inhabitant = Organism(init_pos, 0, food_source,
                                   False, self.grid_size)
        
        temp_cave = Cave(init_pos, cave_inhabitant, 510, 520)
        self.entities.append(temp_cave)
        
    def spawn_tree(self, init_pos, has_fruit):
        temp_tree = Tree(init_pos, has_fruit)
        self.entities.append(temp_tree)
        
    def spawn_rock(self, init_pos):
        temp_rock = Rock(init_pos)
        self.entities.append(temp_rock)
        
    def update_sun_color(self):
        if self.time > 0 and self.time < 200:
            self.sun_color = np.array([0.9, 0.9, 1.0])
        elif self.time > 800 and self.time < 1000:
            self.sun_color = np.array([1.0, 0.8, 0.8])
        else:
            self.sun_color = np.array([1.0, 1.0, 1.0])
        
    def update_time(self):
        self.time = self.time + 0.1
        if self.time > self.max_time:
            self.time = 0
        self.update_sun_angle()
        self.update_sun_intensity()
        self.update_sun_color()
        
    def update_sun_intensity(self):
        # Flipped square function. 500 = max sun; 0 & 1000 - max_time = min sun
        self.sun_intensity = -0.000004 * (self.time - 500)**2 + 1
        if self.sun_intensity < self.min_sun_intensity:
            self.sun_intensity = self.min_sun_intensity
            
    def update_sun_angle(self):
        self.sun_angle = self.time / self.max_time * math.pi * 2
        
        # Flipped square function to calculate angles
        self.east_side_light = -0.2 * (self.sun_angle - con.THREE_PI_DIV_4)**2 + 1
        if self.east_side_light < 0.4:
            self.east_side_light = 0.4
            
        self.west_side_light = -0.2 * (self.sun_angle - con.PI_DIV_4)**2 + 1
        if self.west_side_light < 0.4:
            self.west_side_light = 0.4
        
    def load_worldfile(self, worldname):
        if worldname.endswith(".png"):
            worldname = os.path.splitext(worldname)[0]
        worldmap = Image.open("worlds" + os.sep + worldname + ".png")
        
        mapsize = np.array(worldmap.size)
        self.world_map = np.zeros(mapsize)
        self.size = mapsize * self.grid_size
        worldmap = np.asarray(worldmap)
        for y in range(mapsize[1]):
            for x in range(mapsize[0]):
                position = np.array([x*self.grid_size, y*self.grid_size]) + self.grid_size / 2
                obj_color = worldmap[y,x]
                
                if is_color(obj_color, con.MAPC_GREY_WALL):
                    self.spawn_wall(position, con.MAP_GREY_WALL, con.MAPC_GREY_WALL)
                elif is_color(obj_color, con.MAPC_GREEN_WALL):
                    self.spawn_wall(position, con.MAP_GREEN_WALL, con.MAPC_GREEN_WALL)
                elif is_color(obj_color, con.MAPC_FOOD_MEAT):
                    self.spawn_food(position, PROP_MEAT)
                elif is_color(obj_color, con.MAPC_FOOD_FRUIT):
                    self.spawn_food(position, PROP_FRUIT)
                elif is_color(obj_color, con.MAPC_BLUEMEEP):
                    self.spawn_npc(position, HERBIVORE)
                elif is_color(obj_color, con.MAPC_REDMEEP):
                    self.spawn_npc(position, CARNIVORE)
                elif is_color(obj_color, con.MAPC_PLAYER):
                    self.spawn_player(position, HERBIVORE)
                elif is_color(obj_color, con.MAPC_RED_CAVE):
                    self.spawn_cave(position, CARNIVORE)
                elif is_color(obj_color, con.MAPC_TREE):
                    self.spawn_tree(position, False)
                elif is_color(obj_color, con.MAPC_FRUIT_TREE):
                    self.spawn_tree(position, True)
                elif is_color(obj_color, con.MAPC_ROCK):
                    self.spawn_rock(position)