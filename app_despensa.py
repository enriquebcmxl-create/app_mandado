import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json
import streamlit.components.v1 as components

# 1. Configuración de la página
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# URL de tu hoja (Copiada de tu captura)
URL_HOJA = "https://docs.google.com/spreadsheets/d/18NivGQDAaAlkzU9WCi7iqO9aTlabs5FqdqdYN839qtM/edit?usp=sharing"

# 2. Estética iOS y JS para teclado numérico
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; width: 100%; height: 3em; background-color: #007AFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 15px; }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

components.html(
    """
    <script>
    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        if (input.getAttribute('aria-label') === "Precio") {
            input.setAttribute('inputmode', 'decimal');
        }
    });
    </script>
    """,
    height=0,
)

# 3. Conexión y Estado
# Cambiamos la forma de llamar a la conexión para evitar el AttributeError
conn = st.connection("gsheets", type=GSheetsConnection)

if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "limpiador" not in st.session_state:
    st.session_state.limpiador = 0

# 4. Funciones de Datos
def cargar_datos_cache():
    try:
        return conn.read(spreadsheet=URL_HOJA, worksheet="Historial")
    except:
        return pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])

def guardar_compra(total, items):
    try:
        df_existente = conn.read(spreadsheet=URL_HOJA, worksheet="Historial")
    except:
        df_existente = pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])
    
    nueva_fila = pd.DataFrame([{
        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "TOTAL": float(total),
        "ITEMS": json.dumps(items)
    }])
    
    df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
    # Usamos la sintaxis más compatible para subir datos
    conn.update(spreadsheet=URL_HOJA, worksheet="Historial", data=df_final)

# 5. Interfaz
st.title("🛒 Despensa Pro")
t1, t2 = st.tabs(["🛍️ Nueva Compra", "📊 Historial"])

with t1:
    c1, c2 = st.columns(2)
    with c1:
        producto = st.text_input("Producto", placeholder="Ej. Leche", key=f"p_{st.session_state.limpiador}")
    with c2:
        precio_raw = st.text_input("Precio", placeholder="0.00", key=f"v_{st.session_state.limpiador}")

    if st.button("Agregar"):
        if producto and precio_raw:
            try:
                precio = float(precio_raw.replace(',', '.'))
                st.session_state.carrito.append({"producto": producto, "precio": precio})
                st.session_state.limpiador += 1
                st.rerun()
            except:
                st.error("Precio no válido")

    if st.session_state.carrito:
        df_c = pd.DataFrame(st.session_state.carrito)
        st.table(df_c)
        total = df_c["precio"].sum()
        st.metric("Total", f"${total:,.2f}")

        if st.button("✅ Finalizar y Guardar"):
            with st.spinner("Guardando..."):
                guardar_compra(total, st.session_state.carrito)
                st.session_state.carrito = []
                st.success("¡Guardado!")
                st.rerun()

with t2:
    df_h = cargar_datos_cache()
    if not df_h.empty:
        st.line_chart(df_h.set_index("FECHA")["TOTAL"])
        st.write(df_h)