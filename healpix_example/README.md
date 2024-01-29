# FESOM Data on HEALPix Grid
 This folder contains jupyter notebooks with examples for processing and quick visualisation of FESOM data (initially on an unstructured mesh) on a [HEALPix](https://healpix.sourceforge.io/) (Hierarchical Equal Area isoLatitude Pixelation of a sphere) grid. 

### References
 - [healpy tutorial](https://healpy.readthedocs.io/en/latest/index.html)
 - [nextGEMS HEALPix output data processing](https://easy.gems.dkrz.de/Processing/healpix/index.html) 
## FESOM_to_HEALPix.ipynb
### Contents
 - #### supporting functions:
     - load_mesh - loading mesh from FESOM2 (from [fint](https://github.com/FESOM/fint))
     - create_healpix_grid - creating the healpix grid based on unstructured mesh 
     - nnshow an worldmap - support the plotting of healpix data (based on [plotting with cartopy](https://easy.gems.dkrz.de/Processing/healpix/healpix_cartopy.html))
 - #### main functions:
     - to_healpix - Converts FESOM data to Healpix grid
     - plot_healpix - Plots the converted Healpix data

### How to use
 - #### Provide the path to the data and mesh
 Modify the MESH and DATA variables:
```python
MESH = '/work/ab0995/a270088/meshes/FORCA12/'
DATA = '/work/ab0995/a270088/sisters/runs/F12/temp.fesom.2010.nc'
```
```python
lon, lat, elem = load_mesh(MESH)
data = xr.open_dataset(DATA)
variable_name = list(data.data_vars)[0]
data = data[variable_name]
```
 - #### Converts FESOM data to Healpix grid
     The function determines the resolution of the Healpix grid based on the 'zoom' parameter, where higher 'zoom' values yield higher resolution grids.
 
     NOTE: conversion will take more time when the number of healpix grid data points (with higer zoom level) is greater than the original dataset (due to the interpolation process). The default time and depth index of the data to be converted is 0.
```python 
data_healpix,sel_time,sel_depth = to_healpix(data, lon,lat, zoom = 8)
```
 - #### Plots data on a Healpix grid with various customization options
 As a bare minimum, you should provide data_healpix - data on a Healpix grid, which we got in a previous step:
```python
plot_healpix(data_healpix)
```
 - #### Interactive visualisation
HEALpy allows to make quick and nice interactive visualisation using [zoomtool](https://healpy.readthedocs.io/en/latest/healpy_zoomtool.html). You can use it with the plot_healpix:
```python
plot_healpix(data_healpix, interactive = True)
```
![](https://github.com/FESOM/FESOM_examples/assets/80640421/c59c9387-b744-4bd6-bedb-008d6a08cfd4)


## healpix_data_processing.ipynb
This jupyter notebook shows how to interpolate FESOM data into HEALPix grid using Climate Data Operators (CDO)

Before we do CDO interpolation, we need to do some preprocessing - define land masks for the surface and each depth level

Then, we use the subprocess Python package in order to run CDO in a loop:
  - remapnn, hpzZ - nearest neighbor on HEALPix grid, Z is the zoom level (from 0 to 9)
  - setgrid - sets the grid to our source file
  - last two files are input on FESOM grid and output file.

```python
gridfile = 'core2_old_griddes_nodes_IFS.nc'
original_file = 'temp_and_mask.nc'
for z in range(0,10):
    output_file = f'temp_and_mask_hp{z}zoom.nc'

    command = [
        "cdo",
        f"-remapnn,hpz{z}",
        f"-setgrid,{gridfile}",
        f"{original_file}",
        f"{output_file}"
    ]

    # Execute the command
    subprocess.run(command)
```
The get_mask function from [pyfesom2](https://github.com/FESOM/pyfesom2/tree/main) was implemented to do calculations for specific regions on HEALPix grid
```python
mask1 = get_mask(lon_healpy,lat_healpy, "Atlantic_Basin")
depth = 0
time = 5
data_healpix = ds.temp.isel(time=time,nz1=depth).where(ocean(ds,depth)).where(mask1)
plot_healpix(data_healpix,cbar = True,vmin = -2, vmax = 28)
```
![image](https://github.com/FESOM/FESOM_examples/assets/80640421/cb9676d6-76ad-4d30-b55e-bc76a9f3bdff)


### Authors

Boris Shapkin, Nikolay Koldunov.
