
from ..base_classes.registers import Registry, HierarchicalRegistry
from ..log import logger
from colorama import Fore, Style, init
init(autoreset=True)

categories = HierarchicalRegistry(str, int)

categories.add_hierarchy('Acquistion', value=60)
categories.add_hierarchy('Tomography', value=68)
categories.add_hierarchy('Visualization', value=76)

categories.add_hierarchy("Deform", value=60, parent = 'Tomography')
categories.add_hierarchy("Image Processing", value=64, parent= 'Tomography')
categories.add_hierarchy("Align", value=68, parent = 'Tomography')
categories.add_hierarchy("Reconstruct", value=72, parent = 'Tomography')
categories.add_hierarchy("Project", value=76, parent = 'Tomography')
categories.add_hierarchy("Segment", value=80, parent='Tomography')
categories.add_hierarchy("Analyze", value=84, parent='Tomography')

