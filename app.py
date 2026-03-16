# ---------------------------------------------------
# IMPORTACIÓN DE LIBRERÍAS
# ---------------------------------------------------

import streamlit as st        # librería para crear la web
import json                   # para manejar archivos JSON
import requests               # para hacer peticiones HTTP
import base64                 # GitHub guarda archivos codificados en base64
from urllib.parse import urlparse
from bs4 import BeautifulSoup # para leer el HTML de la página


# ---------------------------------------------------
# TÍTULO DE LA APP
# ---------------------------------------------------

st.title("Rastreador de precios")


# ---------------------------------------------------
# CONFIGURACIÓN DE GITHUB
# ---------------------------------------------------

# Token secreto guardado en Streamlit
TOKEN = st.secrets["GITHUB_TOKEN"]

# Repositorio donde está el archivo products.json
REPO = st.secrets["REPO"]

# Nombre del archivo donde se guardan los productos
FILE = "products.json"

# Rama principal del repositorio
BRANCH = "main"

# URL de la API de GitHub para acceder al archivo
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras necesarias para autenticarse contra GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabecera para simular navegador (evita bloqueos)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ---------------------------------------------------
# FUNCIÓN PARA VALIDAR URLs
# ---------------------------------------------------

def valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# ---------------------------------------------------
# FUNCIÓN PARA CARGAR PRODUCTOS DESDE GITHUB
# ---------------------------------------------------

def load_products():

    # pedimos el archivo products.json a GitHub
    r = requests.get(API, headers=headers, timeout=30)

    # si hay error lanza excepción
    r.raise_for_status()

    # convertimos respuesta a JSON
    data = r.json()

    # GitHub devuelve el contenido codificado en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    # convertimos JSON a lista de productos
    products = json.loads(content)

    # devolvemos productos y el SHA del archivo
    return products, data["sha"]


# ---------------------------------------------------
# FUNCIÓN PARA GUARDAR PRODUCTOS EN GITHUB
# ---------------------------------------------------

def save_products(products, sha):

    # convertimos lista de productos a texto JSON
    json_text = json.dumps(products, ensure_ascii=False, indent=2)

    # codificamos en base64 (GitHub lo exige)
    encoded = base64.b64encode(json_text.encode()).decode()

    # datos del commit
    payload = {
        "message": "Update products.json from Streamlit app",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    # enviamos actualización a GitHub
    r = requests.put(API, headers=headers, json=payload, timeout=30)

    r.raise_for_status()


# ---------------------------------------------------
# FUNCIÓN PARA EXTRAER EL PRECIO DEL HTML
# ---------------------------------------------------

def extract_price_from_jsonld(soup):

    # muchas webs guardan datos del producto en JSON-LD
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

            # caso 1: offers es un diccionario
            if isinstance(offers, dict):
                price = offers.get("price")

                if price is not None:
                    return float(str(price).replace(",", "."))

            # caso 2: offers es una lista
            elif isinstance(offers, list):

                for offer in offers:
                    if isinstance(offer, dict) and offer.get("price") is not None:
                        return float(str(offer["price"]).replace(",", "."))

    return None


# ---------------------------------------------------
# FUNCIÓN PARA OBTENER PRECIO ACTUAL
# ---------------------------------------------------

def get_current_price(url):

    try:
        # descargamos la página del producto
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=30)

        r.raise_for_status()

        # parseamos el HTML
        soup = BeautifulSoup(r.text, "html.parser")

        # intentamos extraer precio
        return extract_price_from_jsonld(soup)

    except:
        return None


# ---------------------------------------------------
# CARGAMOS PRODUCTOS
# ---------------------------------------------------

products, sha = load_products()


# ---------------------------------------------------
# FORMULARIO PARA AÑADIR PRODUCTO
# ---------------------------------------------------

st.subheader("Añadir producto")

name = st.text_input("Nombre del producto")
url = st.text_input("URL del producto")


if st.button("Añadir producto"):

    if not name.strip() or not url.strip():
        st.error("Debes introducir nombre y URL.")

    elif not valid_url(url):
        st.error("URL no válida.")

    elif any(p["url"] == url for p in products):
        st.warning("Este producto ya está monitorizado.")

    else:

        # añadimos producto a la lista
        products.append({
            "name": name.strip(),
            "url": url.strip()
        })

        # guardamos en GitHub
        save_products(products, sha)

        st.success("Producto añadido")

        # refrescamos app
        st.rerun()


# ---------------------------------------------------
# LISTA DE PRODUCTOS MONITORIZADOS
# ---------------------------------------------------

st.subheader("Productos monitorizados")

if len(products) == 0:
    st.info("No hay productos aún.")


# recorremos productos
for i, p in enumerate(products):

    # obtenemos precio actual
    price = get_current_price(p["url"])

    col1, col2 = st.columns([6,1])

    # mostramos nombre y precio
    if price is not None:
        col1.write(f"**{p['name']}** — **{price:.2f} €**")
    else:
        col1.write(f"**{p['name']}** — Precio no disponible")

    col1.caption(p["url"])

    # botón eliminar
    if col2.button("Eliminar", key=i):

        new_products = products[:i] + products[i+1:]

        save_products(new_products, sha)

        st.success("Producto eliminado")

        st.rerun()
