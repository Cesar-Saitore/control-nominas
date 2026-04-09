import streamlit as st
from sqlalchemy import text

# Configuración de la página
st.set_page_config(page_title="Control de Nóminas", layout="wide", page_icon="📝")

# 1. Conexión a la base de datos
# Asegúrate de tener los secretos configurados en Streamlit Cloud o en .streamlit/secrets.toml
conn = st.connection("postgresql", type="sql")

st.title("📝 Gestión de Firmas de Nómina")
st.markdown("---")

# --- SECCIÓN 1: REGISTRO DE TRABAJADORES (BARRA LATERAL) ---
with st.sidebar:
    st.header("Registrar Pendiente")
    with st.form("registro_form", clear_on_submit=True):
        num = st.number_input("Número de Trabajador", step=1, min_value=1)
        nom = st.text_input("Nombre Completo")
        hoja = st.text_input("Número de Hoja / Folio")
        quin = st.selectbox("Quincena", [1, 2])
        mes = st.selectbox("Mes", [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ])
        anio = st.number_input("Año", value=2026)
        
        submit = st.form_submit_button("Añadir a la lista")
        
        if submit:
            if nom and hoja:
                query_insert = text("""
                    INSERT INTO registros_nomina (num_trabajador, nombre, num_hoja, quincena, mes, anio) 
                    VALUES (:num, :nom, :hoja, :quin, :mes, :anio)
                """)
                try:
                    with conn.session as s:
                        s.execute(query_insert, {
                            "num": num, 
                            "nom": nom, 
                            "hoja": hoja, 
                            "quin": quin, 
                            "mes": mes, 
                            "anio": anio
                        })
                        s.commit()
                    st.success(f"Registrado: {nom} (Hoja {hoja})")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("Por favor rellena el nombre y el número de hoja.")

# --- SECCIÓN 2: GESTIÓN DE FIRMAS (CUERPO PRINCIPAL) ---
st.subheader("Pendientes por Firmar")

# Consultar solo los que NO han firmado
# Usamos ttl=0 para que la consulta siempre traiga datos frescos de la DB
query_select = "SELECT * FROM registros_nomina WHERE firmado = FALSE ORDER BY id DESC"
df_pendientes = conn.query(query_select, ttl=0)

if not df_pendientes.empty:
    # Encabezados de tabla simples
    cols_header = st.columns([1, 3, 1.5, 1.5])
    cols_header[0].write("**ID/Hoja**")
    cols_header[1].write("**Nombre del Trabajador**")
    cols_header[2].write("**Periodo**")
    cols_header[3].write("**Acción**")
    st.markdown("---")

    for index, row in df_pendientes.iterrows():
        c1, c2, c3, c4 = st.columns([1, 3, 1.5, 1.5])
        
        with c1:
            st.write(f"#{row['num_trabajador']}")
            st.caption(f"Hoja: {row['num_hoja']}")
        
        with c2:
            st.write(f"**{row['nombre']}**")
        
        with c3:
            st.write(f"{row['mes']} (Q{row['quincena']})")
            st.caption(f"Año: {row['anio']}")
            
        with c4:
            # Botón único para cada registro usando su ID de base de datos
            if st.button("Marcar Firmado", key=f"btn_{row['id']}", use_container_width=True, type="primary"):
                query_update = text("UPDATE registros_nomina SET firmado = TRUE WHERE id = :id_reg")
                try:
                    with conn.session as s:
                        s.execute(query_update, {"id_reg": row['id']})
                        s.commit()
                    st.toast(f"Firma confirmada para {row['nombre']}")
                    st.rerun() # Recarga la app para que desaparezca de la lista
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")
else:
    st.balloons() # Pequeña animación de éxito si no hay pendientes
    st.info("¡Excelente! No hay firmas pendientes por el momento. ✨")

# --- SECCIÓN 3: BÚSQUEDA RÁPIDA (OPCIONAL) ---
with st.expander("🔍 Buscar trabajador específico"):
    busqueda = st.text_input("Escribe el nombre o número de trabajador")
    if busqueda:
        # Buscamos coincidencias en nombre o número de trabajador
        df_busqueda = df_pendientes[
            df_pendientes['nombre'].str.contains(busqueda, case=False, na=False) | 
            df_pendientes['num_trabajador'].astype(str).str.contains(busqueda)
        ]
        st.dataframe(df_busqueda, use_container_width=True)