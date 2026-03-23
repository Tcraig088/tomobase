
from ..data import Sinogram
from ..tiltschemes import TiltScheme
from typing import Union

import holoviews as hv
import numpy as np


#testing commits 
def plot_tiltscheme(tilt: Union[Sinogram, TiltScheme], **kwargs):
# ----- radial spokes -----

    if isinstance(tilt, Sinogram):
        angles = tilt.data.coords['angle'].values
        times = tilt.data.coords['time'].values
        indices = tilt.data.coords['projections'].values

    else:
        angles = tilt.angles
        times = np.arange(len(angles))
        indices = np.arange(len(angles))


    length = 1
    curves = []

    for a in angles:
        theta = np.deg2rad(a)
        x = [0, length*np.sin(theta)]
        y = [0, length*np.cos(theta)]
        curves.append(hv.Curve((x, y)))

    spokes = hv.Overlay(curves)


    theta = np.linspace(-np.pi/2, np.pi/2, 200)
    arc = hv.Curve((np.sin(theta), np.cos(theta)))

    radial = (arc * spokes).opts(
        width=400,
        height=400,
        xlim=(-1.1, 1.1),
        ylim=(-0.1, 1.1),
        aspect='equal',
        title="Tilt Geometry"
    )

    xy = (
        hv.Curve((indices, angles))
        * hv.Scatter((indices, angles))
    ).opts(
        width=400,
        height=400,
        xlabel="Projection Index",
        ylabel="Angle (deg)",
        show_grid=True
    )

    return (radial + xy)