import leafmap


def hydro_map():
    m = leafmap.Map(center=(40, -100), zoom=4)
    return m


def visualise_geojson(path):
    m = leafmap.Map(layers_control=True)
    m.add_geojson(path, layer_name='Geojson')
    return m
