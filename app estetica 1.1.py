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

# Estilos CSS Avanzados
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    section[data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 100 !important; }

    html, body, [class*="css"], .stApp {
        background-color: #0d0d0d !important;
        color: #e5e5e5 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }

    h1, h2, h3, .brand-title {
        font-family: 'Playfair Display', serif !important;
        color: #d4af37 !important;
        letter-spacing: 0.5px !important;
    }

    .brand-subtext {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 10px;
        color: #a89047;
        letter-spacing: 3px;
        margin-top: -4px;
        text-transform: uppercase;
    }

    .card-metric {
        background: linear-gradient(145deg, #181818 0%, #111111 100%);
        border: 1px solid #333333;
        border-left: 4px solid #d4af37;
        border-radius: 10px;
        padding: 15px 20px;
        text-align: center;
    }

    .stButton>button {
        background: linear-gradient(135deg, #d4af37 0%, #997819 100%) !important;
        color: #000000 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 18px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 3px 8px rgba(212, 175, 55, 0.25) !important;
    }

    .stLinkButton>a {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important;
        color: #ffffff !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        border: none !important;
        text-decoration: none !important;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div, .stDateInput>div>div>input, .stTimeInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS CON MIGRACIÓN COMPLETA (CITAS, CAJAS Y FACTURAS) ---
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
                        estado_cobro TEXT DEFAULT 'Pendiente',
                        metodo_pago TEXT,
                        monto_cobrado REAL DEFAULT 0.0,
                        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
                        FOREIGN KEY(servicio_id) REFERENCES servicios(id))''')

    # MIGRADOR TABLA CITAS
    cursor.execute("PRAGMA table_info(citas)")
    cols_citas = [c[1] for c in cursor.fetchall()]
    if "estado_cobro" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN estado_cobro TEXT DEFAULT 'Pendiente'")
    if "metodo_pago" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN metodo_pago TEXT")
    if "monto_cobrado" not in cols_citas:
        cursor.execute("ALTER TABLE citas ADD COLUMN monto_cobrado REAL DEFAULT 0.0")

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

    # MIGRADOR TABLA CAJAS
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

    # MIGRADOR TABLA FACTURAS
    cursor.execute("PRAGMA table_info(facturas)")
    cols_fact = [c[1] for c in cursor.fetchall()]
    if "metodo_pago" not in cols_fact:
        cursor.execute("ALTER TABLE facturas ADD COLUMN metodo_pago TEXT")

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

    cursor.execute('''CREATE TABLE IF NOT EXISTS bloqueos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha_inicio TEXT NOT NULL,
                        fecha_fin TEXT NOT NULL,
                        motivo TEXT)''')

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

# --- HEADER SUPERIOR ELEGANTE ---
col_h1, col_h2 = st.columns([8, 2])
with col_h1:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 15px;">
            <div>
                <div class="brand-title" style="font-size: 26px; font-weight:600; line-height:1.1;">Judit Domingo</div>
                <div class="brand-subtext">CENTRE D'ESTÈTICA</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_h2:
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# --- MENÚ SUPERIOR ---
opcion = st.tabs([
    "📅 Agenda", 
    "💳 Caja & Cobros", 
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

@st.dialog("💶 Cobrar Servicio del Día")
def modal_cobrar_cita(cita_id, cliente_nom, servicio_nom, precio_defecto):
    st.markdown(f"**Cliente:** {cliente_nom}")
    st.markdown(f"**Servicio:** {servicio_nom}")
    
    col1, col2 = st.columns(2)
    with col1: monto = st.number_input("Importe (€)", value=float(precio_defecto), step=1.0)
    with col2: metodo = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Bizum", "Tarjeta Regalo"])

    if st.button("✅ Confirmar Cobro", use_container_width=True, type="primary"):
        hoy_str = datetime.date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE citas SET estado_cobro='Cobrado', metodo_pago=?, monto_cobrado=? WHERE id=?", (metodo, monto, cita_id))
        
        if metodo != "Tarjeta Regalo":
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
    st.subheader("Agenda Semanal de Citas")
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

    calendar(events=events, options={"initialView": "timeGridWeek", "firstDay": 1, "slotMinTime": "08:00:00", "slotMaxTime": "20:30:00"}, key="koibox_cal")

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

# 3. FISCAL & TRIMESTRAL
with opcion[2]:
    st.subheader("🏛️ Panel de Control Fiscal & Estimación de Trimestres")
    
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
        st.markdown("<div class='card-metric'><h4>📊 IVA a Liquidar (Mod. 303)</h4><h2 style='color:#d4af37;'>{:.2f} €</h2><p>Repercutido - Soportado</p></div>".format(iva_a_pagar), unsafe_allow_html=True)
    with c_m2:
        st.markdown("<div class='card-metric'><h4>📈 IRPF Estimado (Mod. 130)</h4><h2 style='color:#3498db;'>{:.2f} €</h2><p>20% s/ Rendimiento Neto</p></div>".format(irpf_estimado), unsafe_allow_html=True)
    with c_m3:
        st.markdown("<div class='card-metric'><h4>💵 Rendimiento Neto Real</h4><h2 style='color:#2ecc71;'>{:.2f} €</h2><p>Ingresos - Gastos Totales</p></div>".format(rendimiento_neto), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📊 Exportar Informe Oficial para la Gestoría (.CSV / Excel)", use_container_width=True):
        if not df_f_ing.empty:
            csv = df_f_ing.to_csv(index=False).encode('utf-8')
            st.download_button(label="💾 Guardar Excel para Gestoría", data=csv, file_name=f"Contabilidad_{trim_f[:2]}_{anio_f}.csv", mime='text/csv')

# 4. GASTOS & FACTURAS
with opcion[3]:
    st.subheader("📉 Registro de Facturas y Compras de Material")

    with st.expander("➕ Subir Nueva Factura / Gasto", expanded=True):
        with st.form("form_gasto"):
            col1, col2 = st.columns(2)
            with col1: prov = st.text_input("Proveedor (Ej. Iberdrola, Almacén Cosmética)")
            with col2: cat = st.selectbox("Categoría", ["Suministros (Luz/Agua/Teléfono)", "Productos Cosméticos", "Gestoría/Seguros", "Otros"])

            concept = st.text_input("Concepto Factura")
            col3, col4 = st.columns(2)
            with col3: base = st.number_input("Base Imponible (€)", value=0.0, step=5.0)
            with col4: iva = st.selectbox("IVA %", [21.0, 10.0, 4.0, 0.0])

            foto = st.file_uploader("📷 Subir Foto o PDF de la Factura", type=["jpg", "png", "pdf"])

            if st.form_submit_button("💾 Guardar Gasto"):
                if prov and base > 0:
                    ruta = None
                    if foto:
                        nom_f = f"gasto_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{foto.name.split('.')[-1]}"
                        ruta = os.path.join(GASTOS_DIR, nom_f)
                        with open(ruta, "wb") as f: f.write(foto.getbuffer())

                    tot = base * (1 + (iva / 100))
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO gastos (fecha, proveedor, concepto, categoria, base_imponible, iva_porcentaje, total, ruta_factura) VALUES (?,?,?,?,?,?,?,?)",
                                   (datetime.date.today().strftime("%Y-%m-%d"), prov, concept, cat, base, iva, tot, ruta))
                    conn.commit()
                    conn.close()
                    st.success("Gasto registrado.")
                    st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_g = pd.read_sql_query("SELECT fecha as 'Fecha', proveedor as 'Proveedor', concepto as 'Concepto', base_imponible as 'Base (€)', total as 'Total (€)' FROM gastos ORDER BY fecha DESC", conn)
    conn.close()
    st.dataframe(df_g, use_container_width=True)

# 5. STOCK TOP
with opcion[4]:
    st.subheader("📦 Control de Stock Seleccionado (Productos Top & Cabina)")

    with st.expander("➕ Añadir Producto al Inventario", expanded=False):
        with st.form("form_stock"):
            col1, col2 = st.columns(2)
            with col1: nom_prod = st.text_input("Nombre del Producto *")
            with col2: cat_prod = st.selectbox("Tipo", ["Producto Venta Clienta", "Uso Cabina / Tratamiento"])

            col3, col4, col5 = st.columns(3)
            with col3: coste = st.number_input("Precio Coste (€)", value=0.0)
            with col4: pvp = st.number_input("PVP Venta (€)", value=0.0)
            with col5: unidades = st.number_input("Unidades en Stock", value=5, step=1)

            if st.form_submit_button("💾 Guardar Producto"):
                if nom_prod:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO stock (nombre, categoria, precio_coste, pvp, unidades) VALUES (?,?,?,?,?)",
                                   (nom_prod, cat_prod, coste, pvp, unidades))
                    conn.commit()
                    conn.close()
                    st.success("Producto añadido.")
                    st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_st = pd.read_sql_query("SELECT id, nombre as 'Producto', categoria as 'Tipo', pvp as 'PVP (€)', unidades as 'Unidades Stock' FROM stock", conn)
    conn.close()
    st.dataframe(df_st, use_container_width=True)

# 6. MARKETING & REGALOS
with opcion[5]:
    st.subheader("📣 Gestor de Tarjetas Regalo y Promociones")
    
    with st.expander("🎁 Emitir Nueva Tarjeta Regalo", expanded=True):
        with st.form("form_tr"):
            cod_tr = f"REGALO-{random.randint(1000, 9999)}"
            st.text_input("Código de la Tarjeta", value=cod_tr, disabled=True)
            
            c1, c2 = st.columns(2)
            with c1: comprador = st.text_input("Comprador (Quien regala)")
            with c2: beneficiario = st.text_input("Beneficiaria (Quien la disfruta)")

            c3, c4 = st.columns(2)
            with c3: concepto_tr = st.text_input("Tratamiento / Concepto", value="Tratamiento Facial / Saldo Libre")
            with c4: valor_tr = st.number_input("Importe (€)", value=50.0, step=5.0)

            if st.form_submit_button("🎁 Generar Tarjeta Regalo"):
                if comprador and beneficiario:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO tarjetas_regalo (codigo, comprador, beneficiario, concepto, saldo_inicial, saldo_actual, fecha_emision, estado) VALUES (?,?,?,?,?,?,?,'Activa')",
                                   (cod_tr, comprador, beneficiario, concepto_tr, valor_tr, valor_tr, datetime.date.today().strftime("%Y-%m-%d")))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Tarjeta Regalo {cod_tr} emitida!")
                    st.rerun()

    conn = sqlite3.connect(DB_NAME)
    df_tr_list = pd.read_sql_query("SELECT codigo as 'Código', comprador as 'Comprador', beneficiario as 'Beneficiaria', concepto as 'Concepto', saldo_actual as 'Saldo Disponible (€)' FROM tarjetas_regalo WHERE estado='Activa'", conn)
    conn.close()
    st.dataframe(df_tr_list, use_container_width=True)

# 7. CLIENTES
with opcion[6]:
    st.subheader("Fichero de Clientes")
    conn = sqlite3.connect(DB_NAME)
    df_cli = pd.read_sql_query("SELECT id, nombre || ' ' || COALESCE(primer_apellido,'') as 'Nombre', telefono as 'Móvil', email as 'Email' FROM clientes ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_cli, use_container_width=True)

# 8. SERVICIOS
with opcion[7]:
    st.subheader("Catálogo de Tratamientos")
    conn = sqlite3.connect(DB_NAME)
    df_serv = pd.read_sql_query("SELECT nombre as 'Tratamiento', duracion_min as 'Duración (min)', precio as 'Precio (€)' FROM servicios", conn)
    conn.close()
    st.dataframe(df_serv, use_container_width=True)
