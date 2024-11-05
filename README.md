# DEM Web Based Visualisation Tool

This project provides a cross-platform, lightweight solution for visualizing the lunar surface using data from the Tiff Files (Like DEM Data from Chandrayan 2 Mission). It employs geospatial data processing and 3D rendering to create an interactive and accurate representation of the lunar terrain.

## Table of Contents

- [Overview](#overview)
- [Technologies Used](#technologies-used)
- [Approach](#approach)


## Overview

This tool visualizes the lunar surface by processing and rendering high-resolution GeoTIFF data into a 3D terrain model. By leveraging the capabilities of GDAL, Flask, and Three.js, we provide users with an interactive experience where they can explore the lunar landscape under various lighting conditions.

## Technologies Used

- **GDAL**: For accessing and processing large GeoTIFF files.
- **Flask**: A lightweight backend framework to handle file uploads and processing requests.
- **Three.js**: JavaScript library for 3D rendering.
- **HTML/CSS/JavaScript/Bootstrap**: For front-end development and responsiveness.

## Approach

### GDAL for Geospatial Data Processing
- **Reason**: GDAL is widely used for handling geospatial data and is capable of managing large TIFF files.
- **Function**: The GeoTIFF files from Chandrayaan-2 (around 4000x96000 pixels) are cropped into smaller tiles based on latitude and longitude coordinates. This approach ensures efficient data handling and manageable rendering sections without overwhelming the system.

### Three.js for 3D Terrain Visualization
- **Reason**: Three.js is a cross-platform, lightweight JavaScript library, ideal for 3D rendering on web and mobile platforms.
- **Function**: Three.js renders the cropped height maps in 3D, incorporating sun parameters such as azimuth and elevation for realistic lighting conditions across the lunar terrain.

### Flask for Backend Support
- **Reason**: Flask is a lightweight web framework that is easy to set up and deploy across platforms.
- **Function**: Flask handles data requests, processes DEM files, and serves heightmaps and synthetic images to the front end, which then builds the 3D terrain.

### Screenshots
![image](https://github.com/user-attachments/assets/bd3f1c1a-3b82-4e85-b860-4bdf1f98324b)
- **Single Band View Vs 3D Generated Render**: 

