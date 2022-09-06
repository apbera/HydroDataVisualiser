import leafmap
from ipyleaflet import Map, SplitMapControl,LayersControl,WidgetControl
from ipywidgets import FloatSlider, jslink
from localtileserver import get_leaflet_tile_layer

def hydro_map():
    m = leafmap.Map(center=(40, -100), zoom=4)
    return m

def visualise_geojson(path):
    m = leafmap.Map(layers_control=True)
    m.add_geojson(path, layer_name='Geojson')
    return m

def create_split_map(base,left_layer_source, right_layer_source, style=None, zoom=1, center=(0., 0.)):
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

    return result

#pinsArray format: [{x1, y2}, {x2, y2}...]
def draw_chart(charts):
    data1 = pd.DataFrame(np.random.normal(size = 50))
    charts.clear_output()
    sns.set_theme()
    with charts:
        fig1, axes1 = plt.subplots()
        data1.hist(ax = axes1)
        plt.show(fig1)    

def handle_click(number, out, charts):
    def update_widget(**kwargs):
        out.clear_output()
        out.append_stdout("Example station nr: " + str(number) + "data")
        out.append_stdout("\n")
        draw_chart(charts)
    return update_widget

def addPinsAndWidgets(base, pinsArray):
    pins=[]
    out = widgets.Output(layout={'border': '1px solid black'})
    charts = widgets.Output(layout={'border': '1px solid black'})
    children=[]
    tab = widgets.Tab(children = [out, charts])
    for i in range(len(children)):
        tab.set_title(i, 'a')
    widget_tab = WidgetControl(widget = tab, position="bottomleft")
    base.add(widget_tab)

    for i in range(1, len(pinsArray)):
        new_marker = Marker(location = (pinsArray[i][0], pinsArray[i][1]), draggable=False)
        new_marker.on_click(handle_click(i, out, charts))
        pins.append(new_marker)
    marker_cluster = MarkerCluster(
        markers=pins
    )
    base.add_layer(marker_cluster)
    return base
