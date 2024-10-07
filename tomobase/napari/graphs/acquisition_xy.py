import numpy as np
import plotly.graph_objects as go
import matplotlib

from tomobase.data import Sinogram, Volume

def acquisition_xy_plot(sino: Sinogram, saveas: str = None):
    """Plot the sinogram

    Arguments:
        sinogram (Sinogram)
            The sinogram to plot
        slice (int)
            The slice to plot (default: None)
    """
    
    fig = go.Figure()
    if hasattr(sino, 'time') is False:
        time = np.linspace(1, sino.angles.shape[0], sino.angles.shape[0])
    else:
        time = sino.time
    
    cm = matplotlib.cm.get_cmap('viridis')
    norm_time = (time - np.min(time)) / (np.max(time) - np.min(time))
    colors = [cm(t) for t in norm_time]
    colors = ['rgb({}, {}, {})'.format(int(c[0]*255), int(c[1]*255), int(c[2]*255)) for c in colors]
    
    
    fig.add_trace(go.Scatter(x=time, y=sino.angles, mode='markers+lines', marker=dict(color=colors)))
    
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
    if saveas is not None:
        fig.write_image(saveas)