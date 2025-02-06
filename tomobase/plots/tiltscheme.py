import numpy as np
import plotly.graph_objects as go
import matplotlib

from tomobase.data import Sinogram, Volume


def acquisition_radial_plot(**kwargs):
    """Plot the sinogram in a radial half-circle

    Arguments:
        sinogram (Sinogram)
            The sinogram to plot
    """

    sino = kwargs.get('sinogram', None)
    angles = kwargs.get('angles', None)
    start = kwargs.get('start', None)
    frame = kwargs.get('frame', None)
    times = kwargs.get('times', None)
    
    if sino is None:
        if angles is None:
            raise ValueError('Either a Sinogram or a list of angles should be provided.')
    elif hasattr(sino, 'times'):
        times = sino.times
        
    if times is None:
        time = np.linspace(1, angles.shape[0], angles.shape[0])
        time_title = 'Time (s)'
    else:
        time = sino.time
        time_title = 'Projections'
    
    cm = matplotlib.cm.get_cmap('viridis')
    norm_time = (time - np.min(time)) / (np.max(time) - np.min(time))
    colors = [cm(t) for t in norm_time]
    colors = ['rgb({}, {}, {})'.format(int(c[0]*255), int(c[1]*255), int(c[2]*255)) for c in colors]
    traces = []
    
   # Add a scatter plot for the colorbar
    colorbar_trace = go.Scatter(
        x=[None], y=[None],  # Dummy data
        mode='markers',
        marker=dict(
            colorscale='Viridis',
            cmin=np.min(time),
            cmax=np.max(time),
            colorbar=dict(
                title=time_title,
                titleside='bottom',
                orientation='h',
                x=0.5,
                y=-0.3,
                xanchor='center',
                yanchor='top'
            )
        ),
        showlegend=False
    )
    if start is not None and frame is not None:
        angles = angles[start:start+frame]

    # append 0 at start and end of radia
    radia = np.ones(100)
    radia = np.insert(radia, 0, 0)
    radia = np.append(radia, 0) 
    theta = np.linspace(-90, -70, 100) 
    theta = np.insert(theta, 0, 0)
    theta = np.append(theta, 0)
    traces.append(go.Scatterpolar(
        r=radia,
        theta=theta,
        mode='lines',
        fill='toself',
        line=dict(color='black'),
        showlegend=False
    ))
    
    theta = np.linspace(90, 70, 100) 
    theta = np.insert(theta, 0, 0)
    theta = np.append(theta, 0)
    traces.append(go.Scatterpolar(
        r=radia,
        theta=theta,
        mode='lines',
        fill='toself',
        line=dict(color='black'),
        showlegend=False
    ))
    
    theta = np.linspace(-70,np.min(angles), 100) 
    theta = np.insert(theta, 0, 0)
    theta = np.append(theta, 0)
    traces.append(go.Scatterpolar(
        r=radia,
        theta=theta,
        mode='lines',
        fill='toself',
        line=dict(color='grey'),
        showlegend=False
    ))
    
    theta = np.linspace(70,np.max(angles), 100) 
    theta = np.insert(theta, 0, 0)
    theta = np.append(theta, 0)
    traces.append(go.Scatterpolar(
        r=radia,
        theta=theta,
        mode='lines',
        fill='toself',
        line=dict(color='grey'),
        showlegend=False
    ))  
    
    for index, angle in enumerate(angles):
        traces.append(go.Scatterpolar(
            r=[0,1],
            theta=[0, angle],
            mode='lines',
            line=dict(color=colors[index]),
            showlegend=False
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
        xaxis=dict(visible=False),  # Hide x-axis
        yaxis=dict(visible=False), 
        autosize=False,
        width=600,
        height=600
    )
    fig = go.Figure(data=traces+ [colorbar_trace], layout=layout)

    fig.show()
    return fig