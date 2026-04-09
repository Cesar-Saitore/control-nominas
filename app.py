import streamlit as st

st.set_page_config(page_title="Control de Nóminas", layout="wide")

# Conexión a la base de datos (se configura en .streamlit/secrets.toml)
conn = st.connection("postgresql", type="sql")

st.title("📝 Gestión de Firmas de Nómina")

# --- SECCIÓN 1: REGISTRO ---
with st.sidebar:
    st.header("Registrar Pendiente")
    with st.form("registro_form", clear_on_submit=True):
        num = st.number_input("Número de Trabajador", step=1)
        nom = st.text_input("Nombre Completo")
        quin = st.selectbox("Quincena", [1, 2])
        mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        anio = st.number_input("Año", value=2026)
        
        if st.form_submit_button("Añadir a la lista"):
            query = f"INSERT INTO registros_nomina (num_trabajador, nombre, quincena, mes, anio) VALUES ({num}, '{nom}', {quin}, '{mes}', {anio})"
            with conn.session as s:
                s.execute(query)
                s.commit()
            st.success("Trabajador registrado")

# --- SECCIÓN 2: GESTIÓN DE FIRMAS ---
st.subheader("Pendientes por Firmar")

# Consultar pendientes
df_pendientes = conn.query("SELECT * FROM registros_nomina WHERE firmado = FALSE", ttl=0)

if not df_pendientes.empty:
    for index, row in df_pendientes.iterrows():
        col1, col2, col3 = st.columns([1, 3, 1])
        col1.write(f"#{row['num_trabajador']}")
        col2.write(f"**{row['nombre']}** - {row['mes']} (Q{row['quincena']}) {row['anio']}")
        
        # Botón para eliminar de la lista (marcar como firmado)
        if col3.button("Marcar Firmado", key=row['id']):
            with conn.session as s:
                s.execute(f"UPDATE registros_nomina SET firmado = TRUE WHERE id = {row['id']}")
                s.commit()
            st.rerun()
else:
    st.info("No hay firmas pendientes por ahora. ✨")