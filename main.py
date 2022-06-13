#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 19:00:53 2022

@author: cycrus
"""

from engine_simulator import EngineSimulator
from environment import World
import numpy as np
import pygame
import cv2
import math
import random

## Logistics
# TODO Create Git Repo

## World
# X TODO Allow loading maps
# X TODO Different wall types
# X TODO Food dispenser
# X TODO Day-Night cycle
# X TODO Functional Caves for Organisms

## Organisms
# TODO Weak AI passives
# TODO Weak AI hunter
# TODO Strong AI UDP nodes
# X TODO Make organisms smaller and symmetric
# TODO Create Sprites (Animations) for different actions

## Organs
# X TODO Create hearing organ
# X TODO Sprites for vision
# X TODO Create vectoral vision
# X TODO Touch input
# X TODO Pain input
# TODO Vision: Fix transparent hiding of objects in Ray Casting Sprites

## Actions
# X TODO Sound output
# X TODO Bite/Attack
# X TODO Carry Food

## Low Priority
# TODO Texture to raycasting engine?
# TODO Stamina sensation

if __name__ == "__main__":
    env = World(worldname="testworld1")
    sim = EngineSimulator(env)
    
    sim.start_simulation()