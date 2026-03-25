from ...core import registers

# These registers are exclusively used for storing knowledge about the Qt backend
images = registers.Registry(str, object)
tilts = registers.Registry(str, object)
measurements = registers.Registry(str, object)
controller_pairs = registers.Registry(str, tuple)
magic_widgets = registers.Registry(str, tuple)
