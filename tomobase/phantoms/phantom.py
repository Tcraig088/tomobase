import numpy as np
import numpy as np
import matplotlib.pyplot as plt
import enum

from . import load_cube, load_cage, load_rod
# Enum for the phantoms with string names
class Phantom(enum.Enum):
    Cube = 'cube'
    Cage = 'cage'
    Rod = 'rod'

# Function to get list of phantom display names 
def get_phantoms_list():
    return [phantom.name for phantom in Phantom]

#loads phantom depernding on the name given
def load_phantom(phantom,*args):
    match phantom:
        case 'cube':
            return load_cube(*args)
        case 'cage':
            return load_cage()
        case 'rod':
            return load_rod(*args)
        case _:
            raise ValueError('No phantom with this name exists')

