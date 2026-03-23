import os 
import pickle

from ..data import Volume
from ..core import registers

@registers.phantoms.register(name='Nanocage')
def get_nanocage():
    """
    Creates a nanocage phantom.

    Returns:
        Volume: The created nanocage phantom.
    """
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'nanocage.pkl')
    return Volume('Nanocage', pickle.load(open(path,'rb')))



