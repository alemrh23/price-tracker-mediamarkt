# ===================================================
# IMPORTACIÓN DE LIBRERÍAS
# ===================================================

import streamlit as st
import json
import requests
import base64
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime


# ===================================================
# CONFIGURACIÓN DE LA PÁGINA
# ===================================================

st.set_page_config(
    page_title="Rastreador de precios",
    page_icon="💸",
    layout="wide"
)


# ===================================================
# ESTILOS CSS
# ===================================================
# Objetivos:
# - título alineado a la izquierda
# - bloque "Añadir producto" en una tarjeta clara
# - botón "Añadir" más pequeño y elegante
# - productos en tarjetas bien separadas
# - columna derecha con el precio destacado
# - botón eliminar más agradable visualmente

st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #f6f8fb;
    }

    /* Contenedor principal */
    .main .block-container {
        max-width: 1140px;
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }

    /* Título principal */
    .app-title {
        font-size: 2.45rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.1;
        margin-bottom: 0.2rem;
        text-align: left;
    }

    /* Subtítulo */
    .app-subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
        text-align: left;
    }

    /* Títulos de sección */
    .section-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 1.15rem;
        margin-bottom: 1rem;
    }

    /* Tarjeta del formulario */
    .form-card {
        background: #ffffff;
        border: 1px solid #e7edf5;
        border-radius: 22px;
        padding: 1.25rem 1.25rem 1rem 1.25rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 2rem;
    }

    /* Caja del contador */
    .counter-box {
        background: #eef4ff;
        color: #1d4ed8;
        border-radius: 14px;
        padding: 0.75rem 1rem;
        font-weight: 700;
        margin-bottom: 1rem;
        display: inline-block;
    }

    /* Tarjeta de producto */
    .product-card {
        background: #ffffff;
        border: 1px solid #e8edf5;
        border-radius: 22px;
        padding: 1.2rem 1.25rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 1.1rem;
    }

    /* Etiqueta superior */
    .product-chip {
        display: inline-block;
        background: #eef4ff;
        color: #1d4ed8;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 0.28rem 0.7rem;
        border-radius: 999px;
        margin-bottom: 0.8rem;
    }

    /* Nombre del producto */
    .product-name {
        font-size: 1.2rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.35;
        margin-bottom: 0.55rem;
    }

    /* Texto secundario */
    .product-meta {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 0.35rem;
        line-height: 1.45;
    }

    /* URL */
    .product-url {
        font-size: 0.9rem;
        color: #64748b;
        line-height: 1.45;
        word-break: break-word;
        margin-top: 0.35rem;
    }

    /* Bloque del precio */
    .price-box {
        background: linear-gradient(180deg, #f8fffc 0%, #eefcf6 100%);
        border: 1px solid #d9f5e7;
        border-radius: 18px;
        padding: 1rem;
        text-align: center;
        min-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Etiqueta del bloque precio */
    .price-label {
        font-size: 0.82rem;
        font-weight: 700;
        color: #64748b;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Precio disponible */
    .product-price {
        font-size: 2.15rem;
        font-weight: 900;
        color: #059669;
        line-height: 1.05;
    }

    /* Precio no disponible */
    .product-price-unavailable {
        font-size: 1rem;
        font-weight: 700;
        color: #b45309;
        line-height: 1.3;
    }

    /* Inputs */
    div[data-baseweb="input"] > div {
        border-radius: 14px !important;
    }

    /* Form sin borde extraño */
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* Ocultar líneas horizontales si apareciesen */
    hr {
        display: none !important;
    }

    /* Botón primario */
    .stForm button[kind="primary"] {
        background: #1f2937 !important;
        border: 1px solid #1f2937 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        min-height: 2.6rem !important;
        padding: 0 1.1rem !important;
    }

    .stForm button[kind="primary"]:hover {
        background: #111827 !important;
        border-color: #111827 !important;
        color: white !important;
    }

    /* Botón eliminar */
    .stButton button[kind="secondary"] {
        border-radius: 12px !important;
        border: 1px solid #fecaca !important;
        background: #fff5f5 !important;
        color: #dc2626 !important;
        font-weight: 800 !important;
        min-height: 2.7rem !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: #fee2e2 !important;
        border-color: #fca5a5 !important;
        color: #b91c1c !important;
    }
</style>
""", unsafe_allow_html=True)


# ===================================================
# CABECERA
# ===================================================

st.markdown(
    '<div class="app-title">💸 Rastreador de precios</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="app-subtitle">Controla tus productos y consulta su precio actual de forma clara y visual.</div>',
    unsafe_allow_html=True
)


# ===================================================
# CONFIGURACIÓN DE GITHUB
# ===================================================

# Token guardado en Secrets de Streamlit
TOKEN = st.secrets["GITHUB_TOKEN"]

# Repositorio en formato usuario/repositorio
REPO = st.secrets["REPO"]

# Archivo donde se guardan los productos
FILE = "products.json"

# Rama principal
BRANCH = "main"

# Endpoint de la API de GitHub
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras para autenticación con GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para pedir páginas simulando navegador
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===================================================
# VALIDAR URL
# ===================================================

def valid_url(url):
    """
    Comprueba si una URL tiene formato válido.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# ===================================================
# FORMATEAR FECHA DE ALTA
# ===================================================

def format_added_at(added_at):
    """
    Convierte una fecha ISO a formato legible.
    Si no existe, devuelve un texto amigable.
    """
    if not added_at:
        return "Fecha no disponible"

    try:
        dt = datetime.fromisoformat(added_at)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Fecha no disponible"


# ===================================================
# CARGAR PRODUCTOS DESDE GITHUB
# ===================================================

def load_products():
    """
    Lee products.json desde GitHub.

    Devuelve:
    - lista de productos
    - SHA actual del archivo

    Además, si hay productos antiguos sin campo 'added_at',
    les añade ese campo con valor None para evitar errores.
    """
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # GitHub devuelve el contenido en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    products = json.loads(content)

    # Compatibilidad con productos antiguos
    for product in products:
        if "added_at" not in product:
            product["added_at"] = None

    return products, data["sha"]


# ===================================================
# GUARDAR PRODUCTOS EN GITHUB
# ===================================================

def save_products(products, sha):
    """
    Guarda la lista actualizada de productos en GitHub.
    """
    json_text = json.dumps(products, ensure_ascii=False, indent=2)

    encoded = base64.b64encode(json_text.encode("utf-8")).decode("utf-8")

    payload = {
        "message": "Update products.json from Streamlit app",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    r = requests.put(API, headers=headers, json=payload, timeout=30)
    r.raise_for_status()


# ===================================================
# EXTRAER PRECIO DESDE JSON-LD
# ===================================================

def extract_price_from_jsonld(soup):
    """
    Intenta obtener el precio desde scripts JSON-LD.
    """
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]

        for obj in items:
            if not isinstance(obj, dict):
                continue

            offers = obj.get("offers")

            # Caso: offers es diccionario
            if isinstance(offers, dict):
                price = offers.get("price")
                if price is not None:
                    try:
                        return float(str(price).replace(",", "."))
                    except Exception:
                        pass

            # Caso: offers es lista
            elif isinstance(offers, list):
                for offer in offers:
                    if isinstance(offer, dict) and offer.get("price") is not None:
                        try:
                            return float(str(offer["price"]).replace(",", "."))
                        except Exception:
                            pass

    return None


# ===================================================
# EXTRAER PRECIO DESDE TEXTO VISIBLE
# ===================================================

def extract_price_from_text(soup):
    """
    Si falla JSON-LD, intenta encontrar el precio en el texto visible.
    """
    text = soup.get_text(" ", strip=True)

    matches = re.findall(r"(\d+[.,]\d{2})\s*€", text)

    if not matches:
        return None

    try:
        return float(matches[0].replace(",", "."))
    except Exception:
        return None


# ===================================================
# OBTENER PRECIO ACTUAL
# ===================================================

def get_current_price(url):
    """
    Descarga la página del producto e intenta extraer el precio actual.
    """
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Primer intento: JSON-LD
        price = extract_price_from_jsonld(soup)
        if price is not None:
            return price

        # Segundo intento: texto visible
        price = extract_price_from_text(soup)
        if price is not None:
            return price

        return None

    except Exception:
        return None


# ===================================================
# DIÁLOGO DE CONFIRMACIÓN DE BORRADO
# ===================================================

@st.dialog("Confirmar eliminación")
def confirm_delete_dialog(product_index, product_name, products, sha):
    """
    Muestra una ventana modal para confirmar el borrado.
    """
    st.write(f"¿Seguro que quieres eliminar **{product_name}**?")

    col_yes, col_no = st.columns(2)

    if col_yes.button(
        "Sí, eliminar",
        key=f"confirm_yes_{product_index}",
        use_container_width=True
    ):
        new_products = products[:product_index] + products[product_index + 1:]
        save_products(new_products, sha)
        st.success("Producto eliminado")
        st.rerun()

    if col_no.button(
        "Cancelar",
        key=f"confirm_no_{product_index}",
        use_container_width=True
    ):
        st.rerun()


# ===================================================
# CARGA INICIAL DE PRODUCTOS
# ===================================================

products, sha = load_products()


# ===================================================
# SECCIÓN: AÑADIR PRODUCTO
# ===================================================

st.markdown(
    '<div class="section-title">Añadir producto</div>',
    unsafe_allow_html=True
)

# Apertura visual de la tarjeta del formulario
st.markdown('<div class="form-card">', unsafe_allow_html=True)

# Contador de productos
st.markdown(
    f'<div class="counter-box">{len(products)} / 10 productos</div>',
    unsafe_allow_html=True
)

# Límite máximo de productos
limit_reached = len(products) >= 10

with st.form("add_product_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input(
            "Nombre",
            placeholder="Ej: Juego FC 26 PS5",
            disabled=limit_reached
        )

    with col2:
        url = st.text_input(
            "URL",
            placeholder="https://...",
            disabled=limit_reached
        )

    # El botón va en una columna pequeña para no ocupar demasiado ancho
    btn_col_1, btn_col_2, btn_col_3 = st.columns([1, 1, 5])

    with btn_col_1:
        submitted = st.form_submit_button(
            "Añadir",
            type="primary",
            use_container_width=True,
            disabled=limit_reached
        )

    if submitted:
        # Validación del límite
        if len(products) >= 10:
            st.error("Has alcanzado el límite de 10 productos.")

        # Validación de campos vacíos
        elif not name.strip() or not url.strip():
            st.error("Debes introducir nombre y URL.")

        # Validación del formato de URL
        elif not valid_url(url):
            st.error("URL no válida.")

        # Evitar duplicados
        elif any(p["url"] == url for p in products):
            st.warning("Este producto ya está monitorizado.")

        else:
            # Añadimos el nuevo producto con fecha de alta
            products.append({
                "name": name.strip(),
                "url": url.strip(),
                "added_at": datetime.now().isoformat(timespec="seconds")
            })

            save_products(products, sha)
            st.success("Producto añadido")
            st.rerun()

if limit_reached:
    st.warning("Has alcanzado el máximo de 10 productos. Elimina uno para añadir otro.")

# Cierre visual de la tarjeta del formulario
st.markdown('</div>', unsafe_allow_html=True)


# ===================================================
# SECCIÓN: PRODUCTOS MONITORIZADOS
# ===================================================

st.markdown(
    '<div class="section-title">Productos monitorizados</div>',
    unsafe_allow_html=True
)

if len(products) == 0:
    st.info("No hay productos aún.")

# Recorremos todos los productos
for i, p in enumerate(products):
    # Intentamos obtener el precio actual
    price = get_current_price(p["url"])

    # Columnas externas:
    # - izquierda: tarjeta principal
    # - derecha: botón eliminar
    outer_left, outer_right = st.columns([10, 2], vertical_alignment="center")

    with outer_left:
        # Dentro de la tarjeta usamos dos columnas:
        # - izquierda: nombre, fecha y URL
        # - derecha: bloque de precio
        card_left, card_right = st.columns([7, 3], vertical_alignment="center")

        with card_left:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown('<div class="product-chip">Producto monitorizado</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="product-name">{p["name"]}</div>', unsafe_allow_html=True)

            # Fecha de alta del producto
            st.markdown(
                f'<div class="product-meta"><strong>Añadido:</strong> {format_added_at(p.get("added_at"))}</div>',
                unsafe_allow_html=True
            )

            # URL del producto
            st.markdown(
                f'<div class="product-url">{p["url"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with card_right:
            if price is not None:
                price_html = f"""
                <div class="price-box">
                    <div class="price-label">Precio actual</div>
                    <div class="product-price">{price:.2f} €</div>
                </div>
                """
            else:
                price_html = """
                <div class="price-box">
                    <div class="price-label">Precio actual</div>
                    <div class="product-price-unavailable">No disponible</div>
                </div>
                """

            st.markdown(price_html, unsafe_allow_html=True)

    with outer_right:
        if st.button(
            "🗑 Eliminar",
            key=f"del_{i}",
            type="secondary",
            use_container_width=True
        ):
            confirm_delete_dialog(i, p["name"], products, sha)
