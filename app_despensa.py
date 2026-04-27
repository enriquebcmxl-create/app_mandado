import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json
import streamlit.components.v1 as components

# 1. Configuración de la página
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# URL de tu hoja (Verificada)
URL_HOJA = "https://docs.google.com/spreadsheets/d/18NivGQDAaAlkzU9WCi7iqO9aTlabs5FqdqdYN839qtM/edit?usp=sharing"

# 2. Estética y JS para Teclado
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; width: 100%; height: 3em; background-color: #007AFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 15px; }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Conexión y Estado
conn = st.connection("gsheets", type=GSheetsConnection)

if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "limpiador" not in st.session_state:
    st.session_state.limpiador = 0

# 4. Funciones de Datos
def cargar_datos_cache():
    try:
        return conn.read(spreadsheet=URL_HOJA, worksheet="Historial", ttl=0)
    except Exception as e:
        return pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])

def guardar_compra(total, items):
    try:
        df_existente = cargar_datos_cache()
        nueva_fila = pd.DataFrame([{
            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "TOTAL": float(total),
            "ITEMS": json.dumps(items)
        }])
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(spreadsheet=URL_HOJA, worksheet="Historial", data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

# 5. Interfaz
st.title("🛒 Despensa Pro")
t1, t2 = st.tabs(["🛍️ Nueva Compra", "📊 Historial"])

with t1:
    col1, col2 = st.columns(2)
    with col1:
        producto = st.text_input("Producto", key=f"p_{st.session_state.limpiador}")
    with col2:
        precio_raw = st.text_input("Precio", key=f"v_{st.session_state.limpiador}")

    if st.button("Agregar"):
        if producto and precio_raw:
            try:
                p = float(precio_raw.replace(',', '.'))
                st.session_state.carrito.append({"producto": producto, "precio": p})
                st.session_state.limpiador += 1
                st.rerun()
            except:
                st.error("Precio no válido")

    if st.session_state.carrito:
        df_c = pd.DataFrame(st.session_state.carrito)
        st.table(df_c)
        total_p = df_c["precio"].sum()
        st.metric("Total", f"${total_p:,.2f}")

        if st.button("✅ Finalizar y Guardar"):
            if guardar_compra(total_p, st.session_state.carrito):
                st.session_state.carrito = []
                st.success("¡Guardado!")
                st.balloons()
                st.rerun()

with t2:
    df_h = cargar_datos_cache()
    if not df_h.empty:
        st.write(df_h)