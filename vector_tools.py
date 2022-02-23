#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 18:45:27 2022

@author: cycrus
"""

import numpy as np
import math

SIDE_LEFT = 0
SIDE_TOP = 1
SIDE_RIGHT = 2
SIDE_BOTTOM = 3

R0 = math.pi/8
R1 = 3*R0
R2 = 5*R0
R3 = 7*R0
R4 = 9*R0
R5 = 11*R0
R6 = 13*R0
R7 = 15*R0
R8 = 17*R0

RAD_45 = math.pi / 4
RAD_90 = math.pi / 2
RAD_180 = math.pi
RAD_360 = math.pi * 2
RAD_720 = math.pi * 4

def correct_negative_angle(angle):
    while(angle < 0):
        angle = angle + RAD_360
    return angle

def check_between_angle(angle, lower_bound, upper_bound):
    if angle >= lower_bound and angle <= upper_bound:
        return True
    else:
        return False
    
def angle_to_discrete(angle):
    angle = correct_negative_angle(angle)
    value = 0
        
    if angle > -R0 and angle <= R0 or angle > R7 and angle <= R8:
        value = 4
    elif angle > R0 and angle <= R1:
        value = 3
    elif angle > R1 and angle <= R2:
        value = 2
    elif angle > R2 and angle <= R3:
        value = 1
    elif angle > R3 and angle <= R4:
        value = 0
    elif angle > R4 and angle <= R5:
        value = 7
    elif angle > R5 and angle <= R6:
        value = 6
    elif angle > R6 and angle <= R7:
        value = 5
        
    return value

def get_rotated_sprite_offset(angle, sprite_height):
    offset = angle_to_discrete(angle)
        
    sprite_y = sprite_height * offset
    return sprite_y

def is_color(color1, color2):
        truth_value = color1[0] == color2[0] and \
                      color1[1] == color2[1] and \
                      color1[2] == color2[2]
        return truth_value
    
def solid_stop(entity1, entity2, checked_entity):
    # From left
    if entity1.sides[SIDE_RIGHT] > checked_entity.sides[SIDE_LEFT] and \
            entity1.prev_sides[SIDE_RIGHT] <= checked_entity.sides[SIDE_LEFT]:
        dist = checked_entity.sides[SIDE_LEFT] - entity1.sides[SIDE_RIGHT]
        entity1.change_position(delta=dist, axis=0)
        if entity2 is not None:
            entity2.change_position(delta=dist, axis=0)
        
    # From top
    if entity1.sides[SIDE_BOTTOM] > checked_entity.sides[SIDE_TOP] and \
            entity1.prev_sides[SIDE_BOTTOM] <= checked_entity.sides[SIDE_TOP]:
        dist = checked_entity.sides[SIDE_TOP] - entity1.sides[SIDE_BOTTOM]
        entity1.change_position(delta=dist, axis=1)
        if entity2 is not None:
            entity2.change_position(delta=dist, axis=1)
    
    # From right
    if entity1.sides[SIDE_LEFT] < checked_entity.sides[SIDE_RIGHT] and \
            entity1.prev_sides[SIDE_LEFT] >= checked_entity.sides[SIDE_RIGHT]:
        dist = checked_entity.sides[SIDE_RIGHT] - entity1.sides[SIDE_LEFT]
        entity1.change_position(delta=dist, axis=0)
        if entity2 is not None:
            entity2.change_position(delta=dist, axis=0)
        
    # From bottom
    if entity1.sides[SIDE_TOP] < checked_entity.sides[SIDE_BOTTOM] and \
            entity1.prev_sides[SIDE_TOP] >= checked_entity.sides[SIDE_BOTTOM]:
        dist = checked_entity.sides[SIDE_BOTTOM] - entity1.sides[SIDE_TOP]
        entity1.change_position(delta=dist, axis=1)
        if entity2 is not None:
            entity2.change_position(delta=dist, axis=1)

def collide(entity1, entity2):
    if entity1.sides[SIDE_LEFT] < entity2.sides[SIDE_RIGHT] and \
            entity1.sides[SIDE_RIGHT] > entity2.sides[SIDE_LEFT]:
        if entity1.sides[SIDE_TOP] < entity2.sides[SIDE_BOTTOM] and \
                entity1.sides[SIDE_BOTTOM] > entity2.sides[SIDE_TOP]:
            return True
    return False

def basic_collision(pos1, size1, pos2, size2):
    if pos1[0] < pos2[0] + size2[0] and \
            pos1[0] + size1[0] > pos2[0]:
        if pos1[1] < pos2[1] + size2[1] and \
                pos1[1] + size1[1] > pos2[1]:
            return True
    return False

def project_vectors(v1, v2):
    return (np.dot(v1, v2) / np.linalg.norm(v2)) * v2

def rotate_vector(vector, angle, is_deg=True, origin=(0,0)):
    if is_deg:
        theta = np.radians(angle)
    else:
        theta = angle
    translated_vector = vector - origin
    rotation_matrix = np.array([[np.cos(theta), -np.sin(theta)],
                                [np.sin(theta), np.cos(theta)]])
    result = np.matmul(translated_vector, rotation_matrix)
    result = result + origin
    return result

def calc_vector(p1, p2):
    return p2-p1

def calc_vector_from_angle(alpha):
    vector = np.array([math.cos(alpha), -math.sin(alpha)])
    return np.round(vector, 10)

def get_vector_rotation_axis(vector, coord_vector):
        scalarproduct = np.dot(vector, coord_vector)
        absolute_vector = np.linalg.norm(vector)
        absolute_coord_vector = np.linalg.norm(coord_vector)
        dividend = absolute_vector * absolute_coord_vector
        if dividend != 0:
            return math.acos(scalarproduct / dividend)
        else:
            return 0
        
def get_vector_angle(vector1, vector2):
    cos = get_vector_rotation_axis(vector1, vector2)
    
    if vector1[1] > 0:
        angle = math.pi - cos + math.pi
    else:
        angle = cos
        
    return angle
        
def get_vector_rotation(vector):
    cos = get_vector_rotation_axis(vector, [1,0])
    
    if vector[1] > 0:
        angle = math.pi - cos + math.pi
    else:
        angle = cos
        
    return angle

def deg_to_rad(deg):
    return deg * math.pi/180

def rad_to_deg(rad):
    return rad * 180/math.pi

def crop_image_pixels(image):
    size = image.get_size()
    left = 0
    top = 0
    right = 0
    bottom = 0
    
    for x in range(size[0]):
        check = False
        for y in range(size[1]):
            color = image.get_at((x, y))
            if color[3] > 0:
                left = x
                check = True
                break
        if check:
            break
            
    for x in reversed(range(size[0])):
        check = False
        for y in range(size[1]):
            color = image.get_at((x, y))
            if color[3] > 0:
                right = x
                check = True
                break
        if check:
            break
        
    for y in range(size[1]):
        check = False
        for x in range(size[0]):
            color = image.get_at((x, y))
            if color[3] > 0:
                top = y
                check = True
                break
        if check:
            break
        
    for y in reversed(range(size[1])):
        check = False
        for x in range(size[0]):
            color = image.get_at((x, y))
            if color[3] > 0:
                bottom = y
                check = True
                break
        if check:
            break
        
    width = right - left
    height = bottom - top
    cropped_image = image.subsurface((left, top, width, height))
    offset = np.array([left, top, right, bottom])
    
    return image, offset

if __name__ == "__main__":
    angle = math.pi / 2
    vector = calc_vector_from_angle(angle)
    print(vector)
    print(get_vector_rotation(vector))
    