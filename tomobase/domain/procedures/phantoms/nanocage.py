import os 
import pickle

from ....core.data_classes.images import Volume
from ....core import registers

@registers.procedures.register(name="Nanocage", category=registers.categories["Phantoms"])
def get_nanocage():
    """
    Creates a nanocage phantom.

    Returns:
        Volume: The created nanocage phantom.
    """
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'nanocage.pkl')
    return Volume('Nanocage', pickle.load(open(path,'rb')))



