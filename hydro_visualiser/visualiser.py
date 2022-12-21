from time import sleep
import requests
import json
import numpy as np
import pandas as pd
import seaborn as sns
from ipyleaflet import Map, SplitMapControl, WidgetControl, Marker, MarkerCluster, GeoJSON, Polygon
from ipywidgets import FloatSlider, jslink, widgets, Play
from localtileserver import get_leaflet_tile_layer
from matplotlib import pyplot as plt
from shapely.geometry import Point
import geopandas as gpd
from tqdm.notebook import tqdm


def empty_map(center=(40, -100), zoom=4):
    m = Map(center=center, zoom=zoom)
    return m


def visualise_geojson(path):
    if path[:4] == "http":
        r = requests.get(path)
        data = r.json()
    else:
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except IOError:
            print("There is no such a file")
            return None

    def get_single_feature_cords(feature):
        feature_type = feature['geometry']['type'].lower()
        if feature_type == "point":
            return feature['geometry']['coordinates']
        elif feature_type == "linestring" or feature_type == "multipoint":
            return feature['geometry']['coordinates'][0]
        elif feature_type == "polygon" or feature_type == "multilinestring":
            return feature['geometry']['coordinates'][0][0]
        elif feature_type == "multipolygon":
            return feature['geometry']['coordinates'][0][0][0]
        elif feature_type == "geometrycollection":
            return feature['geometry']['coordinates'][0][0]

    def get_map_cords(data):
        if data['type'] == "FeatureCollection":
            return get_single_feature_cords(data['features'][0])
        else:
            return get_single_feature_cords(data)

    cords = get_map_cords(data)
    m = Map(center=(cords[1], cords[0]), zoom=6)
    geo_json = GeoJSON(
        data=data,
        style={'color': 'black'},
        hover_style={'color': 'gray'}
    )
    m.add(geo_json)
    return m


def visualise_tif(path):
    if path is None:
        return None
    if path[:4] == "http":
        local_filename = path.split('/')[-1]
        with requests.get(path, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        path = local_filename

    styler = {"clamp": False, "palette": "matplotlib.Plasma_6", "band": 1}
    layer = get_leaflet_tile_layer(path, style=styler)
    m = Map(zoom=6, center=(layer.bounds[0][0], layer.bounds[0][1]))
    opacity_slider = FloatSlider(description='Opacity:', min=0., max=1., step=0.01, value=1.)
    jslink((opacity_slider, 'value'), (layer, 'opacity'))
    opacity_control = WidgetControl(widget=opacity_slider, position='topright')
    m.add(layer)
    m.add(opacity_control)
    return m


def add_split_map(base,left_layer_source, right_layer_source, style=None):
    if left_layer_source is None or right_layer_source is None:
        return None
    styler = {"clamp": False, "palette": "matplotlib.Plasma_6", "band": 1}
    if not style is None:
        styler = style

    left_layer = get_leaflet_tile_layer(left_layer_source, style=styler)
    right_layer = get_leaflet_tile_layer(right_layer_source, style=styler)

    split_control = SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    base.add(split_control)

    opacity_slider_left = FloatSlider(description='Opacity of left layer:', min=0., max=1., step=0.01, value=1.)
    opacity_slider_right = FloatSlider(description='Opacity of right layer:', min=0., max=1., step=0.01, value=1.)
    jslink((opacity_slider_left, 'value'), (split_control.left_layer, 'opacity'))
    jslink((opacity_slider_right, 'value'), (split_control.right_layer, 'opacity'))
    opacity_control_left = WidgetControl(widget=opacity_slider_left, position='topright')
    opacity_control_right = WidgetControl(widget=opacity_slider_right, position='topright')
    base.add(opacity_control_left)
    base.add(opacity_control_right)

    return base


# pinsArray format: [{x1, y2}, {x2, y2}...]
def draw_chart(charts):
    data1 = pd.DataFrame(np.random.normal(size=50))
    charts.clear_output()
    sns.set_theme()
    with charts:
        fig1, axes1 = plt.subplots()
        data1.hist(ax=axes1)
        plt.show(fig1)


def handle_click(number, out, charts):
    def update_widget(**kwargs):
        out.clear_output()
        out.append_stdout("Example station nr: " + str(number) + "data")
        out.append_stdout("\n")
        draw_chart(charts)

    return update_widget


def addPinsAndWidgets(base, pinsArray):
    pins = []
    out = widgets.Output(layout={'border': '1px solid black'})
    charts = widgets.Output(layout={'border': '1px solid black'})
    children = []
    tab = widgets.Tab(children=[out, charts])
    for i in range(len(children)):
        tab.set_title(i, 'a')
    widget_tab = WidgetControl(widget=tab, position="bottomleft")
    base.add_control(widget_tab)

    for i in range(1, len(pinsArray)):
        new_marker = Marker(location=(pinsArray[i].x, pinsArray[i].y), draggable=False)
        new_marker.on_click(handle_click(i, out, charts))
        pins.append(new_marker)
    marker_cluster = MarkerCluster(
        markers=pins
    )
    base.add_layer(marker_cluster)
    return base

def prepare_layers_series(series_paths):
    styler={"clamp":False,"palette":"matplotlib.Plasma_6","band":1}
    series=[]
    for i in tqdm(range(len(series_paths))):
        series.append(get_leaflet_tile_layer(series_paths[i],style=styler))
    return series

def add_animation_from_raster_series(base, raster_series, interval=300):
    if (len(raster_series)) < 2:
        return None
    base.add_layer(raster_series[0])
    play = Play(value=0, min=0, max=len(raster_series) - 1, step=1, interval=interval, description="Press play",
                disabled=False)

    def _animation_handler(caller):
        if (caller.new == 0):
            base.layers = tuple([base.layers[0]])
            base.add_layer(raster_series[0])
            return
        base.add_layer(raster_series[caller.new])
        if len(base.layers[1:])>2:
            base.remove_layer(raster_series[base.layers[1]])

    play.observe(_animation_handler, names='value')
    animation_control = WidgetControl(widget=play, position='bottomright')
    base.add_control(animation_control)
    return base

#temperature widget -> to get value just print(to_fill)
polygon=[]
temp_array=[]
paused = False

def add_pin(map, coordinates):
    map.add_layer(Marker(location=coordinates))


def create_dataframe(m, to_fill_array):
    finish_button = widgets.Button(description='Finish polygon')
    button = widgets.Button(description='Submit temperature')
    slider = widgets.FloatSlider(
        value=7.5,
        min=-50,
        max=50,
        step=0.1,
        orientation='horizontal'
    )
    def handle_click1(**kwargs):
        if kwargs.get('type') == 'click':
            finish_button.layout.display="none"
            global paused
            if paused == False:
                button.layout.display = "block"
                slider.layout.display = "block"
                polygon.append(Point(kwargs.get('coordinates')[0], kwargs.get('coordinates')[1]))
                add_pin(m, kwargs.get('coordinates'))
                paused=True
    def display_form(m):
        def on_ok_button_clicked(b):
            temp_array.append(slider.value)
            button.layout.display = "none"
            slider.layout.display = "none"
            global paused
            paused = False
            finish_button.layout.display="block"
        button.on_click(on_ok_button_clicked)
        submit_control = WidgetControl(widget=button, position='bottomright')
        widget_control_slider = WidgetControl(widget=slider, position='topright')
        m.add_control(submit_control)
        m.add_control(widget_control_slider)
        button.layout.display = "none"
        slider.layout.display = "none"
    def on_end_button_clicked(b):
        button.close()
        slider.close()
        finish_button.close()
        global polygon
        global temp_array
        tmp = gpd.GeoDataFrame(geometry=polygon, data={'temperature':temp_array}, crs='EPSG:4326')
        to_fill_array.append(tmp)
        print(f'{tmp}')
        polygon=[]
        temp_array=[]
    finish_button.on_click(on_end_button_clicked)
    submit_control = WidgetControl(widget=finish_button, position='bottomleft')
    m.add_control(submit_control)
    display_form(m)
    m.on_interaction(handle_click1)
    return m

#polygon widget -> to get value just print(to_fill_array[index])

polygon_array=[]
locations_array=[]
def create_dataframe_polygons(m, to_fill_array):
    submit_button = widgets.Button(description='Submit polygon')
    end_button = widgets.Button(description='End/Make another polygon')
    submit_control = WidgetControl(widget=submit_button, position='bottomright')
    end_button.layout.display = "none"
    end_control = WidgetControl(widget=end_button, position='bottomleft')
    def handle_click2(**kwargs):
        if kwargs.get('type') == 'click':
            submit_button.layout.display = "block"
            polygon_array.append(Point(kwargs.get('coordinates')[0], kwargs.get('coordinates')[1]))
            point = (kwargs.get('coordinates')[0], kwargs.get('coordinates')[1])
            locations_array.append(point)
            add_pin(m, kwargs.get('coordinates'))
    def on_finish_button_clicked(b):
        submit_button.close()
        end_button.close()
        m.remove_control(submit_control)
        m.remove_control(end_control)
        print(f"{to_fill_array}")
    def display_form2(m):
        def on_submit_button_clicked(b):
            end_button.layout.display = "block"
            global locations_array
            submit_button.layout.display = "none"
            multipolygon = Polygon(
            locations=[
                locations_array
            ],
            color="green",
            fill_color="green"
            )
            m.add_layer(multipolygon)
            global polygon_array
            tmp = gpd.GeoDataFrame(geometry=polygon_array, crs='EPSG:4326')
            to_fill_array.append(tmp)
            print(f"[1] : {tmp}")
            locations_array=[]
            polygon_array=[]
        submit_button.on_click(on_submit_button_clicked)
        submit_button.layout.display = "none"
    end_button.on_click(on_finish_button_clicked)
    m.add_control(submit_control)
    m.add_control(end_control)
    display_form2(m)
    m.on_interaction(handle_click2)
    return m