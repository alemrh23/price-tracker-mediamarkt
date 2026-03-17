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
# Aquí mejoramos el aspecto general y, sobre todo,
# la zona donde se listan los productos.

st.markdown("""
<style>
    /* Fondo general y márgenes superiores */
    .main {
        padding-top: 1.5rem;
    }

    /* Título principal */
    .app-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1f2937;
        margin-bottom: 0.15rem;
    }

    /* Subtítulo */
    .app-subtitle {
        color: #6b7280;
        margin-bottom: 2rem;
        font-size: 1rem;
    }

    /* Caja del formulario de añadir producto */
    .form-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 1.25rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 1.5rem;
    }

    /* Tarjeta de cada producto */
    .product-card {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 1.15rem 1.2rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
    }

    /* Cabecera de la tarjeta */
    .product-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    /* Nombre del producto */
    .product-name {
        font-size: 1.15rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.3;
        margin: 0;
    }

    /* Etiqueta pequeña */
    .product-badge {
        display: inline-block;
        background: #eef6ff;
        color: #1d4ed8;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        margin-bottom: 0.75rem;
    }

    /* Precio cuando está disponible */
    .product-price {
        font-size: 2rem;
        font-weight: 900;
        color: #059669;
        line-height: 1.1;
        margin: 0.25rem 0 0.35rem 0;
    }

    /* Precio no disponible */
    .product-price-unavailable {
        font-size: 1rem;
        font-weight: 700;
        color: #b45309;
        margin: 0.25rem 0 0.35rem 0;
    }

    /* URL */
    .product-url {
        font-size: 0.88rem;
        color: #6b7280;
        word-break: break-word;
        line-height: 1.4;
        margin-top: 0.35rem;
    }

    /* Separación visual entre título y listado */
    .section-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1f2937;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Ajuste visual del botón de eliminar */
    div[data-testid="stButton"] > button[kind="secondary"] {
        border-radius: 12px;
    }

    /* Botón pequeño visualmente agradable */
    .small-note {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: -0.25rem;
        margin-bottom: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


# ===================================================
# CABECERA
# ===================================================

st.markdown('<div class="app-title">💸 Rastreador de precios</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Controla tus productos y consulta su precio actual de forma visual.</div>', unsafe_allow_html=True)


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

# Cabeceras HTTP para autenticación con GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para simular un navegador al pedir páginas
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===================================================
# VALIDACIÓN DE URL
# ===================================================

def valid_url(url):
    """
    Comprueba si una URL tiene un formato válido.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# ===================================================
# CARGA DE PRODUCTOS DESDE GITHUB
# ===================================================

def load_products():
    """
    Lee products.json desde GitHub y devuelve:
    - lista de productos
    - SHA actual del archivo
    """
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # El contenido viene codificado en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    products = json.loads(content)

    return products, data["sha"]


# ===================================================
# GUARDAR PRODUCTOS EN GITHUB
# ===================================================

def save_products(products, sha):
    """
    Guarda la lista de productos actualizada en GitHub.
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
    Busca el precio en scripts JSON-LD de la página.
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
    Si falla JSON-LD, intenta encontrar un precio en el texto visible.
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
    Descarga la página del producto e intenta obtener el precio actual.
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
# DIÁLOGO DE CONFIRMACIÓN PARA BORRAR
# ===================================================

@st.dialog("Confirmar eliminación")
def confirm_delete_dialog(product_index, product_name, products, sha):
    """
    Muestra una ventana modal para confirmar el borrado.
    """
    st.write(f"¿Seguro que quieres eliminar **{product_name}**?")

    col_yes, col_no = st.columns(2)

    # Confirmar borrado
    if col_yes.button("Sí, eliminar", key=f"confirm_yes_{product_index}", use_container_width=True):
        new_products = products[:product_index] + products[product_index + 1:]
        save_products(new_products, sha)
        st.success("Producto eliminado")
        st.rerun()

    # Cancelar borrado
    if col_no.button("Cancelar", key=f"confirm_no_{product_index}", use_container_width=True):
        st.rerun()


# ===================================================
# CARGA INICIAL DE PRODUCTOS
# ===================================================

products, sha = load_products()


# ===================================================
# FORMULARIO PARA AÑADIR PRODUCTOS
# ===================================================

st.markdown('<div class="section-title">Añadir producto</div>', unsafe_allow_html=True)

st.markdown('<div class="form-box">', unsafe_allow_html=True)

# Mostramos cuántos productos hay añadidos
st.info(f"{len(products)} / 10 productos")

# Si ya hay 10, bloqueamos el formulario
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
        # Validación de límite
        if len(products) >= 10:
            st.error("Has alcanzado el límite de 10 productos.")

        # Validación de campos vacíos
        elif not name.strip() or not url.strip():
            st.error("Debes introducir nombre y URL.")

        # Validación de formato de URL
        elif not valid_url(url):
            st.error("URL no válida.")

        # Evitar duplicados por URL
        elif any(p["url"] == url for p in products):
            st.warning("Este producto ya está monitorizado.")

        else:
            # Añadimos el producto a la lista
            products.append({
                "name": name.strip(),
                "url": url.strip()
            })

            # Guardamos en GitHub
            save_products(products, sha)

            st.success("Producto añadido")
            st.rerun()

# Mensaje si se alcanza el límite
if limit_reached:
    st.warning("Has alcanzado el máximo de 10 productos. Elimina uno para añadir otro.")

st.markdown('</div>', unsafe_allow_html=True)


# ===================================================
# LISTA DE PRODUCTOS
# ===================================================

st.markdown('<div class="section-title">Productos monitorizados</div>', unsafe_allow_html=True)

if len(products) == 0:
    st.info("No hay productos aún.")

# Recorremos todos los productos guardados
for i, p in enumerate(products):
    # Intentamos obtener el precio actual
    price = get_current_price(p["url"])

    # Creamos dos columnas:
    # - izquierda grande: tarjeta del producto
    # - derecha pequeña: botón eliminar
    col_card, col_action = st.columns([10, 1])

    with col_card:
        # Abrimos la tarjeta visual
        st.markdown('<div class="product-card">', unsafe_allow_html=True)

        # Pequeña etiqueta decorativa
        st.markdown('<div class="product-badge">Producto monitorizado</div>', unsafe_allow_html=True)

        # Nombre del producto
        st.markdown(f'<div class="product-name">{p["name"]}</div>', unsafe_allow_html=True)

        # Precio o aviso de no disponible
        if price is not None:
            st.markdown(f'<div class="product-price">{price:.2f} €</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="product-price-unavailable">Precio no disponible</div>', unsafe_allow_html=True)

        # URL del producto
        st.markdown(f'<div class="product-url">{p["url"]}</div>', unsafe_allow_html=True)

        # Cerramos la tarjeta
        st.markdown('</div>', unsafe_allow_html=True)

    with col_action:
        # Espaciado vertical para alinear mejor el botón
        st.write("")
        st.write("")
        st.write("")

        # Botón para borrar producto
        if st.button("✕", key=f"del_{i}", use_container_width=True):
            confirm_delete_dialog(i, p["name"], products, sha)
