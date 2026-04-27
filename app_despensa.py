import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# URL verificada de tu documento
URL_HOJA = "https://docs.google.com/spreadsheets/d/18NivGQDAaAlkzU9WCi7iqO9aTlabs5FqdqdYN839qtM/edit?usp=sharing"

# --- JS PARA TECLADO NUMÉRICO ---
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

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "carrito" not in st.session_state:
    st.session_state.carrito = []
if "limpiador" not in st.session_state:
    st.session_state.limpiador = 0

# --- FUNCIONES DE DATOS ---
def cargar_datos_cache():
    try:
        # Intentamos leer la hoja "Historial"
        return conn.read(spreadsheet=URL_HOJA, worksheet="Historial", ttl=0)
    except Exception as e:
        st.error(f"Error al leer: {e}")
        return pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])

def guardar_compra(total, items):
    try:
        # 1. Intentar obtener datos previos
        df_existente = cargar_datos_cache()
        
        # 2. Preparar nueva fila
        nueva_fila = pd.DataFrame([{
            "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "TOTAL": float(total),
            "ITEMS": json.dumps(items)
        }])
        
        # 3. Combinar
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        # 4. Actualizar en la nube
        conn.update(spreadsheet=URL_HOJA, worksheet="Historial", data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# --- INTERFAZ ---
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
                p = float(precio_raw.replace(',', '.'))
                st.session_state.carrito.append({"producto": producto, "precio": p})
                st.session_state.limpiador += 1
                st.rerun()
            except:
                st.error("Número inválido")

    if st.session_state.carrito:
        df_c = pd.DataFrame(st.session_state.carrito)
        st.table(df_c)
        total_p = df_c["precio"].sum()
        st.metric("Total", f"${total_p:,.2f}")

        if st.button("✅ Finalizar y Guardar"):
            with st.spinner("Sincronizando..."):
                if guardar_compra(total_p, st.session_state.carrito):
                    st.session_state.carrito = []
                    st.success("¡Compra guardada!")
                    st.balloons()
                    st.rerun()

with t2:
    df_h = cargar_datos_cache()
    if not df_h.empty:
        st.line_chart(df_h.set_index("FECHA")["TOTAL"])
        st.write(df_h)