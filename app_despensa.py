import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json

# Configuración estilo iOS (Limpio y ancho)
st.set_page_config(page_title="Despensa Pro", page_icon="🛒", layout="centered")

# Estética personalizada con CSS para bordes redondeados y fuentes claras
st.markdown("""
    <style>
    .stButton>button { border-radius: 10px; width: 100%; height: 3em; background-color: #007AFF; color: white; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# ================= PERSISTENCIA DE DATOS (OPTIMIZADA) =================

@st.cache_data(ttl=300) # Caché de 5 minutos para evitar latencia de red
def cargar_datos_cache():
    try:
        df = conn.read(worksheet="Historial", ttl=0)
        return df if df is not None else pd.DataFrame(columns=["fecha","total","items"])
    except:
        return pd.DataFrame(columns=["fecha","total","items"])

def guardar_compra(total, items):
    df_historial = conn.read(worksheet="Historial", ttl=0)
    nueva_fila = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": total,
        "items": json.dumps(items)
    }
    df_actualizado = pd.concat([df_historial, pd.DataFrame([nueva_fila])], ignore_index=True)
    conn.write(worksheet="Historial", data=df_actualizado)
    st.cache_data.clear() # Limpia el caché para mostrar los nuevos datos

# ================= LÓGICA DE ESTADO =================
if "carrito" not in st.session_state:
    st.session_state.carrito = []

# ================= INTERFAZ DE USUARIO =================
st.title("🛒 Despensa Pro")

tab1, tab2 = st.tabs(["🛍️ Nueva Compra", "📊 Análisis"])

with tab1:
    presupuesto = st.sidebar.number_input("Presupuesto Mensual ($)", value=1500.0, step=100.0)
    
    with st.expander("➕ Agregar Producto", expanded=True):
        col_prod, col_cat = st.columns([2, 1])
        nombre = col_prod.text_input("¿Qué compraste?")
        categoria = col_cat.selectbox("Categoría", ["Alimentos","Limpieza","Carnes","Lácteos","Bebidas","Otros"])
        
        col_pre, col_can = st.columns(2)
        precio = col_pre.number_input("Precio Unitario", min_value=0.0, step=0.5)
        cantidad = col_can.number_input("Cantidad", min_value=1, value=1)
        
        if st.button("Agregar al Carrito"):
            if nombre:
                st.session_state.carrito.append({
                    "producto": nombre,
                    "categoria": categoria,
                    "cantidad": cantidad,
                    "subtotal": precio * cantidad
                })
                st.rerun()

    if st.session_state.carrito:
        st.subheader("Tu Carrito")
        # Editor interactivo: permite borrar filas seleccionándolas
        df_edit = st.data_editor(
            pd.DataFrame(st.session_state.carrito),
            use_container_width=True,
            num_rows="dynamic",
            key="editor_carrito"
        )
        
        total_actual = df_edit["subtotal"].sum()
        
        # Métricas visuales
        m1, m2 = st.columns(2)
        restante = presupuesto - total_actual
        m1.metric("Total Hoy", f"${total_actual:.2f}")
        m2.metric("Disponible", f"${restante:.2f}", delta=f"{restante}", delta_color="normal")

        if total_actual > presupuesto:
            st.error(f"⚠️ Has excedido el presupuesto por ${abs(restante):.2f}")

        if st.button("✅ Finalizar y Guardar en la Nube"):
            guardar_compra(total_actual, df_edit.to_dict(orient="records"))
            st.session_state.carrito = []
            st.success("¡Compra registrada exitosamente!")
            st.balloons()
            st.rerun()

with tab2:
    df_historial = cargar_datos_cache()
    if not df_historial.empty:
        st.subheader("Histórico de Gastos")
        df_historial["fecha"] = pd.to_datetime(df_historial["fecha"])
        
        # Gráfico de líneas fluido
        chart_data = df_historial.set_index("fecha")["total"]
        st.line_chart(chart_data)
        
        if st.checkbox("Ver detalle de compras pasadas"):
            st.write(df_historial)
    else:
        st.info("Aún no hay compras registradas en el historial.") 