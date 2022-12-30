import requests
import json
import numpy as np
import pandas as pd
import seaborn as sns
from ipyleaflet import Map, SplitMapControl, WidgetControl, Marker, MarkerCluster, GeoJSON, Polygon
from ipywidgets import FloatSlider, jslink, widgets, Play, HTML, Button, HBox
from localtileserver import get_leaflet_tile_layer
from matplotlib import pyplot as plt
from shapely.geometry import Point
import geopandas as gpd
from tqdm.notebook import tqdm


def empty_map(center=(40, -100), zoom=4):
    m = Map(center=center, zoom=zoom)
    return m


def add_geojson(m,path,style=None):
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

    if style is None:
        styler={'color': 'black'}
    else:
        styler=style

    geo_json = GeoJSON(
        data=data,
        style=styler,
        hover_style={'color': 'gray'}
    )
    m.add(geo_json)
    return m


def add_tif(m, path, opacity=False):
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
    else:
        local_filename = path.split('\\')[-1]

    styler = {"clamp": False, "palette": "matplotlib.Plasma_6", "band": 1}
    layer = get_leaflet_tile_layer(path, style=styler)
    m.add(layer)
    if opacity:
        opacity_slider = FloatSlider(description='{}: '.format(local_filename), min=0., max=1., step=0.01, value=1.)
        jslink((opacity_slider, 'value'), (layer, 'opacity'))
        opacity_control = WidgetControl(widget=opacity_slider, position='topright')
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


def add_pins_and_widgets(base, pinsArray):
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

def prepare_layers_series(series_paths):
    styler={"clamp":False,"palette":"matplotlib.Plasma_6","band":1}
    series=[]
    for i in tqdm(range(len(series_paths))):
        series.append(get_leaflet_tile_layer(series_paths[i],style=styler))
    return series


def add_animation_from_raster_series(base, raster_series, raster_url_list, interval=300):
    if (len(raster_series)) < 2:
        return None
    for layer in raster_series:
        base.add_layer(layer)
    base.layers[1].opacity = 1.
    play = Play(value=0, min=0, max=len(raster_series) - 1, step=1, interval=interval, description="Press play",
                disabled=False)
    filenames = HTML(value=raster_url_list[0], placeholder='Placeholder', description='File URL:')

    step_back = Button(description='', disabled=False, button_style='', icon='step-backward',
                       layout=Layout(width='50%', height='30px'))
    step_forward = Button(description='', disabled=False, button_style='', icon='step-forward',
                          layout=Layout(width='50%', height='30px'))

    def _animation_handler(caller):
        base.layers[caller.new + 1].opacity = 1.
        base.layers[caller.old + 1].opacity = 0.
        filenames.value = raster_url_list[caller.new]

    def _step_controller(caller):
        if caller.new:
            step_back.disabled = True
            step_forward.disabled = True
        else:
            step_back.disabled = False
            step_forward.disabled = False

    def _step_back_handler(caller):
        if play.value > 0:
            play.value = play.value - 1

    def _step_forward_handler(caller):
        if play.value < play.max:
            play.value = play.value + 1

    play.observe(_animation_handler, names='value')
    play.observe(_step_controller, names='_playing')
    step_back.on_click(_step_back_handler)
    step_forward.on_click(_step_forward_handler)

    animation_box = HBox([step_back, step_forward, play])

    animation_control = WidgetControl(widget=animation_box, position='bottomright')
    filename_control = WidgetControl(widget=filenames, position='bottomleft')

    base.add_control(animation_control)
    base.add_control(filename_control)
    return base

#Old animation version

# def add_animation_from_raster_series(base, raster_series, interval=300):
#     if (len(raster_series)) < 2:
#         return None
#     base.add_layer(raster_series[0])
#     play = Play(value=0, min=0, max=len(raster_series) - 1, step=1, interval=interval, description="Press play",
#                 disabled=False)
#     def _animation_handler(caller):
#         if (caller.new == 0):
#             base.layers = tuple([base.layers[0]])
#             base.add_layer(raster_series[0])
#             return
#         print(play._playing)
#         base.add_layer(raster_series[caller.new])
#         if len(base.layers[1:])>2:
#             base.remove_layer(raster_series[base.layers[1]])
#
#     play.observe(_animation_handler, names='value')
#     animation_control = WidgetControl(widget=play, position='bottomright')
#     base.add_control(animation_control)
#     return base

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