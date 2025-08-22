# API References

## Top Level Module

## Globals
This module contains registries that store data, functions or classes. Useful for registering items within this library or libraries built on Tomo Base. 

::: tomobase.globals
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
      show_submodules: false
      members:
        - GPUContext
        - xp
        - logger
        - ItemDictNonSingleton
        - ItemDict
        - Item
        - TOMOBASE_TRANSFORM_CATEGORIES
        - TOMOBASE_PROCESSES
        - TOMOBASE_DATATYPES
        - TOMOBASE_TILTSCHEMES
        - TOMOBASE_PHANTOMS
      members_order: source
      separate_signature: true
      inherited_members: false
      docstring_style: google   # or "numpy"
      filters:
        - "!^_"   



## Data
The Data module contains the data types supported by the Tomo Base library. Each module is registered with an id stored in TOMOBASE_DATATYPES in the global registers.

::: tomobase.data
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
      show_submodules: false
      members:
        - Data
        - Image
        - Sinogram
        - Volume
      members_order: source
      separate_signature: true
      inherited_members: false
      docstring_style: google   # or "numpy"
      filters:
        - "!^_"   

## Phantoms 
The phantoms functions are functions which generate a Volume class for sample data. Registered globally to the TOMOBASE_PHANTOMS register. To register a phantom to the library use the phantom_hook function. 

::: tomobase.phantoms
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
      show_submodules: true
      members:
       - get_nanocage
       - get_nanorod
       - get_nanocube
      members_order: source
      separate_signature: true
      inherited_members: true
      filters:
        - "!^_" 

## Tilt Schemes
This module contains classes used to implement a tilt scheme. Registered with TOMOBASE_TILTSCHEMES and added to the registration by using the decorator tiltscheme_hook.

::: tomobase.tiltschemes
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
      show_submodules: true
      members:
       - TiltScheme
       - Incremental
       - Binary
       - GRS
      members_order: source
      separate_signature: true
      inherited_members: true
      filters:
        - "!^_" 



## Hooks 
::: tomobase.hooks
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
      show_submodules: true
      members_order: source
      separate_signature: true
      inherited_members: true
      docstring_style: google   # or "numpy"
      filters:
        - "!^_"   

## Processes
::: tomobase.processes
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
      show_submodules: true
      members_order: source
      separate_signature: true
      inherited_members: true
      docstring_style: google   # or "numpy"
      filters:
        - "!^_"   