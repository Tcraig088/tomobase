
import stackview
from tomobase.data import Sinogram, Volume

def imagine(*args):
    nargs = len(args)
    tomotype = None
    if isinstance(args[0], Sinogram):
        tomotype = Sinogram
    elif isinstance(args[0], Volume):
        tomotype = Volume
            
    for arg in args:
        if not isinstance(arg, tomotype):
            raise TypeError("All arguments must be of the same type")
    
    if nargs == 1:
        if isinstance(args[0], Sinogram):
            return stackview.slice(args[0].data)
            
    
        