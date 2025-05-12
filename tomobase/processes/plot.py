import logging
import time
import progressbar
from qtpy.QtCore import QObject, Signal

from tomobase.registrations.base import ItemDictNonSingleton, ItemDict, Item
from tomobase.registrations.environment import xp

import plotly.graph_objects as go


def concatenate(df, *args, **kwargs):
    df = xp.df.DataFrame({})
    for arg in args:
        if df.metadata['data type'] == arg.metadata['data type']:
            if df.metadata['plot type'] != 'line':
                # add the new rows to the dataframe
                df = xp.df.concat([df, arg], axis=0)
            else:
                # add the new columns to the dataframe
                df = xp.df.concat([df, arg], axis=1)
        else:
            pass


def plot(df, fig_properties={}, plot_properties={}, **kwargs):
    width = fig_properties.get('width', 800)
    height = fig_properties.get('height', 800)
    autosize = fig_properties.get('autosize', True)
    fig = go.Figure()
    #make figure square
    fig.update_layout(autosize=autosize, width=width, height=height **fig_properties)
    
    if df.metadata['plot type'] == 'projection':
        istime = kwargs.get('istime', False)
        j = 0
        for i, col in enumerate(df.columns):
            if istime and j == 1:
                x_col = col
            if not istime and j == 0:
                x_col = col
            if j == 2:
                name = col.name
                y_col = col
                j = -1
            
            j+=1 
            fig.add_trace(go.Scatter(x=x_col, y=y_col, name=name, **plot_properties))
    
    elif df.metadata['plot type'] == 'line':
        j = 0
        for i, col in enumerate(df.columns):
            if j == 0:
                x_col = col
            if j == 1:
                name = col.name
                y_col = col
                j = -1

            j+=1
            fig.add_trace(go.Scatter(x=df.index, y=y_col, name=name, **plot_properties))

    elif df.metadata['plot type'] == 'bar':
        x_col = df.iloc[:, 0]  # First column for names
        y_col = df.iloc[:, 1]  # Second column for values
        fig.add_trace(go.Bar(x=x_col, y=y_col, **plot_properties))

    elif df.metadata['plot type'] == 'histogram':
        x_col = df.iloc[:, 0]
        y_col = df.iloc[:, 1]
        fig.add_trace(go.Histogram(x=x_col, y=y_col, **plot_properties))

    elif df.metadata['plot type'] == 'heatmap':
        pass

    return fig


        
