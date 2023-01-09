# HydroDataVisualiser
This repository contains the HydroDataVisualiser, a library/tool adding support 
for advanced hydrological data visualisation.

This project was developed as part of [WATERLINE Project](http:/www.waterlineproject.eu/)

The library offers user several functions to assist him in his work:

* empty_map - Creates empty map, ready to add layers and other modifications
* add_tiff - Adds visualisation of a geospatial raster, supplied by the user to the map
* add_geojson - Adds visualisation of geojson files to the map
* add_split_map - Adds a [Split Map](https://ipyleaflet.readthedocs.io/en/latest/controls/split_map_control.html) functionality, for two rasters provided by the user
* prepare_raster_series - Creates raster series from user data that can be used to add animation to the map
* add_animation_from_raster_series - Adds animation to the map based on the raster series provided by the previous function
* add_pins_and_widgets - Allows to visualise groups of points on the map
* create_dataframe - Allows user to create dataframes with custom data, by using interactive maps
* create_dataframe_polygons - Allows user to create dataframes containing series of shapes, by using interactive maps

# Demo
![](./docs/demo.gif)
