from ipyleaflet import Map, SplitMapControl,LayersControl,WidgetControl
from ipywidgets import FloatSlider, jslink
from localtileserver import get_leaflet_tile_layer

class SplitMap:
    def __init__(self,sources):
        self.sources=sources

    def create_split_map(self,left_layer_source, right_layer_source, style=None, zoom=1, center=(0., 0.)):
        if left_layer_source is None or right_layer_source is None:
            return None
        styler = {"clamp": False, "palette": "matplotlib.Plasma_6", "band": 1}
        if not style is None:
            styler = style

        left_layer = get_leaflet_tile_layer(left_layer_source, style=styler)
        right_layer = get_leaflet_tile_layer(right_layer_source, style=styler)

        result = Map(center=center, zoom=zoom)
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

        return result