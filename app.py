# ===================================================
# IMPORTACIÓN DE LIBRERÍAS
# ===================================================

import streamlit as st        # Framework para crear la web
import json                   # Para manejar JSON (products.json)
import requests               # Para hacer peticiones HTTP
import base64                 # GitHub usa base64 para los archivos
import re                     # Para buscar precios en texto
from urllib.parse import urlparse
from bs4 import BeautifulSoup # Para leer HTML de las páginas


# ===================================================
# CONFIGURACIÓN DE LA PÁGINA
# ===================================================

st.set_page_config(
    page_title="Rastreador de precios",
    page_icon="💸",
    layout="wide"  # aprovecha todo el ancho
)


# ===================================================
# ESTILOS (CSS) PARA HACER LA APP MÁS BONITA
# ===================================================

st.markdown("""
<style>
    .title-app {
        font-size: 2.4rem;
        font-weight: 800;
    }

    .subtitle-app {
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .price-card {
        background: white;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }

    .product-name {
        font-weight: 700;
        font-size: 1.1rem;
    }

    .product-price {
        font-size: 1.5rem;
        font-weight: bold;
        color: green;
    }

    .product-url {
        font-size: 0.85rem;
        color: gray;
    }
</style>
""", unsafe_allow_html=True)


# ===================================================
# CABECERA
# ===================================================

st.markdown('<div class="title-app">💸 Rastreador de precios</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-app">Controla precios fácilmente</div>', unsafe_allow_html=True)


# ===================================================
# CONFIGURACIÓN DE GITHUB
# ===================================================

# Token secreto (NO visible en código)
TOKEN = st.secrets["GITHUB_TOKEN"]

# Repositorio donde está products.json
REPO = st.secrets["REPO"]

FILE = "products.json"
BRANCH = "main"

# URL API GitHub
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabecera para evitar bloqueos de webs
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===================================================
# VALIDACIÓN DE URL
# ===================================================

def valid_url(url):
    """
    Comprueba que la URL tenga formato correcto
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# ===================================================
# CARGAR PRODUCTOS DESDE GITHUB
# ===================================================

def load_products():
    """
    Lee products.json desde GitHub
    """
    r = requests.get(API, headers=headers)
    data = r.json()

    # GitHub devuelve el archivo codificado
    content = base64.b64decode(data["content"]).decode()

    products = json.loads(content)

    return products, data["sha"]


# ===================================================
# GUARDAR PRODUCTOS EN GITHUB
# ===================================================

def save_products(products, sha):
    """
    Guarda los productos modificados en GitHub
    """
    json_text = json.dumps(products, indent=2)

    encoded = base64.b64encode(json_text.encode()).decode()

    payload = {
        "message": "update products",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    requests.put(API, headers=headers, json=payload)


# ===================================================
# OBTENER PRECIO DESDE LA WEB
# ===================================================

def get_price(url):
    """
    Intenta sacar el precio de la página
    """
    try:
        r = requests.get(url, headers=REQUEST_HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar precios tipo 79,99 €
        text = soup.get_text()
        match = re.search(r"(\d+[.,]\d{2})\s*€", text)

        if match:
            return float(match.group(1).replace(",", "."))

        return None

    except:
        return None


# ===================================================
# MODAL PARA CONFIRMAR BORRADO
# ===================================================

@st.dialog("Confirmar eliminación")
def confirm_delete(index, name, products, sha):
    """
    Ventana emergente para confirmar borrado
    """
    st.write(f"¿Eliminar {name}?")

    col1, col2 = st.columns(2)

    if col1.button("Sí"):
        new_products = products[:index] + products[index+1:]
        save_products(new_products, sha)
        st.rerun()

    if col2.button("Cancelar"):
        st.rerun()


# ===================================================
# CARGA DE PRODUCTOS
# ===================================================

products, sha = load_products()


# ===================================================
# FORMULARIO PARA AÑADIR PRODUCTOS
# ===================================================

st.subheader("Añadir producto")

# Contador
st.info(f"{len(products)} / 10 productos")

limit = len(products) >= 10

with st.form("form", clear_on_submit=True):

    name = st.text_input("Nombre", disabled=limit)
    url = st.text_input("URL", disabled=limit)

    submit = st.form_submit_button("Añadir", disabled=limit)

    if submit:

        # Límite de productos
        if len(products) >= 10:
            st.error("Máximo 10 productos")

        # Validaciones
        elif not name or not url:
            st.error("Campos vacíos")

        elif not valid_url(url):
            st.error("URL inválida")

        elif any(p["url"] == url for p in products):
            st.warning("Duplicado")

        else:
            products.append({"name": name, "url": url})
            save_products(products, sha)
            st.rerun()


# ===================================================
# LISTA DE PRODUCTOS
# ===================================================

st.subheader("Productos")

for i, p in enumerate(products):

    price = get_price(p["url"])

    col1, col2 = st.columns([8,1])

    with col1:
        st.markdown('<div class="price-card">', unsafe_allow_html=True)

        st.markdown(f'<div class="product-name">{p["name"]}</div>', unsafe_allow_html=True)

        if price:
            st.markdown(f'<div class="product-price">{price} €</div>', unsafe_allow_html=True)
        else:
            st.write("Precio no disponible")

        st.markdown(f'<div class="product-url">{p["url"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if st.button("❌", key=i):
            confirm_delete(i, p["name"], products, sha)
