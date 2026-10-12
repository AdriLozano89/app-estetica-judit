import streamlit as st
from streamlit_calendar import calendar
import sqlite3
import datetime
import pandas as pd
import hashlib
import os
import base64
import urllib.parse

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN Y ESTILOS UI/UX
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Judit Domingo - Centre d'Estètica",
    page_icon="💆‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "gestion_estetica_v2.db"

def cargar_logo_base64():
    directorio = os.path.dirname(os.path.abspath(__file__))
    nombres_posibles = ["imagen_2026-10-08_205258476.jpg", "images.jpg", "logo.jpg", "logo.png", "images.png"]
    for nombre in nombres_posibles:
        ruta = os.path.join(directorio, nombre)
        if os.path.exists(ruta):
            try:
                with open(ruta, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                    mime = "image/png" if nombre.endswith(".png") else "image/jpeg"
                    return f"data:{mime};base64,{encoded}"
            except Exception:
                pass
    return None

logo_data_uri = cargar_logo_base64()

css_logo_fondo = ""
if logo_data_uri:
    css_logo_fondo = f"""
    .stApp::before {{
        content: ""; position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%); width: 100vw; height: 100vh;
        background-image: url("{logo_data_uri}"); background-repeat: no-repeat;
        background-position: center; background-size: contain; opacity: 0.12 !important;
        pointer-events: none !important; z-index: 0 !important;
    }}
    """

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Great+Vibes&family=Quicksand:wght@400;500;600;700&display=swap');

    {css_logo_fondo}

    section[data-testid="stSidebar"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 100 !important; }}

    .stApp {{
        background-color: #0b0a0f !important;
        color: #f7f5fd !important;
        font-family: 'Quicksand', sans-serif !important;
    }}

    .block-container {{
        padding-top: 0.5rem !important; padding-bottom: 5rem !important;
        padding-left: 0.5rem !important; padding-right: 0.5rem !important;
        max-width: 100% !important; z-index: 1 !important;
    }}

    .brand-title {{
        font-family: 'Great Vibes', cursive !important;
        color: #e6c566 !important; font-size: 40px !important; line-height: 0.9 !important;
    }}

    .brand-subtext {{
        font-family: 'Quicksand', sans-serif; font-size: 10px;
        color: #d4af37; letter-spacing: 3px; text-transform: uppercase; font-weight: 600;
    }}

    .card-metric {{
        background: rgba(22, 19, 32, 0.9); border: 1px solid #3d3550;
        border-left: 4px solid #e6c566; border-radius: 12px; padding: 14px; text-align: center;
    }}

    .stButton>button {{
        background: linear-gradient(135deg, #e6c566 0%, #ba9530 100%) !important;
        color: #1a1600 !important; font-weight: 700 !important; border-radius: 12px !important;
        border: none !important; width: 100% !important;
    }}

    /* BOTÓN FLOTANTE ANIMADO EN LA ESQUINA INFERIOR DERECHA */
    @keyframes botSaludo {{
        0% {{ transform: rotate(0deg) scale(1); }}
        15% {{ transform: rotate(14deg) scale(1.1); }}
        30% {{ transform: rotate(-12deg) scale(1.1); }}
        45% {{ transform: rotate(10deg) scale(1.05); }}
        60% {{ transform: rotate(0deg) scale(1); }}
        100% {{ transform: rotate(0deg) scale(1); }}
    }}

    div[data-testid="stPopover"] {{
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        z-index: 999999 !important;
    }}

    div[data-testid="stPopover"] > button {{
        animation: botSaludo 3.2s infinite ease-in-out !important;
        background: linear-gradient(135deg, #ba9530 0%, #e6c566 100%) !important;
        color: #0d0c12 !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        border-radius: 50px !important;
        padding: 12px 22px !important;
        box-shadow: 0 6px 20px rgba(230, 197, 102, 0.5) !important;
        border: 2px solid #fff3c4 !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0 0 !important; padding: 10px 16px !important;
        background-color: rgba(18, 16, 26, 0.95) !important; color: #bfa8db !important; font-weight: 700 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(38, 32, 54, 0.95) !important; color: #e6c566 !important;
        border-bottom: 3px solid #e6c566 !important;
    }}

    .fc {{
        font-size: 12px !important; font-family: 'Quicksand', sans-serif !important;
        background-color: rgba(15, 14, 22, 0.88) !important; border-radius: 12px; padding: 6px;
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. BASE DE DATOS
# ------------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
                        primer_apellido TEXT, telefono TEXT, email TEXT, fecha_nacimiento TEXT, monedero REAL DEFAULT 0.0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS servicios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL,
                        duracion_min INTEGER NOT NULL, precio REAL NOT NULL, color TEXT DEFAULT '#9b59b6')''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS citas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_inicio TEXT NOT NULL, fecha_fin TEXT NOT NULL,
                        cliente_id INTEGER, servicio_id INTEGER, notas TEXT, estado_cobro TEXT DEFAULT 'Pendiente',
                        metodo_pago TEXT, monto_cobrado REAL DEFAULT 0.0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS facturas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, num_factura TEXT UNIQUE,
                        fecha_hora TEXT, concepto TEXT, total REAL, metodo_pago TEXT, hash_registro TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS tarjetas_regalo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE NOT NULL,
                        comprador TEXT NOT NULL, beneficiario TEXT NOT NULL, concepto TEXT NOT NULL,
                        saldo_actual REAL NOT NULL, fecha_caducidad TEXT, estado TEXT DEFAULT 'Activa')''')

    cursor.execute("SELECT COUNT(*) FROM servicios")
    if cursor.fetchone()[0] == 0:
        servicios_def = [
            ("Manicura Semipermanente", 45, 25.0, "#e74c3c"),
            ("Acrylgel uñas largas", 60, 40.0, "#9b59b6"),
            ("Higiene Facial Profunda", 60, 45.0, "#3498db"),
            ("Maderoterapia Corporal", 60, 50.0, "#2ecc71")
        ]
        cursor.executemany("INSERT INTO servicios (nombre, duracion_min, precio, color) VALUES (?,?,?,?)", servicios_def)

    conn.commit()
    conn.close()

init_db()

def generar_link_whatsapp(telefono, texto):
    tel = "".join(filter(str.isdigit, str(telefono or "")))
    if len(tel) == 9 and not tel.startswith("34"): tel = f"34{tel}"
    return f"https://api.whatsapp.com/send?phone={tel}&text={urllib.parse.quote(texto)}"

def renderizar_tarjeta_regalo_html(codigo, comprador, beneficiario, concepto, importe):
    logo_html = f'<img src="{logo_data_uri}" style="max-width:300px; max-height:200px; opacity:0.25; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); z-index:1;">' if logo_data_uri else ''
    return f"""
    <div style="position:relative; width:100%; max-width:650px; margin:0 auto; background:#0f0e15; border:3px solid #e6c566; border-radius:18px; padding:25px; color:#fff; font-family:'Quicksand', sans-serif;">
        {logo_html}
        <div style="position:relative; z-index:2;">
            <div style="text-align:center; margin-bottom:15px;">
                <div style="font-family:'Great Vibes', cursive; font-size:46px; color:#e6c566; line-height:1;">Judit Domingo</div>
                <div style="font-size:11px; color:#d4af37; letter-spacing:3px; font-weight:700;">CENTRE D'ESTÈTICA — TARJETA REGALO</div>
            </div>
            <div style="background:rgba(22,19,32,0.85); border:1px solid #3d3550; border-radius:12px; padding:15px; margin-bottom:15px;">
                <div style="font-size:17px; margin-bottom:6px;"><b>Para:</b> {beneficiario}</div>
                <div style="font-size:15px; color:#dcd6f7; margin-bottom:6px;"><b>De:</b> {comprador}</div>
                <div style="font-size:15px; color:#e6c566;"><b>Tratamiento:</b> {concepto}</div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-size:13px; color:#a29bfe; font-weight:600;">Código: {codigo}</div>
                <div style="background:linear-gradient(135deg, #e6c566 0%, #ba9530 100%); color:#1a1600; font-weight:800; font-size:22px; padding:8px 20px; border-radius:10px;">
                    {importe:.2f} €
                </div>
            </div>
        </div>
    </div>
    """

# ------------------------------------------------------------------------------
# 3. MODALES DE CITA
# ------------------------------------------------------------------------------
@st.dialog("➕ Agendar Cita")
def modal_crear_cita(f_str):
    conn = sqlite3.connect(DB_NAME)
    df_c = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes", conn)
    df_s = pd.read_sql_query("SELECT id, nombre, duracion_min FROM servicios", conn)
    conn.close()

    if df_c.empty:
        st.warning("Añade al menos un cliente primero.")
        return

    c_sel = st.selectbox("Clienta *", options=df_c["id"], format_func=lambda x: df_c[df_c["id"]==x]["nom"].values[0])
    s_sel = st.selectbox("Servicio *", options=df_s["id"], format_func=lambda x: df_s[df_s["id"]==x]["nombre"].values[0])
    obs = st.text_input("Notas")

    if st.button("💾 Guardar Cita", type="primary", use_container_width=True):
        dur = int(df_s[df_s["id"]==s_sel]["duracion_min"].values[0])
        dt_i = datetime.datetime.fromisoformat(f_str.replace('Z', ''))
        dt_f = dt_i + datetime.timedelta(minutes=dur)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO citas (fecha_inicio, fecha_fin, cliente_id, servicio_id, notas) VALUES (?,?,?,?,?)",
                       (dt_i.isoformat(), dt_f.isoformat(), c_sel, s_sel, obs))
        conn.commit()
        conn.close()
        st.success("¡Cita agendada!")
        st.rerun()

# ------------------------------------------------------------------------------
# 4. INTERFAZ Y NAVEGACIÓN
# ------------------------------------------------------------------------------
st.markdown("""
    <div>
        <div class="brand-title">Judit Domingo</div>
        <div class="brand-subtext">CENTRE D'ESTÈTICA</div>
    </div>
""", unsafe_allow_html=True)

bloques = st.tabs([
    "📅 Agenda & Citas", 
    "💶 Caja & Finanzas", 
    "👤 Clientes", 
    "📣 Marketing & Regalos", 
    "📊 Analítica"
])

# BLOQUE 1: AGENDA
with bloques[0]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT c.id, c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, s.nombre, s.color, c.estado_cobro
                      FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id""")
    citas_db = cursor.fetchall()
    conn.close()

    events = [{
        "id": f"cita_{r[0]}",
        "title": f"{'✅ ' if r[7]=='Cobrado' else ''}[{r[3]} {r[4] or ''}] {r[5]}",
        "start": r[1], "end": r[2],
        "backgroundColor": "#2ecc71" if r[7]=="Cobrado" else r[6],
        "borderColor": r[6]
    } for r in citas_db]

    cal_opts = {
        "locale": "es", "initialView": "timeGridWeek", "firstDay": 1,
        "slotMinTime": "08:30:00", "slotMaxTime": "20:30:00", "height": 700, "selectable": True,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "timeGridWeek,timeGridDay"}
    }

    st_cal = calendar(events=events, options=cal_opts, key="main_cal")

    if st_cal.get("dateClick"):
        modal_crear_cita(st_cal["dateClick"]["date"])

# BLOQUE 2: CAJA
with bloques[1]:
    st.subheader("💶 Arqueo de Caja del Día")
    conn = sqlite3.connect(DB_NAME)
    df_f = pd.read_sql_query("SELECT num_factura, fecha_hora, concepto, total, metodo_pago FROM facturas", conn)
    conn.close()

    c1, c2, c3 = st.columns(3)
    tot = df_f["total"].sum() if not df_f.empty else 0.0
    with c1: st.metric("🏆 Ingresos Totales", f"{tot:.2f} €")
    with c2: st.metric("📊 IVA Repercutido (21%)", f"{tot*0.21:.2f} €")
    with c3: st.metric("📈 Base Imponible", f"{tot*0.79:.2f} €")

    st.markdown("### 📋 Registro de Facturas")
    st.dataframe(df_f, use_container_width=True)

# BLOQUE 3: CLIENTES
with bloques[2]:
    st.subheader("👤 Fichero de Clientes")
    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql_query("SELECT id, nombre, primer_apellido, telefono, email FROM clientes", conn)
    conn.close()
    
    with st.expander("➕ Dar de Alta Nueva Clienta"):
        c_n = st.text_input("Nombre *")
        c_a = st.text_input("Apellidos")
        c_t = st.text_input("Móvil (WhatsApp)")
        if st.button("💾 Guardar Clienta"):
            if c_n:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO clientes (nombre, primer_apellido, telefono) VALUES (?,?,?)", (c_n, c_a, c_t))
                conn.commit()
                conn.close()
                st.success("¡Clienta añadida!")
                st.rerun()

    st.dataframe(df_cli, use_container_width=True)

# BLOQUE 4: MARKETING & REGALOS
with bloques[3]:
    st.subheader("🎁 Emitir Tarjeta Regalo")
    col1, col2 = st.columns(2)
    with col1:
        comp = st.text_input("Comprador/a *")
        ben = st.text_input("Beneficiario/a *")
        conc = st.text_input("Tratamiento *", value="Tratamiento Facial VIP / Maderoterapia")
    with col2:
        imp = st.number_input("Importe (€) *", value=50.0, step=5.0)
        tel = st.text_input("Móvil Beneficiaria")

    if st.button("🎁 Generar Tarjeta Regalo", type="primary", use_container_width=True):
        if comp and ben:
            cod = f"TR-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tarjetas_regalo (codigo, comprador, beneficiario, concepto, saldo_actual) VALUES (?,?,?,?,?)",
                           (cod, comp, ben, conc, imp))
            conn.commit()
            conn.close()
            
            st.components.v1.html(renderizar_tarjeta_regalo_html(cod, comp, ben, conc, imp), height=320)
            if tel:
                msg = f"¡Hola {ben}! 🎁 Te han regalado una Tarjeta Regalo por valor de {imp:.2f}€ en Judit Domingo Centre d'Estètica."
                st.link_button("📲 Notificar por WhatsApp", generar_link_whatsapp(tel, msg), use_container_width=True)

# BLOQUE 5: ANALÍTICA
with bloques[4]:
    st.subheader("📊 Analítica de Ventas")
    conn = sqlite3.connect(DB_NAME)
    df_analisis = pd.read_sql_query("""SELECT s.nombre as servicio, c.monto_cobrado 
                                       FROM citas c JOIN servicios s ON c.servicio_id = s.id WHERE c.estado_cobro='Cobrado'""", conn)
    conn.close()

    if not df_analisis.empty:
        st.bar_chart(df_analisis["servicio"].value_counts())

# BOT ASISTENTE FLOTANTE (ESQUINA INFERIOR DERECHA CON ANIMACIÓN)
with st.popover("🤖 Bot Asistente (👋)", help="Haz clic para chatear con el asistente"):
    st.markdown("### 🤖 Asistente del Centro")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [{"role": "assistant", "content": "¡Hola Judit y Adri! 💆‍♀️ ¿En qué puedo ayudaros hoy?"}]

    for m in st.session_state["chat_history"]:
        st.chat_message(m["role"]).write(m["content"])

    if user_p := st.chat_input("Escribe tu duda..."):
        st.session_state["chat_history"].append({"role": "user", "content": user_p})
        st.chat_message("user").write(user_p)
        
        p = user_p.lower()
        if "caja" in p or "cobrar" in p:
            resp = "Para cobrar una cita, pulsa directamente sobre ella en la agenda o revisa el bloque '💶 Caja & Finanzas'."
        elif "maderoterapia" in p:
            resp = "La Maderoterapia corporal drena líquidos y moldea la figura. Sesiones recomendadas de 60 minutos."
        elif "llamo" in p or "nombre" in p:
            resp = "¡Sois Judit y Adri! Esta app es el gestor personalizado para Judit Domingo Centre d'Estètica."
        else:
            resp = f"Entendido. He procesado tu consulta sobre '{user_p}'. ¿Necesitas ayuda adicional?"

        st.session_state["chat_history"].append({"role": "assistant", "content": resp})
        st.chat_message("assistant").write(resp)
