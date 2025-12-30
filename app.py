import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuración de la página
st.set_page_config(page_title="Monitor de Licitaciones SIP Energy", page_icon="⚡", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Monitor de Licitaciones - SIP Energy")

# --- Barra Lateral ---
st.sidebar.header("Configuración de API")
DEFAULT_TICKET = "F8537A18-6766-4DEF-9E59-426B4FEE2844"
api_ticket = st.sidebar.text_input("Ingresa tu Ticket API", placeholder=DEFAULT_TICKET)

if not api_ticket:
    api_ticket = DEFAULT_TICKET
    st.sidebar.warning("⚠️ Usando ticket de prueba por defecto.")

# --- Lógica de Búsqueda ---
KEYWORDS = ['caldera', 'fotovoltaico', 'solar', 'eficiencia', 'climatización', 
            'eléctrico', 'montaje', 'industrial', 'térmico', 'mantención', 
            'hospital', 'escuela']

def fetch_licitaciones(ticket):
    results = []
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%d%m%Y") for i in range(3)]
    
    # Session para reutilizar la conexión y headers de navegador moderno
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    })
    
    with st.spinner('Consultando API de Mercado Público (esto puede tardar por los reintentos)...'):
        for date in dates:
            for attempt in range(3): # Reintentar hasta 3 veces
                url = f"http://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha={date}&ticket={ticket}"
                try:
                    response = session.get(url, timeout=25)
                    if response.status_code == 200:
                        data = response.json()
                        if "Listado" in data and data["Listado"]:
                            results.extend(data["Listado"])
                        break # Éxito: saltar al siguiente día
                    elif response.status_code == 401:
                        st.error(f"Ticket API inválido para la fecha {date}.")
                        break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    if attempt < 2:
                        time.sleep(3) # Esperar antes de reintentar
                        continue
                except Exception:
                    break
            
            time.sleep(1) # Pausa de cortesía entre días
    
    return results

def filter_licitaciones(listado, keywords):
    filtered = []
    for item in listado:
        nombre = str(item.get("Nombre", "")).lower()
        descripcion = str(item.get("Descripcion", "")).lower()
        if any(kw.lower() in nombre or kw.lower() in descripcion for kw in keywords):
            filtered.append({
                "Código Externo": f"http://www.mercadopublico.cl/ficha/al/id/{item.get('CodigoExterno')}",
                "Nombre": item.get("Nombre"),
                "Estado": item.get("Estado"),
                "Fecha Cierre": item.get("FechaCierre")
            })
    return filtered

# --- Ejecución ---
all_tenders = fetch_licitaciones(api_ticket)
filtered_tenders = filter_licitaciones(all_tenders, KEYWORDS)

st.metric("Total de Oportunidades Encontradas", len(filtered_tenders))

if filtered_tenders:
    df = pd.DataFrame(filtered_tenders)
    st.dataframe(
        df,
        column_config={
            "Código Externo": st.column_config.LinkColumn("Ficha Mercado Público", display_text="Ver Licitación"),
            "Nombre": st.column_config.TextColumn("Nombre", width="large")
        },
        hide_index=True,
        use_container_width=True
    )
    st.success("✅ Datos actualizados correctamente.")
else:
    st.info("No se encontraron licitaciones nuevas en los últimos 3 días. Por favor, revisa tu Ticket API si crees que es un error.")

st.markdown("---")
st.caption("Desarrollado para SIP Energy - Mercado Público Chile")
