import streamlit as st
from sqlalchemy import text

# Configuración de la página
st.set_page_config(page_title="Control de Nóminas", layout="wide", page_icon="📝")

# 1. Conexión a la base de datos
conn = st.connection("postgresql", type="sql")

st.title("📝 Gestión de Firmas de Nómina")

# --- NUEVA SECCIÓN: BUSCADOR (HASTA ARRIBA) ---
st.markdown("### 🔍 Buscar Trabajador")
busqueda = st.text_input(
    "Filtrar por nombre, número de trabajador o número de hoja", 
    placeholder="Ejemplo: Juan Perez o 12345...",
    label_visibility="collapsed"
)
st.markdown("---")

# --- SECCIÓN: REGISTRO (BARRA LATERAL) ---
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
        
        if st.form_submit_button("Añadir a la lista"):
            if nom and hoja:
                query_insert = text("""
                    INSERT INTO registros_nomina (num_trabajador, nombre, num_hoja, quincena, mes, anio) 
                    VALUES (:num, :nom, :hoja, :quin, :mes, :anio)
                """)
                try:
                    with conn.session as s:
                        s.execute(query_insert, {"num": num, "nom": nom, "hoja": hoja, "quin": quin, "mes": mes, "anio": anio})
                        s.commit()
                    st.success(f"Registrado: {nom}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Completa los campos obligatorios.")

# --- SECCIÓN: LISTADO DINÁMICO ---
st.subheader("Pendientes por Firmar")

# Consultar datos frescos
df = conn.query("SELECT * FROM registros_nomina WHERE firmado = FALSE ORDER BY id DESC", ttl=0)

if not df.empty:
    # Lógica de Filtrado (Lista en lugar de Tabla)
    if busqueda:
        df_mostrar = df[
            df['nombre'].str.contains(busqueda, case=False, na=False) | 
            df['num_trabajador'].astype(str).str.contains(busqueda) |
            df['num_hoja'].astype(str).str.contains(busqueda, case=False, na=False)
        ]
    else:
        df_mostrar = df

    if not df_mostrar.empty:
        # Encabezados
        h1, h2, h3, h4 = st.columns([1, 3, 1.5, 1.5])
        h1.write("**ID / Hoja**")
        h2.write("**Nombre**")
        h3.write("**Periodo**")
        h4.write("**Acción**")
        st.divider()

        # Renderizado de la lista
        for _, row in df_mostrar.iterrows():
            c1, c2, c3, c4 = st.columns([1, 3, 1.5, 1.5])
            
            with c1:
                st.write(f"#{row['num_trabajador']}")
                st.caption(f"📄 Hoja: {row['num_hoja']}")
            
            with c2:
                st.write(f"**{row['nombre']}**")
            
            with c3:
                st.write(f"{row['mes']} Q{row['quincena']}")
                st.caption(f"Año: {row['anio']}")
                
            with c4:
                if st.button("Confirmar Firma", key=f"f_{row['id']}", use_container_width=True):
                    with conn.session as s:
                        s.execute(text("UPDATE registros_nomina SET firmado = TRUE WHERE id = :id"), {"id": row['id']})
                        s.commit()
                    st.toast(f"Firma de {row['nombre']} registrada.")
                    st.rerun()
    else:
        st.warning(f"No se encontraron resultados para: '{busqueda}'")
else:
    st.info("No hay firmas pendientes. ✨")