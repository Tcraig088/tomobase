import skimage
import copy
import numpy as np

from tomobase.data import Volume
from qtpy.QtWidgets import QDoubleSpinBox, QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QWidget, QFrame, QGridLayout, QPushButton, QSpinBox, QDialog
from PyQt5.QtCore import Qt

"""
from ......tomondt.tomondt.plugins.decorators import *
from ......tomondt.tomondt.utils.context import device_context
if device_context.availability.cupy:
    import cupy as cp
    from cupyx.scipy import ndimage as scicp
"""

def _knockon(volume,knockon):
    mask = (volume != 0).astype(int)
    pmask = skimage.filters.gaussian(mask, 1)
    #pmask = scicp.gaussian_filter(mask, 1)
    mask_interior = np.zeros(volume.shape,bool)
    #mask_interior = cp.zeros(obj.shape,bool)
    mask_interior[pmask>0.999]=1
    pmask = np.power(knockon, pmask*(27/3))
    #pmask = cp.power(ko, pmask*(27/3))
    seed = np.random.rand(volume.shape[0],volume.shape[1],volume.shape[2])
    #seed = cp.random.rand(obj.shape[0],obj.shape[1],obj.shape[2])
    mask[pmask>seed] = skimage.morphology.binary_erosion(mask[pmask>seed])
    #mask[pmask>seed] = scicp.binary_erosion(mask[pmask>seed])
    mask[mask_interior]= 1
    volume = volume*mask
    return volume

def _deform(volume, deform):
    sig = 5
    if iscupy:
        coord = cp.indices(obj.shape)
        seed = cp.random.rand(3, obj.shape[0],obj.shape[1], obj.shape[2])
        seed = (seed*2)-1
        seed_list = [scicp.gaussian_filter(seed[i,:,:,:].squeeze(),sig) for i in range(3)]
        amplitude = cp.sqrt((seed_list[0]**2)+(seed_list[1]**2)+(seed_list[2]**2))
    else:
        coord = np.indices(obj.shape)
        seed = np.random.rand(3, obj.shape[0],obj.shape[1], obj.shape[2])
        seed = (seed*2)-1
        seed_list = [skimage.filters.gaussian(seed[i,:,:,:].squeeze(),sig) for i in range(3)]
        amplitude = np.sqrt((seed_list[0]**2)+(seed_list[1]**2)+(seed_list[2]**2))
    for i in range(3):
        seed[i,:,:,:] =(deform*seed_list[i])
    coord = seed+coord
    if iscupy:
        obj = scicp.map_coordinates(obj, coord, order=1)
    else:
        obj = skimage.transform.warp(obj,coord)
    return obj

#@tomobase_hook_process(name='Subtract Median', category=TOMOBASE_TRANSFORM_CATEGORIES.DEFORM.value(), subcategories=_subcategories)
def  beamdamage(volume:Volume, knockon:float=0.01, elasticdeform=0.1):
    obj = _knockon(obj, knockon)
    obj = _deform(obj, elasticdeform)
    return obj




