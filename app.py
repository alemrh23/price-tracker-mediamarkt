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
# - Quitar barras/separaciones grises
# - Dar más protagonismo a cada producto
# - Hacer tarjetas limpias, modernas y con sombra
# - Destacar mucho más el precio

st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #f6f8fb;
    }

    /* Reduce espacio superior */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Título principal */
    .app-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #0f172a;
        margin-bottom: 0.15rem;
        line-height: 1.1;
    }

    /* Subtítulo */
    .app-subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }

    /* Títulos de sección */
    .section-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #111827;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    /* Caja del formulario */
    .form-shell {
        background: #ffffff;
        border: none;
        border-radius: 24px;
        padding: 1.25rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        margin-bottom: 2rem;
    }

    /* Tarjeta de producto */
    .product-card {
        background: #ffffff;
        border: none;
        border-radius: 24px;
        padding: 1.25rem 1.35rem;
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
        margin-bottom: 1rem;
    }

    /* Cabecera superior de la tarjeta */
    .product-top-row {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Etiqueta */
    .product-chip {
        display: inline-block;
        background: #eef4ff;
        color: #1d4ed8;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 0.3rem 0.65rem;
        border-radius: 999px;
        letter-spacing: 0.01em;
        margin-bottom: 0.75rem;
    }

    /* Nombre del producto */
    .product-name {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.3;
        margin: 0;
    }

    /* Precio destacado */
    .product-price {
        font-size: 2.2rem;
        font-weight: 900;
        color: #059669;
        line-height: 1.05;
        margin: 0.25rem 0 0.5rem 0;
    }

    /* Texto cuando no hay precio */
    .product-no-price {
        font-size: 1rem;
        font-weight: 700;
        color: #b45309;
        margin: 0.35rem 0 0.6rem 0;
    }

    /* URL más discreta */
    .product-url {
        font-size: 0.9rem;
        color: #64748b;
        line-height: 1.45;
        word-break: break-word;
    }

    /* Info auxiliar */
    .small-muted {
        font-size: 0.9rem;
        color: #64748b;
    }

    /* Quitar posibles bordes raros en elementos internos */
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    div[data-testid="stForm"] > div {
        border: none !important;
    }

    /* Botones más redondeados */
    .stButton > button {
        border-radius: 14px;
        font-weight: 700;
    }

    /* Botón de eliminar más elegante */
    .delete-button-wrap {
        margin-top: 0.1rem;
    }

    /* Inputs */
    div[data-baseweb="input"] > div {
        border-radius: 14px !important;
    }

    /* Quita líneas horizontales que a veces aparecen */
    hr {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)


# ===================================================
# CABECERA
# ===================================================

st.markdown('<div class="app-title">💸 Rastreador de precios</div>', unsafe_allow_html=True)
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

# Endpoint de GitHub API para leer/escribir products.json
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras para autenticación con GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para pedir páginas web simulando navegador
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
# CARGAR PRODUCTOS DESDE GITHUB
# ===================================================

def load_products():
    """
    Lee products.json desde GitHub.
    Devuelve:
    - la lista de productos
    - el SHA actual del archivo
    """
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # GitHub devuelve el contenido en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    products = json.loads(content)

    return products, data["sha"]


# ===================================================
# GUARDAR PRODUCTOS EN GITHUB
# ===================================================

def save_products(products, sha):
    """
    Guarda la lista actualizada en GitHub.
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

            # Caso 1: offers es dict
            if isinstance(offers, dict):
                price = offers.get("price")
                if price is not None:
                    try:
                        return float(str(price).replace(",", "."))
                    except Exception:
                        pass

            # Caso 2: offers es lista
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
    Si falla JSON-LD, busca precios tipo 79,99 € o 79.99 € en el texto.
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

    if col_yes.button("Sí, eliminar", key=f"confirm_yes_{product_index}", use_container_width=True):
        new_products = products[:product_index] + products[product_index + 1:]
        save_products(new_products, sha)
        st.success("Producto eliminado")
        st.rerun()

    if col_no.button("Cancelar", key=f"confirm_no_{product_index}", use_container_width=True):
        st.rerun()


# ===================================================
# CARGA INICIAL DE PRODUCTOS
# ===================================================

products, sha = load_products()


# ===================================================
# SECCIÓN AÑADIR PRODUCTO
# ===================================================

st.markdown('<div class="section-title">Añadir producto</div>', unsafe_allow_html=True)

# Caja visual del formulario
st.markdown('<div class="form-shell">', unsafe_allow_html=True)

# Indicador de límite
st.info(f"{len(products)} / 10 productos")

# Si ya hay 10 productos, desactivamos el formulario
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

    submitted = st.form_submit_button(
        "Añadir",
        use_container_width=True,
        disabled=limit_reached
    )

    if submitted:
        # Validación del límite
        if len(products) >= 10:
            st.error("Has alcanzado el límite de 10 productos.")

        # Validación de campos
        elif not name.strip() or not url.strip():
            st.error("Debes introducir nombre y URL.")

        # Validación de URL
        elif not valid_url(url):
            st.error("URL no válida.")

        # Evitar duplicados
        elif any(p["url"] == url for p in products):
            st.warning("Este producto ya está monitorizado.")

        else:
            products.append({
                "name": name.strip(),
                "url": url.strip()
            })

            save_products(products, sha)
            st.success("Producto añadido")
            st.rerun()

if limit_reached:
    st.warning("Has alcanzado el máximo de 10 productos. Elimina uno para añadir otro.")

st.markdown('</div>', unsafe_allow_html=True)


# ===================================================
# SECCIÓN PRODUCTOS MONITORIZADOS
# ===================================================

st.markdown('<div class="section-title">Productos monitorizados</div>', unsafe_allow_html=True)

if len(products) == 0:
    st.info("No hay productos aún.")

# Recorremos todos los productos
for i, p in enumerate(products):
    # Intentamos obtener el precio actual
    price = get_current_price(p["url"])

    # Dos columnas:
    # - izquierda: tarjeta
    # - derecha: acción de eliminar
    col_card, col_delete = st.columns([12, 1])

    with col_card:
        st.markdown('<div class="product-card">', unsafe_allow_html=True)

        # Etiqueta pequeña
        st.markdown('<div class="product-chip">Producto monitorizado</div>', unsafe_allow_html=True)

        # Nombre
        st.markdown(f'<div class="product-name">{p["name"]}</div>', unsafe_allow_html=True)

        # Precio muy destacado
        if price is not None:
            st.markdown(f'<div class="product-price">{price:.2f} €</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="product-no-price">Precio no disponible</div>', unsafe_allow_html=True)

        # URL
        st.markdown(f'<div class="product-url">{p["url"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_delete:
        st.markdown('<div class="delete-button-wrap"></div>', unsafe_allow_html=True)
        st.write("")
        st.write("")

        if st.button("✕", key=f"del_{i}", use_container_width=True):
            confirm_delete_dialog(i, p["name"], products, sha)
