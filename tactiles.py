#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 13 18:59:49 2022

@author: cycrus
"""

import numpy as np
import math
import vector_tools as vec
import pygame

TOUCH_AREAS = 8
FULL_CIRCLE = math.pi * 2
CIRCLE_SEGMENT = FULL_CIRCLE / TOUCH_AREAS

ON = 1
OFF = 0

FRONTAL = [0, 1, 7]
BACK = [3, 4, 5]
LEFT = [1, 2, 3]
RIGHT = [5, 6, 7]

class Touch():
    def __init__(self, pos, direction):
        self.pos = pos
        self.direction = direction
        self.touch_input = np.zeros(TOUCH_AREAS)
        
    def update_touch(self, pos, direction):
        self.pos = pos
        self.direction = direction
        self.touch_input = np.zeros(TOUCH_AREAS)
        
    def check_touch(self, entity_pos):
        entity_vector = self.pos - entity_pos
        angle = vec.get_vector_angle(self.direction, entity_vector)
        if entity_vector[0] < 0:
            angle = -angle
        touch_position = vec.angle_to_discrete(angle)
        self.touch_input[touch_position] = ON
        return touch_position
        
    def render_touch(self, size, screen):
        dot_size = 4
        for dot in range(TOUCH_AREAS):
            angle = CIRCLE_SEGMENT * dot
            dot_pos = self.pos + vec.rotate_vector(self.direction, angle, False) * 15
            
            if self.touch_input[dot] == ON:
                color = (200, 100, 100)
            else:
                color = (200, 200, 200)
                
            pygame.draw.rect(screen, color, [dot_pos[0], dot_pos[1],
                                             dot_size, dot_size])


class PainReceptor():
    def __init__(self):
        self.pain_input = np.zeros(TOUCH_AREAS)
        self.pain_timer = np.zeros(TOUCH_AREAS)
        self.pain_max_time = 10
        self.does_hurt = np.zeros(TOUCH_AREAS)
        
    def update_pain(self):
        if np.sum(self.pain_input) > 0:
            for idx, pain in enumerate(self.pain_input):
                if self.pain_input[idx] == ON:
                    if self.pain_timer[idx] <= 0:
                        self.pain_input[idx] = OFF
                        self.pain_timer[idx] = self.pain_max_time
                    else:
                        self.pain_timer[idx] = self.pain_timer[idx] - 1
        
    def inflict_pain(self, touch_location):
        self.pain_input[touch_location] = ON
        self.pain_timer[touch_location] = self.pain_max_time
        
    def render_pain(self, pos, direction, size, screen):
        dot_size = 6
        for dot in range(TOUCH_AREAS):
            angle = CIRCLE_SEGMENT * dot
            dot_pos = pos + vec.rotate_vector(direction, angle, False) * 14
            
            if self.pain_input[dot] == ON:
                color = (255, 0, 0)
                pygame.draw.rect(screen, color, [dot_pos[0], dot_pos[1],
                                                 dot_size, dot_size])