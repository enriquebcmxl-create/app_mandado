import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json
import streamlit.components.v1 as components

# 1. Configuración de la página (Estilo iOS)
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# 2. Estética personalizada y Truco de Teclado Numérico
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; width: 100%; height: 3em; background-color: #007AFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 15px; }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# JS para forzar teclado numérico en dispositivos móviles
components.html(
    """
    <script>
    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
    inputs.forEach(input => {
        if (input.getAttribute('aria-label') === "Precio") {
            input.setAttribute('inputmode', 'decimal');
            input.setAttribute('pattern', '[0-9]*');
        }
    });
    </script>
    """,
    height=0,
)

# 3. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. Función para cargar datos con caché
@st.cache_data(ttl=300)
def cargar_datos_cache():
    try:
        df = conn.read(worksheet="Historial", ttl=0)
        return df
    except Exception:
        return pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])

# 5. Función para guardar nueva compra
def guardar_compra(total, items):
    try:
        df_historial = conn.read(worksheet="Historial", ttl=0)
    except Exception:
        df_historial = pd.DataFrame(columns=["FECHA", "TOTAL", "ITEMS"])
    
    nueva_fila = {
        "FECHA": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "TOTAL": float(total),
        "ITEMS": json.dumps(items)
    }
    
    nueva_fila_df = pd.DataFrame([nueva_fila])
    
    if df_historial.empty:
        df_actualizado = nueva_fila_df
    else:
        df_actualizado = pd.concat([df_historial, nueva_fila_df], ignore_index=True)
    
    conn.update(worksheet="Historial", data=df_actualizado)
    st.cache_data.clear()

# 6. Lógica de Estado (Carrito)
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# 7. INTERFAZ DE USUARIO
st.title("🛒 Despensa Pro")

tab1, tab2 = st.tabs(["🛍️ Nueva Compra", "📊 Análisis"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        producto = st.text_input("Producto", placeholder="Ej. Leche")
    with col2:
        # El label "Precio" es clave para que el script de arriba lo encuentre
        precio_input = st.text_input("Precio", placeholder="0.00")

    if st.button("Agregar al Carrito"):
        if producto and precio_input:
            try:
                # Reemplazamos coma por punto por si el teclado numérico usa comas
                precio_limpio = precio_input.replace(',', '.')
                precio = float(precio_limpio)
                if precio > 0:
                    st.session_state.carrito.append({"producto": producto, "precio": precio})
                    st.toast(f"Agregado: {producto}")
                    # No reiniciamos el producto aquí para que sea más rápido si compras varios iguales
                else:
                    st.error("El precio debe ser mayor a 0")
            except ValueError:
                st.error("Ingresa un número válido")
        else:
            st.warning("Faltan datos")

    if st.session_state.carrito:
        st.write("### Tu Carrito")
        df_carrito = pd.DataFrame(st.session_state.carrito)
        st.table(df_carrito)
        
        total_actual = df_carrito["precio"].sum()
        st.metric("Total a Pagar", f"${total_actual:,.2f}")

        if st.button("✅ Finalizar y Guardar en la Nube"):
            with st.spinner("Sincronizando con la nube..."):
                guardar_compra(total_actual, st.session_state.carrito)
                st.session_state.carrito = []
                st.success("¡Listo! Guardado en la base de datos.")
                st.balloons()
                st.rerun()

with tab2:
    df_historial = cargar_datos_cache()
    if not df_historial.empty:
        st.subheader("Tendencia de Gastos")
        df_plot = df_historial.copy()
        df_plot["FECHA"] = pd.to_datetime(df_plot["FECHA"])
        chart_data = df_plot.set_index("FECHA")["TOTAL"]
        st.line_chart(chart_data)
        
        if st.checkbox("Ver historial completo"):
            st.write(df_historial)
    else:
        st.info("El historial aparecerá después de tu primera compra.")