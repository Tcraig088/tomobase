import numpy as np
import plotly.graph_objects as go
import matplotlib

from tomobase.data import Sinogram, Volume


def acquisition_radial_plot(sino: Sinogram):
    """Plot the sinogram in a radial half-circle

    Arguments:
        sinogram (Sinogram)
            The sinogram to plot
    """

    traces = []
    for angle in sino.angles:
        traces.append(go.Scatterpolar(
            r=[0,1],
            theta=[0, angle],
            mode='lines',
            line=dict(color='black')
        ))
    layout = go.Layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        polar=dict(
            sector = [0,180],
            radialaxis=dict(
                visible=False,
                range=[0, 1],
                showline=False,
            ),
            angularaxis=dict(
                rotation= 90,
                showline=True,
                linewidth=2,
                linecolor='black',
                ticks='outside',
                tickwidth=2,
                tickcolor='black',
                ticklen=5,
                thetaunit='degrees',
                dtick=30, 
            )
        ),
        autosize=False,
        width=600,
        height=600
    )
    fig = go.Figure(data=traces, layout=layout)

    fig.show()
