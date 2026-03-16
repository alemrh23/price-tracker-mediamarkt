# ---------------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS
# ---------------------------------------------------

import streamlit as st
import json
import requests
import base64
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup


# ---------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------

st.title("Rastreador de precios")

# Secrets de Streamlit
TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]

# Archivo donde se guardan los productos
FILE = "products.json"

# Rama principal
BRANCH = "main"

# URL de la API de GitHub para leer/escribir products.json
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras para GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para pedir páginas web como si fuera un navegador
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ---------------------------------------------------
# ESTADO DE LOS CAMPOS DEL FORMULARIO
# ---------------------------------------------------
# Esto permite vaciar los inputs después de añadir un producto

if "name_input" not in st.session_state:
    st.session_state.name_input = ""

if "url_input" not in st.session_state:
    st.session_state.url_input = ""


# ---------------------------------------------------
# VALIDAR URL
# ---------------------------------------------------

def valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# ---------------------------------------------------
# CARGAR PRODUCTOS DESDE GITHUB
# ---------------------------------------------------

def load_products():
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # El contenido viene en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    products = json.loads(content)

    # Devolvemos también el SHA, necesario para actualizar el archivo
    return products, data["sha"]


# ---------------------------------------------------
# GUARDAR PRODUCTOS EN GITHUB
# ---------------------------------------------------

def save_products(products, sha):
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


# ---------------------------------------------------
# EXTRAER PRECIO DESDE JSON-LD
# ---------------------------------------------------
# Primer intento: buscar precio estructurado en scripts JSON-LD

def extract_price_from_jsonld(soup):
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except:
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
                    except:
                        pass

            # Caso 2: offers es lista
            elif isinstance(offers, list):
                for offer in offers:
                    if isinstance(offer, dict) and offer.get("price") is not None:
                        try:
                            return float(str(offer["price"]).replace(",", "."))
                        except:
                            pass

    return None


# ---------------------------------------------------
# EXTRAER PRECIO COMO TEXTO VISIBLE
# ---------------------------------------------------
# Segundo intento: buscar patrones tipo "79,99 €" en el texto de la página

def extract_price_from_text(soup):
    text = soup.get_text(" ", strip=True)

    # Busca números tipo 79,99 € o 79.99 €
    matches = re.findall(r"(\d+[.,]\d{2})\s*€", text)

    if not matches:
        return None

    # Tomamos el primer precio encontrado
    try:
        return float(matches[0].replace(",", "."))
    except:
        return None


# ---------------------------------------------------
# OBTENER PRECIO ACTUAL DE UNA URL
# ---------------------------------------------------

def get_current_price(url):
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Intento 1: JSON-LD
        price = extract_price_from_jsonld(soup)
        if price is not None:
            return price

        # Intento 2: texto visible
        price = extract_price_from_text(soup)
        if price is not None:
            return price

        return None

    except:
        return None


# ---------------------------------------------------
# CARGA INICIAL
# ---------------------------------------------------

products, sha = load_products()


# ---------------------------------------------------
# FORMULARIO PARA AÑADIR PRODUCTO
# ---------------------------------------------------

st.subheader("Añadir producto")

name = st.text_input(
    "Nombre del producto",
    key="name_input"
)

url = st.text_input(
    "URL del producto",
    key="url_input"
)

if st.button("Añadir producto"):

    if not name.strip() or not url.strip():
        st.error("Debes introducir nombre y URL.")

    elif not valid_url(url):
        st.error("URL no válida.")

    elif any(p["url"] == url for p in products):
        st.warning("Este producto ya está monitorizado.")

    else:
        # Añadimos el producto
        products.append({
            "name": name.strip(),
            "url": url.strip()
        })

        # Guardamos cambios en GitHub
        save_products(products, sha)

        # Limpiamos los campos
        st.session_state.name_input = ""
        st.session_state.url_input = ""

        st.success("Producto añadido")

        # Recarga para ver cambios
        st.rerun()


# ---------------------------------------------------
# LISTA DE PRODUCTOS
# ---------------------------------------------------

st.subheader("Productos monitorizados")

if len(products) == 0:
    st.info("No hay productos aún.")

for i, p in enumerate(products):

    # Obtenemos precio actual
    price = get_current_price(p["url"])

    col1, col2 = st.columns([6, 1])

    if price is not None:
        col1.write(f"**{p['name']}** — **{price:.2f} €**")
    else:
        col1.write(f"**{p['name']}** — Precio no disponible")

    col1.caption(p["url"])

    if col2.button("Eliminar", key=f"del_{i}"):
        new_products = products[:i] + products[i + 1:]
        save_products(new_products, sha)
        st.success("Producto eliminado")
        st.rerun()
