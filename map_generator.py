
import geopandas as gpd
import folium
import numpy as np

# CRS
METRIC_CRS = 'EPSG:32614'
WGS84_CRS  = 'EPSG:4326'

# Datos
HIDALGO_GEOJSON = 'data/hidalgo.json'
RIOS_GEOJSON    = 'data/rios.geojson'
LAGOS_GEOJSON   = 'data/lagos.geojson'
PRESAS_GEOJSON  = 'data/presas.geojson'

# Imagen de fondo
IMAGE_URL = 'static/mapa_hidalgo_base.png'
IMAGE_BOUNDS = [[19.646994, -99.341121], [21.134986, -98.363338]]

def generar_mapa_html(output_path='static/mapa_hidalgo.html'):
    # Cargar y proyectar datos
    hidalgo = gpd.read_file(HIDALGO_GEOJSON).to_crs(METRIC_CRS)
    rios    = gpd.read_file(RIOS_GEOJSON).to_crs(METRIC_CRS)
    lagos   = gpd.read_file(LAGOS_GEOJSON).to_crs(METRIC_CRS)
    presas  = gpd.read_file(PRESAS_GEOJSON).to_crs(METRIC_CRS)

    # Unificar geometría de Hidalgo
    union_hidalgo = hidalgo.unary_union
    mask = gpd.GeoSeries([union_hidalgo], crs=METRIC_CRS)

    # Recortar
    rios_clip   = rios.clip(mask)
    lagos_clip  = lagos.clip(mask)
    presas_clip = presas.clip(mask)

    # Geometría de puntos
    rios_clip['midpoint']   = rios_clip.geometry.apply(lambda g: g.interpolate(g.length/2))
    lagos_clip['centroid']  = lagos_clip.geometry.centroid
    presas_clip['centroid'] = presas_clip.geometry.centroid

    # Convertir a WGS84
    rios_mid_wgs    = rios_clip.set_geometry('midpoint').to_crs(WGS84_CRS)
    lagos_cent_wgs  = lagos_clip.set_geometry('centroid').to_crs(WGS84_CRS)
    presas_cent_wgs = presas_clip.set_geometry('centroid').to_crs(WGS84_CRS)

    # Mapa base centrado
    center = [(19.646994 + 21.134986) / 2, (-99.341121 + -98.363338) / 2]
    m = folium.Map(location=center, zoom_start=9, max_bounds=True)
    m.fit_bounds(IMAGE_BOUNDS)

    # Imagen como capa base
    folium.raster_layers.ImageOverlay(
        name="Mapa Base de Hidalgo",
        image=IMAGE_URL,
        bounds=IMAGE_BOUNDS,
        opacity=1,
        interactive=False,
        cross_origin=False
    ).add_to(m)

    # FeatureGroups
    fg_rios   = folium.FeatureGroup(name='Ríos')
    fg_lagos  = folium.FeatureGroup(name='Lagos')
    fg_presas = folium.FeatureGroup(name='Presas')

    # Marcadores
    for _, r in rios_mid_wgs.iterrows():
        geom = r.geometry
        if geom and not geom.is_empty:
            folium.Marker([geom.y, geom.x], popup=f"Río: {r.get('name', '')}").add_to(fg_rios)

    for _, r in lagos_cent_wgs.iterrows():
        geom = r.geometry
        if geom and not geom.is_empty:
            folium.Marker([geom.y, geom.x], popup=f"Lago: {r.get('name', '')}",
                          icon=folium.Icon(color='blue', icon='tint')).add_to(fg_lagos)

    for _, r in presas_cent_wgs.iterrows():
        geom = r.geometry
        if geom and not geom.is_empty:
            folium.Marker([geom.y, geom.x], popup=f"Presa: {r.get('name', '')}",
                          icon=folium.Icon(color='green', icon='tower')).add_to(fg_presas)

    # Agregar capas
    m.add_child(fg_rios)
    m.add_child(fg_lagos)
    m.add_child(fg_presas)
    folium.LayerControl().add_to(m)

    # Guardar mapa
    m.save(output_path)
    print(f"✅ Mapa generado en: {output_path}")
