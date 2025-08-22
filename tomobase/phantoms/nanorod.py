import numpy as np
from ..data import Volume
from ..hooks import phantom_hook

from magicgui import magicgui
from magicgui.tqdm import trange, tqdm

@phantom_hook()
def get_nanorod(dim:int=512,length:int=300,radius:int=100,proportion:float=0.5,intensity:float=0.3):
    """Creates a nanorod phantom.

    Args:
        dim (int, optional): The dimension of the volume. Defaults to 512.
        length (int, optional): The length of the rod. Defaults to 300.
        radius (int, optional): The radius of the rod. Defaults to 100.
        proportion (float, optional): The proportion of the rod's radius to its length. Defaults to 0.5.
        intensity (float, optional): The intensity of the rod. Defaults to 0.3.

    Returns:
        Volume: The created nanorod phantom.
    """
    pradius = 2*(radius/dim)
    obj = np.zeros((dim,dim,dim),dtype=np.float32)
    img = np.zeros((dim,dim),dtype=np.float32)
    x = np.linspace(-1, 1, dim)
    y = np.linspace(-1, 1, dim)
    z = np.linspace(-1, 1, dim)

    X, Y = np.meshgrid(x, y)
    disk1= (X**2 + Y**2) <= pradius**2
    dissk2 = (X**2 + Y**2) <= (pradius*proportion)**2
    img[disk1>0] = intensity
    img[dissk2>0] = 1

    L = length - 2*radius

    z1, z2 = dim//2 - L//2, dim//2 + L//2
    for i in tqdm(range(dim), label="building nanorod slice by slice"):
        if i >= z1 and i <= z2:
            obj[:,:,i] = img

    sphere = np.zeros((dim,dim,dim),dtype=np.float32)
    X,Y,Z = np.meshgrid(x,y,z)
    sphere1 = (X**2 + Y**2 + Z**2) <= pradius**2
    a,b,c = pradius*proportion, pradius*proportion, pradius
    sphere2 = ((X**2)/(a**2) + (Y**2)/(b**2) + (Z**2)/(c**2)) <= 1
    sphere[sphere1>0] = intensity
    sphere[sphere2>0] = 1

    y1,y2 = dim//2 + radius, dim//2 - radius
    xz1,xz2 = dim//2 - radius, dim//2 + radius
    top_limit,bottom_limit  = z2+radius, z1-radius
    obj[xz1:xz2, xz1:xz2, z2:top_limit] = sphere[xz1:xz2, xz1:xz2, dim//2:y1] 
    obj[xz1:xz2, xz1:xz2, bottom_limit:z1] = sphere[xz1:xz2, xz1:xz2, y2:dim//2]
    return Volume(obj)
