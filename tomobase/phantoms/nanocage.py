import os 
import pickle

from ..data import Volume
from ..hooks import phantom_hook


@phantom_hook()
def get_nanocage():
    """
    Creates a nanocage phantom.

    Returns:
        Volume: The created nanocage phantom.
    """
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'nanocage.pkl')
    return Volume(pickle.load(open(path,'rb')))



