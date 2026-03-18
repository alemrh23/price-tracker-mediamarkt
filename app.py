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
# Objetivos visuales:
# - bloque "Añadir producto" dentro de un recuadro
# - listado de productos con formato tipo tabla
# - filas limpias y bien separadas
# - botón eliminar discreto
# - precio con color destacado
# - sin barras extrañas

st.markdown("""
<style>
    .stApp {
        background-color: #f6f8fb;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .app-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.7rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* Caja visual del contador */
    .counter-box {
        background: #eef4ff;
        color: #1d4ed8;
        border-radius: 12px;
        padding: 0.7rem 0.95rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 1rem;
    }

    /* Tabla: cabecera */
    .table-header {
        background: #eaf0f7;
        color: #334155;
        font-weight: 800;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
        font-size: 0.92rem;
    }

    /* Tabla: fila */
    .table-row {
        background: white;
        border: 1px solid #e7edf5;
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }

    .name-cell {
        font-weight: 800;
        color: #111827;
        line-height: 1.35;
    }

    .date-cell {
        color: #475569;
        font-size: 0.95rem;
    }

    .price-cell {
        font-size: 1.3rem;
        font-weight: 900;
        color: #059669;
        white-space: nowrap;
    }

    .price-unavailable {
        font-size: 0.95rem;
        font-weight: 700;
        color: #b45309;
        white-space: nowrap;
    }

    .url-cell {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.4;
        word-break: break-word;
    }

    /* Inputs */
    div[data-baseweb="input"] > div {
        border-radius: 12px !important;
    }

    /* Form sin borde extraño */
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    hr {
        display: none !important;
    }

    /* Botón Añadir */
    .stForm button[kind="primary"] {
        background: #1f2937 !important;
        border: 1px solid #1f2937 !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        min-height: 2.55rem !important;
        padding: 0 1.1rem !important;
    }

    .stForm button[kind="primary"]:hover {
        background: #111827 !important;
        border-color: #111827 !important;
        color: white !important;
    }

    /* Botón Eliminar */
    .stButton button[kind="secondary"] {
        border-radius: 12px !important;
        border: 1px solid #fecaca !important;
        background: #fff5f5 !important;
        color: #dc2626 !important;
        font-weight: 800 !important;
        min-height: 2.55rem !important;
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

# Rama principal del repositorio
BRANCH = "main"

# Endpoint de la API de GitHub para leer/escribir products.json
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras de autenticación
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para descargar páginas simulando navegador
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


def format_added_at(added_at):
    """
    Convierte una fecha ISO a formato legible.
    """
    if not added_at:
        return "Fecha no disponible"

    try:
        dt = datetime.fromisoformat(added_at)
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Fecha no disponible"


# ===================================================
# CARGA Y GUARDADO EN GITHUB
# ===================================================

def load_products():
    """
    Lee products.json desde GitHub.

    Devuelve:
    - lista de productos
    - SHA actual del archivo
    """
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # GitHub entrega el contenido codificado en base64
    content = base64.b64decode(data["content"]).decode("utf-8")
    products = json.loads(content)

    # Compatibilidad con productos antiguos
    for product in products:
        if "added_at" not in product:
            product["added_at"] = None

    return products, data["sha"]


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
# EXTRACCIÓN DE PRECIOS
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

            # Caso 1: offers es un diccionario
            if isinstance(offers, dict):
                price = offers.get("price")
                if price is not None:
                    try:
                        return float(str(price).replace(",", "."))
                    except Exception:
                        pass

            # Caso 2: offers es una lista
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

    # Busca valores tipo 79,99 € o 79.99 €
    matches = re.findall(r"(\d+[.,]\d{2})\s*€", text)

    if not matches:
        return None

    try:
        return float(matches[0].replace(",", "."))
    except Exception:
        return None


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
    Muestra una ventana modal para confirmar si se quiere borrar un producto.
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

# Recuadro visual usando container con borde
with st.container(border=True):
    st.markdown(
        f'<div class="counter-box">{len(products)} / 10 productos</div>',
        unsafe_allow_html=True
    )

    # Si se alcanza el límite, se desactiva el formulario
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

        # Botón más pequeño
        btn_col_1, btn_col_2, btn_col_3 = st.columns([1.1, 1, 5])

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


# ===================================================
# SECCIÓN: PRODUCTOS MONITORIZADOS
# ===================================================

st.markdown(
    '<div class="section-title">Productos monitorizados</div>',
    unsafe_allow_html=True
)

if len(products) == 0:
    st.info("No hay productos aún.")
else:
    # ---------------------------------------------------
    # CABECERA DE LA "TABLA"
    # ---------------------------------------------------
    header_cols = st.columns([2.2, 1.5, 1.1, 4.2, 1.2])

    with header_cols[0]:
        st.markdown('<div class="table-header">Nombre</div>', unsafe_allow_html=True)

    with header_cols[1]:
        st.markdown('<div class="table-header">Fecha alta</div>', unsafe_allow_html=True)

    with header_cols[2]:
        st.markdown('<div class="table-header">Precio</div>', unsafe_allow_html=True)

    with header_cols[3]:
        st.markdown('<div class="table-header">URL</div>', unsafe_allow_html=True)

    with header_cols[4]:
        st.markdown('<div class="table-header">Acción</div>', unsafe_allow_html=True)

    # ---------------------------------------------------
    # FILAS DE PRODUCTOS
    # ---------------------------------------------------
    for i, p in enumerate(products):
        price = get_current_price(p["url"])

        row_cols = st.columns([2.2, 1.5, 1.1, 4.2, 1.2], vertical_alignment="center")

        # Nombre
        with row_cols[0]:
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="name-cell">{p["name"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Fecha de alta
        with row_cols[1]:
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="date-cell">{format_added_at(p.get("added_at"))}</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Precio
        with row_cols[2]:
            st.markdown('<div class="table-row">', unsafe_allow_html=True)

            if price is not None:
                st.markdown(
                    f'<div class="price-cell">{price:.2f} €</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="price-unavailable">No disponible</div>',
                    unsafe_allow_html=True
                )

            st.markdown('</div>', unsafe_allow_html=True)

        # URL
        with row_cols[3]:
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="url-cell">{p["url"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Acción
        with row_cols[4]:
            if st.button(
                "🗑 Eliminar",
                key=f"del_{i}",
                type="secondary",
                use_container_width=True
            ):
                confirm_delete_dialog(i, p["name"], products, sha)
