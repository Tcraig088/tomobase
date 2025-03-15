import numpy as np


from tomobase.tiltschemes.tiltscheme import TiltScheme
from tomobase.hooks import tomobase_hook_tiltscheme
from ipywidgets import widgets
from IPython.display import display
from tomobase.log import logger



    
@tomobase_hook_tiltscheme('BINARY')  
class Binary(TiltScheme):
    """Binary Tilt Scheme Class.
    The purpose of this class is to calculate angles using the binary acquisition tilt scheme.


    Attributes:
        angle_min (float): The minimum angle in the tilt series.
        angle_max (float): The maximum angle in the tilt series.
        k (int): The number of angles in one subdivision of the tiltscheme.
        isbidirectional (bool): Default is True. Determines wether the tiltscheme is calculated performed by going unidirectionally negative to positve.
            If true the tiltscheme will be calculated bidirectionally. The first k angles are collected from min to max but and reversed in next k angles.
            If false the tiltscheme will be calculated unidirectionally min to max for all sets of 8 angles.
    """
    def __init__(self, angle_min:float=-70, angle_max:float=70, k:int=8, isbidirectional:bool=True):
        super().__init__()
        self.angle_max = angle_max
        self.angle_min = angle_min
        self.k = k
        
        #Setting parameters
        self.isbidirectional = isbidirectional
        if isbidirectional:
            self.isforward=True
        
        self.step = (self.angle_max - self.angle_min)/(k+0.5)
        self.i = 0
        self.offset = 0
        self.offset_set = 2
        self.offset_run = 1/self.offset_set
        self.angle = 0
        self.max_cutoff = self.angle_max - (self.step/2)
        
    def get_angle(self):
        if self.isbidirectional:
            return self._get_angle_bidirectional()
        else:
            return self._get_angle_unidirectional() 
    
    def _get_angle_bidirectional(self):
        if self.i == 0:
            self.angle = self.angle_min
        elif self.isforward:
            if np.isclose(self.angle + self.step, self.angle_max) or (self.angle+self.step) > self.angle_max:
                self._get_offsets()
                self.isforward = False
                if np.isclose(self.max_cutoff + (self.step*self.offset), self.angle_max) or (self.max_cutoff + (self.step*self.offset)) >=  self.angle_max:
                    self.angle = self.max_cutoff + (self.step*self.offset) - self.step
                else:
                    self.angle = self.max_cutoff + (self.step*self.offset)
                self.step *= -1 
            else:
                self.angle = self.angle + self.step
        else:
            if np.isclose(self.angle+self.step, self.angle_max) or (self.angle+self.step) < self.angle_min:
                self._get_offsets()
                self.isforward = True
                self.angle = self.angle_min + (np.abs(self.step)*self.offset)
                self.step *= -1
            else:
                self.angle = self.angle + self.step
        self.i += 1
        return np.round(self.angle,2)
    
    
    def _get_angle_unidirectional(self):
        if self.i == 0:
            self.angle = self.angle_min
        elif np.isclose(self.angle + self.step, self.angle_max) or (self.angle + self.step) > self.angle_max:
            self._get_offsets()
            self.angle = self.angle_min + (self.step * self.offset)
        else:
            self.angle += self.step
        self.i += 1
        return np.round(self.angle, 2)
    
    def _get_offsets(self):
        if (self.offset + 0.5) >= 1:
            if self.offset == ((self.offset_set-1)/(self.offset_set)):
                self.offset_set = self.offset_set*2
                self.offset_run = 1/self.offset_set
                self.offset = self.offset_run
            else:
                self.offset_run += 2/self.offset_set
                self.offset = self.offset_run
        else:
            self.offset += 0.5  
            
    def get_angle_array(self, indices):
        return super().get_angle_array(indices)
    
    @staticmethod
    def TiltSchemeWidget():
        widget_max = widgets.FloatText(value=70, description='angle_max')
        widget_min = widgets.FloatText(value=70, description='angle_min')
        widget_k = widgets.IntText(value=8, description='k')
        widget_bidirectional = widgets.Checkbox(value=True, description='bidirectional')
        widget = widgets.HBox([widget_max, widget_min, widget_k, widget_bidirectional])
        return widget
    
    @classmethod
    def parsewidget(cls, widget):
        _dict = {
            'angle_max': widget.children[0].value,
            'angle_min': widget.children[1].value,
            'k': widget.children[2].value,
            'isbidirectional': widget.children[3].value
        }
        return cls(**_dict)