# ===================================================
# IMPORTACIÓN DE LIBRERÍAS
# ===================================================

import base64
import json
import re
from datetime import datetime
from urllib.parse import urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup


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
# - mantener inputs visibles y claros
# - botón Añadir centrado y con mejor color
# - listado tipo tabla
# - nombre y URL algo más grandes
# - botón eliminar discreto

st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #f6f8fb;
    }

    /* Contenedor principal */
    .main .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* Título principal */
    .app-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }

    /* Subtítulo */
    .app-subtitle {
        color: #64748b;
        margin-bottom: 2rem;
        font-size: 1rem;
    }

    /* Títulos de sección */
    .section-title {
        font-size: 1.7rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* Caja contador */
    .counter-box {
        background: #eef4ff;
        color: #1d4ed8;
        border-radius: 12px;
        padding: 0.7rem 1rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 1rem;
    }

    /* Cabecera de la tabla */
    .table-header {
        font-weight: 800;
        color: #475569;
        font-size: 0.92rem;
        padding-left: 0.2rem;
    }

    /* Celda tipo tarjeta */
    .table-row {
        background: white;
        border-radius: 14px;
        padding: 0.9rem;
        margin-bottom: 0.55rem;
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.05);
        min-height: 72px;
        display: flex;
        align-items: center;
    }

    /* Nombre más grande */
    .name-cell {
        font-size: 1.05rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.4;
    }

    /* Fecha */
    .date-cell {
        font-size: 0.95rem;
        color: #475569;
    }

    /* Precio */
    .price-cell {
        font-size: 1.2rem;
        font-weight: 900;
        color: #059669;
        white-space: nowrap;
    }

    /* Precio no disponible */
    .price-unavailable {
        font-size: 0.95rem;
        font-weight: 700;
        color: #b45309;
        white-space: nowrap;
    }

    /* URL más grande */
    .url-cell {
        font-size: 0.98rem;
        color: #475569;
        line-height: 1.5;
        word-break: break-word;
    }

    /* Inputs visibles y redondeados */
    div[data-baseweb="input"] > div {
        border-radius: 10px !important;
    }

    /* Botón Añadir */
    .stForm button[kind="primary"] {
        background: #2563eb !important;
        border: 1px solid #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        min-height: 2.6rem !important;
    }

    .stForm button[kind="primary"]:hover {
        background: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }

    /* Botón Eliminar */
    .stButton button[kind="secondary"] {
        background: #fff5f5 !important;
        border: 1px solid #fecaca !important;
        color: #dc2626 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        min-height: 2.55rem !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: #fee2e2 !important;
        border-color: #fca5a5 !important;
        color: #b91c1c !important;
    }

    /* Ocultar líneas horizontales si aparecieran */
    hr {
        display: none !important;
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
    '<div class="app-subtitle">Controla tus productos fácilmente</div>',
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

# Rama principal del repositorio
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
# FUNCIONES AUXILIARES
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


def format_date(date_value):
    """
    Convierte una fecha ISO a formato dd/mm/YYYY.
    Si no existe, devuelve un guion.
    """
    if not date_value:
        return "—"

    try:
        return datetime.fromisoformat(date_value).strftime("%d/%m/%Y")
    except Exception:
        return "—"


# ===================================================
# CARGAR Y GUARDAR PRODUCTOS EN GITHUB
# ===================================================

def load_products():
    """
    Lee products.json desde GitHub.

    Devuelve:
    - la lista de productos
    - el SHA actual del archivo

    Si algún producto antiguo no tiene added_at,
    se le añade el campo con valor None.
    """
    response = requests.get(API, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    # El contenido llega en base64
    content = base64.b64decode(data["content"]).decode("utf-8")
    products = json.loads(content)

    # Compatibilidad con productos antiguos
    for product in products:
        if "added_at" not in product:
            product["added_at"] = None

    return products, data["sha"]


def save_products(products, sha):
    """
    Guarda la lista de productos actualizada en GitHub.
    """
    json_text = json.dumps(products, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(json_text.encode("utf-8")).decode("utf-8")

    payload = {
        "message": "update products",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    response = requests.put(API, headers=headers, json=payload, timeout=30)
    response.raise_for_status()


# ===================================================
# EXTRACCIÓN DE PRECIO
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

            # Caso: offers es un diccionario
            if isinstance(offers, dict):
                price = offers.get("price")
                if price is not None:
                    try:
                        return float(str(price).replace(",", "."))
                    except Exception:
                        pass

            # Caso: offers es una lista
            elif isinstance(offers, list):
                for offer in offers:
                    if isinstance(offer, dict) and offer.get("price") is not None:
                        try:
                            return float(str(offer["price"]).replace(",", "."))
                        except Exception:
                            pass

    return None


def extract_price_from_text(soup):
    """
    Si falla JSON-LD, intenta buscar el precio en el texto visible.
    """
    text = soup.get_text(" ", strip=True)

    matches = re.findall(r"(\d+[.,]\d{2})\s*€", text)

    if not matches:
        return None

    try:
        return float(matches[0].replace(",", "."))
    except Exception:
        return None


def get_price(url):
    """
    Descarga la página del producto e intenta extraer su precio actual.
    """
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

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

@st.dialog("Confirmar")
def confirm_delete(index, name, products, sha):
    """
    Muestra una ventana modal para confirmar el borrado.
    """
    st.write(f"¿Eliminar {name}?")

    col_yes, col_no = st.columns(2)

    with col_yes:
        if st.button("Sí", key=f"yes_{index}", use_container_width=True):
            new_products = products[:index] + products[index + 1:]
            save_products(new_products, sha)
            st.rerun()

    with col_no:
        if st.button("Cancelar", key=f"no_{index}", use_container_width=True):
            st.rerun()


# ===================================================
# CARGA INICIAL
# ===================================================

products, sha = load_products()


# ===================================================
# SECCIÓN: AÑADIR PRODUCTO
# ===================================================

st.markdown(
    '<div class="section-title">Añadir producto</div>',
    unsafe_allow_html=True
)

# Recuadro visual para el formulario
with st.container(border=True):
    st.markdown(
        f'<div class="counter-box">{len(products)} / 10 productos</div>',
        unsafe_allow_html=True
    )

    # Si se alcanza el límite, desactivamos el formulario
    limit_reached = len(products) >= 10

    with st.form("form", clear_on_submit=True):
        col_name, col_url = st.columns(2)

        with col_name:
            name = st.text_input(
                "Nombre",
                disabled=limit_reached
            )

        with col_url:
            url = st.text_input(
                "URL",
                disabled=limit_reached
            )

        # Botón centrado
        col_left, col_center, col_right = st.columns([2, 1, 2])

        with col_center:
            submit = st.form_submit_button(
                "Añadir",
                type="primary",
                use_container_width=True,
                disabled=limit_reached
            )

        if submit:
            # Límite máximo
            if len(products) >= 10:
                st.error("Has alcanzado el límite de 10 productos.")

            # Campos vacíos
            elif not name.strip() or not url.strip():
                st.error("Campos vacíos.")

            # URL inválida
            elif not valid_url(url):
                st.error("URL inválida.")

            # Duplicado
            elif any(p["url"] == url for p in products):
                st.warning("Este producto ya está añadido.")

            else:
                products.append({
                    "name": name.strip(),
                    "url": url.strip(),
                    "added_at": datetime.now().isoformat()
                })

                save_products(products, sha)
                st.rerun()


# ===================================================
# SECCIÓN: PRODUCTOS MONITORIZADOS
# ===================================================

st.markdown(
    '<div class="section-title">Productos monitorizados</div>',
    unsafe_allow_html=True
)

if len(products) == 0:
    st.info("No hay productos añadidos.")
else:
    # ---------------------------------------------------
    # CABECERA DE LA TABLA
    # ---------------------------------------------------
    header_cols = st.columns([2, 1.5, 1, 3, 1])

    with header_cols[0]:
        st.markdown('<div class="table-header">Nombre</div>', unsafe_allow_html=True)

    with header_cols[1]:
        st.markdown('<div class="table-header">Fecha</div>', unsafe_allow_html=True)

    with header_cols[2]:
        st.markdown('<div class="table-header">Precio</div>', unsafe_allow_html=True)

    with header_cols[3]:
        st.markdown('<div class="table-header">URL</div>', unsafe_allow_html=True)

    with header_cols[4]:
        st.markdown('<div class="table-header">Acción</div>', unsafe_allow_html=True)

    # ---------------------------------------------------
    # FILAS DE LA TABLA
    # ---------------------------------------------------
    for i, product in enumerate(products):
        price = get_price(product["url"])

        row_cols = st.columns([2, 1.5, 1, 3, 1], vertical_alignment="center")

        # Nombre
        with row_cols[0]:
            st.markdown(
                f'<div class="table-row name-cell">{product["name"]}</div>',
                unsafe_allow_html=True
            )

        # Fecha
        with row_cols[1]:
            st.markdown(
                f'<div class="table-row date-cell">{format_date(product.get("added_at"))}</div>',
                unsafe_allow_html=True
            )

        # Precio
        with row_cols[2]:
            if price is not None:
                st.markdown(
                    f'<div class="table-row price-cell">{price:.2f} €</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="table-row price-unavailable">—</div>',
                    unsafe_allow_html=True
                )

        # URL
        with row_cols[3]:
            st.markdown(
                f'<div class="table-row url-cell">{product["url"]}</div>',
                unsafe_allow_html=True
            )

        # Acción
        with row_cols[4]:
            if st.button("Eliminar", key=i, type="secondary", use_container_width=True):
                confirm_delete(i, product["name"], products, sha)
