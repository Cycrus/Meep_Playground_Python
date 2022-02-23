#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 01:00:02 2022

@author: cycrus
"""

from helper_functions import make_noise
import vector_tools as vec
import numpy as np
import math
import pygame

CHANNEL_NUMBER = 5


class Ear():
    def __init__(self, direction):
        self.direction = direction
        self.sound_input = np.zeros(CHANNEL_NUMBER)
        
    def reset_hearing(self, direction):
        self.sound_input = np.zeros(CHANNEL_NUMBER)
        self.direction = direction
        
    def hear(self, channel, intensity, direction_vector):
        
        # Commented out block is an attempt for audio direction, but not mature yet
        """
        if self.sound_input[channel] > 0:
            is_occupied = True
        else:
            is_occupied = False
        
        dir_vector_len = np.linalg.norm(direction_vector)
        
        # Calculate direction from where audio input comes (left or right)
        if dir_vector_len > 0:
            if self.direction[0] < 0:
                rotation_angle = -vec.get_vector_rotation_axis(self.direction, [0,1])
            else:
                rotation_angle = vec.get_vector_rotation_axis(self.direction, [0,1])
            rotated_dir_vector = vec.rotate_vector(direction_vector, rotation_angle, False)
            
            rotated_dir_vector_unit = rotated_dir_vector / dir_vector_len
            temp_direction = rotated_dir_vector_unit[0]
        else:
            temp_direction = 0
        """
        
        self.sound_input[channel] = self.sound_input[channel] + intensity
        
        """
        if self.sound_direction[channel] > 1:
            self.sound_direction[channel] = 1
        elif self.sound_direction[channel] < -1:
            self.sound_direction[channel] = -1
        """
        
    def render_hearing(self, sides, size, screen):
        for bar in range(CHANNEL_NUMBER):
            bar_height = 2 + self.sound_input[bar] * 10
            bar_width = 5
            bar_y = 12
            bar_left = sides[0] + (bar_width + 2) * bar - 5
            bar_top = sides[1] - bar_y
            pygame.draw.rect(screen, (204, 204, 0), [bar_left, bar_top-bar_height,
                                                     bar_width, bar_height])


class Voice():
    def __init__(self):
        self.base_radius = 150
        self.does_talk = False
        self.channel = 0
        self.intensity = 0
        self.talk_timer = 0
        self.max_talk_time = 10
        
    def init_talking(self, channel, intensity, force=False):
        if self.talk_timer > self.max_talk_time or force:
            self.talk_timer = 0
            self.does_talk = True
            self.channel = channel
            self.intensity = intensity
        
    def talk(self, pos, world):
        make_noise(pos, self.base_radius, self.channel, self.intensity, world)
        
        if self.talk_timer <= self.max_talk_time:
            self.talk_timer = self.talk_timer + 1
        else:
            self.does_talk = False
            self.intensity = 0
            
    def check_for_talking(self):
        return self.does_talk