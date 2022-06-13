#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 18:55:29 2022

@author: cycrus
"""

"""
Action space
1. Forward
2. Backward
3. Turn Left
4. Turn Right
"""

from vision import RayCastingEye, VectorEye
from helper_functions import make_noise
from auditory import Ear, Voice
from tactiles import Touch, PainReceptor, FRONTAL
import vector_tools as vec
from constants import COLOR_ENERGY_BAR
import objects
import numpy as np
import pygame
import copy
import itertools

ACTION_SPACE = 4

CARNIVORE = 0
HERBIVORE = 1
OMNIVORE = 2

class Organism(objects.Entity):
    def __init__(self, pos, rotation, food_source, is_controlled, grid_size):
        if food_source == CARNIVORE:
            top_sprite = "img/hunter.png"
            proj_sprite = "img/red_meep_proj_sprite.png"
        elif food_source == HERBIVORE:
            top_sprite = "img/npc.png"
            proj_sprite = "img/blue_meep_proj_sprite.png"
        if is_controlled:
            top_sprite = "img/player.png"
        
        super().__init__(pos, 20, top_sprite, proj_sprite, (40,40), objects.TYPE_ORGANISM, [objects.PROP_LIVING])
        
        self.is_controlled = is_controlled
        self.rotation_angle = 0
        self.base_max_velocity = 5
        self.max_velocity = self.base_max_velocity
        self.curr_velocity = 0
        self.dest_velocity = 0
        self.acc_value = 0
        self.base_min_velocity = -5
        self.min_velocity = self.base_min_velocity
        self.global_rotation_angle = 0
        self.food_source = food_source
        
        self.max_energy = 100.0
        self.energy = self.max_energy
        self.rotation_energy_cost = 0.002
        self.walking_energy_cost = 0.004
        self.living_cost = 0.005
        self.eat_timer = 0
        self.required_eat_time = 100
        self.init_eat = False
        self.eat_energy_cost = 0.7
        self.talk_energy_cost = 0.1
        self.init_grab = False
        self.grabbed_entity = None
        self.grab_timer = 0
        self.required_grab_time = 50
        
        self.home_cave = None
            
        self.ear = Ear(self.direction)
        self.voice = Voice()
        self.touch = Touch(self.pos, self.direction)
        self.pain = PainReceptor()
        
        self.set_mode(grid_size)
        self.calc_proj_sprite_width()
        
        self.init_rotation(rotation)
    
        self.calc_sides()
        
    def sense_world(self, world, debug):
        self.eye.see(self.pos, self.direction, world, debug)
        self.ear.reset_hearing(self.direction)
        self.pain.update_pain()
        
    def render_sensations(self, screen):
        self.eye.render_gaze(screen)
        self.ear.render_hearing(self.sides, self.size, screen)
        self.render_energy(screen)
        self.touch.render_touch(self.size, screen)
        self.pain.render_pain(self.pos, self.direction, self.size, screen)
        
    def render_energy(self, screen):
        bar_length = self.energy * 0.4
        bar_left = self.sides[0] + self.size[0] / 2 - bar_length / 2
        bar_top = self.sides[1] - 10
        pygame.draw.rect(screen, COLOR_ENERGY_BAR, [bar_left, bar_top, bar_length, 4])
        
    def set_mode(self, grid_size):
        if self.food_source == HERBIVORE or self.food_source == OMNIVORE:
            self.attack_strength = 10
        elif self.food_source == CARNIVORE:
            self.attack_strength = 20
            
        self.sprite = self.base_sprite
        self.proj_sprite = pygame.Surface(self.proj_sprite_dims, flags=pygame.SRCALPHA)
        self.proj_sprite.blit(self.base_proj_sprite, (0,0), (0,0,self.proj_sprite_dims[0],self.proj_sprite_dims[1]))
        self.size = np.array(self.sprite.get_size())
        self.prev_size = self.size
        
        if self.is_controlled:
            #self.eye = VectorEye(self.pos, self.direction, 60, 300, grid_size)
            self.eye = RayCastingEye(self.pos, self.direction, 60, 800, 200, grid_size)
        else:
            self.eye = VectorEye(self.pos, self.direction, 60, 300, grid_size)
            #self.eye = RayCastingEye(self.pos, self.direction, 60, 800, 200, grid_size)
        
    def set_acc_value(self, value):
        self.acc_value = value
            
    def accelerate(self):
        self.dest_velocity = self.dest_velocity + self.acc_value
        
        if self.acc_value == 0:
            self.dest_velocity = 0
        
        if self.grabbed_entity is not None:
            self.max_velocity = self.base_max_velocity * 0.7
            self.min_velocity = self.base_min_velocity * 0.7
        else:
            self.max_velocity = self.base_max_velocity
            self.min_velocity = self.base_min_velocity
        
        if self.dest_velocity > self.max_velocity:
            self.dest_velocity = self.max_velocity
        elif self.dest_velocity < self.min_velocity:
            self.dest_velocity = self.min_velocity
            
    def init_rotation(self, rotate_angle):
        self.rotation_angle = -rotate_angle
        
    def perform_rotation(self):
        if self.rotation_angle != 0:
            self.direction = vec.rotate_vector(self.direction, self.rotation_angle)
            if self.grabbed_entity is not None:
                self.grabbed_entity.pos = vec.rotate_vector(self.grabbed_entity.pos,
                                                            self.rotation_angle,
                                                            True, self.pos)
                self.grabbed_entity.calc_sides()
            
            self.global_rotation_angle = self.global_rotation_angle + self.rotation_angle
            self.sprite = pygame.transform.rotate(self.base_sprite,
                                                  self.global_rotation_angle)
            self.sprite, offset = vec.crop_image_pixels(self.sprite)
            self.size = np.array(self.sprite.get_size())
            
            self.energy = self.energy + self.rotation_angle * self.rotation_energy_cost
            self.rotation_angle = 0
            self.calc_sides()
        
    def walk(self, world):
        self.save_prev_state()
        if self.grabbed_entity is not None:
            self.grabbed_entity.save_prev_state()
        
        self.perform_rotation()
        
        position_delta = self.direction * self.curr_velocity
        self.pos = self.pos + position_delta
        if self.grabbed_entity is not None:
            self.grabbed_entity.change_position(delta=position_delta)
        
        left_border = self.size[0] / 2
        top_border = self.size[1] / 2
        right_border = world.size[0] - self.size[0] / 2
        bottom_border = world.size[1] - self.size[1] / 2
        
        if self.pos[0] < left_border:
            self.pos[0] = left_border
        if self.pos[0] > right_border:
            self.pos[0] = right_border
        if self.pos[1] < top_border:
            self.pos[1] = top_border
        if self.pos[1] > bottom_border:
            self.pos[1] = bottom_border
            
        self.energy = self.energy - self.curr_velocity * self.walking_energy_cost
        
        self.calc_sides()
        
        if self.curr_velocity > 0:
            temp_velocity = abs(self.curr_velocity)
            sound_intensity = temp_velocity / self.max_velocity * 0.5
            make_noise(self.pos, 500, 0, sound_intensity, world)
            
        self.curr_velocity = (self.curr_velocity + (self.dest_velocity - self.curr_velocity) * 0.2)
        
    def check_stop(self, entity):
        vec.solid_stop(self, self.grabbed_entity, entity)
        
    def check_grabbed_stop(self, entity):
        vec.solid_stop(self.grabbed_entity, self, entity)
        
    def change_energy_level(self, value):
        self.energy = self.energy + value
        self.eat_timer = self.required_eat_time
        if self.energy > self.max_energy:
            self.energy = self.max_energy
            
        if value < 0:
            self.voice.init_talking(4, 2.0, True)
        else:
            self.voice.init_talking(1, 1.0, True)
        
    def eat(self, entity):
        if self.energy < self.max_energy and self.eat_timer == 0 and self.grabbed_entity is None:
            entity_direction = self.touch.check_touch(entity.pos)
            if entity_direction in FRONTAL:
                if self.food_source == HERBIVORE or self.food_source == OMNIVORE:
                    entity.shrink()
                    self.change_energy_level(entity.portion_energy)
            
    def attack(self, entity):
        if self.eat_timer == 0 and self.grabbed_entity is None:
            entity_direction = self.touch.check_touch(entity.pos)
            if entity_direction in FRONTAL:
                entity.change_energy_level(-self.attack_strength)
                inverse_direction = entity.touch.check_touch(self.pos)
                entity.pain.inflict_pain(inverse_direction)
                
                if self.food_source == CARNIVORE or self.food_source == OMNIVORE:
                    self.change_energy_level(self.attack_strength * 2)
                self.eat_timer = self.required_eat_time
            
    def grab(self, entity):
        if self.grab_timer == 0:
            if self.grabbed_entity is None and \
                    not objects.PROP_IS_CARRIED in entity.properties:
                entity_direction = self.touch.check_touch(entity.pos)
                if entity_direction in FRONTAL:
                    self.grabbed_entity = entity
                    self.grabbed_entity.properties.append(objects.PROP_IS_CARRIED)
            elif self.grabbed_entity:
                self.grabbed_entity.properties.remove(objects.PROP_IS_CARRIED)
                self.grabbed_entity = None
            self.grab_timer = self.required_grab_time

    def interact(self, entity_list, organism_list, wall_list):
        for entity in itertools.chain(entity_list, organism_list, wall_list):
            if vec.collide(self, entity) or entity is self.grabbed_entity:
                if entity is not self:
                    self.touch.check_touch(entity.pos)
                    if objects.PROP_EDIBLE in entity.properties:
                        if self.init_eat and self.grabbed_entity is None:
                            self.eat(entity)
                            if entity.portions <= 0:
                                entity_list.remove(entity)
                    if objects.PROP_CARRIABLE in entity.properties:
                        if self.init_grab:
                            self.grab(entity)
                    if objects.PROP_SOLID in entity.properties and entity is not self.grabbed_entity:
                        self.check_stop(entity)
                    if objects.PROP_LIVING in entity.properties:
                        if self.init_eat:
                            self.attack(entity)
                            
        if self.grabbed_entity is not None:
            for entity in itertools.chain(entity_list, organism_list, wall_list):
                if entity is not self and entity is not self.grabbed_entity:
                    if objects.PROP_SOLID in entity.properties  or objects.PROP_LIVING in entity.properties:
                        if vec.basic_collision(self.grabbed_entity.pos, self.grabbed_entity.size,
                                               entity.pos, entity.size):
                            print(self.grabbed_entity.pos)
                            self.check_grabbed_stop(entity)
        
    def random_action(self):
        actions = np.random.rand(ACTION_SPACE)
        actions[0] = actions[0] * 1.2
        actions[2] = actions[2] * 1.1
        action = np.argmax(actions)
        force = np.random.rand() * 10
        
        return action, force
    
    def remote_control(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.set_acc_value(2)
        if keys[pygame.K_s]:
            self.set_acc_value(-1)
        if keys[pygame.K_d]:
            self.init_rotation(5)
        if keys[pygame.K_a]:
            self.init_rotation(-5)
        if keys[pygame.K_q]:
            self.voice.init_talking(3, 1.2)
        if keys[pygame.K_e]:
            self.voice.init_talking(4, 1.2)
        if keys[pygame.K_f]:
            self.init_eat = True
        if keys[pygame.K_c]:
            self.init_grab = True
    
    def act(self, world):
        self.init_eat = False
        self.init_grab = False
        
        if self.is_controlled:
            self.remote_control()
        """
        else:
            action, force = self.random_action()
            
            if action == 0:
                self.set_acc_value(force)
            elif action == 1:
                self.set_acc_value(-force)
            elif action == 2:
                self.init_rotation(force)
            elif action == 3:
                self.init_rotation(-force)
        """
            
        if self.init_eat:
            self.energy = self.energy - self.eat_energy_cost
        
        if self.voice.check_for_talking():
            self.energy = self.energy - self.talk_energy_cost
            
        self.accelerate()
        self.walk(world)
        self.acc_value = 0
        
        self.touch.update_touch(self.pos, self.direction)
        
        self.voice.talk(self.pos, world)
        
        self.energy = self.energy - self.living_cost
        if self.eat_timer > 0:
            self.eat_timer = self.eat_timer - 1
        if self.grab_timer > 0:
            self.grab_timer = self.grab_timer - 1