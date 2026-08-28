import streamlit as st
import networkx as nx
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
import shapely.wkt
import plotly.graph_objects as go
import plotly.express as px
import random

# 1. Configuración de Interfaz
st.set_page_config(page_title="Motor Logístico Saltillo", layout="wide")
st.title("🚚 Suite de Inteligencia Operativa y Ruteo (Última Milla)")
st.markdown("Plataforma analítica con datos de la Red Nacional de Caminos (INEGI).")

# 2. Motor de Base de Datos Espacial
@st.cache_resource
def cargar_grafo():
    G_crudo = nx.read_graphml("red_vial_inegi_saltillo.graphml")
    
    # Filtro Topológico: Extraer solo la red principal conectada (elimina islas cartográficas)
    componentes = list(nx.connected_components(G_crudo))
    componente_principal = max(componentes, key=len)
    G = G_crudo.subgraph(componente_principal).copy()
    
    # Calculamos el costo en TIEMPO para cada calle de Saltillo
    for u, v, data in G.edges(data=True):
        distancia_m = float(data.get('mm_len', 1.0))
        velocidad_str = data.get('VELOCIDAD', '30')
        try:
            velocidad_kmh = float(velocidad_str)
            if velocidad_kmh <= 0: velocidad_kmh = 30.0
        except ValueError:
            velocidad_kmh = 30.0
            
        velocidad_ms = velocidad_kmh / 3.6
        data['tiempo_segundos'] = distancia_m / velocidad_ms
        
    return G

try:
    G = cargar_grafo()
    nodos_lista = list(G.nodes(data=True)) # Alimentación segura de nodos conectados
except FileNotFoundError:
    st.error("No se encontró el archivo red_vial_inegi_saltillo.graphml.")
    st.stop()

# Funciones de Soporte Geométrico
def extraer_coordenadas(ruta_nodos, G):
    coords = []
    for i in range(len(ruta_nodos) - 1):
        u, v = ruta_nodos[i], ruta_nodos[i+1]
        data = G.get_edge_data(u, v)
        if data and 0 in data: data = data[0]
        
        if data and 'geometry' in data and data['geometry']:
            curva = shapely.wkt.loads(data['geometry'])
            for coord in curva.coords:
                coords.append(Point(coord[0], coord[1]))
        else:
            coords.append(Point(float(G.nodes[u]['x']), float(G.nodes[u]['y'])))
            coords.append(Point(float(G.nodes[v]['x']), float(G.nodes[v]['y'])))
            
    gdf = gpd.GeoDataFrame(geometry=coords, crs="EPSG:32614").to_crs(epsg=4326)
    return pd.DataFrame({'Latitud': gdf.geometry.y, 'Longitud': gdf.geometry.x})

def calcular_metricas(ruta_nodos, G):
    distancia = 0.0
    tiempo = 0.0
    for i in range(len(ruta_nodos) - 1):
        u, v = ruta_nodos[i], ruta_nodos[i+1]
        data = G.get_edge_data(u, v)
        if data and 0 in data: data = data[0]
        distancia += float(data.get('mm_len', 0))
        tiempo += float(data.get('tiempo_segundos', 0))
    return distancia, tiempo

# 3. Navegación por Pestañas
tab1, tab2, tab3 = st.tabs(["A vs B (Competitivas)", "Problema del Agente Viajero (Multi-Parada)", "Isócronas (Cobertura por Tiempo)"])

# ==========================================
# TAB 1: RUTAS COMPETITIVAS
# ==========================================
with tab1:
    st.subheader("Simulación de Rutas: Distancia vs. Tiempo")
    if st.button("Generar Competitiva", type="primary", key="btn_ab"):
        with st.spinner("Calculando heurísticas..."):
            origen, destino = random.choice(nodos_lista)[0], random.choice(nodos_lista)[0]
            try:
                ruta_dist = nx.shortest_path(G, source=origen, target=destino, weight='mm_len')
                ruta_tiem = nx.shortest_path(G, source=origen, target=destino, weight='tiempo_segundos')
                
                df_dist = extraer_coordenadas(ruta_dist, G)
                df_tiem = extraer_coordenadas(ruta_tiem, G)
                
                dist_1, tiem_1 = calcular_metricas(ruta_dist, G)
                dist_2, tiem_2 = calcular_metricas(ruta_tiem, G)
                
                fig = go.Figure()
                fig.add_trace(go.Scattermapbox(mode="lines", lon=df_tiem['Longitud'], lat=df_tiem['Latitud'], line=dict(width=6, color="#00FFCC"), name=f"⚡ Más Rápida ({tiem_2/60:.1f} min | {dist_2/1000:.2f} km)"))
                fig.add_trace(go.Scattermapbox(mode="lines", lon=df_dist['Longitud'], lat=df_dist['Latitud'], line=dict(width=3, color="#FF3366"), name=f"📏 Más Corta ({tiem_1/60:.1f} min | {dist_1/1000:.2f} km)"))
                fig.add_trace(go.Scattermapbox(mode="markers+text", lon=[df_tiem['Longitud'].iloc[0], df_tiem['Longitud'].iloc[-1]], lat=[df_tiem['Latitud'].iloc[0], df_tiem['Latitud'].iloc[-1]], marker=dict(size=14, color=['white', '#FF9900']), text=["Origen", "Destino"], textposition="bottom right", textfont=dict(color="white"), name="Ubicaciones"))
                
                fig.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=df_tiem['Latitud'].iloc[0], lon=df_tiem['Longitud'].iloc[0]), zoom=13), margin={"r":0,"t":0,"l":0,"b":0}, legend=dict(bgcolor="rgba(0,0,0,0.7)", font=dict(color="white")))
                st.plotly_chart(fig, width='stretch')
            except:
                st.warning("Puntos sin conexión encontrados. Intenta de nuevo.")

# ==========================================
# TAB 2: AGENTE VIAJERO (TSP)
# ==========================================
with tab2:
    st.subheader("Secuenciación Óptima de Reparto")
    st.markdown("Construye la secuencia matemáticamente más eficiente para entregar múltiples pedidos partiendo de un almacén.")
    num_paradas = st.slider("Número de Entregas (Nodos)", 3, 8, 5)
    
    if st.button("Optimizar Flotilla", type="primary", key="btn_tsp"):
        with st.spinner("Construyendo grafo completo y resolviendo TSP..."):
            puntos = [random.choice(nodos_lista)[0] for _ in range(num_paradas + 1)]
            
            G_tsp = nx.Graph()
            for i in range(len(puntos)):
                for j in range(i+1, len(puntos)):
                    try:
                        tiempo = nx.shortest_path_length(G, puntos[i], puntos[j], weight='tiempo_segundos')
                        G_tsp.add_edge(puntos[i], puntos[j], weight=tiempo)
                    except:
                        pass
            
            try:
                secuencia_optima = nx.approximation.traveling_salesman_problem(G_tsp, weight='weight', cycle=True)
                
                ruta_fisica = []
                for i in range(len(secuencia_optima)-1):
                    tramo = nx.shortest_path(G, secuencia_optima[i], secuencia_optima[i+1], weight='tiempo_segundos')
                    if i > 0: tramo = tramo[1:]
                    ruta_fisica.extend(tramo)
                    
                df_tsp = extraer_coordenadas(ruta_fisica, G)
                
                lat_paradas, lon_paradas = [], []
                for p in secuencia_optima[:-1]:
                    x, y = float(G.nodes[p]['x']), float(G.nodes[p]['y'])
                    pt = gpd.GeoSeries([Point(x, y)], crs="EPSG:32614").to_crs(epsg=4326).iloc[0]
                    lat_paradas.append(pt.y)
                    lon_paradas.append(pt.x)
                
                fig2 = go.Figure()
                fig2.add_trace(go.Scattermapbox(mode="lines", lon=df_tsp['Longitud'], lat=df_tsp['Latitud'], line=dict(width=4, color="#b200ff"), name="Ruta TSP"))
                fig2.add_trace(go.Scattermapbox(mode="markers+text", lon=lon_paradas, lat=lat_paradas, marker=dict(size=[16]+[10]*(len(lon_paradas)-1), color=['#00FFCC']+['white']*(len(lon_paradas)-1)), text=["🏠 Almacén"] + [f"📦 P{i}" for i in range(1, len(lon_paradas))], textposition="top right", textfont=dict(color="black", size=12), name="Paradas"))
                fig2.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=lat_paradas[0], lon=lon_paradas[0]), zoom=12.5), margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig2, width='stretch')
                st.success(f"Logística resuelta: Se evaluaron matemáticamente las rutas entre {num_paradas} puntos para encontrar la secuencia de menor tiempo de conducción.")
            except:
                st.warning("Error topológico aislando un punto. Intenta de nuevo.")

# ==========================================
# TAB 3: ISÓCRONAS (COBERTURA ESPACIAL)
# ==========================================
with tab3:
    st.subheader("Análisis de Cobertura Geográfica (Isócronas)")
    st.markdown("¿Hasta dónde puede llegar un repartidor en un tiempo límite respetando el flujo vehicular?")
    minutos_limite = st.slider("Tiempo de Cobertura (Minutos)", 2, 15, 5)
    
    if st.button("Calcular Alcance", type="primary", key="btn_iso"):
        with st.spinner("Construyendo polígono de área de servicio..."):
            centro = random.choice(nodos_lista)[0]
            segundos_limite = minutos_limite * 60
            
            nodos_alcanzables = nx.single_source_dijkstra_path_length(G, centro, cutoff=segundos_limite, weight='tiempo_segundos')
            
            coords_utm = []
            for n in nodos_alcanzables.keys():
                coords_utm.append(Point(float(G.nodes[n]['x']), float(G.nodes[n]['y'])))
                
            gdf_puntos = gpd.GeoSeries(coords_utm, crs="EPSG:32614").to_crs(epsg=4326)
            lats_puntos, lons_puntos = gdf_puntos.y, gdf_puntos.x
            
            centro_pt = gpd.GeoSeries([Point(float(G.nodes[centro]['x']), float(G.nodes[centro]['y']))], crs="EPSG:32614").to_crs(epsg=4326).iloc[0]
            
            multipunto = MultiPoint(coords_utm)
            poligono_utm = multipunto.convex_hull
            
            # Usamos Plotly Express para evitar problemas de compatibilidad de mapas
            df_iso_puntos = pd.DataFrame({'Latitud': lats_puntos, 'Longitud': lons_puntos})
            fig3 = px.scatter_mapbox(df_iso_puntos, lat="Latitud", lon="Longitud", zoom=12.5, height=550)
            fig3.update_traces(marker=dict(size=5, color="#00FFCC", opacity=0.7))
            
            if len(coords_utm) >= 3 and poligono_utm.geom_type == 'Polygon':
                poligono_latlon = gpd.GeoSeries([poligono_utm], crs="EPSG:32614").to_crs(epsg=4326).iloc[0]
                lon_poly, lat_poly = poligono_latlon.exterior.coords.xy
                
                # Agregamos la traza del polígono usando líneas de Scattermapbox de forma segura
                fig3.add_trace(go.Scattermapbox(
                    mode="lines",
                    lon=list(lon_poly), lat=list(lat_poly),
                    fill="toself", fillcolor="rgba(178, 0, 255, 0.2)",
                    line=dict(color="#b200ff", width=2),
                    name=f"Área Máxima ({minutos_limite} min)"
                ))
            
            # Marcador del almacén origen
            fig3.add_trace(go.Scattermapbox(
                mode="markers+text",
                lon=[centro_pt.x], lat=[centro_pt.y],
                marker=dict(size=18, color="#FF3366"),
                text=["📍 Almacén"], textposition="bottom right",
                textfont=dict(color="black", size=15),
                name="Origen"
            ))
            
            fig3.update_layout(
                mapbox_style="open-street-map", 
                margin={"r":0,"t":0,"l":0,"b":0},
                legend=dict(bgcolor="rgba(255,255,255,0.7)", font=dict(color="black"))
            )
            
            st.plotly_chart(fig3, width='stretch')
            st.success(f"Logística resuelta: El polígono sombreado demuestra exactamente hasta qué calles puede llegar la unidad de reparto antes de rebasar los {minutos_limite} minutos.")
