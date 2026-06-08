# API References

## Top Level Module

## Core
This module contains registries that store data, functions or classes. Useful for registering items within this library or libraries built on Tomo Base. 

::: tomobase.core
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true
      members:
        - logger
        - progress
  

### Registers
::: tomobase.core.registers
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true
      members:
        - image_types
        - tiltschemes
        - phantoms
        - procedures
        - categories
        - Registry
        - HierarchicalRegistry



### Environment
::: tomobase.core.environment
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true
      members:
        - get_xp
        - GPUContext
        - proxy
        - EnvironmentContext
  

### Base Classes
::: tomobase.core.base_classes
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true
      members:
        - BaseDataModel
        - BaseMeasurementModel
        - ImageAbstract
        - MeasurementAbstract
        - TiltSchemeAbstract
        - TiltSchemeCursor


### Data Classes
::: tomobase.core.data_classes
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 5
      show_submodules: true
      members:
        - Coordinate
        - Measurement

#### Images
::: tomobase.core.data_classes.images
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 5
      show_submodules: true
      members:
        - Image
        - Sinogram
        - Volume


#### TiltSchemes
::: tomobase.core.data_classes.tiltschemes
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 5
      show_submodules: true
      members:
        - Incremental
        - GRS
        - BD


## Domain
### Phantoms
::: tomobase.domain.phantoms
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 4
      show_submodules: true
      members:
        - get_nanocage
        - get_nanorod
        - get_nanocube

### Procedures
#### Alignments
::: tomobase.domain.procedures
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 5
      show_submodules: true
      members:
        - align_sinogram_center_of_mass
        - align_sinogram_xcorr
        - align_tilt_axis_rotation
        - align_tilt_axis_shift

#### Image Processing
::: tomobase.domain.procedures
    handler: python
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 5
      show_submodules: true
      members:
        - bin
        - normalize
        - background_subtract_median
        - pad_sinogram
        - gaussian_filter
        - poisson_noise
        - rotational_misalignment
        - translational_misalignment