import streamlit as st
from streamlit_calendar import calendar
import sqlite3
import datetime
import pandas as pd
import hashlib
import os
import base64
import urllib.parse

# Configuración inicial de la página
st.set_page_config(
    page_title="Judit Domingo - Centre d'Estètica",
    page_icon="💆‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "gestion_estetica_v2.db"

# Función para cargar el logo en Base64
def cargar_logo_base64():
    directorio = os.path.dirname(os.path.abspath(__file__))
    nombres_posibles = ["imagen_2026-10-08_205258476.jpg", "images.jpg", "logo.jpg", "logo.png", "images.png"]
    
    for nombre in nombres_posibles:
        ruta_completa = os.path.join(directorio, nombre)
        if os.path.exists(ruta_completa):
            try:
                with open(ruta_completa, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                    mime_type = "image/png" if nombre.endswith(".png") else "image/jpeg"
                    return f"data:{mime_type};base64,{encoded_string}"
            except Exception:
                pass
    return None

logo_data_uri = cargar_logo_base64()

# --- SISTEMA DE AUTENTICACIÓN / LOGIN CON LOGO GRANDE ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("""
        <style>
        .login-logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .login-logo-container img {
            width: 100%;
            max-width: 220px;
            height: auto;
            border-radius: 12px;
            border: 1px solid #d4af37;
            box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.3);
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        
        if logo_data_uri:
            st.markdown(f"""
                <div class="login-logo-container">
                    <img src="{logo_data_uri}" alt="Judit Domingo Centre d'Estètica">
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="font-size: 28px; color: #d4af37; margin-bottom: 0px;">Judit Domingo</h1>
                <p style="color: #d4af37; font-size: 11px; letter-spacing: 3px; font-weight: 300; margin-top: 2px;">CENTRE D'ESTÈTICA</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("🔑 Iniciar Sesión", use_container_width=True)

            if submit:
                if "passwords" in st.secrets and user_input in st.secrets["passwords"]:
                    if password_input == st.secrets["passwords"][user_input]:
                        st.session_state["authenticated"] = True
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
                elif password_input == "1234":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña no válidos")

    return False

if not check_password():
    st.stop()

# --- BASE DE DATOS E INICIALIZACIÓN ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        primer_apellido TEXT,
                        segundo_apellido TEXT,
                        sexo TEXT,
                        telefono TEXT,
                        telefono_fijo TEXT,
                        email TEXT,
                        dni TEXT,
                        direccion TEXT,
                        ciudad TEXT,
                        cp TEXT,
                        fecha_nacimiento TEXT,
                        notas TEXT,
                        info_clinica TEXT,
                        rgpd INTEGER DEFAULT 1)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS servicios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        duracion_min INTEGER NOT NULL,
                        precio REAL NOT NULL,
                        color TEXT DEFAULT '#9b59b6')''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS citas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_inicio TEXT NOT NULL,
                        fecha_fin TEXT NOT NULL,
                        cliente_id INTEGER,
                        servicio_id INTEGER,
                        notas TEXT,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                        FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS facturas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        num_factura TEXT UNIQUE,
                        fecha_hora TEXT,
                        concepto TEXT,
                        total REAL,
                        hash_registro TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS bloqueos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_inicio TEXT NOT NULL,
                        fecha_fin TEXT NOT NULL,
                        motivo TEXT)''')

    # Tabla para el control de la caja del día
    cursor.execute('''CREATE TABLE IF NOT EXISTS cajas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT UNIQUE NOT NULL,
                        abonos_efectivo REAL DEFAULT 0.0,
                        ingresos REAL DEFAULT 0.0,
                        extracciones REAL DEFAULT 0.0,
                        descuadre REAL DEFAULT 0.0,
                        total_caja REAL DEFAULT 0.0,
                        estado TEXT DEFAULT 'Cerrada')''')

    cursor.execute("SELECT COUNT(*) FROM servicios")
    if cursor.fetchone()[0] == 0:
        servicios_def = [
            ("Manicura Semipermanente", 45, 25.0, "#e74c3c"),
            ("Acrylgel uñas largas", 60, 40.0, "#9b59b6"),
            ("Higiene Facial Profunda", 60, 45.0, "#3498db"),
            ("Diseño de Cejas", 30, 18.0, "#2ecc71")
        ]
        cursor.executemany("INSERT INTO servicios (nombre, duracion_min, precio, color) VALUES (?,?,?,?)", servicios_def)

    conn.commit()
    conn.close()

    importar_excel_koibox()

def importar_excel_koibox():
    directorio = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(directorio, "Clientes.xlsx")
    if not os.path.exists(excel_path):
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    try:
        df = pd.read_excel(excel_path)
        headers = df.iloc[1].values.tolist()
        df_data = df.iloc[2:].copy()
        df_data.columns = headers

        clientes_a_insertar = []
        for _, row in df_data.iterrows():
            nom = str(row.get('Nombre*', '')).strip()
            if not nom or nom == 'nan':
                continue
            p_ap = str(row.get('Primer apellido', '')).strip() if pd.notna(row.get('Primer apellido')) else ''
            s_ap = str(row.get('Segundo apellido', '')).strip() if pd.notna(row.get('Segundo apellido')) else ''
            sexo = str(row.get('Sexo (h: hombre; m: mujer)', '')).strip() if pd.notna(row.get('Sexo (h: hombre; m: mujer)')) else ''
            tf_m = str(row.get('Teléfono móvil', '')).strip() if pd.notna(row.get('Teléfono móvil')) else ''
            tf_f = str(row.get('Teléfono fijo (sin prefijo país)', '')).strip() if pd.notna(row.get('Teléfono fijo (sin prefijo país)')) else ''
            email = str(row.get('Email', '')).strip() if pd.notna(row.get('Email')) else ''
            dni = str(row.get('Documento de identidad', '')).strip() if pd.notna(row.get('Documento de identidad')) else ''
            dir_c = str(row.get('Dirección', '')).strip() if pd.notna(row.get('Dirección')) else ''
            ciudad = str(row.get('Ciudad', '')).strip() if pd.notna(row.get('Ciudad')) else ''
            cp = str(row.get('Código postal', '')).strip() if pd.notna(row.get('Código postal')) else ''
            f_nac = str(row.get('Fecha de nacimiento', '')).strip() if pd.notna(row.get('Fecha de nacimiento')) else ''
            notas = str(row.get('Notas', '')).strip() if pd.notna(row.get('Notas')) else ''
            clinica = str(row.get('Información clínica', '')).strip() if pd.notna(row.get('Información clínica')) else ''

            clientes_a_insertar.append((
                nom, p_ap, s_ap, sexo, tf_m, tf_f, email, dni, dir_c, ciudad, cp, f_nac, notas, clinica, 1
            ))

        cursor.executemany('''INSERT INTO clientes (
            nombre, primer_apellido, segundo_apellido, sexo, telefono, telefono_fijo, email,
            dni, direccion, ciudad, cp, fecha_nacimiento, notas, info_clinica, rgpd
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', clientes_a_insertar)
        
        conn.commit()
    except Exception as e:
        print("Error al importar Excel Koibox:", e)
    finally:
        conn.close()

init_db()

def generar_link_whatsapp(telefono, nombre_cliente, fecha_str, hora_str, servicio_nombre):
    tel_clean = "".join(filter(str.isdigit, str(telefono or "")))
    if tel_clean and len(tel_clean) == 9 and not tel_clean.startswith("34"):
        tel_clean = f"34{tel_clean}"
        
    mensaje = (
        f"Hola {nombre_cliente}! ✨ Te recordamos tu cita en *Judit Domingo - Centre d'Estètica* "
        f"para el servicio de *{servicio_nombre}* el día *{fecha_str}* a las *{hora_str}h*. "
        f"Por favor, confírmanos si puedes asistir. ¡Te esperamos! 💆‍♀️"
    )
    mensaje_encoded = urllib.parse.quote(mensaje)
    return f"https://wa.me/{tel_clean}?text={mensaje_encoded}"

# Estilos CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap');

    header[data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 100 !important;
    }

    button[data-testid="stSidebarCollapseButton"], 
    button[data-testid="baseButton-header"] {
        display: block !important;
        visibility: visible !important;
        color: #d4af37 !important;
        background-color: #1a1a1a !important;
        border: 1px solid #d4af37 !important;
        border-radius: 4px !important;
        z-index: 999999 !important;
    }

    html, body, [class*="css"], .stApp {
        background-color: #121212 !important;
        color: #e0e0e0 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 300 !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 97% !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #181818 !important;
        border-right: 1px solid #2d2d2d !important;
        padding-top: 1rem !important;
    }

    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p {
        color: #d4af37 !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        font-family: 'Montserrat', sans-serif !important;
    }

    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 25px;
        margin-bottom: 20px;
        padding: 5px;
    }
    .sidebar-logo-container img {
        width: 100%;
        max-width: 240px;
        height: auto;
        border-radius: 10px;
        border: 1px solid #d4af37;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.6);
    }

    .stButton>button {
        background: linear-gradient(135deg, #d4af37 0%, #aa820a 100%) !important;
        color: #000000 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 18px !important;
        border-radius: 6px !important;
        border: none !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4) !important;
    }

    h1, h2, h3, h4, .stHeaderTitle {
        color: #d4af37 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 400 !important;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 6px !important;
    }
    
    .caja-card {
        background-color: #181818;
        border: 1px solid #2d2d2d;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal lateral
st.sidebar.markdown("""
    <div style="margin-bottom: 30px; text-align: center;">
        <h2 style="font-size: 26px; font-weight: 500; color: #d4af37; margin-bottom: 2px; letter-spacing: 1px;">Judit Domingo</h2>
        <p style="color: #d4af37; font-size: 11px; letter-spacing: 3px; font-weight: 300; margin-top: 0px;">CENTRE D'ESTÈTICA</p>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["authenticated"] = False
    st.rerun()

opcion = st.sidebar.radio("Navegación", ["📅 Agenda Koibox", "👤 Clientes", "💳 Caja", "💆‍♀️ Servicios", "📑 Facturación Veri*Factu"])

if logo_data_uri:
    st.sidebar.markdown(f"""
        <div class="sidebar-logo-container">
            <img src="{logo_data_uri}" alt="Judit Domingo Centre d'Estètica">
        </div>
    """, unsafe_allow_html=True)

# DIÁLOGO EMERGENTE PARA CREAR CITA
@st.dialog("📅 Nueva Cita")
def modal_nueva_cita(default_date=None, default_time=None):
    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql_query("SELECT id, nombre, primer_apellido, telefono FROM clientes ORDER BY nombre ASC", conn)
    df_serv = pd.read_sql_query("SELECT id, nombre, duracion_min, precio FROM servicios", conn)
    conn.close()

    if df_cli.empty or df_serv.empty:
        st.warning("Asegúrate de registrar clientes y servicios antes de agendar.")
        return

    df_cli['nombre_completo'] = df_cli['nombre'] + " " + df_cli['primer_apellido'].fillna('')
    opciones_clientes = [None] + list(df_cli["id"])

    def format_cli(x):
        if x is None:
            return "🔍 Selecciona / Busca un cliente..."
        row = df_cli[df_cli['id'] == x]
        if not row.empty:
            tel = f" ({row['telefono'].values[0]})" if row['telefono'].values[0] else ""
            return f"{row['nombre_completo'].values[0]}{tel}"
        return ""

    f_val = default_date if default_date else datetime.date.today()
    h_val = default_time if default_time else datetime.time(9, 0)

    col1, col2 = st.columns(2)
    with col1:
        fecha_c = st.date_input("Fecha", f_val)
        hora_c = st.time_input("Hora de Inicio (24h)", h_val)
    with col2:
        cli_sel = st.selectbox("Buscar / Seleccionar Cliente *", options=opciones_clientes, format_func=format_cli, index=0)
        serv_sel = st.selectbox("Servicio / Tratamiento", options=df_serv["id"], format_func=lambda x: f"{df_serv[df_serv['id']==x]['nombre'].values[0]} ({df_serv[df_serv['id']==x]['duracion_min'].values[0]} min - {df_serv[df_serv['id']==x]['precio'].values[0]}€)")

    dur_min = int(df_serv[df_serv["id"]==serv_sel]["duracion_min"].values[0])
    dt_i = datetime.datetime.combine(fecha_c, hora_c)
    dt_f = dt_i + datetime.timedelta(minutes=dur_min)

    st.text_input("Hora de Fin Calculada", value=dt_f.strftime("%H:%M"), disabled=True)
    obs = st.text_input("Observaciones / Notas")

    if st.button("💾 Guardar Cita", use_container_width=True, type="primary"):
        if cli_sel is None:
            st.error("⚠️ Por favor, busca y selecciona un cliente de la lista antes de guardar.")
        else:
            str_i = dt_i.strftime("%Y-%m-%dT%H:%M:%S")
            str_f = dt_f.strftime("%Y-%m-%dT%H:%M:%S")
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO citas (fecha_inicio, fecha_fin, cliente_id, servicio_id, notas) VALUES (?,?,?,?,?)",
                           (str_i, str_f, int(cli_sel), int(serv_sel), obs))
            conn.commit()
            conn.close()
            st.success("¡Cita reservada!")
            st.rerun()

# DIÁLOGO EMERGENTE PARA EDITAR CLIENTE EXISTENTE
@st.dialog("✏️ Editar Ficha de Cliente")
def modal_editar_cliente(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT nombre, primer_apellido, segundo_apellido, sexo, telefono, telefono_fijo, email,
                             dni, direccion, ciudad, cp, fecha_nacimiento, notas, info_clinica 
                      FROM clientes WHERE id = ?""", (cliente_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("No se encontró el cliente.")
        return

    tab1, tab2, tab3 = st.tabs(["DATOS BÁSICOS", "DATOS FISCALES Y DIRECCIÓN", "NOTAS Y CLÍNICA"])

    with st.form("form_editar_cliente"):
        with tab1:
            c1, c2, c3 = st.columns(3)
            with c1: e_nom = st.text_input("Nombre *", value=row[0] or "")
            with c2: e_p_ap = st.text_input("Primer Apellido", value=row[1] or "")
            with c3: e_s_ap = st.text_input("Segundo Apellido", value=row[2] or "")

            c4, c5, c6 = st.columns(3)
            idx_sexo = 0
            if row[3] in ["Mujer", "m"]: idx_sexo = 1
            elif row[3] in ["Hombre", "h"]: idx_sexo = 2
            with c4: e_sexo = st.selectbox("Sexo", ["", "Mujer", "Hombre"], index=idx_sexo)
            with c5: e_tel_m = st.text_input("Teléfono Móvil", value=row[4] or "")
            with c6: e_tel_f = st.text_input("Teléfono Fijo", value=row[5] or "")
            
            e_email = st.text_input("Email", value=row[6] or "")

        with tab2:
            d1, d2 = st.columns(2)
            with d1: e_dni = st.text_input("Documento Identidad (DNI/NIE)", value=row[7] or "")
            with d2: e_f_nac = st.text_input("Fecha Nacimiento (DD/MM/AAAA)", value=row[11] or "")

            e_dir = st.text_input("Dirección", value=row[8] or "")
            d3, d4 = st.columns(2)
            with d3: e_ciudad = st.text_input("Ciudad", value=row[9] or "")
            with d4: e_cp = st.text_input("Código Postal", value=row[10] or "")

        with tab3:
            e_notas = st.text_area("Notas Generales", value=row[12] or "")
            e_clinica = st.text_area("Información Clínica (Alergias, Piel, etc.)", value=row[13] or "")

        if st.form_submit_button("💾 Guardar Cambios del Cliente", use_container_width=True, type="primary"):
            if e_nom:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""UPDATE clientes SET
                    nombre=?, primer_apellido=?, segundo_apellido=?, sexo=?, telefono=?, telefono_fijo=?, email=?,
                    dni=?, direccion=?, ciudad=?, cp=?, fecha_nacimiento=?, notas=?, info_clinica=?
                    WHERE id=?""", (
                    e_nom, e_p_ap, e_s_ap, e_sexo, e_tel_m, e_tel_f, e_email,
                    e_dni, e_dir, e_ciudad, e_cp, e_f_nac, e_notas, e_clinica, cliente_id
                ))
                conn.commit()
                conn.close()
                st.success("Ficha de cliente actualizada con éxito.")
                st.rerun()

# DIÁLOGO EMERGENTE PARA BLOQUEAR HORARIO
@st.dialog("🚫 Bloquear Horario / Día")
def modal_bloquear_horario():
    b_fecha = st.date_input("Fecha a Bloquear", datetime.date.today())
    b_dia_completo = st.checkbox("Bloquear Día Completo")
    
    col1, col2 = st.columns(2)
    with col1:
        if not b_dia_completo:
            b_hora_i = st.time_input("Hora Inicio", datetime.time(9, 0))
        else:
            b_hora_i = datetime.time(8, 0)
    with col2:
        if not b_dia_completo:
            b_hora_f = st.time_input("Hora Fin", datetime.time(14, 0))
        else:
            b_hora_f = datetime.time(20, 30)
            
    b_motivo = st.text_input("Motivo / Notas", value="Médico / Cierre / Asuntos Personales")
    
    if st.button("🔒 Confirmar Bloqueo", use_container_width=True, type="primary"):
        dt_b_i = datetime.datetime.combine(b_fecha, b_hora_i).strftime("%Y-%m-%dT%H:%M:%S")
        dt_b_f = datetime.datetime.combine(b_fecha, b_hora_f).strftime("%Y-%m-%dT%H:%M:%S")
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO bloqueos (fecha_inicio, fecha_fin, motivo) VALUES (?,?,?)",
                       (dt_b_i, dt_b_f, b_motivo))
        conn.commit()
        conn.close()
        st.success("Horario bloqueado con éxito.")
        st.rerun()

# DIÁLOGO EMERGENTE PARA EDITAR CITA / WHATSAPP
@st.dialog("⚙️ Detalle Cita / Bloqueo")
def modal_editar_elemento(item_id, es_bloqueo=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if es_bloqueo:
        cursor.execute("SELECT fecha_inicio, fecha_fin, motivo FROM bloqueos WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            st.warning(f"🚫 **Horario Bloqueado**\n\n**Motivo:** {row[2]}\n\n**Desde:** {row[0].replace('T', ' ')}\n**Hasta:** {row[1].replace('T', ' ')}")
            if st.button("🗑️ Eliminar Bloqueo", use_container_width=True, type="primary"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM bloqueos WHERE id = ?", (item_id,))
                conn.commit()
                conn.close()
                st.success("Bloqueo liberado.")
                st.rerun()
        return

    cursor.execute("SELECT fecha_inicio, fecha_fin, cliente_id, servicio_id, notas FROM citas WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    
    df_cli = pd.read_sql_query("SELECT id, nombre, primer_apellido, telefono FROM clientes ORDER BY nombre ASC", conn)
    df_serv = pd.read_sql_query("SELECT id, nombre, duracion_min, precio FROM servicios", conn)
    conn.close()

    if not row:
        st.error("No se encontró la cita seleccionada.")
        return

    df_cli['nombre_completo'] = df_cli['nombre'] + " " + df_cli['primer_apellido'].fillna('')

    f_inicio_dt = datetime.datetime.fromisoformat(row[0])
    cli_row = df_cli[df_cli['id'] == row[2]]
    serv_row = df_serv[df_serv['id'] == row[3]]

    cli_nom = cli_row['nombre_completo'].values[0] if not cli_row.empty else "Cliente"
    cli_tel = cli_row['telefono'].values[0] if not cli_row.empty else ""
    serv_nom = serv_row['nombre'].values[0] if not serv_row.empty else "Servicio"

    col1, col2 = st.columns(2)
    with col1:
        fecha_c = st.date_input("Fecha", f_inicio_dt.date())
        hora_c = st.time_input("Hora de Inicio", f_inicio_dt.time())
    with col2:
        idx_cli = list(df_cli["id"]).index(row[2]) if row[2] in list(df_cli["id"]) else 0
        cli_sel = st.selectbox("Cliente", options=df_cli["id"], index=idx_cli, format_func=lambda x: f"{df_cli[df_cli['id']==x]['nombre_completo'].values[0]}")
        
        idx_serv = list(df_serv["id"]).index(row[3]) if row[3] in list(df_serv["id"]) else 0
        serv_sel = st.selectbox("Servicio / Tratamiento", options=df_serv["id"], index=idx_serv, format_func=lambda x: f"{df_serv[df_serv['id']==x]['nombre'].values[0]} ({df_serv[df_serv['id']==x]['duracion_min'].values[0]} min - {df_serv[df_serv['id']==x]['precio'].values[0]}€)")

    dur_min = int(df_serv[df_serv["id"]==serv_sel]["duracion_min"].values[0])
    dt_i = datetime.datetime.combine(fecha_c, hora_c)
    dt_f = dt_i + datetime.timedelta(minutes=dur_min)

    st.text_input("Hora de Fin", value=dt_f.strftime("%H:%M"), disabled=True)
    obs = st.text_input("Observaciones / Notas", value=row[4] if row[4] else "")

    if cli_tel:
        url_wa = generar_link_whatsapp(cli_tel, cli_nom, fecha_c.strftime("%d/%m/%Y"), hora_c.strftime("%H:%M"), serv_nom)
        st.markdown(f'''
            <a href="{url_wa}" target="_blank" style="text-decoration:none;">
                <button style="background: linear-gradient(135deg, #25D366 0%, #128C7E 100%); color:white; border:none; padding:10px 16px; border-radius:6px; font-weight:600; font-family:'Montserrat', sans-serif; cursor:pointer; width:100%; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
                    📲 Enviar Recordatorio por WhatsApp
                </button>
            </a>
        ''', unsafe_allow_html=True)
    else:
        st.info("💡 Este cliente no tiene número de teléfono registrado para enviar WhatsApp.")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
            str_i = dt_i.strftime("%Y-%m-%dT%H:%M:%S")
            str_f = dt_f.strftime("%Y-%m-%dT%H:%M:%S")
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE citas SET fecha_inicio=?, fecha_fin=?, cliente_id=?, servicio_id=?, notas=? WHERE id=?",
                           (str_i, str_f, int(cli_sel), int(serv_sel), obs, item_id))
            conn.commit()
            conn.close()
            st.success("Cita actualizada.")
            st.rerun()

    with col_btn2:
        if st.button("🗑️ Eliminar Cita", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM citas WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            st.warning("Cita eliminada.")
            st.rerun()

# 1. AGENDA VISUAL INTERACTIVA
if opcion == "📅 Agenda Koibox":
    col_t1, col_t3, col_t4 = st.columns([6, 2, 2])
    with col_t1:
        st.subheader("Agenda Semanal de Citas")
    with col_t3:
        if st.button("➕ Nueva Cita", use_container_width=True):
            modal_nueva_cita()
    with col_t4:
        if st.button("🚫 Bloquear Horario", use_container_width=True):
            modal_bloquear_horario()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT c.id, c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, cl.telefono, s.nombre, s.color, s.precio
                      FROM citas c
                      JOIN clientes cl ON c.cliente_id = cl.id
                      JOIN servicios s ON c.servicio_id = s.id''')
    citas_db = cursor.fetchall()

    cursor.execute("SELECT id, fecha_inicio, fecha_fin, motivo FROM bloqueos")
    bloqueos_db = cursor.fetchall()
    conn.close()

    events = []
    for cita in citas_db:
        c_id, f_ini, f_fin, cl_nombre, cl_p_ap, cl_tel, s_nombre, color, precio = cita
        nom_comp = f"{cl_nombre} {cl_p_ap or ''}".strip()
        events.append({
            "id": f"cita_{c_id}",
            "title": f"[{nom_comp}] {s_nombre}",
            "start": f_ini,
            "end": f_fin,
            "backgroundColor": color,
            "borderColor": color
        })

    for bloq in bloqueos_db:
        b_id, b_ini, b_fin, b_mot = bloq
        events.append({
            "id": f"bloqueo_{b_id}",
            "title": f"🚫 BLOQUEADO: {b_mot}",
            "start": b_ini,
            "end": b_fin,
            "backgroundColor": "#3a3a3a",
            "borderColor": "#d4af37"
        })

    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "timeGridWeek,timeGridDay,dayGridMonth"
        },
        "buttonText": {
            "today": "Hoy",
            "month": "Mes",
            "week": "Semana",
            "day": "Día"
        },
        "locale": "es",
        "firstDay": 1,
        "initialView": "timeGridWeek",
        "slotMinTime": "08:00:00",
        "slotMaxTime": "20:30:00",
        "slotDuration": "00:15:00",
        "slotLabelFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        },
        "eventTimeFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        },
        "timeZone": "UTC",
        "allDaySlot": False,
        "selectable": True,
        "editable": False,
        "height": "780px"
    }

    custom_css = """
        .fc {
            background-color: #181818 !important;
            border-radius: 8px !important;
            padding: 8px !important;
            border: 1px solid #2d2d2d !important;
        }
        .fc-theme-standard td, .fc-theme-standard th {
            border-color: #2a2a2a !important;
        }
        .fc-timegrid-slot {
            height: 18px !important;
        }
        .fc-timegrid-slot-label-cushion {
            font-size: 11px !important;
            font-weight: 400 !important;
            font-family: 'Montserrat', sans-serif !important;
            color: #d4af37 !important;
        }
        .fc-col-header-cell-cushion {
            font-size: 13px !important;
            font-weight: 500 !important;
            font-family: 'Montserrat', sans-serif !important;
            color: #ffffff !important;
            text-transform: capitalize;
        }
        .fc-event-title {
            font-size: 11.5px !important;
            font-weight: 500 !important;
            font-family: 'Montserrat', sans-serif !important;
            color: #ffffff !important;
        }
        .fc-toolbar-title {
            font-size: 17px !important;
            font-weight: 400 !important;
            color: #d4af37 !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        .fc-button {
            background-color: #262626 !important;
            border: 1px solid #d4af37 !important;
            color: #d4af37 !important;
            font-size: 12px !important;
            border-radius: 4px !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        .fc-button-active, .fc-button:hover {
            background-color: #d4af37 !important;
            color: #000000 !important;
        }
    """

    state = calendar(events=events, options=calendar_options, custom_css=custom_css, key="koibox_calendar")

    if state.get("dateClick"):
        clicked_str = state["dateClick"]["date"]
        clean_str = clicked_str.replace("Z", "").split(".")[0]
        if "T" in clean_str:
            fecha_part, hora_part = clean_str.split("T")
            f_obj = datetime.datetime.strptime(fecha_part, "%Y-%m-%d").date()
            h_obj = datetime.datetime.strptime(hora_part, "%H:%M:%S").time()
        else:
            dt_obj = datetime.datetime.fromisoformat(clean_str)
            f_obj = dt_obj.date()
            h_obj = dt_obj.time()
            
        modal_nueva_cita(default_date=f_obj, default_time=h_obj)

    if state.get("eventClick"):
        raw_id = state["eventClick"]["event"]["id"]
        if raw_id.startswith("bloqueo_"):
            bloq_id = int(raw_id.replace("bloqueo_", ""))
            modal_editar_elemento(bloq_id, es_bloqueo=True)
        elif raw_id.startswith("cita_"):
            cita_id = int(raw_id.replace("cita_", ""))
            modal_editar_elemento(cita_id, es_bloqueo=False)

# 2. CLIENTES CON EDICIÓN EN POP-UP Y BUSCADOR
elif opcion == "👤 Clientes":
    st.subheader("Fichero de Clientes")

    with st.expander("➕ Añadir Nuevo Cliente", expanded=False):
        tab1, tab2, tab3 = st.tabs(["DATOS BÁSICOS", "DATOS FISCALES Y DIRECCIÓN", "NOTAS Y CLÍNICA"])

        with st.form("form_nuevo_cliente", clear_on_submit=True):
            with tab1:
                c1, c2, c3 = st.columns(3)
                with c1: n_nom = st.text_input("Nombre *")
                with c2: n_p_ap = st.text_input("Primer Apellido")
                with c3: n_s_ap = st.text_input("Segundo Apellido")

                c4, c5, c6 = st.columns(3)
                with c4: n_sexo = st.selectbox("Sexo", ["", "Mujer", "Hombre"])
                with c5: n_tel_m = st.text_input("Teléfono Móvil")
                with c6: n_tel_f = st.text_input("Teléfono Fijo")
                
                n_email = st.text_input("Email")

            with tab2:
                d1, d2 = st.columns(2)
                with d1: n_dni = st.text_input("Documento Identidad (DNI/NIE)")
                with d2: n_f_nac = st.text_input("Fecha Nacimiento (DD/MM/AAAA)")

                n_dir = st.text_input("Dirección")
                d3, d4 = st.columns(2)
                with d3: n_ciudad = st.text_input("Ciudad")
                with d4: n_cp = st.text_input("Código Postal")

            with tab3:
                n_notas = st.text_area("Notas Generales")
                n_clinica = st.text_area("Información Clínica (Alergias, Piel, etc.)")

            if st.form_submit_button("💾 Guardar Cliente"):
                if n_nom:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO clientes (
                        nombre, primer_apellido, segundo_apellido, sexo, telefono, telefono_fijo, email,
                        dni, direccion, ciudad, cp, fecha_nacimiento, notas, info_clinica, rgpd
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
                        n_nom, n_p_ap, n_s_ap, n_sexo, n_tel_m, n_tel_f, n_email,
                        n_dni, n_dir, n_ciudad, n_cp, n_f_nac, n_notas, n_clinica, 1
                    ))
                    conn.commit()
                    conn.close()
                    st.success("Cliente guardado correctamente.")
                    st.rerun()
                else:
                    st.error("El campo Nombre es obligatorio.")

    busqueda = st.text_input("🔍 Buscar Cliente por nombre, apellidos o teléfono:", "")

    conn = sqlite3.connect(DB_NAME)
    query = """SELECT id as 'ID', 
                      nombre || ' ' || COALESCE(primer_apellido,'') || ' ' || COALESCE(segundo_apellido,'') as 'Nombre Completo',
                      telefono as 'Móvil', 
                      email as 'Email', 
                      dni as 'DNI', 
                      ciudad as 'Ciudad',
                      info_clinica as 'Info Clínica'
               FROM clientes"""
    if busqueda:
        query += f" WHERE nombre LIKE '%{busqueda}%' OR primer_apellido LIKE '%{busqueda}%' OR telefono LIKE '%{busqueda}%'"
    query += " ORDER BY id DESC"

    df_c = pd.read_sql_query(query, conn)
    conn.close()

    st.write(f"**Total Clientes Registrados:** {len(df_c)}")

    # Visualización con botón de edición por cada cliente
    for idx, row in df_c.head(50).iterrows():
        col_c1, col_c2, col_c3, col_c4 = st.columns([3, 2, 2, 1])
        with col_c1:
            st.markdown(f"**{row['Nombre Completo']}**")
        with col_c2:
            st.caption(f"📱 {row['Móvil'] or 'Sin teléfono'}")
        with col_c3:
            st.caption(f"📍 {row['Ciudad'] or 'N/D'}")
        with col_c4:
            if st.button("✏️ Editar", key=f"edit_cli_{row['ID']}"):
                modal_editar_cliente(row['ID'])
        st.markdown("<hr style='margin: 4px 0; border-color: #2d2d2d;'>", unsafe_allow_html=True)

# 3. MÓDULO DE CAJA (ESTILO KOIBOX)
elif opcion == "💳 Caja":
    st.subheader("Caja del Día")

    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT abonos_efectivo, ingresos, extracciones, descuadre, total_caja, estado FROM cajas WHERE fecha = ?", (hoy_str,))
    caja_hoy = cursor.fetchone()
    conn.close()

    if not caja_hoy:
        caja_hoy = (0.0, 0.0, 0.0, 0.0, 0.0, 'Cerrada')

    # Alerta superior
    if caja_hoy[5] == 'Cerrada':
        st.warning("⚠️ **Atención Judit:** Caja del día sin abrir")

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown("<div class='caja-card'><h3>🔓 Apertura</h3><p>Gestión de inicio del día</p></div>", unsafe_allow_html=True)
        if st.button("Abrir / Modificar Caja", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO cajas (fecha, estado) VALUES (?, 'Abierta')", (hoy_str,))
            conn.commit()
            conn.close()
            st.success("Caja abierta para el día de hoy.")
            st.rerun()

    with col_k2:
        st.markdown(f"<div class='caja-card'><h3>👁️ Resumen</h3><p><strong>{caja_hoy[4]:.2f}€</strong> Total</p></div>", unsafe_allow_html=True)

    with col_k3:
        st.markdown(f"<div class='caja-card'><h3>🔍 Ingresos</h3><p><strong>{caja_hoy[1]:.2f}€</strong> Ventas</p></div>", unsafe_allow_html=True)

    with col_k4:
        st.markdown(f"<div class='caja-card'><h3>↔️ Extracciones</h3><p><strong>{caja_hoy[2]:.2f}€</strong> Retirado</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Histórico de Cajas Diarias")

    conn = sqlite3.connect(DB_NAME)
    df_cajas = pd.read_sql_query("""SELECT fecha as 'Fecha', 
                                          PRINTF('%.2f€', abonos_efectivo) as 'Abonos Efectivo', 
                                          PRINTF('%.2f€', ingresos) as 'Ingresos', 
                                          PRINTF('%.2f€', extracciones) as 'Extracciones', 
                                          PRINTF('%.2f€', descuadre) as 'Descuadre', 
                                          PRINTF('%.2f€', total_caja) as 'Caja' 
                                   FROM cajas ORDER BY fecha DESC""", conn)
    conn.close()

    st.dataframe(df_cajas, use_container_width=True)

# 4. SERVICIOS
elif opcion == "💆‍♀️ Servicios":
    st.subheader("Catálogo de Tratamientos")
    with st.form("nuevo_servicio", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1: s_nom = st.text_input("Tratamiento")
        with col2: s_dur = st.number_input("Duración (min)", value=45, step=15)
        with col3: s_pre = st.number_input("Precio (€)", value=25.0, step=5.0)
        with col4: s_col = st.color_picker("Color Bloque", "#9b59b6")
        
        if st.form_submit_button("Añadir Tratamiento") and s_nom:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO servicios (nombre, duracion_min, precio, color) VALUES (?,?,?,?)", (s_nom, int(s_dur), float(s_pre), s_col))
            conn.commit()
            conn.close()
            st.success("Tratamiento guardado.")
            st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_s = pd.read_sql_query("SELECT id as 'ID', nombre as 'Tratamiento', duracion_min as 'Duración (min)', precio as 'Precio (€)', color as 'Color' FROM servicios", conn)
    conn.close()
    st.dataframe(df_s, use_container_width=True)

# 5. FACTURACIÓN
elif opcion == "📑 Facturación Veri*Factu":
    st.subheader("Facturación Expedida (Estándar Veri*Factu)")
    if st.button("⚡ Emitir Factura de Prueba"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT hash_registro FROM facturas ORDER BY id DESC LIMIT 1")
        last_row = cursor.fetchone()
        hash_ant = last_row[0] if last_row else "00000000000000000000000000000000"
        
        num_f = f"F2026-{datetime.datetime.now().strftime('%M%S')}"
        fecha_h = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        total = 50.0
        
        cadena = f"{num_f}|{fecha_h}|{total:.2f}|{hash_ant}"
        hash_reg = hashlib.sha256(cadena.encode('utf-8')).hexdigest()
        
        cursor.execute("INSERT INTO facturas (num_factura, fecha_hora, concepto, total, hash_registro) VALUES (?,?,?,?,?)",
                       (num_f, fecha_h, "Tratamiento Estética", total, hash_reg))
        conn.commit()
        conn.close()
        st.success(f"Factura {num_f} expedida e encadenada con Hash SHA-256.")
        st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_f = pd.read_sql_query("SELECT num_factura as 'Nº Factura', fecha_hora as 'Fecha/Hora', concepto as 'Concepto', total as 'Total (€)', hash_registro as 'Hash Veri*Factu' FROM facturas", conn)
    conn.close()
    st.dataframe(df_f, use_container_width=True)
