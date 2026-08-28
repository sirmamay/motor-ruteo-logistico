Markdown
# 🚚 Motor de Inteligencia Operativa y Ruteo (Última Milla)

Plataforma analítica desarrollada en Python para la optimización matemática de logística urbana utilizando datos oficiales de la Red Nacional de Caminos (INEGI). Diseñada para transformar la planeación operativa tradicional en decisiones basadas en teoría de grafos, minimizando costos y maximizando la eficiencia de las flotillas en campo.

## ⚙️ Funcionalidades Principales

* **Análisis Competitivo de Rutas:** Implementación de heurísticas para evaluar y contrastar matemáticamente la ruta más corta (distancia física) frente a la más rápida (tiempo real), procesando velocidades límite y topología vehicular.
* **Optimización de Flotillas (TSP):** Integración de algoritmos de aproximación para resolver el Problema del Agente Viajero (Traveling Salesperson Problem), calculando la secuenciación óptima de reparto para múltiples paradas desde un centro de distribución.
* **Inteligencia de Cobertura Espacial:** Generación dinámica de polígonos de isócronas (áreas de servicio por tiempo) para visualizar exactamente hasta qué calles puede llegar un repartidor respetando la geometría urbana y el flujo de tráfico.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.x
* **Frontend / Dashboard:** Streamlit
* **Geometría y Análisis Espacial:** GeoPandas, Shapely
* **Teoría de Grafos:** NetworkX
* **Visualización Dinámica:** Plotly (Scattermapbox / OpenStreetMap)

## 🚀 Guía de Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/motor-ruteo-logistico.git](https://github.com/tu-usuario/motor-ruteo-logistico.git)
   cd motor-ruteo-logistico
Crear y activar un entorno virtual (Recomendado):

Bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
Instalar dependencias:

Bash
pip install -r requirements.txt
Ejecutar la aplicación:

Bash
streamlit run app_logistica.py
📁 Estructura del Proyecto
app_logistica.py: Script principal de la aplicación y renderizado de la interfaz.

red_vial_inegi_saltillo.graphml: Base de datos topológica de la red de caminos de Saltillo.

requirements.txt: Dependencias y versiones del entorno.

Autor: Mario Alberto Miramontes López

Especialista en Automatización de Procesos (RPA) e Inteligencia Espacial (GIS).
