import os 
import pickle

from ..data import Volume
from ..hooks import phantom_hook


@phantom_hook(name='nanocage')
def get_nanocage():
    """
    Creates a nanocage phantom.

    Returns:
        Volume: The created nanocage phantom.
    """
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'nanocage.pkl')
    return Volume('Nanocage', pickle.load(open(path,'rb')))



