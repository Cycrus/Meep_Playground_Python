# Meep_Playground_Python

## Reqirements and Startup
You need a Python version of at least Python 3.6 and the packages installed as defined in the "requirements.txt" file.
To start the program, you just run the main.py file in the root folder in python. Have fun playing around.

## Concept
This is a version of a reinforcement learning AI playground and a sandbox for a curstom game engine. Later versions have been ported to Unity and are written in C#.
A level can be created by painting a map where every pixel color means another object. An example and the meaning of colors can be found in the folder "worlds".
A world contains different Meeps (lifeforms) currently moving randomly through the map. They are capable of moving, eating, replacing obstacles like rocks and attacking each other.
The lose energy over time and with every action they perform. When the energy drops to 0 they die and become eadible meat.
The Meeps are capable of sensing the direction of a touch, a simplified concept of sound, pain and their energy level representing hunger.
Two types of vision are implemented:
- A vector containing the rotation and distance of other objects.
- A custom raycasting algorithm allowing for a simulated 3D environment.
Meeps can be carnivore and eat other Meeps, herbivore and eat only fruits, or omnivore.
The environment has a day-night cycle of a few minutes and there are fruit trees growing fruits after a time.

The current player is a herbivore Meep. This can be changed in the "environment.py" file at the very bottom.
The map file can be changed in the "main.py" file as the parameter for the World object constructor.

## Controls
If one controllable Meep is set, this one can be controlled with the keyboard.
- w = move forward
- s = move backward
- d = turn right
- a = turn left
- c = carry a rock
- f = attack and eat
- q = Shout on frequency 3
- e = Shout on frequency 4

## Screenshots
### Image of the existing testmap
![Playground Map](screenshots/map_1.PNG)

### Images of raycasting vision
![Raycasting 1](screenshots/raycast_1.PNG)
![Raycasting 2](screenshots/raycast_2.PNG)