#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 18:52:50 2022

@author: cycrus
"""

from organism import HERBIVORE, CARNIVORE, OMNIVORE
from objects import TYPE_WALL, PROP_MEAT, PROP_FRUIT
from constants import COLOR_EMPTY, COLOR_GRID
from constants import MAP_GREY_WALL, MAPC_GREY_WALL
from vision import RayCastingEye
import vector_tools as vec
import pygame
import numpy as np
import cv2

class EngineSimulator(object):
    def __init__(self, world):
        self.world = world
        self.size = self.world.size
        self.fps = 30
        self.grid_size = self.world.grid_size
        self.running = True
        self.world.sort_entites_by_size()
        
    def start_engine(self):
        pygame.init()
        self.size = self.size
        self.virtual_screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("AI Simulator")
        
    def render_grid(self):
        for x in range(self.size[0] // self.grid_size):
            grid_x = x * self.grid_size
            pygame.draw.line(self.virtual_screen, COLOR_GRID,
                             (grid_x, 0), (grid_x, self.size[1]))
        for y in range(self.size[1] // self.grid_size):
            grid_y = y  * self.grid_size
            pygame.draw.line(self.virtual_screen, COLOR_GRID,
                             (0, grid_y), (self.size[0], grid_y))
        
    def render_topdown(self):
        for entity in self.world.entities:
            left = entity.pos[0] - entity.size[0] / 2
            top = entity.pos[1] - entity.size[1] / 2
            self.virtual_screen.blit(entity.sprite, (left, top))
        for wall in self.world.walls:
            left = wall.pos[0] - wall.size[0] / 2
            top = wall.pos[1] - wall.size[1] / 2
            self.virtual_screen.blit(wall.sprite, (left, top))

        self.render_grid()
            
        for organism in self.world.organisms:
            self.virtual_screen.blit(organism.sprite, (organism.sides[0], organism.sides[1]))
            
            organism.render_sensations(self.virtual_screen)
        
    def render_eye(self, eye):
        # Take col --> testimg[:, 0]
        # Take row --> testimg[0]
        # Expand col --> np.expand_dims(col, 1)
        # Expand row --> np.expand_dims(row, 0)
        # Append col --> np.append(testimg, col, 1)
        # Append row --> np.append(testimg, row, 0)
        
        cv2.namedWindow("Rendered Eye View")
        cv2.moveWindow("Rendered Eye View", 5, 5)
        cv2.imshow("Rendered Eye View", eye.perceived_image)
        cv2.waitKey(1)
        
    def control_events(self):
        events = pygame.event.get()
            
        for event in events:
            pos = np.array(pygame.mouse.get_pos())
            
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.world.spawn_npc(pos, HERBIVORE)
                elif event.button == 3:
                    self.world.spawn_player(pos, HERBIVORE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_1:
                    self.world.spawn_food(pos, PROP_FRUIT)
                elif event.key == pygame.K_2:
                    self.world.spawn_food(pos, PROP_MEAT)
                elif event.key == pygame.K_0:
                    grid_diff = np.zeros(2)
                    grid_diff[0] = pos[0] % self.grid_size
                    grid_diff[1] = pos[1] % self.grid_size
                    pos = pos - grid_diff + self.grid_size // 2
                    pos = pos.astype(int)
                    self.world.spawn_wall(pos, MAP_GREY_WALL, MAPC_GREY_WALL)
        
    def start_simulation(self):
        self.start_engine()
        clock = pygame.time.Clock()
        
        while self.running:
            for organism in self.world.organisms:
                organism.act(self.world)
                organism.interact(self.world.entities, self.world.organisms, self.world.walls)
                if organism.energy <= 0:
                    self.world.spawn_food(organism.pos, PROP_MEAT)
                    self.world.organisms.remove(organism)
                    
            self.virtual_screen.fill(self.world.background_color)
            self.control_events()
            self.render_topdown()
                    
            for organism in self.world.organisms:
                organism.sense_world(self.world, self.virtual_screen)
                if organism.is_controlled and isinstance(organism.eye, RayCastingEye):
                    self.render_eye(organism.eye)
                    
            for entity in self.world.entities:
                entity.exist(self.world)
            
            self.world.update_time()
            self.world.sort_entites_by_size()
            
            pygame.display.flip()
            clock.tick(self.fps)
            
        cv2.destroyAllWindows()
        pygame.quit()
            