import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json

# 1. Configuración de la página (Estilo iOS)
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# 2. Estética personalizada con CSS
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; width: 100%; height: 3em; background-color: #007AFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. Función para cargar datos con caché (evita lentitud)
@st.cache_data(ttl=300)
def cargar_datos_cache():
    try:
        df = conn.read(worksheet="Historial", ttl=0)
        return df
    except Exception:
        # Si la hoja está vacía, creamos la estructura base
        return pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])

# 5. Función para guardar nueva compra
def guardar_compra(total, items):
    df_historial = conn.read(worksheet="Historial", ttl=0)
    
    nueva_fila = {
        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "TOTAL": total,
        "ITEMS": json.dumps(items)
    }
    
    # Concatenar y subir a la nube
    df_actualizado = pd.concat([df_historial, pd.DataFrame([nueva_fila])], ignore_index=True)
    conn.write(worksheet="Historial", data=df_actualizado)
    st.cache_data.clear() # Limpiar caché para ver los cambios de inmediato

# 6. Lógica de Estado (Carrito)
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# 7. INTERFAZ DE USUARIO
st.title("🛒 Despensa Pro")

tab1, tab2 = st.tabs(["🛍️ Nueva Compra", "📊 Análisis"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        producto = st.text_input("Producto")
    with col2:
        precio = st.number_input("Precio", min_value=0.0, step=0.5)

    if st.button("Agregar al Carrito"):
        if producto and precio > 0:
            st.session_state.carrito.append({"producto": producto, "precio": precio})
            st.toast(f"Agregado: {producto}")

    if st.session_state.carrito:
        st.write("### Tu Carrito")
        df_carrito = pd.DataFrame(st.session_state.carrito)
        st.table(df_carrito)
        
        total_actual = df_carrito["precio"].sum()
        st.metric("Total a Pagar", f"${total_actual:,.2f}")

        if st.button("✅ Finalizar y Guardar en la Nube"):
            with st.spinner("Subiendo datos..."):
                guardar_compra(total_actual, st.session_state.carrito)
                st.session_state.carrito = []
                st.success("¡Compra registrada exitosamente!")
                st.balloons()
                st.rerun()

with tab2:
    df_historial = cargar_datos_cache()
    if not df_historial.empty:
        st.subheader("Histórico de Gastos")
        
        # Convertir fecha para el gráfico
        df_historial["FECHA"] = pd.to_datetime(df_historial["FECHA"])
        
        # Gráfico de líneas
        chart_data = df_historial.set_index("FECHA")["TOTAL"]
        st.line_chart(chart_data)
        
        if st.checkbox("Ver detalle de compras pasadas"):
            st.write(df_historial)
    else:
        st.info("Aún no hay compras registradas en el historial.")