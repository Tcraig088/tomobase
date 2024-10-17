import numpy as np
import plotly.graph_objects as go
import matplotlib

from tomobase.data import Sinogram, Volume

def acquisition_xy_plot(angles1, angles2, angles3):
    """Plot the sinogram

    Arguments:
        sinogram (Sinogram)
            The sinogram to plot
        slice (int)
            The slice to plot (default: None)
    """
    
    fig = go.Figure()

    
    time1 = np.linspace(1, angles1.shape[0], angles1.shape[0])
    time2 = np.linspace(1, angles2.shape[0], angles2.shape[0])
    time3 = np.linspace(1, angles3.shape[0], angles3.shape[0])
    
    cm = matplotlib.cm.get_cmap('viridis')
    norm_time = (time1 - np.min(time1)) / (np.max(time1) - np.min(time1))
    colors = [cm(t) for t in norm_time]
    colors = ['rgb({}, {}, {})'.format(int(c[0]*255), int(c[1]*255), int(c[2]*255)) for c in colors]
    
    
    fig.add_trace(go.Scatter(x=time1, y=angles1, mode='lines'))

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            ticks='outside',
            tickwidth=2,
            tickcolor='black',
            ticklen=5,
            title='Time'
        ),
        yaxis=dict(
            range = [-90, 90],
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            ticks='outside',
            tickwidth=2,
            tickcolor='black',
            ticklen=5,
            title='Angles'
        ),
        autosize=False,
        width=600,  # Set the width of the plot
        height=600  # Set the height of the plot to be equal to the width
        )
    
    
    fig.show()
    return fig