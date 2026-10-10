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

# Configuración inicial
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

# CSS CON LOGO DE FONDO COMPLETO
css_logo_fondo = ""
if logo_data_uri:
    css_logo_fondo = f"""
    .stApp::before {{
        content: "";
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100vw;
        height: 100vh;
        background-image: url("{logo_data_uri}");
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        opacity: 0.15 !important;
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
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
        max-width: 100% !important;
        position: relative !important;
        z-index: 1 !important;
    }}

    h1, h2, h3, .brand-title {{
        font-family: 'Great Vibes', 'Alex Brush', cursive !important;
        color: #e6c566 !important;
        letter-spacing: 1px !important;
        font-weight: 400 !important;
        font-size: 38px !important;
    }}

    .brand-subtext {{
        font-family: 'Quicksand', sans-serif;
        font-size: 10px;
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
        padding: 8px 16px !important;
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
        padding: 8px 16px !important;
        border-radius: 14px !important;
        border: none !important;
        text-decoration: none !important;
        display: block !important;
        text-align: center !important;
        width: 100% !important;
    }}

    /* NAVEGACIÓN SUPERIOR POR BLOQUES LIMPIOS */
    .stTabs [data-baseweb="tab-list"] {{ 
        gap: 6px; 
        overflow-x: auto;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px 12px 0px 0px !important;
        padding: 10px 16px !important;
        background-color: rgba(18, 16, 26, 0.95) !important;
        color: #bfa8db !important;
        font-family: 'Quicksand', sans-serif !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(38, 32, 54, 0.95) !important;
        color: #e6c566 !important;
        border-bottom: 3px solid #e6c566 !important;
    }}

    .fc {{
        font-size: 12px !important;
        font-family: 'Quicksand', sans-serif !important;
        background-color: rgba(15, 14, 22, 0.88) !important;
        border-radius: 12px;
        padding: 6px;
    }}
    .fc-timegrid-slot {{
        height: 40px !important;
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

# HEADER Y BOTÓN FLOTANTE
col_h1, col_h2 = st.columns([7, 3])
with col_h1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px;">
            <div>
                <div class="brand-title" style="font-size: 36px; line-height:0.9;">Judit Domingo</div>
                <div class="brand-subtext">CENTRE D'ESTÈTICA</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🔒 Salir", use_container_width=True, key="btn_logout_top"):
        st.session_state["authenticated"] = False
        st.rerun()

# NAVEGACIÓN PRINCIPAL REDISEÑADA EN 5 GRANDES BLOQUES
opcion_bloque = st.tabs([
    "📅 Agenda & Citas", 
    "💶 Caja & Finanzas", 
    "👤 Gestión Centro", 
    "📣 Marketing & Regalos", 
    "📊 Analítica & Legal"
])

def generar_link_whatsapp(telefono, texto_mensaje):
    tel_clean = "".join(filter(str.isdigit, str(telefono or "")))
    if tel_clean and len(tel_clean) == 9 and not tel_clean.startswith("34"):
        tel_clean = f"34{tel_clean}"
    return f"https://api.whatsapp.com/send?phone={tel_clean}&text={urllib.parse.quote(texto_mensaje, encoding='utf-8')}"

# GENERADOR DE TARJETA REGALO CON PROPORCIÓN DE LOGO PERFECTA Y TIPOGRAFÍA CLARA
def generar_tarjeta_regalo_img(codigo, comprador, beneficiario, concepto, importe):
    ancho, alto = 1200, 680
    base_img = Image.new("RGBA", (ancho, alto), (14, 12, 18, 255))

    # Cargar logo manteniendo su proporción original en el fondo del recuadro
    if ruta_logo_file and os.path.exists(ruta_logo_file):
        try:
            logo_img = Image.open(ruta_logo_file).convert("RGBA")
            logo_img.thumbnail((ancho - 160, alto - 160), Image.Resampling.LANCZOS)
            pos_x = (ancho - logo_img.width) // 2
            pos_y = (alto - logo_img.height) // 2
            
            # Opacidad del logo al 25% para no entorpecer la lectura
            alpha = logo_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.25))
            logo_img.putalpha(alpha)
            base_img.paste(logo_img, (pos_x, pos_y), logo_img)
        except Exception:
            pass

    overlay = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # Marco dorado elegante
    draw_overlay.rectangle([25, 25, ancho-25, alto-25], outline="#e6c566", width=5)
    draw_overlay.rectangle([35, 35, ancho-35, alto-35], outline="#ba9530", width=2)
    draw_overlay.rectangle([65, 65, ancho-65, alto-65], fill=(14, 12, 20, 215), outline="#e6c566", width=2)

    final_img = Image.alpha_composite(base_img, overlay)
    draw = ImageDraw.Draw(final_img)

    # Tipografía moderna de alta legibilidad
    f_tit = ImageFont.load_default()
    f_txt = ImageFont.load_default()

    draw.text((ancho//2, 120), "Judit Domingo", fill="#e6c566", anchor="mm", font=f_tit)
    draw.text((ancho//2, 180), "CENTRE D'ESTETICA - TARJETA REGALO", fill="#d4af37", anchor="mm", font=f_txt)

    draw.text((110, 260), f"Para: {beneficiario}", fill="#ffffff", font=f_txt)
    draw.text((110, 320), f"De: {comprador}", fill="#dcd6f7", font=f_txt)
    draw.text((110, 380), f"Tratamiento: {concepto}", fill="#e6c566", font=f_txt)

    draw.rectangle([ancho-380, alto-190, ancho-100, alto-90], fill=(28, 22, 40, 240), outline="#e6c566", width=3)
    draw.text((ancho-240, alto-140), f"{importe:.2f} EUR", fill="#e6c566", anchor="mm", font=f_txt)

    draw.text((110, alto-120), f"Codigo: {codigo}", fill="#a29bfe", font=f_txt)

    buf = io.BytesIO()
    final_img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
# MODALES CITA
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

# MODAL EDITAR TARJETA REGALO
@st.dialog("✏️ Gestor de Tarjeta Regalo")
def modal_editar_tarjeta_regalo(tr_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, comprador, beneficiario, concepto, saldo_actual, fecha_caducidad FROM tarjetas_regalo WHERE id=?", (tr_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        st.error("No se encontró la tarjeta.")
        return

    cod, comp, ben, conc, saldo, cad = row
    st.markdown(f"### 🎁 Tarjeta `{cod}`")
    
    e_comp = st.text_input("Comprador", value=comp)
    e_ben = st.text_input("Beneficiario", value=ben)
    e_conc = st.text_input("Concepto", value=conc)
    e_saldo = st.number_input("Saldo Disponible (€)", value=float(saldo), step=5.0)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE tarjetas_regalo SET comprador=?, beneficiario=?, concepto=?, saldo_actual=? WHERE id=?",
                           (e_comp, e_ben, e_conc, e_saldo, tr_id))
            conn.commit()
            conn.close()
            st.success("¡Tarjeta actualizada!")
            st.rerun()
    with col2:
        if st.button("🗑️ Eliminar Tarjeta", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tarjetas_regalo WHERE id=?", (tr_id,))
            conn.commit()
            conn.close()
            st.success("Tarjeta eliminada.")
            st.rerun()

# 1. BLOQUE: AGENDA
with opcion_bloque[0]:
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
        "height": 720,
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

    state = calendar(events=events, options=cal_options, key="koibox_cal_v20")

    if state.get("eventClick"):
        raw_id = state["eventClick"]["event"]["id"]
        if raw_id.startswith("cita_"):
            c_id = int(raw_id.replace("cita_", ""))
            modal_editar_cita(c_id)

    if state.get("dateClick"):
        click_str = state["dateClick"]["date"]
        modal_crear_cita(click_str)
        # 2. BLOQUE: CAJA & FINANZAS
with opcion_bloque[1]:
    tab_f1, tab_f2 = st.tabs(["💳 Caja del Día", "🏛️ Fiscal & Gastos"])

    with tab_f1:
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

    with tab_f2:
        st.subheader("🏛️ Control Fiscal & Trimestral")
        col_f1, col_f2 = st.columns(2)
        with col_f1: anio_f = st.selectbox("Año Fiscal", [2026, 2025])
        with col_f2: trim_f = st.selectbox("Trimestre", ["1T (Ene - Mar)", "2T (Abr - Jun)", "3T (Jul - Sep)", "4T (Oct - Dic)"])

        conn = sqlite3.connect(DB_NAME)
        df_f_ing = pd.read_sql_query("SELECT total FROM facturas", conn)
        df_f_gas = pd.read_sql_query("SELECT base_imponible, total FROM gastos", conn)
        conn.close()

        total_ventas = df_f_ing['total'].sum() if not df_f_ing.empty else 0.0
        iva_repercutido = total_ventas * 0.21
        total_gastos_base = df_f_gas['base_imponible'].sum() if not df_f_gas.empty else 0.0
        total_gastos_iva = (df_f_gas['total'] - df_f_gas['base_imponible']).sum() if not df_f_gas.empty else 0.0

        iva_a_pagar = iva_repercutido - total_gastos_iva
        rendimiento_neto = total_ventas - (total_gastos_base + total_gastos_iva)

        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1: st.markdown(f"<div class='card-metric'><h4>📊 IVA a Liquidar</h4><h2 style='color:#e6c566;'>{iva_a_pagar:.2f} €</h2></div>", unsafe_allow_html=True)
        with c_m2: st.markdown(f"<div class='card-metric'><h4>📈 IRPF Estimado</h4><h2 style='color:#74b9ff;'>{max(0.0, rendimiento_neto*0.2):.2f} €</h2></div>", unsafe_allow_html=True)
        with c_m3: st.markdown(f"<div class='card-metric'><h4>💵 Neto Real</h4><h2 style='color:#55efc4;'>{rendimiento_neto:.2f} €</h2></div>", unsafe_allow_html=True)

# 3. BLOQUE: GESTIÓN DE CENTRO
with opcion_bloque[2]:
    tab_g1, tab_g2, tab_g3 = st.tabs(["👤 Clientes", "💆‍♀️ Tratamientos", "📦 Stock"])

    with tab_g1:
        st.subheader("👤 Fichero de Clientes")
        conn = sqlite3.connect(DB_NAME)
        df_cli = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as 'Nombre', telefono as 'Móvil', PRINTF('%.2f €', monedero) as 'Saldo Monedero' FROM clientes ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_cli, use_container_width=True)

    with tab_g2:
        st.subheader("💆‍♀️ Catálogo de Tratamientos")
        conn = sqlite3.connect(DB_NAME)
        df_serv = pd.read_sql_query("SELECT nombre as 'Tratamiento', duracion_min as 'Duración (min)', precio as 'Precio (€)' FROM servicios", conn)
        conn.close()
        st.dataframe(df_serv, use_container_width=True)

    with tab_g3:
        st.subheader("📦 Control de Stock")
        conn = sqlite3.connect(DB_NAME)
        df_st = pd.read_sql_query("SELECT nombre as 'Producto', categoria as 'Tipo', pvp as 'PVP (€)', unidades as 'Unidades Stock' FROM stock", conn)
        conn.close()
        st.dataframe(df_st, use_container_width=True)

# 4. BLOQUE: MARKETING & REGALOS
with opcion_bloque[3]:
    tab_m1, tab_m2, tab_m3 = st.tabs(["🎁 Tarjetas Regalo", "🎂 Cumpleaños", "💬 WhatsApp Promo"])

    with tab_m1:
        st.markdown("### 🎁 Crear Nueva Tarjeta Regalo")
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            tr_comprador = st.text_input("Comprador/a *")
            tr_beneficiario = st.text_input("Beneficiario/a *")
            tr_concepto = st.text_input("Concepto / Tratamiento *", value="Tratamiento Facial VIP / Maderoterapia")
        with col_tr2:
            tr_importe = st.number_input("Importe (€) *", value=50.0, step=5.0)
            tr_caducidad = st.date_input("Fecha Caducidad", value=datetime.date.today() + datetime.timedelta(days=90))
            tr_tel_envio = st.text_input("Móvil Beneficiaria")

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
                st.success(f"¡Tarjeta Regalo {cod_tr} Emitida!")

                img_bytes = generar_tarjeta_regalo_img(cod_tr, tr_comprador, tr_beneficiario, tr_concepto, tr_importe)
                st.image(img_bytes, caption="Vista Previa Tarjeta Regalo Pro", use_container_width=True)

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.download_button("📥 Descargar Tarjeta PNG", data=img_bytes, file_name=f"Tarjeta_{cod_tr}.png", mime="image/png", use_container_width=True)
                with col_d2:
                    if tr_tel_envio:
                        msg_tr = f"¡Hola {tr_beneficiario}! 🎁 Te han regalado una Tarjeta Regalo en *Judit Domingo Centre d'Estètica* por valor de *{tr_importe:.2f}€* (*{tr_concepto}*). ¡Llámanos para agendar tu cita!"
                        st.link_button("📲 Notificar por WhatsApp", generar_link_whatsapp(tr_tel_envio, msg_tr), use_container_width=True)

        st.markdown("---")
        st.markdown("### 📋 Tarjetas Regalo Emitidas")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, codigo, comprador, beneficiario, concepto, saldo_actual, fecha_caducidad FROM tarjetas_regalo WHERE estado='Activa' ORDER BY id DESC")
        tr_rows = cursor.fetchall()
        conn.close()

        if tr_rows:
            for tr_item in tr_rows:
                tr_id, t_cod, t_comp, t_ben, t_conc, t_saldo, t_cad = tr_item
                col_t1, col_t2, col_t3 = st.columns([5, 3, 2])
                with col_t1: st.markdown(f"🎁 **{t_cod}** — *{t_ben}* (De: {t_comp})")
                with col_t2: st.markdown(f"💰 **Saldo:** {t_saldo:.2f} €")
                with col_t3:
                    if st.button("✏️ Gestor / Borrar", key=f"btn_tr_{tr_id}"):
                        modal_editar_tarjeta_regalo(tr_id)

    with tab_m2:
        st.markdown("### 🎂 Cumpleaños del Mes")
        mes_actual = datetime.date.today().strftime("%m")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre || ' ' || COALESCE(primer_apellido,''), telefono, fecha_nacimiento FROM clientes WHERE fecha_nacimiento LIKE ?", (f"%-{mes_actual}-%",))
        cump_rows = cursor.fetchall()
        conn.close()

        for nom_c, tel_c, fnac_c in cump_rows:
            col1, col2 = st.columns([3, 1])
            with col1: st.markdown(f"🎉 **{nom_c}** ({fnac_c})")
            with col2:
                if tel_c:
                    msg_cump = f"¡Feliz Cumpleaños {nom_c}! 🥳✨ Tienes un 10% de descuento en tu próximo tratamiento en Judit Domingo Centre d'Estètica!"
                    st.link_button("📲 Felicitar", generar_link_whatsapp(tel_c, msg_cump), use_container_width=True)

    with tab_m3:
        st.markdown("### 💬 Difusión y Promociones")
        txt_p = "Hola! ✨ Novedad en Judit Domingo Centre d'Estètica. Hemos abierto agenda para el nuevo tratamiento facial/corporal. ¡Reserva tu plaza!"
        st.text_area("Texto Promocional", value=txt_p, height=100)

# 5. BLOQUE: ANALÍTICA & LEGAL
with opcion_bloque[4]:
    tab_a1, tab_a2, tab_a3 = st.tabs(["📈 Estadísticas Top", "✍️ RGPD & Firmas", "⏳ Lista Espera"])

    with tab_a1:
        st.subheader("📈 Centro de Analítica")
        conn = sqlite3.connect(DB_NAME)
        df_citas_cob = pd.read_sql_query("""SELECT c.monto_cobrado, c.metodo_pago, s.nombre as servicio
                                            FROM citas c JOIN servicios s ON c.servicio_id = s.id WHERE c.estado_cobro='Cobrado'""", conn)
        conn.close()

        if not df_citas_cob.empty:
            c1, c2 = st.columns(2)
            with c1: st.metric("💶 Facturación Acumulada", f"{df_citas_cob['monto_cobrado'].sum():.2f} €")
            with c2: st.metric("🎟️ Ticket Medio", f"{df_citas_cob['monto_cobrado'].mean():.2f} €")
            st.bar_chart(df_citas_cob["servicio"].value_counts())

    with tab_a2:
        st.subheader("✍️ Firma Digital RGPD")
        conn = sqlite3.connect(DB_NAME)
        df_cli_sel = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as nom FROM clientes", conn)
        conn.close()

        if not df_cli_sel.empty:
            c_sel = st.selectbox("Clienta *", options=df_cli_sel["id"], format_func=lambda x: df_cli_sel[df_cli_sel["id"]==x]["nom"].values[0])
            tipo_t = st.selectbox("Tratamiento", ["Maderoterapia Corporal", "Higiene Facial Profunda", "Lifting Pestañas", "Microblading"])
            nombre_f = st.text_input("Nombre Completo (Firma Digital) *")

            if st.button("✍️ Guardar Firma", use_container_width=True):
                if nombre_f:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO consentimientos (cliente_id, tipo_tratamiento, fecha_firma, acepta_rgpd, firma_texto) VALUES (?,?,?,?,?)",
                                   (c_sel, tipo_t, datetime.date.today().strftime("%Y-%m-%d"), 1, nombre_f))
                    conn.commit()
                    conn.close()
                    st.success("¡Consentimiento guardado!")

    with tab_a3:
        st.subheader("⏳ Lista de Espera")
        conn = sqlite3.connect(DB_NAME)
        df_le = pd.read_sql_query("""SELECT le.id, cl.nombre || ' ' || COALESCE(cl.primer_apellido,'') as 'Clienta', cl.telefono as 'Móvil', s.nombre as 'Tratamiento'
                                     FROM lista_espera le JOIN clientes cl ON le.cliente_id = cl.id JOIN servicios s ON le.servicio_id = s.id WHERE le.estado='Pendiente'""", conn)
        conn.close()
        st.dataframe(df_le, use_container_width=True)

# BOT FLOTANTE IA EN LA ESQUINA INFERIOR DERECHA
with st.popover("🤖 Bot Asistente", help="Consulta dudas sobre tratamientos o la app"):
    st.markdown("### 🤖 Asistente del Centro")
    st.caption("Pregunta lo que necesites sobre citas, caja o información de tratamientos.")

    if "bot_chat" not in st.session_state:
        st.session_state["bot_chat"] = [
            {"role": "assistant", "content": "¡Hola Judit y Adri! 💆‍♀️ ¿En qué puedo ayudaros hoy?"}
        ]

    for msg in st.session_state["bot_chat"]:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_prompt := st.chat_input("Escribe tu duda aquí..."):
        st.session_state["bot_chat"].append({"role": "user", "content": user_prompt})
        st.chat_message("user").write(user_prompt)

        p_low = user_prompt.lower()
        if "maderoterapia" in p_low:
            resp = "La Maderoterapia ayuda a drenar líquidos y reafirmar. Se recomiendan sesiones de 45-60 min."
        elif "caja" in p_low or "cobrar" in p_low:
            resp = "Para cobrar, ve a '💶 Caja & Finanzas' o pulsa en la cita del calendario y selecciona 'Cobrar'."
        elif "tarjeta" in p_low:
            resp = "Puedes emitir o editar tarjetas regalo en '📣 Marketing & Regalos' > '🎁 Tarjetas Regalo'."
        else:
            resp = "¡Entendido! Consulta registrada. ¿Necesitas ayuda con algo más?"

        st.session_state["bot_chat"].append({"role": "assistant", "content": resp})
        st.chat_message("assistant").write(resp)
