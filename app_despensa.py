import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json
import streamlit.components.v1 as components

# 1. Configuración de la página (Estilo iOS)
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# 2. Estética y JS para Teclado Numérico (Forzar modo decimal)
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; width: 100%; height: 3em; background-color: #007AFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 15px; }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Inyección de JS para que el iPhone saque el teclado de números
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

# 3. Conexión y Inicialización de variables de sesión
conn = st.connection("gsheets", type=GSheetsConnection)

if "carrito" not in st.session_state:
    st.session_state.carrito = []
# Este contador 'limpiador' es el que borra los campos automáticamente
if "limpiador" not in st.session_state:
    st.session_state.limpiador = 0

# 4. Funciones de Datos
@st.cache_data(ttl=300)
def cargar_datos_cache():
    try:
        return conn.read(worksheet="Historial", ttl=0)
    except Exception:
        return pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])

def guardar_compra(total, items):
    try:
        df_historial = conn.read(worksheet="Historial", ttl=0)
    except Exception:
        df_historial = pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])
    
    nueva_fila = pd.DataFrame([{
        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "TOTAL": float(total),
        "ITEMS": json.dumps(items)
    }])
    
    df_actualizado = pd.concat([df_historial, nueva_fila], ignore_index=True)
    conn.update(worksheet="Historial", data=df_actualizado)
    st.cache_data.clear()

# 5. INTERFAZ DE USUARIO
st.title("🛒 Despensa Pro")

tab1, tab2 = st.tabs(["🛍️ Nueva Compra", "📊 Análisis"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Usamos la llave dinámica para que se limpie solo
        producto = st.text_input("Producto", placeholder="Ej. Leche", key=f"prod_{st.session_state.limpiador}")
    with col2:
        # Aquí el placeholder está vacío, por lo que no hay nada que borrar
        precio_raw = st.text_input("Precio", placeholder="", key=f"pre_{st.session_state.limpiador}")

    if st.button("Agregar al Carrito"):
        if producto and precio_raw:
            try:
                # Limpiamos el texto por si el teclado mete comas en lugar de puntos
                precio = float(precio_raw.replace(',', '.'))
                st.session_state.carrito.append({"producto": producto, "precio": precio})
                st.toast(f"✅ {producto} agregado")
                
                # ¡MAGIA! Aumentamos el contador y los campos se vacían solos
                st.session_state.limpiador += 1
                st.rerun()
            except ValueError:
                st.error("⚠️ Escribe un número válido")
        else:
            st.warning("⚠️ Llena ambos cuadros")

    if st.session_state.carrito:
        st.write("---")
        df_carrito = pd.DataFrame(st.session_state.carrito)
        st.table(df_carrito)
        
        total_pago = df_carrito["precio"].sum()
        st.metric("Total Actual", f"${total_pago:,.2f}")

        if st.button("✅ Finalizar y Guardar en la Nube"):
            with st.spinner("Subiendo datos..."):
                guardar_compra(total_pago, st.session_state.carrito)
                st.session_state.carrito = []
                st.success("¡Compra guardada con éxito!")
                st.balloons()
                st.rerun()

with tab2:
    df = cargar_datos_cache()
    if not df.empty:
        st.subheader("Tu Histórico")
        df["FECHA"] = pd.to_datetime(df["FECHA"])
        st.line_chart(df.set_index("FECHA")["TOTAL"])
    else:
        st.info("El historial aparecerá después de tu primera compra.")