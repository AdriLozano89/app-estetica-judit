import streamlit as st
from streamlit_calendar import calendar
import sqlite3
import datetime
import pandas as pd
import hashlib
import os
import base64
import urllib.parse
import random

# Configuración inicial de la página
st.set_page_config(
    page_title="Judit Domingo - Centre d'Estètica",
    page_icon="💆‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "gestion_estetica_v2.db"
GASTOS_DIR = "facturas_gastos"

if not os.path.exists(GASTOS_DIR):
    os.makedirs(GASTOS_DIR)

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

# Estilos CSS Avanzados con Tipografía Comfortaa + Quicksand y Estética Dulce/Elegante
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@400;600;700&family=Quicksand:wght@400;500;600;700&display=swap');

    section[data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 100 !important; }

    html, body, [class*="css"], .stApp {
        background-color: #0f0e13 !important;
        color: #f3effa !important;
        font-family: 'Quicksand', sans-serif !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    h1, h2, h3, .brand-title {
        font-family: 'Comfortaa', cursive !important;
        color: #e6c566 !important;
        letter-spacing: 0.5px !important;
    }

    .brand-subtext {
        font-family: 'Quicksand', sans-serif;
        font-size: 11px;
        color: #d4af37;
        letter-spacing: 3px;
        margin-top: -2px;
        text-transform: uppercase;
        font-weight: 600;
    }

    .card-metric {
        background: linear-gradient(145deg, #191724 0%, #12101a 100%);
        border: 1px solid #332d42;
        border-left: 5px solid #e6c566;
        border-radius: 16px;
        padding: 18px 22px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    .stButton>button {
        background: linear-gradient(135deg, #e6c566 0%, #ba9530 100%) !important;
        color: #1a1600 !important;
        font-family: 'Comfortaa', cursive !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 20px !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(230, 197, 102, 0.25) !important;
    }

    .stLinkButton>a {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important;
        color: #ffffff !important;
        font-family: 'Comfortaa', cursive !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 18px !important;
        border-radius: 20px !important;
        border: none !important;
        text-decoration: none !important;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #191724 !important;
        color: #ffffff !important;
        border: 1px solid #332d42 !important;
        border-radius: 12px !important;
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 500 !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 15px 15px 0px 0px !important;
        padding: 10px 18px !important;
        background-color: #161420 !important;
        color: #bfa8db !important;
        font-family: 'Comfortaa', cursive !important;
        font-size: 13px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #241f33 !important;
        color: #e6c566 !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS COMPLETA PLATINUM CON MIGRADORES ---
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
                        monedero REAL DEFAULT 0.0,
                        rgpd INTEGER DEFAULT 1)''')

    cursor.execute("PRAGMA table_info(clientes)")
    cols_cli = [c[1] for c in cursor.fetchall()]
    if "monedero" not in cols_cli:
        cursor.execute("ALTER TABLE clientes ADD COLUMN monedero REAL DEFAULT 0.0")

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
                        etiqueta TEXT DEFAULT 'General',
                        notas TEXT,
                        estado_cobro TEXT DEFAULT 'Pendiente',
                        metodo_pago TEXT,
                        monto_cobrado REAL DEFAULT 0.0,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                        FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')

    cursor.execute("PRAGMA table_info(citas)")
    cols_citas = [c[1] for c in cursor.fetchall()]
    if "estado_cobro" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN estado_cobro TEXT DEFAULT 'Pendiente'")
    if "metodo_pago" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN metodo_pago TEXT")
    if "monto_cobrado" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN monto_cobrado REAL DEFAULT 0.0")
    if "etiqueta" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN etiqueta TEXT DEFAULT 'General'")

    cursor.execute('''CREATE TABLE IF NOT EXISTS cajas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT UNIQUE NOT NULL,
                        abonos_efectivo REAL DEFAULT 0.0,
                        abonos_tarjeta REAL DEFAULT 0.0,
                        abonos_bizum REAL DEFAULT 0.0,
                        ingresos REAL DEFAULT 0.0,
                        extracciones REAL DEFAULT 0.0,
                        descuadre REAL DEFAULT 0.0,
                        total_caja REAL DEFAULT 0.0,
                        estado TEXT DEFAULT 'Cerrada')''')

    cursor.execute("PRAGMA table_info(cajas)")
    cols_cajas = [c[1] for c in cursor.fetchall()]
    if "abonos_tarjeta" not in cols_cajas:
        cursor.execute("ALTER TABLE cajas ADD COLUMN abonos_tarjeta REAL DEFAULT 0.0")
    if "abonos_bizum" not in cols_cajas:
        cursor.execute("ALTER TABLE cajas ADD COLUMN abonos_bizum REAL DEFAULT 0.0")

    cursor.execute('''CREATE TABLE IF NOT EXISTS facturas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        num_factura TEXT UNIQUE,
                        fecha_hora TEXT,
                        concepto TEXT,
                        total REAL,
                        metodo_pago TEXT,
                        hash_registro TEXT)''')

    cursor.execute("PRAGMA table_info(facturas)")
    cols_fact = [c[1] for c in cursor.fetchall()]
    if "metodo_pago" not in cols_fact:
        cursor.execute("ALTER TABLE facturas ADD COLUMN metodo_pago TEXT")

    cursor.execute('''CREATE TABLE IF NOT EXISTS lista_espera (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_id INTEGER NOT NULL,
                        servicio_id INTEGER NOT NULL,
                        preferencia_horario TEXT,
                        fecha_registro TEXT,
                        estado TEXT DEFAULT 'Pendiente',
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                        FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS consentimientos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_id INTEGER NOT NULL,
                        tipo_tratamiento TEXT NOT NULL,
                        fecha_firma TEXT NOT NULL,
                        acepta_rgpd INTEGER DEFAULT 1,
                        firma_texto TEXT,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS gastos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT NOT NULL,
                        proveedor TEXT NOT NULL,
                        concepto TEXT NOT NULL,
                        categoria TEXT NOT NULL,
                        base_imponible REAL NOT NULL,
                        iva_porcentaje REAL DEFAULT 21.0,
                        total REAL NOT NULL,
                        ruta_factura TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS stock (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        categoria TEXT DEFAULT 'Producto Venta',
                        precio_coste REAL NOT NULL,
                        pvp REAL NOT NULL,
                        unidades INTEGER NOT NULL,
                        minimo_alerta INTEGER DEFAULT 2)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS tarjetas_regalo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT UNIQUE NOT NULL,
                        comprador TEXT NOT NULL,
                        beneficiario TEXT NOT NULL,
                        concepto TEXT NOT NULL,
                        saldo_inicial REAL NOT NULL,
                        saldo_actual REAL NOT NULL,
                        fecha_emision TEXT NOT NULL,
                        fecha_caducidad TEXT,
                        estado TEXT DEFAULT 'Activa')''')

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

init_db()

# --- HEADER SUPERIOR ---
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 15px;">
            <div>
                <div class="brand-title" style="font-size: 28px; font-weight:700; line-height:1.1;">Judit Domingo</div>
                <div class="brand-subtext">CENTRE D'ESTÈTICA</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# --- MENÚ SUPERIOR DE NAVEGACIÓN ---
opcion = st.tabs([
    "📅 Agenda", 
    "💳 Caja & Cobros", 
    "✍️ Firma & RGPD",
    "⏳ Lista Espera",
    "🏛️ Fiscal & Trimestral", 
    "📉 Gastos & Facturas", 
    "📦 Stock Top", 
    "📣 Marketing & Regalos", 
    "👤 Clientes", 
    "💆‍♀️ Servicios"
])

def generar_link_whatsapp(telefono, nombre_cliente, fecha_str, hora_str, servicio_nombre):
    tel_clean = "".join(filter(str.isdigit, str(telefono or "")))
    if tel_clean and len(tel_clean) == 9 and not tel_clean.startswith("34"):
        tel_clean = f"34{tel_clean}"
        
    texto_raw = (
        f"Hola {nombre_cliente}! ✨\n\n"
        f"Te recordamos tu cita en *Judit Domingo - Centre d'Estètica* "
        f"para el servicio de *{servicio_nombre}* el día *{fecha_str}* a las *{hora_str}h*.\n\n"
        f"Por favor, confírmanos si puedes asistir. ¡Te esperamos! 💆‍♀️"
    )
    return f"https://api.whatsapp.com/send?phone={tel_clean}&text={urllib.parse.quote(texto_raw, encoding='utf-8')}"

@st.dialog("⚙️ Detalle de Cita")
def modal_editar_cita(cita_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, cl.telefono, s.nombre, s.precio, c.estado_cobro, c.metodo_pago, c.monto_cobrado, c.etiqueta, c.notas
                      FROM citas c 
                      JOIN clientes cl ON c.cliente_id = cl.id 
                      JOIN servicios s ON c.servicio_id = s.id 
                      WHERE c.id = ?""", (cita_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("No se encontró la cita.")
        return

    f_i, f_f, cl_n, cl_ap, cl_tel, s_n, s_pre, est_c, met_p, monto_c, etiq, obs = row
    nom_cli = f"{cl_n} {cl_ap or ''}".strip()
    dt_i = datetime.datetime.fromisoformat(f_i)

    st.markdown(f"### 💆‍♀️ {s_n}")
    st.markdown(f"🏷️ **Etiqueta:** `{etiq or 'General'}`")
    st.markdown(f"👤 **Cliente:** {nom_cli}")
    st.markdown(f"📅 **Fecha:** {dt_i.strftime('%d/%m/%Y')} a las {dt_i.strftime('%H:%M')}h")
    if obs: st.info(f"📝 **Notas:** {obs}")

    st.markdown("---")
    if est_c == "Cobrado":
        st.success(f"✅ **Cobrado:** {monto_c:.2f}€ en {met_p}")
    else:
        st.warning(f"⏳ **Cobro Pendiente:** {s_pre:.2f}€")
        if st.button("💶 Cobrar Servicio Ahora", use_container_width=True):
            modal_cobrar_cita(cita_id, nom_cli, s_n, s_pre)

    if cl_tel:
        url_wa = generar_link_whatsapp(cl_tel, nom_cli, dt_i.strftime("%d/%m/%Y"), dt_i.strftime("%H:%M"), s_n)
        st.link_button("📲 Enviar Recordatorio por WhatsApp", url_wa, use_container_width=True)

    if st.button("🗑️ Eliminar Cita", use_container_width=True):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM citas WHERE id = ?", (cita_id,))
        conn.commit()
        conn.close()
        st.success("Cita eliminada.")
        st.rerun()

@st.dialog("💶 Cobrar Servicio del Día")
def modal_cobrar_cita(cita_id, cliente_nom, servicio_nom, precio_defecto):
    st.markdown(f"**Cliente:** {cliente_nom}")
    st.markdown(f"**Servicio:** {servicio_nom}")
    
    col1, col2 = st.columns(2)
    with col1: monto = st.number_input("Importe (€)", value=float(precio_defecto), step=1.0)
    with col2: metodo = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Bizum", "Monedero Clienta", "Tarjeta Regalo"])

    if st.button("✅ Confirmar Cobro", use_container_width=True, type="primary"):
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE citas SET estado_cobro='Cobrado', metodo_pago=?, monto_cobrado=? WHERE id=?", (metodo, monto, cita_id))
        
        if metodo not in ["Tarjeta Regalo", "Monedero Clienta"]:
            cursor.execute("SELECT id, abonos_efectivo, abonos_tarjeta, abonos_bizum, ingresos, total_caja FROM cajas WHERE fecha=?", (hoy_str,))
            row_caja = cursor.fetchone()
            
            if row_caja:
                c_id, ef, tar, biz, ing, tot = row_caja
                cursor.execute("UPDATE cajas SET abonos_efectivo=?, abonos_tarjeta=?, abonos_bizum=?, ingresos=?, total_caja=?, estado='Abierta' WHERE id=?",
                               (ef + (monto if metodo == "Efectivo" else 0),
                                tar + (monto if metodo == "Tarjeta" else 0),
                                biz + (monto if metodo == "Bizum" else 0),
                                ing + monto, tot + monto, c_id))
            else:
                cursor.execute("INSERT INTO cajas (fecha, abonos_efectivo, abonos_tarjeta, abonos_bizum, ingresos, total_caja, estado) VALUES (?,?,?,?,?,?,'Abierta')",
                               (hoy_str, monto if metodo == "Efectivo" else 0, monto if metodo == "Tarjeta" else 0, monto if metodo == "Bizum" else 0, monto, monto))

        cursor.execute("SELECT hash_registro FROM facturas ORDER BY id DESC LIMIT 1")
        last_row = cursor.fetchone()
        hash_ant = last_row[0] if last_row else "00000000000000000000000000000000"
        num_f = f"F{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        fecha_h = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cadena = f"{num_f}|{fecha_h}|{monto:.2f}|{hash_ant}"
        hash_reg = hashlib.sha256(cadena.encode('utf-8')).hexdigest()
        
        cursor.execute("INSERT INTO facturas (num_factura, fecha_hora, concepto, total, metodo_pago, hash_registro) VALUES (?,?,?,?,?,?)",
                       (num_f, fecha_h, f"{servicio_nom} - {cliente_nom}", monto, metodo, hash_reg))

        conn.commit()
        conn.close()
        st.success("¡Cobro registrado!")
        st.rerun()
        # 1. AGENDA INTERACTIVA CON ETIQUETAS
with opcion[0]:
    st.subheader("Agenda Semanal de Citas")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT c.id, c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, cl.telefono, s.nombre, s.color, s.precio, c.estado_cobro, c.etiqueta
                      FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id''')
    citas_db = cursor.fetchall()
    conn.close()

    events = []
    for cita in citas_db:
        c_id, f_ini, f_fin, cl_nombre, cl_p_ap, cl_tel, s_nombre, color, precio, est_cobro, etiq = cita
        nom_comp = f"{cl_nombre} {cl_p_ap or ''}".strip()
        prefijo = "✅ " if est_cobro == "Cobrado" else ""
        tag_txt = f"[{etiq}] " if etiq and etiq != 'General' else ""
        events.append({
            "id": f"cita_{c_id}",
            "title": f"{prefijo}{tag_txt}[{nom_comp}] {s_nombre}",
            "start": f_ini, "end": f_fin,
            "backgroundColor": "#2ecc71" if est_cobro == "Cobrado" else color,
            "borderColor": color
        })

    cal_options = {
        "initialView": "timeGridWeek",
        "firstDay": 1,
        "slotMinTime": "08:00:00",
        "slotMaxTime": "20:30:00",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "timeGridWeek,timeGridDay,dayGridMonth"
        }
    }

    state = calendar(events=events, options=cal_options, key="koibox_cal_main")

    if state.get("eventClick"):
        raw_id = state["eventClick"]["event"]["id"]
        if raw_id.startswith("cita_"):
            c_id = int(raw_id.replace("cita_", ""))
            modal_editar_cita(c_id)

# 2. CAJA & COBROS
with opcion[1]:
    st.subheader("Arqueo de Caja del Día")
    hoy_str = datetime.date.today().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT abonos_efectivo, abonos_tarjeta, abonos_bizum, ingresos, total_caja FROM cajas WHERE fecha = ?", (hoy_str,))
    caja_hoy = cursor.fetchone() or (0.0, 0.0, 0.0, 0.0, 0.0)
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("💵 Efectivo", f"{caja_hoy[0]:.2f} €")
    with col2: st.metric("💳 Tarjeta", f"{caja_hoy[1]:.2f} €")
    with col3: st.metric("📲 Bizum", f"{caja_hoy[2]:.2f} €")
    with col4: st.metric("🏆 Total Hoy", f"{caja_hoy[3]:.2f} €")

    st.markdown("### 📋 Citas Agendadas Hoy")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT c.id, c.fecha_inicio, cl.nombre, cl.primer_apellido, s.nombre, s.precio, c.estado_cobro, c.metodo_pago, c.monto_cobrado
                      FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id
                      WHERE DATE(c.fecha_inicio) = ? ORDER BY c.fecha_inicio ASC""", (hoy_str,))
    citas_hoy = cursor.fetchall()
    conn.close()

    for cita_h in citas_hoy:
        c_id, f_i, c_nom, c_p_ap, s_nom, s_precio, est_cobro, met_pago, monto_cob = cita_h
        hora_cita = datetime.datetime.fromisoformat(f_i).strftime("%H:%M")
        nom_cliente = f"{c_nom} {c_p_ap or ''}".strip()

        col_a, col_b, col_c = st.columns([4, 3, 2])
        with col_a: st.markdown(f"**⏰ {hora_cita}h** — {nom_cliente} (*{s_nom}*)")
        with col_b:
            if est_cobro == "Cobrado": st.success(f"✅ Cobrado: {monto_cob:.2f}€ ({met_pago})")
            else: st.warning(f"⏳ Pendiente: {s_precio:.2f}€")
        with col_c:
            if est_cobro != "Cobrado":
                if st.button("💶 Cobrar", key=f"cobrar_{c_id}"):
                    modal_cobrar_cita(c_id, nom_cliente, s_nom, s_precio)

# 3. FIRMA DIGITAL DE CONSENTIMIENTOS Y RGPD
with opcion[2]:
    st.subheader("✍️ Firma Digital de Consentimiento Informado & RGPD")
    st.info("Pasa la tablet o el móvil a la clienta para confirmar sus datos y firmar antes del tratamiento.")

    conn = sqlite3.connect(DB_NAME)
    df_cli_select = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes", conn)
    conn.close()

    if not df_cli_select.empty:
        c_sel = st.selectbox("Seleccionar Clienta *", options=df_cli_select["id"], format_func=lambda x: df_cli_select[df_cli_select["id"]==x]["nom"].values[0])
        tipo_trat = st.selectbox("Tratamiento a Realizar", ["Maderoterapia Corporal", "Higiene Facial Profunda / Peeling", "Lifting / Extensión de Pestañas", "Microblading / Micropigmentación", "Tratamiento General Estética"])
        
        st.markdown("""
            **Cláusula de Consentimiento:**
            Declaro haber sido informada de las características del tratamiento, cuidados posteriores y no presentar contraindicaciones médicas conocidas. Autorizo el tratamiento en *Judit Domingo Centre d'Estètica*.
        """)

        nombre_firma = st.text_input("Escribe tu Nombre Completo como Firma Digital *")
        chk_rgpd = st.checkbox("Acepto la Política de Protección de Datos (RGPD) y tratamiento de datos personales.", value=True)

        if st.button("✍️ Guardar Firma de Consentimiento", use_container_width=True):
            if nombre_firma:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO consentimientos (cliente_id, tipo_tratamiento, fecha_firma, acepta_rgpd, firma_texto) VALUES (?,?,?,?,?)",
                               (c_sel, tipo_trat, datetime.date.today().strftime("%Y-%m-%d"), 1 if chk_rgpd else 0, nombre_firma))
                conn.commit()
                conn.close()
                st.success("¡Consentimiento firmado y guardado en el expediente de la clienta!")
                st.rerun()

# 4. LISTA DE ESPERA
with opcion[3]:
    st.subheader("⏳ Lista de Espera de Citas")
    
    with st.expander("➕ Añadir Clienta a Lista de Espera", expanded=True):
        conn = sqlite3.connect(DB_NAME)
        df_c = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes", conn)
        df_s = pd.read_sql_query("SELECT id, nombre FROM servicios", conn)
        conn.close()

        if not df_c.empty and not df_s.empty:
            c_le = st.selectbox("Clienta", options=df_c["id"], format_func=lambda x: df_c[df_c["id"]==x]["nom"].values[0])
            s_le = st.selectbox("Tratamiento Deseado", options=df_s["id"], format_func=lambda x: df_s[df_s["id"]==x]["nombre"].values[0])
            pref_h = st.text_input("Preferencia Horaria", placeholder="Ej. Tardes a partir de las 17h o viernes mañana")

            if st.button("➕ Guardar en Lista de Espera"):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO lista_espera (cliente_id, servicio_id, preferencia_horario, fecha_registro) VALUES (?,?,?,?)",
                               (c_le, s_le, pref_h, datetime.date.today().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("Añadida a lista de espera.")
                st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_le_view = pd.read_sql_query("""SELECT le.id, cl.nombre || ' ' || COALESCE(cl.primer_apellido,'') as 'Clienta', cl.telefono as 'Móvil', s.nombre as 'Tratamiento', le.preferencia_horario as 'Preferencia', le.fecha_registro as 'Anotada el'
                                      FROM lista_espera le JOIN clientes cl ON le.cliente_id = cl.id JOIN servicios s ON le.servicio_id = s.id WHERE le.estado='Pendiente'""", conn)
    conn.close()
    st.dataframe(df_le_view, use_container_width=True)

# 5. FISCAL & TRIMESTRAL
with opcion[4]:
    st.subheader("🏛️ Panel Fiscal y Estimación de Trimestres")
    col_f1, col_f2 = st.columns(2)
    with col_f1: anio_f = st.selectbox("Año Fiscal", [2026, 2025])
    with col_f2: trim_f = st.selectbox("Trimestre", ["1T (Ene - Mar)", "2T (Abr - Jun)", "3T (Jul - Sep)", "4T (Oct - Dic)"])

    conn = sqlite3.connect(DB_NAME)
    df_f_ing = pd.read_sql_query("SELECT total, metodo_pago FROM facturas", conn)
    df_f_gas = pd.read_sql_query("SELECT base_imponible, iva_porcentaje, total FROM gastos", conn)
    conn.close()

    tot_v = df_f_ing['total'].sum() if not df_f_ing.empty else 0.0
    iva_rep = tot_v * 0.21
    tot_gb = df_f_gas['base_imponible'].sum() if not df_f_gas.empty else 0.0
    tot_gi = (df_f_gas['total'] - df_f_gas['base_imponible']).sum() if not df_f_gas.empty else 0.0

    iva_pag = iva_rep - tot_gi
    rend_net = tot_v - (tot_gb + tot_gi)
    irpf_est = max(0.0, rend_net * 0.20)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='card-metric'><h4>📊 IVA a Liquidar (Mod. 303)</h4><h2 style='color:#e6c566;'>{iva_pag:.2f} €</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='card-metric'><h4>📈 IRPF Estimado (Mod. 130)</h4><h2 style='color:#74b9ff;'>{irpf_est:.2f} €</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='card-metric'><h4>💵 Rendimiento Neto Real</h4><h2 style='color:#55efc4;'>{rend_net:.2f} €</h2></div>", unsafe_allow_html=True)

# 6. GASTOS & FACTURAS
with opcion[5]:
    st.subheader("📉 Gastos del Local y Compras")
    conn = sqlite3.connect(DB_NAME)
    df_g = pd.read_sql_query("SELECT fecha as 'Fecha', proveedor as 'Proveedor', concepto as 'Concepto', total as 'Total (€)' FROM gastos ORDER BY fecha DESC", conn)
    conn.close()
    st.dataframe(df_g, use_container_width=True)

# 7. STOCK TOP
with opcion[6]:
    st.subheader("📦 Control de Stock Seleccionado")
    conn = sqlite3.connect(DB_NAME)
    df_st = pd.read_sql_query("SELECT nombre as 'Producto', categoria as 'Tipo', pvp as 'PVP (€)', unidades as 'Unidades Stock' FROM stock", conn)
    conn.close()
    st.dataframe(df_st, use_container_width=True)

# 8. MARKETING & REGALOS
with opcion[7]:
    st.subheader("📣 Tarjetas Regalo y Fidelización")
    conn = sqlite3.connect(DB_NAME)
    df_tr_list = pd.read_sql_query("SELECT codigo as 'Código', comprador as 'Comprador', beneficiario as 'Beneficiaria', saldo_actual as 'Saldo Disponible (€)' FROM tarjetas_regalo WHERE estado='Activa'", conn)
    conn.close()
    st.dataframe(df_tr_list, use_container_width=True)

# 9. CLIENTES Y MONEDERO
with opcion[8]:
    st.subheader("👤 Fichero de Clientes y Monedero Saldo")
    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as 'Nombre', telefono as 'Móvil', PRINTF('%.2f €', monedero) as 'Saldo Monedero' FROM clientes ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_cli, use_container_width=True)

# 10. SERVICIOS
with opcion[9]:
    st.subheader("💆‍♀️ Catálogo de Tratamientos")
    conn = sqlite3.connect(DB_NAME)
    df_serv = pd.read_sql_query("SELECT nombre as 'Tratamiento', duracion_min as 'Duración (min)', precio as 'Precio (€)' FROM servicios", conn)
    conn.close()
    st.dataframe(df_serv, use_container_width=True)
    
