#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 15:57:43 2022

@author: cycrus
"""

import math

RAD_0 = 0
RAD_90 = math.pi / 2
RAD_180 = math.pi
RAD_270 = math.pi * 1.5
RAD_360 = math.pi * 2
RAD_n90 = -RAD_90

COLOR_EMPTY = (237, 221, 190)
COLOR_ENERGY_BAR = (10, 10, 155)
COLOR_GROUND = (0, 128, 0)

MAPC_EMPTY = (255, 255, 255)
MAPC_GREY_WALL = (50, 50, 50)
MAPC_GREEN_WALL = (0, 50, 30)
MAPC_FOOD_MEAT = (130, 35, 76)
MAPC_FOOD_FRUIT = (0, 84, 5)
MAPC_BLUEMEEP = (0, 0, 255)
MAPC_REDMEEP = (255, 0, 0)
MAPC_PLAYER = (102, 0, 102)
MAPC_RED_CAVE = (128, 82, 33)
MAPC_TREE = (62, 112, 44)
MAPC_FRUIT_TREE = (39, 66, 31)
MAPC_ROCK = (166, 166, 166)

MAP_EMPTY = 0
MAP_GREY_WALL = 1
MAP_GREEN_WALL = 2

COLOR_GRID = (50, 50, 50)

MAX_COLOR = 255.0

PI_DIV_4 = math.pi / 4
THREE_PI_DIV_4 = 3*math.pi / 4
PI_TIMES_2 = math.pi * 2