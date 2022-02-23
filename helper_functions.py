#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 22:30:35 2022

@author: cycrus
"""

import numpy as np
import vector_tools as vec


def make_noise(pos, base_radius, channel, intensity, world):
        radius = base_radius * intensity
        
        for idx, entity in enumerate(world.organisms):
            entity_vector = entity.pos - pos
            entity_distance = np.linalg.norm(entity_vector)
            direction = vec.get_vector_rotation(entity_vector)
            
            if radius == 0:
                sound_intensity = 0
            elif entity_distance > 0:
                sound_intensity = (radius - entity_distance) / radius * intensity
            else:
                sound_intensity = intensity
                
            if entity_distance < radius:
                entity.ear.hear(channel, sound_intensity, entity_vector)