from flask import Flask, request, send_file, render_template, jsonify
from PIL import Image
import numpy as np
import os
from osgeo import gdal, gdalconst
import rasterio
from rasterio.transform import from_origin

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CROPPED_FOLDER'] = 'cropped'
app.config['SNAPSHOTS_FOLDER'] = 'snapshots'

# Ensure the folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CROPPED_FOLDER'], exist_ok=True)
os.makedirs(app.config['SNAPSHOTS_FOLDER'], exist_ok=True)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return render_template('crop.html', file_path=file.filename)
    return 'File not uploaded', 400

@app.route('/crop', methods=['POST'])
def crop_file():
    input_file = os.path.join(app.config['UPLOAD_FOLDER'], request.form['file_path'])
    output_file = os.path.join(app.config['CROPPED_FOLDER'], 'cropped_' + request.form['file_path'])
    
    ulx_geo = float(request.form['ulx_geo'])
    uly_geo = float(request.form['uly_geo'])
    lrx_geo = float(request.form['lrx_geo'])
    lry_geo = float(request.form['lry_geo'])
    
    crop_geotiff(input_file, output_file, ulx_geo, uly_geo, lrx_geo, lry_geo)
    
    return render_template('view_terrain.html', file_path='cropped_' + request.form['file_path'])

@app.route('/process', methods=['POST'])
def process():
    if 'tiff-file' not in request.files:
        return 'No file part', 400

    file = request.files['tiff-file']
    if file.filename == '':
        return 'No selected file', 400

    ulx_geo = request.form.get('ulx_geo')
    uly_geo = request.form.get('uly_geo')
    lrx_geo = request.form.get('lrx_geo')
    lry_geo = request.form.get('lry_geo')

    if file and ulx_geo and uly_geo and lrx_geo and lry_geo:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        output_file = 'cropped_' + file.filename
        crop_geotiff(file_path, os.path.join(app.config['CROPPED_FOLDER'], output_file), 
                      float(ulx_geo), float(uly_geo), float(lrx_geo), float(lry_geo))

        return render_template('view_terrain.html', file_path=output_file)
    
    return 'Failed to process the file', 400

@app.route('/heightmap', methods=['GET'])
def serve_heightmap():
    file_path = request.args.get('file_path')
    if not file_path:
        return 'Heightmap file path not provided', 400
    
    absolute_file_path = os.path.join(app.config['CROPPED_FOLDER'], file_path)
    
    if not os.path.isfile(absolute_file_path):
        return 'Heightmap file not found', 404

    dataset = gdal.Open(absolute_file_path)
    if dataset is None:
        return 'Failed to open heightmap file', 500

    band = dataset.GetRasterBand(1)
    heightmap_array = band.ReadAsArray()

    heightmap_list = heightmap_array.tolist()
    height, width = heightmap_array.shape

    return jsonify({
        'heightmap': heightmap_list,
        'width': width,
        'height': height
    })

@app.route('/save_snapshot', methods=['POST'])
def save_snapshot():
    snapshot = request.files['snapshot']
    camera_position = request.form['cameraPosition']
    camera_rotation = request.form['cameraRotation']
    sun_position = request.form['sunPosition']

    snapshot_path = os.path.join(app.config['SNAPSHOTS_FOLDER'], 'snapshot.png')
    snapshot.save(snapshot_path)

    with Image.open(snapshot_path) as img:
        img = img.convert('RGB')
        img_array = np.array(img)

    geospatial_info = {
        "transform": [123.45, 1, 0, 678.90, 0, -1],  # Example values, replace with your own
        "crs": 'EPSG:4326'
    }

    tiff_path = os.path.join(app.config['SNAPSHOTS_FOLDER'], 'snapshot.tif')
    with rasterio.open(
        tiff_path,
        'w',
        driver='GTiff',
        height=img_array.shape[0],
        width=img_array.shape[1],
        count=3,
        dtype=img_array.dtype,
        crs=geospatial_info['crs'],
        transform=from_origin(*geospatial_info['transform'])
    ) as dst:
        dst.write(img_array[:, :, 0], 1)
        dst.write(img_array[:, :, 1], 2)
        dst.write(img_array[:, :, 2], 3)

    return jsonify({'message': 'Snapshot saved successfully'})

def crop_geotiff(input_file, output_file, ulx_geo, uly_geo, lrx_geo, lry_geo):
    try:
        dataset = gdal.Open(input_file, gdalconst.GA_ReadOnly)
        if dataset is None:
            raise Exception(f"Failed to open {input_file}")

        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        bands = dataset.RasterCount

        ulx_pixel, uly_pixel = geo_to_pixel(dataset, ulx_geo, uly_geo)
        lrx_pixel, lry_pixel = geo_to_pixel(dataset, lrx_geo, lry_geo)

        ulx_pixel = max(0, ulx_pixel)
        uly_pixel = max(0, uly_pixel)
        lrx_pixel = min(cols, lrx_pixel)
        lry_pixel = min(rows, lry_pixel)

        if lrx_pixel <= ulx_pixel or lry_pixel <= uly_pixel:
            raise ValueError("Invalid cropping coordinates. Check the values.")

        new_width = lrx_pixel - ulx_pixel
        new_height = lry_pixel - uly_pixel

        driver = gdal.GetDriverByName('GTiff')
        out_dataset = driver.Create(output_file, new_width, new_height, bands, dataset.GetRasterBand(1).DataType)

        out_dataset.SetProjection(dataset.GetProjection())
        geo_transform = dataset.GetGeoTransform()
        out_geo_transform = (
            ulx_geo, geo_transform[1], geo_transform[2],
            uly_geo, geo_transform[4], geo_transform[5]
        )
        out_dataset.SetGeoTransform(out_geo_transform)

        out_dataset.SetMetadata(dataset.GetMetadata())

        for i in range(1, bands + 1):
            band = dataset.GetRasterBand(i)
            data = band.ReadAsArray(ulx_pixel, uly_pixel, new_width, new_height)
            out_band = out_dataset.GetRasterBand(i)
            out_band.WriteArray(data)
            out_band.SetNoDataValue(band.GetNoDataValue())
            out_band.SetColorInterpretation(band.GetColorInterpretation())
            out_band.SetMetadata(band.GetMetadata())
            color_table = band.GetColorTable()
            if color_table:
                out_band.SetColorTable(color_table)

        dataset = None
        out_dataset = None

        print(f"Cropped area saved as {output_file}")

    except Exception as e:
        print(f"Error: {str(e)}")

def geo_to_pixel(dataset, x_geo, y_geo):
    geo_transform = dataset.GetGeoTransform()
    x_pixel = int((x_geo - geo_transform[0]) / geo_transform[1])
    y_pixel = int((y_geo - geo_transform[3]) / geo_transform[5])
    return x_pixel, y_pixel

if __name__ == '__main__':
    app.run(debug=True)
