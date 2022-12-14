from time import sleep
import requests
import json
import numpy as np
import pandas as pd
import seaborn as sns
from ipyleaflet import Map, SplitMapControl, WidgetControl, Marker, MarkerCluster, GeoJSON
from ipywidgets import FloatSlider, jslink, widgets, Play
from localtileserver import get_leaflet_tile_layer
from matplotlib import pyplot as plt


def empty_map(center=(40, -100), zoom=4):
    m = Map(center=center, zoom=zoom)
    return m


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
    m.add(layer)
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
        new_marker = Marker(location=(pinsArray[i][0], pinsArray[i][1]), draggable=False)
        new_marker.on_click(handle_click(i, out, charts))
        pins.append(new_marker)
    marker_cluster = MarkerCluster(
        markers=pins
    )
    base.add_layer(marker_cluster)
    return base


def add_animation_with_rasters_series(base, raster_series, interval=300):
    if (len(raster_series)) < 2:
        return None
    base.add(raster_series[0])
    play = Play(value=0, min=0, max=len(raster_series) - 1, step=1, interval=interval, description="Press play",
                disabled=False)

    def _animation_handler(caller):
        if (caller.new == 0):
            base.layers = tuple([base.layers[0]])
            base.add_layer(raster_series[0])
            return
        base.add_layer(raster_series[caller.new])
        sleep(0.001)  # Necessary to prevent clipping
        base.remove_layer(raster_series[caller.old])

    play.observe(_animation_handler, names='value')
    animation_control = WidgetControl(widget=play, position='bottomright')
    base.add(animation_control)
    return base
