import leafmap
<<<<<<< HEAD
from ipyleaflet import SplitMapControl, LayersControl, WidgetControl
from ipywidgets import FloatSlider, jslink
from localtileserver import get_leaflet_tile_layer

=======
from ipyleaflet import Map, SplitMapControl,LayersControl,WidgetControl
from ipywidgets import FloatSlider, jslink
from localtileserver import get_leaflet_tile_layer
>>>>>>> f207c06... Initial SplitMap with opacity controls

def hydro_map():
    m = leafmap.Map(center=(40, -100), zoom=4)
    return m


def visualise_geojson(path):
    m = leafmap.Map(layers_control=True)
    m.add_geojson(path, layer_name='Geojson')
    return m

<<<<<<< HEAD

def create_split_map(base, left_layer_source, right_layer_source, style=None):
=======
def create_split_map(base,left_layer_source, right_layer_source, style=None, zoom=1, center=(0., 0.)):
>>>>>>> f207c06... Initial SplitMap with opacity controls
    if left_layer_source is None or right_layer_source is None:
        return None
    styler = {"clamp": False, "palette": "matplotlib.Plasma_6", "band": 1}
    if not style is None:
        styler = style

    left_layer = get_leaflet_tile_layer(left_layer_source, style=styler)
    right_layer = get_leaflet_tile_layer(right_layer_source, style=styler)

    result = base
    result.add_control(LayersControl(position="bottomright"))
    split_control = SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    result.add_control(split_control)

    opacity_slider_left = FloatSlider(description='Opacity of left layer:', min=0., max=1., step=0.01, value=1.)
    opacity_slider_right = FloatSlider(description='Opacity of right layer:', min=0., max=1., step=0.01, value=1.)
    jslink((opacity_slider_left, 'value'), (split_control.left_layer, 'opacity'))
    jslink((opacity_slider_right, 'value'), (split_control.right_layer, 'opacity'))
    opacity_control_left = WidgetControl(widget=opacity_slider_left, position='topright')
    opacity_control_right = WidgetControl(widget=opacity_slider_right, position='topright')
    result.add_control(opacity_control_left)
    result.add_control(opacity_control_right)

<<<<<<< HEAD
    return result
=======
    return result
>>>>>>> f207c06... Initial SplitMap with opacity controls
