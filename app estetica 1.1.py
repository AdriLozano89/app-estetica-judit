import streamlit as st
from streamlit_calendar import calendar
import sqlite3
import datetime
import pandas as pd
import hashlib
import os
import base64
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import io

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

# Cargar el logo local en Base64
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
                    return f"data:{mime_type};base64,{encoded_string}", ruta_completa
            except Exception:
                pass
    return None, None

logo_data_uri, ruta_logo_file = cargar_logo_base64()

# GESTIÓN DE SESIÓN
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = True

# CSS CON LOGO DE FONDO GIGANTE Y FUENTE ESTILO BALQIS (Great Vibes / Alex Brush)
css_logo_fondo = ""
if logo_data_uri:
    css_logo_fondo = f"""
    .stApp::before {{
        content: "";
        position: fixed;
        top: 52%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 85vw;
        max-width: 650px;
        height: 75vh;
        max-height: 650px;
        background-image: url("{logo_data_uri}");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        opacity: 0.30 !important;
        pointer-events: none !important;
        z-index: 0 !important;
    }}
    """

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Alex+Brush&family=Great+Vibes&family=Quicksand:wght@400;500;600;700&display=swap');

    {css_logo_fondo}

    section[data-testid="stSidebar"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ background-color: transparent !important; z-index: 100 !important; }}

    .stApp {{
        background-color: #0b0a0f !important;
        color: #f7f5fd !important;
        font-family: 'Quicksand', sans-serif !important;
    }}

    .block-container {{
        padding-top: 0.8rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
        position: relative !important;
        z-index: 1 !important;
    }}

    /* TÍTULOS CURSIVOS ELEGANTES ESTILO BALQIS */
    h1, h2, h3, .brand-title {{
        font-family: 'Great Vibes', 'Alex Brush', cursive !important;
        color: #e6c566 !important;
        letter-spacing: 1px !important;
        font-weight: 400 !important;
        font-size: 38px !important;
    }}

    .brand-subtext {{
        font-family: 'Quicksand', sans-serif;
        font-size: 11px;
        color: #d4af37;
        letter-spacing: 3px;
        margin-top: -8px;
        text-transform: uppercase;
        font-weight: 600;
    }}

    .card-metric {{
        background: rgba(22, 19, 32, 0.88);
        border: 1px solid #3d3550;
        border-left: 4px solid #e6c566;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        margin-bottom: 10px;
    }}

    .stButton>button {{
        background: linear-gradient(135deg, #e6c566 0%, #ba9530 100%) !important;
        color: #1a1600 !important;
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 18px !important;
        border-radius: 14px !important;
        border: none !important;
        box-shadow: 0 3px 10px rgba(230, 197, 102, 0.25) !important;
        width: 100% !important;
    }}

    .stLinkButton>a {{
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important;
        color: #ffffff !important;
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 18px !important;
        border-radius: 14px !important;
        border: none !important;
        text-decoration: none !important;
        display: block !important;
        text-align: center !important;
        width: 100% !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{ 
        gap: 4px; 
        overflow-x: auto;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px 10px 0px 0px !important;
        padding: 8px 12px !important;
        background-color: rgba(18, 16, 26, 0.9) !important;
        color: #bfa8db !important;
        font-family: 'Quicksand', sans-serif !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(35, 30, 50, 0.95) !important;
        color: #e6c566 !important;
        font-weight: 700 !important;
    }}

    /* FIX HORAS Y TEXTOS EN CALENDARIO */
    .fc {{
        font-size: 12px !important;
        font-family: 'Quicksand', sans-serif !important;
        background-color: rgba(15, 14, 22, 0.85) !important;
        border-radius: 12px;
        padding: 6px;
    }}
    .fc-timegrid-slot {{
        height: 38px !important;
    }}
    .fc-timegrid-slot-label-frame {{
        text-align: center !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #d4af37 !important;
    }}
    .fc-toolbar-title {{
        font-size: 18px !important;
        font-family: 'Great Vibes', cursive !important;
        color: #e6c566 !important;
    }}
    .fc-button {{
        padding: 4px 10px !important;
        font-size: 11px !important;
        border-radius: 10px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# CONTROL LOGIN
if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("""
            <div class='card-metric'>
                <h2 style='font-family: "Great Vibes", cursive; font-size:42px;'>Judit Domingo</h2>
                <p class='brand-subtext'>CENTRE D'ESTÈTICA</p>
                <hr style='border-color: #3d3550;'>
            </div>
        """, unsafe_allow_html=True)
        usr = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("🔑 Iniciar Sesión", use_container_width=True):
            if usr == "judit" and pwd == "1234":
                st.session_state["authenticated"] = True
                st.success("¡Bienvenida!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

# BASE DE DATOS
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
                        estado_cobro TEXT DEFAULT 'Pendiente',
                        metodo_pago TEXT,
                        monto_cobrado REAL DEFAULT 0.0,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                        FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')

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

    cursor.execute('''CREATE TABLE IF NOT EXISTS facturas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        num_factura TEXT UNIQUE,
                        fecha_hora TEXT,
                        concepto TEXT,
                        total REAL,
                        metodo_pago TEXT,
                        hash_registro TEXT)''')

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

# HEADER
col_h1, col_h2 = st.columns([7, 3])
with col_h1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div>
                <div class="brand-title" style="font-size: 38px; line-height:0.9;">Judit Domingo</div>
                <div class="brand-subtext">CENTRE D'ESTÈTICA</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🔒 Salir", use_container_width=True, key="btn_logout_top"):
        st.session_state["authenticated"] = False
        st.rerun()

# NAVEGACIÓN
opcion = st.tabs([
    "📅 Agenda", 
    "💳 Caja & Cobros", 
    "📈 Estadísticas Top",
    "📣 Marketing & Promo", 
    "👤 Clientes", 
    "💆‍♀️ Servicios",
    "📦 Stock", 
    "🏛️ Fiscal & Trimestral", 
    "📉 Gastos", 
    "⏳ Lista Espera",
    "✍️ Firma & RGPD"
])

def generar_link_whatsapp(telefono, texto_mensaje):
    tel_clean = "".join(filter(str.isdigit, str(telefono or "")))
    if tel_clean and len(tel_clean) == 9 and not tel_clean.startswith("34"):
        tel_clean = f"34{tel_clean}"
    return f"https://api.whatsapp.com/send?phone={tel_clean}&text={urllib.parse.quote(texto_mensaje, encoding='utf-8')}"

# GENERADOR DE IMAGEN TARJETA REGALO FÍSICA
def generar_tarjeta_regalo_img(codigo, comprador, beneficiario, concepto, importe):
    ancho, alto = 1000, 580
    img = Image.new("RGB", (ancho, alto), color="#0f0e13")
    draw = ImageDraw.Draw(img)

    draw.rectangle([20, 20, ancho-20, alto-20], outline="#e6c566", width=4)
    draw.rectangle([30, 30, ancho-30, alto-30], outline="#ba9530", width=2)

    if ruta_logo_file and os.path.exists(ruta_logo_file):
        try:
            logo_img = Image.open(ruta_logo_file).convert("RGBA")
            logo_img.thumbnail((260, 260))
            alpha = logo_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))
            logo_img.putalpha(alpha)
            pos_x = (ancho - logo_img.width) // 2
            pos_y = (alto - logo_img.height) // 2
            img.paste(logo_img, (pos_x, pos_y), logo_img)
        except Exception:
            pass

    draw.text((ancho//2, 70), "Judit Domingo", fill="#e6c566", anchor="mm", font_size=52)
    draw.text((ancho//2, 120), "CENTRE D'ESTÈTICA — TARJETA REGALO", fill="#d4af37", anchor="mm", font_size=20)

    draw.text((80, 200), f"Para: {beneficiario}", fill="#ffffff", font_size=30)
    draw.text((80, 260), f"De: {comprador}", fill="#dcd6f7", font_size=26)
    draw.text((80, 320), f"Tratamiento / Regalo: {concepto}", fill="#e6c566", font_size=26)

    draw.rectangle([ancho-320, alto-160, ancho-60, alto-60], fill="#1e192c", outline="#e6c566", width=2)
    draw.text((ancho-190, alto-110), f"{importe:.2f} €", fill="#e6c566", anchor="mm", font_size=38)

    draw.text((80, alto-80), f"Código Regalo: {codigo}", fill="#a29bfe", font_size=22)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
# MODAL NUEVA CITA
@st.dialog("➕ Agendar Nueva Cita")
def modal_crear_cita(fecha_hora_inicio):
    conn = sqlite3.connect(DB_NAME)
    df_c = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes ORDER BY nombre ASC", conn)
    df_s = pd.read_sql_query("SELECT id, nombre, duracion_min, precio FROM servicios ORDER BY nombre ASC", conn)
    conn.close()

    if df_c.empty or df_s.empty:
        st.warning("Debes dar de alta al menos a 1 cliente y 1 servicio primero.")
        return

    st.markdown(f"📅 **Hora Seleccionada:** `{fecha_hora_inicio.replace('T', ' ')[:16]}`")

    opciones_cli = [0] + list(df_c["id"])
    dict_cli = {0: "--- Selecciona una clienta ---"}
    for _, r in df_c.iterrows(): dict_cli[r["id"]] = r["nom"]

    c_sel = st.selectbox("Clienta *", options=opciones_cli, format_func=lambda x: dict_cli[x])
    s_sel = st.selectbox("Servicio / Tratamiento *", options=df_s["id"], format_func=lambda x: df_s[df_s["id"]==x]["nombre"].values[0])
    obs = st.text_input("Observaciones / Notas")

    if st.button("💾 Confirmar y Guardar Cita", use_container_width=True, type="primary"):
        if c_sel == 0:
            st.error("Por favor, selecciona una clienta.")
            return

        serv_row = df_s[df_s["id"] == s_sel].iloc[0]
        dur_min = int(serv_row["duracion_min"])
        
        dt_ini = datetime.datetime.fromisoformat(fecha_hora_inicio.replace('Z', ''))
        dt_fin = dt_ini + datetime.timedelta(minutes=dur_min)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO citas (fecha_inicio, fecha_fin, cliente_id, servicio_id, notas) VALUES (?,?,?,?,?)",
                       (dt_ini.isoformat(), dt_fin.isoformat(), c_sel, s_sel, obs))
        conn.commit()
        conn.close()
        st.success("¡Cita agendada correctamente!")
        st.rerun()

# MODAL DETALLE CITA
@st.dialog("⚙️ Detalle de Cita")
def modal_editar_cita(cita_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, cl.telefono, s.nombre, s.precio, c.estado_cobro, c.metodo_pago, c.monto_cobrado, c.notas, cl.id
                      FROM citas c 
                      JOIN clientes cl ON c.cliente_id = cl.id 
                      JOIN servicios s ON c.servicio_id = s.id 
                      WHERE c.id = ?""", (cita_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("No se encontró la cita.")
        return

    f_i, f_f, cl_n, cl_ap, cl_tel, s_n, s_pre, est_c, met_p, monto_c, obs, cl_id = row
    nom_cli = f"{cl_n} {cl_ap or ''}".strip()
    dt_i = datetime.datetime.fromisoformat(f_i)

    st.markdown(f"### 💆‍♀️ {s_n}")
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

    st.markdown("#### 💬 Recordatorio WhatsApp")
    tel_destino = cl_tel if (cl_tel and str(cl_tel).strip() != "") else st.text_input("Número WhatsApp Clienta", placeholder="Ej. 612345678", key=f"tel_manual_{cita_id}")
    
    if tel_destino:
        txt_wa = f"Hola {nom_cli}! ✨\n\nTe recordamos tu cita en *Judit Domingo - Centre d'Estètica* para el servicio de *{s_n}* el día *{dt_i.strftime('%d/%m/%Y')}* a las *{dt_i.strftime('%H:%M')}h*.\n\nPor favor, confírmanos si puedes asistir. ¡Te esperamos! 💆‍♀️"
        url_wa = generar_link_whatsapp(tel_destino, txt_wa)
        st.link_button("📲 Enviar Recordatorio por WhatsApp", url_wa, use_container_width=True)

    st.markdown("---")
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

# 1. AGENDA
with opcion[0]:
    st.subheader("Agenda de Citas")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''SELECT c.id, c.fecha_inicio, c.fecha_fin, cl.nombre, cl.primer_apellido, cl.telefono, s.nombre, s.color, s.precio, c.estado_cobro
                      FROM citas c JOIN clientes cl ON c.cliente_id = cl.id JOIN servicios s ON c.servicio_id = s.id''')
    citas_db = cursor.fetchall()
    conn.close()

    events = []
    for cita in citas_db:
        c_id, f_ini, f_fin, cl_nombre, cl_p_ap, cl_tel, s_nombre, color, precio, est_cobro = cita
        nom_comp = f"{cl_nombre} {cl_p_ap or ''}".strip()
        prefijo = "✅ " if est_cobro == "Cobrado" else ""
        events.append({
            "id": f"cita_{c_id}",
            "title": f"{prefijo}[{nom_comp}] {s_nombre}",
            "start": f_ini, "end": f_fin,
            "backgroundColor": "#2ecc71" if est_cobro == "Cobrado" else color,
            "borderColor": color
        })

    cal_options = {
        "locale": "es",
        "initialView": "timeGridWeek",
        "firstDay": 1,
        "allDaySlot": False,
        "slotMinTime": "08:30:00",
        "slotMaxTime": "20:30:00",
        "slotDuration": "00:30:00",
        "slotLabelFormat": {
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        },
        "dayHeaderFormat": {
            "weekday": "short",
            "day": "numeric",
            "month": "numeric",
            "omitCommas": True
        },
        "height": 750,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next",
            "center": "title",
            "right": "timeGridWeek,timeGridDay"
        },
        "buttonText": {
            "today": "Hoy",
            "week": "Semana",
            "day": "Día"
        }
    }

    state = calendar(events=events, options=cal_options, key="koibox_cal_v15")

    if state.get("eventClick"):
        raw_id = state["eventClick"]["event"]["id"]
        if raw_id.startswith("cita_"):
            c_id = int(raw_id.replace("cita_", ""))
            modal_editar_cita(c_id)

    if state.get("dateClick"):
        click_str = state["dateClick"]["date"]
        modal_crear_cita(click_str)
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

# 3. ESTADÍSTICAS ORGANIZADAS
with opcion[2]:
    st.subheader("📈 Centro de Analítica & Estadísticas")
    
    tab_est1, tab_est2, tab_est3, tab_est4 = st.tabs([
        "💵 Finanzas & Rendimiento", 
        "💆‍♀️ Servicios & Ventas", 
        "👑 Ranking Clientas", 
        "⏰ Ocupación & Horarios"
    ])

    conn = sqlite3.connect(DB_NAME)
    df_citas_cob = pd.read_sql_query("""SELECT c.fecha_inicio, c.monto_cobrado, c.metodo_pago, s.nombre as servicio, cl.nombre || ' ' || COALESCE(cl.primer_apellido,'') as cliente
                                        FROM citas c 
                                        JOIN servicios s ON c.servicio_id = s.id
                                        JOIN clientes cl ON c.cliente_id = cl.id
                                        WHERE c.estado_cobro='Cobrado'""", conn)
    conn.close()

    if df_citas_cob.empty:
        st.info("Aún no hay citas cobradas para mostrar las analíticas.")
    else:
        with tab_est1:
            tot_fact = df_citas_cob["monto_cobrado"].sum()
            num_serv = len(df_citas_cob)
            ticket_med = tot_fact / num_serv if num_serv > 0 else 0.0

            c_f1, c_f2 = st.columns(2)
            with c_f1: st.metric("💶 Facturación Total", f"{tot_fact:.2f} €")
            with c_f2: st.metric("🎟️ Ticket Medio / Cita", f"{ticket_med:.2f} €")

            st.markdown("#### 💳 Distribución por Método de Pago")
            st.bar_chart(df_citas_cob["metodo_pago"].value_counts())

        with tab_est2:
            st.markdown("#### 💆‍♀️ Tratamientos Más Demandados")
            st.bar_chart(df_citas_cob["servicio"].value_counts())

            st.markdown("#### 📊 Facturación Total por Tratamiento")
            df_serv_fact = df_citas_cob.groupby("servicio")["monto_cobrado"].sum().reset_index().sort_values(by="monto_cobrado", ascending=False)
            df_serv_fact.columns = ["Tratamiento", "Total Ingresado (€)"]
            st.dataframe(df_serv_fact, use_container_width=True)

        with tab_est3:
            st.markdown("#### 👑 Top Clientas por Volumen de Gasto")
            df_top_cli = df_citas_cob.groupby("cliente")["monto_cobrado"].sum().reset_index().sort_values(by="monto_cobrado", ascending=False).head(10)
            df_top_cli.columns = ["Clienta", "Gasto Acumulado (€)"]
            st.dataframe(df_top_cli, use_container_width=True)

        with tab_est4:
            st.markdown("#### ⏰ Franjas Horarias con Más Afluencia")
            df_citas_cob["hora"] = pd.to_datetime(df_citas_cob["fecha_inicio"]).dt.hour
            st.bar_chart(df_citas_cob["hora"].value_counts().sort_index())

# 4. MARKETING
with opcion[3]:
    st.subheader("📣 Módulo de Marketing y Fidelización")
    tab_m1, tab_m2, tab_m3 = st.tabs(["🎁 Emisión de Tarjeta Regalo", "🎂 Cumpleaños del Mes", "💬 Plantillas WhatsApp"])

    with tab_m1:
        st.markdown("### 🎁 Crear Nueva Tarjeta Regalo")
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            tr_comprador = st.text_input("Comprador/a (Persona que regala) *")
            tr_beneficiario = st.text_input("Beneficiario/a (Persona que recibe) *")
            tr_concepto = st.text_input("Concepto / Tratamiento Incluido *", value="Tratamiento Facial VIP / Maderoterapia")
        with col_tr2:
            tr_importe = st.number_input("Importe (€) *", value=50.0, step=5.0)
            tr_caducidad = st.date_input("Fecha Caducidad", value=datetime.date.today() + datetime.timedelta(days=90))
            tr_tel_envio = st.text_input("Móvil Beneficiaria (Para envío por WhatsApp)")

        if st.button("🎁 Emitir y Guardar Tarjeta Regalo", use_container_width=True, type="primary"):
            if tr_comprador and tr_beneficiario and tr_concepto:
                cod_tr = f"TR-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO tarjetas_regalo (codigo, comprador, beneficiario, concepto, saldo_inicial, saldo_actual, fecha_emision, fecha_caducidad, estado)
                                  VALUES (?,?,?,?,?,?,?,?,'Activa')""",
                               (cod_tr, tr_comprador, tr_beneficiario, tr_concepto, tr_importe, tr_importe, datetime.date.today().strftime("%Y-%m-%d"), tr_caducidad.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success(f"¡Tarjeta Regalo {cod_tr} Emitida Correctamente!")

                img_bytes = generar_tarjeta_regalo_img(cod_tr, tr_comprador, tr_beneficiario, tr_concepto, tr_importe)
                st.image(img_bytes, caption="Vista Previa Tarjeta Regalo Física", use_container_width=True)

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button("📥 Descargar Tarjeta en PNG (Para Imprimir)", data=img_bytes, file_name=f"Tarjeta_Regalo_{cod_tr}.png", mime="image/png", use_container_width=True)
                with col_d2:
                    if tr_tel_envio:
                        msg_tr = f"¡Hola {tr_beneficiario}! 🎁 Te han regalado una Tarjeta Regalo en *Judit Domingo Centre d'Estètica* por valor de *{tr_importe:.2f}€* (*{tr_concepto}*). ¡Llámanos para agendar tu cita!"
                        url_tr_wa = generar_link_whatsapp(tr_tel_envio, msg_tr)
                        st.link_button("📲 Notificar por WhatsApp", url_tr_wa, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📋 Tarjetas Regalo Emitidas")
        conn = sqlite3.connect(DB_NAME)
        df_tr_list = pd.read_sql_query("SELECT codigo as 'Código', comprador as 'Comprador', beneficiario as 'Beneficiaria', concepto as 'Tratamiento', saldo_actual as 'Saldo Disponible (€)', fecha_caducidad as 'Caducidad' FROM tarjetas_regalo WHERE estado='Activa' ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_tr_list, use_container_width=True)

    with tab_m2:
        st.markdown("### 🎂 Próximos Cumpleaños")
        mes_actual = datetime.date.today().strftime("%m")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre || ' ' || COALESCE(primer_apellido,''), telefono, fecha_nacimiento FROM clientes WHERE fecha_nacimiento LIKE ?", (f"%-{mes_actual}-%",))
        cump_rows = cursor.fetchall()
        conn.close()

        if not cump_rows:
            st.info("No hay cumpleaños registrados para este mes.")
        else:
            for nom_c, tel_c, fnac_c in cump_rows:
                col1, col2 = st.columns([3, 1])
                with col1: st.markdown(f"🎉 **{nom_c}** ({fnac_c})")
                with col2:
                    if tel_c:
                        msg_cump = f"¡Feliz Cumpleaños {nom_c}! 🥳✨ Desde Judit Domingo Centre d'Estètica te deseamos un gran día. ¡Tienes un 10% de descuento en tu próximo tratamiento como regalo!"
                        url_cump = generar_link_whatsapp(tel_c, msg_cump)
                        st.link_button("📲 Felicitar", url_cump, use_container_width=True)

    with tab_m3:
        st.markdown("### 💬 Difusión y Promociones")
        plantilla = st.selectbox("Selecciona Tipo de Campaña", [
            "Lanzamiento de Tratamiento (Maderoterapia/Facial)",
            "Promoción Especial de Temporada",
            "Solicitud de Reseña en Google (5 Estrellas)"
        ])

        if plantilla == "Lanzamiento de Tratamiento (Maderoterapia/Facial)":
            txt_promo = "Hola! ✨ Novedad en Judit Domingo Centre d'Estètica. Hemos abierto agenda para el nuevo tratamiento facial/corporal. ¡Reserva tu plaza esta semana y llévate un diagnóstico gratuito! 💆‍♀️"
        elif plantilla == "Promoción Especial de Temporada":
            txt_promo = "Hola! 🌸 Prepara tu piel esta temporada. Disfruta de un pack especial este mes. ¡Plazas limitadas! Mándanos un mensaje para agendar tu cita."
        else:
            txt_promo = "Hola! ✨ Muchas gracias por confiar en Judit Domingo Centre d'Estètica. Nos encantaría saber tu opinión: ¿nos dejas 5 estrellas en Google? Nos ayuda muchísimo: https://g.page/r/juditestetica"

        st.text_area("Texto de la Promoción (Copia y envía por WhatsApp)", value=txt_promo, height=100)

# 5. CLIENTES
with opcion[4]:
    st.subheader("👤 Fichero de Clientes")
    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as 'Nombre', telefono as 'Móvil', PRINTF('%.2f €', monedero) as 'Saldo Monedero' FROM clientes ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_cli, use_container_width=True)

# 6. SERVICIOS
with opcion[5]:
    st.subheader("💆‍♀️ Catálogo de Tratamientos")
    conn = sqlite3.connect(DB_NAME)
    df_serv = pd.read_sql_query("SELECT nombre as 'Tratamiento', duracion_min as 'Duración (min)', precio as 'Precio (€)' FROM servicios", conn)
    conn.close()
    st.dataframe(df_serv, use_container_width=True)

# 7. STOCK
with opcion[6]:
    st.subheader("📦 Control de Stock")
    conn = sqlite3.connect(DB_NAME)
    df_st = pd.read_sql_query("SELECT nombre as 'Producto', categoria as 'Tipo', pvp as 'PVP (€)', unidades as 'Unidades Stock' FROM stock", conn)
    conn.close()
    st.dataframe(df_st, use_container_width=True)

# 8. FISCAL & TRIMESTRAL
with opcion[7]:
    st.subheader("🏛️ Panel Control Fiscal & Trimestral")
    col_f1, col_f2 = st.columns(2)
    with col_f1: anio_f = st.selectbox("Año Fiscal", [2026, 2025])
    with col_f2: trim_f = st.selectbox("Trimestre a Calcular", ["1T (Ene - Mar)", "2T (Abr - Jun)", "3T (Jul - Sep)", "4T (Oct - Dic)"])

    conn = sqlite3.connect(DB_NAME)
    df_f_ing = pd.read_sql_query("SELECT total, metodo_pago FROM facturas", conn)
    df_f_gas = pd.read_sql_query("SELECT base_imponible, iva_porcentaje, total FROM gastos", conn)
    conn.close()

    total_ventas = df_f_ing['total'].sum() if not df_f_ing.empty else 0.0
    iva_repercutido = total_ventas * 0.21

    total_gastos_base = df_f_gas['base_imponible'].sum() if not df_f_gas.empty else 0.0
    total_gastos_iva = (df_f_gas['total'] - df_f_gas['base_imponible']).sum() if not df_f_gas.empty else 0.0

    iva_a_pagar = iva_repercutido - total_gastos_iva
    rendimiento_neto = total_ventas - (total_gastos_base + total_gastos_iva)
    irpf_estimado = max(0.0, rendimiento_neto * 0.20)

    st.markdown("---")
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.markdown(f"<div class='card-metric'><h4>📊 IVA a Liquidar (Mod. 303)</h4><h2 style='color:#e6c566;'>{iva_a_pagar:.2f} €</h2></div>", unsafe_allow_html=True)
    with c_m2:
        st.markdown(f"<div class='card-metric'><h4>📈 IRPF Estimado (Mod. 130)</h4><h2 style='color:#74b9ff;'>{irpf_estimado:.2f} €</h2></div>", unsafe_allow_html=True)
    with c_m3:
        st.markdown(f"<div class='card-metric'><h4>💵 Rendimiento Neto Real</h4><h2 style='color:#55efc4;'>{rendimiento_neto:.2f} €</h2></div>", unsafe_allow_html=True)

# 9. GASTOS
with opcion[8]:
    st.subheader("📉 Gastos del Local")
    conn = sqlite3.connect(DB_NAME)
    df_g = pd.read_sql_query("SELECT fecha as 'Fecha', proveedor as 'Proveedor', concepto as 'Concepto', total as 'Total (€)' FROM gastos ORDER BY fecha DESC", conn)
    conn.close()
    st.dataframe(df_g, use_container_width=True)

# 10. LISTA DE ESPERA
with opcion[9]:
    st.subheader("⏳ Lista de Espera")
    conn = sqlite3.connect(DB_NAME)
    df_le_view = pd.read_sql_query("""SELECT le.id, cl.nombre || ' ' || COALESCE(cl.primer_apellido,'') as 'Clienta', cl.telefono as 'Móvil', s.nombre as 'Tratamiento', le.preferencia_horario as 'Preferencia'
                                      FROM lista_espera le JOIN clientes cl ON le.cliente_id = cl.id JOIN servicios s ON le.servicio_id = s.id WHERE le.estado='Pendiente'""", conn)
    conn.close()
    st.dataframe(df_le_view, use_container_width=True)

# 11. FIRMA & RGPD
with opcion[10]:
    st.subheader("✍️ Firma Digital de Consentimientos & RGPD")
    conn = sqlite3.connect(DB_NAME)
    df_cli_select = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes", conn)
    conn.close()

    if not df_cli_select.empty:
        c_sel = st.selectbox("Seleccionar Clienta *", options=df_cli_select["id"], format_func=lambda x: df_cli_select[df_cli_select["id"]==x]["nom"].values[0])
        tipo_trat = st.selectbox("Tratamiento a Realizar", ["Maderoterapia Corporal", "Higiene Facial Profunda / Peeling", "Lifting / Extensión de Pestañas", "Microblading / Micropigmentación", "Tratamiento General Estética"])
        
        nombre_firma = st.text_input("Escribe tu Nombre Completo como Firma Digital *")
        chk_rgpd = st.checkbox("Acepto la Política de Protección de Datos (RGPD).", value=True)

        if st.button("✍️ Guardar Firma de Consentimiento", use_container_width=True):
            if nombre_firma:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO consentimientos (cliente_id, tipo_tratamiento, fecha_firma, acepta_rgpd, firma_texto) VALUES (?,?,?,?,?)",
                               (c_sel, tipo_trat, datetime.date.today().strftime("%Y-%m-%d"), 1 if chk_rgpd else 0, nombre_firma))
                conn.commit()
                conn.close()
                st.success("¡Consentimiento firmado y guardado!")
                st.rerun()
    
