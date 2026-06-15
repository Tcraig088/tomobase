# Getting Started

```{toctree}
:hidden:
:maxdepth: 1
```

## Overview

TomoBase is primarily a plugin system for attaching functionality to a STEM workflow. To achieve this goal, TomoBase utilizes a sytem of registers. Each register is essentially a mapped dictionary with additional convienence functions. 
Because a register is allowed to modify an added member, TomoBase must be initialized before using functions, classes and members added to a registers. As a result the library is divided into three parts:

| Module |  Description |
|------|-------------|
| Core | Core system functionality. Anything that can be used without initialization |
| Domain | Built-in tomography tools and data classes. <br>Useful if you just want to run a tomography experiment. |
| Backend | Visualization tools for viewing your data with Jupyter or Qt. <br> To prevent bloat, QT and Jupyter tools are only imported upon initialization.|


## Registers

The primary prebuilt registers are found in the following table. These are not every registry found in Tomobase, just the basic ones required for running tomography experiments. More information can be found in the tutorials and apis.

| Register |  Description |
|------|-------------|
| images (x1) | Includes image datatypes e.g. Image, Sinogram, Volume  <span style="color:red"><br>(x1)Currently named image_types</span>|
| tiltschemes | Basic tiltschemes |
| measurements (x2) | Includes a measurement datatypes <br>(x2) Currently Measurements works but not been added to a register |
| procedures | Includes procedures for modifying or analyzing image data |
| modules (x3) | Includes functions to import CUPY/NUMPY Specific modules <br>(x3)Functions included in utils but not registered |

To add an item to a registry, just include the register method at the top of the function or class you wish to register

```python
from tomobase.core import registers

# basic median subtraction
@registers.procedures.register()
def func(image):
    median = image.xr.median()
    image.xr = image.xr.where(image.xr >= median, 0)
    return image
```

This can then be used after initialization as follows. (x4) New functions can be added after registration 

```python
import tomobase
from tomobase.core import registers

tomobase.bootstrap() #initialize tomobase. 
# use qt_enabled or jupyter_enabled==True to initialize either.

image = registers.procedures.phantoms.nanocage()
image = registers.procedures.func(image)

# x5 the procedures registry is currently hierarchical but doesnt use hierarchical setters (use phantoms register instead)
image = registers.phantoms.nanocage()
image = registers.procedures.func(image)
```


## Procedures

One advantage of the registry system is that functions can be modified on initialization. This is best exemplified in the procedures registry, which uses function decoration to discretely handle memory management tasks. A function added to the procedures registry has the form

```python
from tomobase.core import registers

# basic median subtraction
@registers.procedures.register()
def func(args, kwargs):
    # do stuff
    return return_value1, return_value2
```

upon modification the function has the following form

```python
from tomobase.core import registers

def func(args, 
        kwargs, 
        inplace:bool, 
        verbose_outputs:bool, 
        measurements:list|None, 
        proxy:EnvironmentContext, 
        restore_context:bool):
    # do stuff
    return return_value1, return_value2
```

Inplace: if set to True the data is overridden with the result.
verbose_outputs: Only the first return result is provided, unless more diagnostic information is required.
measurements: If a list of Measurements is supplied measurements are provided to the nearest

## Context Management
There are two global settings that control how procedures are executed in Tomobase. proxy, and logger. They can be set as follows

```python
import tomobase
from tomobase.core.environment import GPUContext
tomobase.bootstrap()

tomobase.logger.setLevel(logging.VERBOSE)
tomobase.proxy.set_context(GPUContext.CUPY) # Set to GPUContext.NUMPY by default
```

The logger is an extended variant of the python logging module which controls the log level of tasks executed in TomoBase. For non-developement usage, their are three log levels of interest. 

- Warning (logging.warning):  Silences everything short of operational anomalies
- Info (logging.info): Shows basic messages.
- Verbose (logging.verbose): Shows intermediary steps.

By default data classes such as images are set to use NUMPY, when a procedure is applied to them, inputs are switched to the global context. Once execution is complete, the context is switched back to NUMPY for all inputs and returns. This behaviour can be overridden, for instance, when used in a with statement, all procedures are executed within the provided context. The final results are switched back to the CPU on exit.

```python
with proxy as ctx
    image = registers.procedures.phantoms.nanocage()
    image = registers.procedures.background_correct_median()
```


The default global context can be overriden by supplying a different context. This is useful for distributed tasks where you may want to use different settings to the global default.

```python
with EnvironmentContext(GPUContext.CUPY, devide=1) as ctx
    image = registers.procedures.phantoms.nanocage()
    image = registers.procedures.background_correct_median()
```

## Abstract Classes

For type hinting, and constructing datatypes there are a number of abstract classes.