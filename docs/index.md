# Welcome to Tomo Base
![OS](https://img.shields.io/badge/os-Windows%20-lightgray)
![Code](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-yellow)
![License](https://img.shields.io/badge/license-GPL3.0-blue)
![Version](https://img.shields.io/badge/version-v0.0.1-blue)
![Testing](https://img.shields.io/badge/test-Experimental-orange)
![build](https://img.shields.io/badge/tested%20build-Windows%2011%20-orange)

# Description

This is the landing page documentation for Tomo Base. The Tomo Base (tomobase) library is a library of basic tools for scanning transmission electron tomography (STEM). It allows the reconstruction of 3D volume data using the ASTRA Toolbox. The library is designed to allow users to perform allignments, reconstructions, and post processing steps withing a Juypter Notebook. Additionally, tomobase is designed as base library with registration systems to allow for extended functionalities to be built on top of. 

For source code visit [Github](https://github.com/Tcraig088/tomobase). 

## Installation

To install, install [PyQt5](https://google.co.nz) or [PySide2](https://google.co.nz) to use graphical interfaces for file saving and loading. Optionally, all functions within Tomo Base can be accelerated using the [cuda toolkit](https://google.co.nz) and [CUPY](https://google.co.nz). These do not have to be installed though. However, if desired install these libraries before usage.

```bash
conda install pyqt cuda-toolkit=XX.X cupy -c conda-forge
pip install .
```


## License
This code is licensed under GNU general public license version 3.0.





