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
# Aquí definimos el aspecto visual de la aplicación.
# Objetivos:
# - eliminar las "barras" blancas/grises que no te gustan
# - mejorar separación entre productos
# - hacer el botón de eliminar más agradable
# - dar más protagonismo al precio

st.markdown("""
<style>
    /* Fondo general de la app */
    .stApp {
        background-color: #f6f8fb;
    }

    /* Ajuste general del contenido */
    .main .block-container {
        max-width: 1150px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* Título principal */
    .app-title {
        font-size: 2.45rem;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }

    /* Subtítulo */
    .app-subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Títulos de sección */
    .section-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 1.25rem;
        margin-bottom: 1rem;
    }

    /* Tarjeta de producto */
    .product-card {
        background: #ffffff;
        border: 1px solid #e8edf5;
        border-radius: 22px;
        padding: 1.2rem 1.3rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 1rem;
    }

    /* Etiqueta pequeña */
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
        font-size: 1.18rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.35;
        margin-bottom: 0.45rem;
    }

    /* Precio disponible */
    .product-price {
        font-size: 2.05rem;
        font-weight: 900;
        color: #059669;
        line-height: 1.05;
        margin-bottom: 0.45rem;
    }

    /* Cuando no hay precio */
    .product-price-unavailable {
        font-size: 1rem;
        font-weight: 700;
        color: #b45309;
        margin-bottom: 0.45rem;
    }

    /* URL */
    .product-url {
        font-size: 0.9rem;
        color: #64748b;
        line-height: 1.45;
        word-break: break-word;
    }

    /* Caja visual pequeña para contador */
    .counter-box {
        background: #eaf2ff;
        color: #1d4ed8;
        border-radius: 14px;
        padding: 0.75rem 1rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    /* Mejora visual de inputs */
    div[data-baseweb="input"] > div {
        border-radius: 14px !important;
    }

    /* Botón principal (Añadir) */
    .stForm button[kind="primary"] {
        border-radius: 14px !important;
        font-weight: 800 !important;
        height: 2.8rem !important;
    }

    /* Botones secundarios (como eliminar) */
    .stButton button[kind="secondary"] {
        border-radius: 14px !important;
        border: 1px solid #fecaca !important;
        background: #fff5f5 !important;
        color: #dc2626 !important;
        font-weight: 800 !important;
        min-height: 2.8rem !important;
    }

    .stButton button[kind="secondary"]:hover {
        background: #fee2e2 !important;
        border-color: #fca5a5 !important;
        color: #b91c1c !important;
    }

    /* Oculta líneas horizontales si aparecieran */
    hr {
        display: none !important;
    }

    /* Evita bordes raros del formulario */
    div[data-testid="stForm"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
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
# Estos valores salen de los Secrets de Streamlit.

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]

# Archivo JSON donde guardamos los productos
FILE = "products.json"

# Rama principal del repositorio
BRANCH = "main"

# URL de la API de GitHub para leer/escribir el archivo
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras para autenticarnos en GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para pedir páginas web simulando un navegador
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===================================================
# VALIDAR URL
# ===================================================

def valid_url(url):
    """
    Comprueba si la URL tiene formato válido.
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
    - el SHA actual del archivo, necesario para actualizarlo después
    """
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # El contenido del archivo viene codificado en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    # Convertimos el JSON a lista Python
    products = json.loads(content)

    return products, data["sha"]


# ===================================================
# GUARDAR PRODUCTOS EN GITHUB
# ===================================================

def save_products(products, sha):
    """
    Guarda la lista de productos en products.json.
    """
    # Convertimos la lista a texto JSON legible
    json_text = json.dumps(products, ensure_ascii=False, indent=2)

    # GitHub exige el contenido en base64
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
    Intenta sacar el precio desde datos estructurados JSON-LD.
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


# ===================================================
# EXTRAER PRECIO DESDE TEXTO VISIBLE
# ===================================================

def extract_price_from_text(soup):
    """
    Si falla el método JSON-LD, intenta encontrar el precio en el texto visible.
    """
    text = soup.get_text(" ", strip=True)

    # Busca patrones tipo 79,99 € o 79.99 €
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
    Descarga la página del producto e intenta obtener su precio.
    """
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Primer intento: datos estructurados
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
    Abre una ventana modal para confirmar el borrado de un producto.
    """
    st.write(f"¿Seguro que quieres eliminar **{product_name}**?")

    col_yes, col_no = st.columns(2)

    # Confirmar eliminación
    if col_yes.button("Sí, eliminar", key=f"confirm_yes_{product_index}", use_container_width=True):
        new_products = products[:product_index] + products[product_index + 1:]
        save_products(new_products, sha)
        st.success("Producto eliminado")
        st.rerun()

    # Cancelar
    if col_no.button("Cancelar", key=f"confirm_no_{product_index}", use_container_width=True):
        st.rerun()


# ===================================================
# CARGA INICIAL DE PRODUCTOS
# ===================================================

products, sha = load_products()


# ===================================================
# SECCIÓN: AÑADIR PRODUCTO
# ===================================================

st.markdown('<div class="section-title">Añadir producto</div>', unsafe_allow_html=True)

# Contador visual
st.markdown(
    f'<div class="counter-box">{len(products)} / 10 productos</div>',
    unsafe_allow_html=True
)

# Si ya hay 10 productos, no permitimos añadir más
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
        type="primary",
        use_container_width=True,
        disabled=limit_reached
    )

    if submitted:
        # Validación del límite
        if len(products) >= 10:
            st.error("Has alcanzado el límite de 10 productos.")

        # Validación de campos obligatorios
        elif not name.strip() or not url.strip():
            st.error("Debes introducir nombre y URL.")

        # Validación de formato de URL
        elif not valid_url(url):
            st.error("URL no válida.")

        # Evita duplicados por URL
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


# ===================================================
# SECCIÓN: PRODUCTOS MONITORIZADOS
# ===================================================

st.markdown('<div class="section-title">Productos monitorizados</div>', unsafe_allow_html=True)

if len(products) == 0:
    st.info("No hay productos aún.")

# Recorremos todos los productos
for i, p in enumerate(products):
    # Intentamos obtener el precio actual
    price = get_current_price(p["url"])

    # Dos columnas:
    # - izquierda: tarjeta del producto
    # - derecha: botón eliminar
    col_card, col_action = st.columns([11, 2], vertical_alignment="center")

    with col_card:
        # Renderizamos toda la tarjeta en un único bloque HTML
        # para evitar separadores raros o barras vacías.
        if price is not None:
            price_html = f'<div class="product-price">{price:.2f} €</div>'
        else:
            price_html = '<div class="product-price-unavailable">Precio no disponible</div>'

        st.markdown(
            f"""
            <div class="product-card">
                <div class="product-chip">Producto monitorizado</div>
                <div class="product-name">{p["name"]}</div>
                {price_html}
                <div class="product-url">{p["url"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_action:
        # Botón eliminar, más claro y agradable
        if st.button(
            "🗑️ Eliminar",
            key=f"del_{i}",
            type="secondary",
            use_container_width=True
        ):
            confirm_delete_dialog(i, p["name"], products, sha)
