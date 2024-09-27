# TomoBase
![OS](https://img.shields.io/badge/os-Windows%20|%20Linux-lightgray)
![Code](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-yellow)
![License](https://img.shields.io/badge/license-GPL3.0-blue)
![Version](https://img.shields.io/badge/version-v0.0.1-blue)
![Testing](https://img.shields.io/badge/test-Experimental-orange)
![build](https://img.shields.io/badge/tested%20build-Windows%2011%20|%20Ubuntu%2024.04-orange)

## Table of Contents

 - **Overview**
   - [**Section 1. Description**](#1-description)
   - [**Section 2. Installation**](#2-installation)
   - [**Section 3. Usage**](#3-usage)
   - [**Section 3. License**](#4-license)
  
## 1. Description

The TomoBase (tomobase) library is a library of basic tools for scanning transmission electron tomography (STEM). It allows the reconstruction of 3D volume data using the ASTRA Toolbox. The library is designed to allow users to perform allignments, reconstructions, and post processing steps withing a Juypter Notebook. Additionally, tomobase is part of the [Time-Depenedent Tomography](https://google.co.nz) library. As such, it has additional components to be used for common datatypes and processes with the other libraries.

## 2. Installation

Tomobase is a conda installable library. Tomobase has some optional dependencies that are not entirely necessary but do allow users to use additional functions which may be disabled when not installed. These include:

1. [PyQt5](https://google.co.nz) **or** [PySide2](https://google.co.nz): a graphical user interface backend. 
2. [Qtpy:](https://google.co.nz) A wrapper for the gui backend
3. [HyperSpy:](https://google.co.nz) A library for handling microscopy & spectroscopy data. 

```bash

conda install tdtomonapari cudatoolkit=X.X pyqt -c TCraig088 -c conda-forge
```

Equally, the tdtomonapari can be installed through the Napari Plugins Market.

## 3. Usage
To use the library open Napari and Select Time-Dependent Tomography from the plugins window. 

## 4. License
This code is licensed under GNU general public license version 3.0.



