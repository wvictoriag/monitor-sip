import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Monitor de Licitaciones SIP Energy", page_icon="⚡", layout="wide")

# Estilo personalizado para mejorar la estética
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Título Principal
st.title("⚡ Monitor de Licitaciones - SIP Energy")

# --- Barra Lateral (Configuración API) ---
st.sidebar.header("Configuración de API")
DEFAULT_TICKET = "F8537A18-6766-4DEF-9E59-426B4FEE2844"
api_ticket = st.sidebar.text_input("Ingresa tu Ticket API", placeholder=DEFAULT_TICKET)

if not api_ticket:
    api_ticket = DEFAULT_TICKET
    st.sidebar.warning("⚠️ Usando ticket de prueba por defecto.")

# --- Lógica de Búsqueda y Filtrado ---
KEYWORDS = ['caldera', 'fotovoltaico', 'solar', 'eficiencia', 'climatización', 
            'eléctrico', 'montaje', 'industrial', 'térmico', 'mantención', 
            'hospital', 'escuela']

def fetch_licitaciones(ticket):
    results = []
    # Obtener fechas de los últimos 3 días
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%d%m%Y") for i in range(3)]
    
    with st.spinner('Consultando API de Mercado Público...'):
        for date in dates:
            url = f"http://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha={date}&ticket={ticket}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if "Listado" in data and data["Listado"]:
                        results.extend(data["Listado"])
                else:
                    st.error(f"Error en API ({date}): Status {response.status_code}")
            except Exception as e:
                st.error(f"Error de conexión ({date}): {str(e)}")
    
    return results

def filter_licitaciones(listado, keywords):
    filtered = []
    for item in listado:
        # Algunos campos pueden venir como None, manejamos eso
        nombre = str(item.get("Nombre", "")).lower()
        descripcion = str(item.get("Descripcion", "")).lower()
        
        if any(kw.lower() in nombre or kw.lower() in descripcion for kw in keywords):
            filtered.append({
                "Código Externo": item.get("CodigoExterno"),
                "Nombre": item.get("Nombre"),
                "Estado": item.get("Estado"),
                "Fecha Cierre": item.get("FechaCierre"),
                "Link": f"http://www.mercadopublico.cl/ficha/al/id/{item.get('CodigoExterno')}"
            })
    return filtered

# --- Ejecución Principal ---
all_tenders = fetch_licitaciones(api_ticket)
filtered_tenders = filter_licitaciones(all_tenders, KEYWORDS)

# Mostrar Métrica
st.metric("Total de Oportunidades Encontradas", len(filtered_tenders))

if filtered_tenders:
    df = pd.DataFrame(filtered_tenders)
    
    # Configurar la columna de enlace para que sea clickeable
    st.dataframe(
        df,
        column_config={
            "Código Externo": st.column_config.LinkColumn(
                "Ficha Mercado Público",
                help="Haz clic para ver el detalle de la licitación",
                validate="^http://.*",
                max_chars=100,
                display_text=r"http://www.mercadopublico.cl/ficha/al/id/(.*)"
            ),
            "Link": None # Ocultar la columna Link original si se desea, o usarla directamente
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.info("💡 Haz clic en los códigos de la columna 'Ficha Mercado Público' para abrir la licitación.")
else:
    st.info("No se encontraron licitaciones con las palabras clave especificadas en los últimos 3 días.")

# Footer
st.markdown("---")
st.caption("Desarrollado para SIP Energy - API Mercado Público Chile")
