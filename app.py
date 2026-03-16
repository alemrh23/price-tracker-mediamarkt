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

# Token de GitHub guardado en Secrets de Streamlit
TOKEN = st.secrets["GITHUB_TOKEN"]

# Repositorio donde está products.json
REPO = st.secrets["REPO"]

# Archivo donde guardamos los productos
FILE = "products.json"

# Rama principal del repositorio
BRANCH = "main"

# URL de la API de GitHub para leer/escribir products.json
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras para autenticarse con GitHub
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Cabeceras para pedir páginas web simulando navegador
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


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
    # Pedimos el archivo products.json a GitHub
    r = requests.get(API, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # GitHub devuelve el contenido en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    # Convertimos el JSON a lista Python
    products = json.loads(content)

    # Devolvemos también el SHA actual del archivo
    return products, data["sha"]


# ---------------------------------------------------
# GUARDAR PRODUCTOS EN GITHUB
# ---------------------------------------------------

def save_products(products, sha):
    # Convertimos la lista a texto JSON bonito
    json_text = json.dumps(products, ensure_ascii=False, indent=2)

    # Lo codificamos en base64 porque GitHub lo exige
    encoded = base64.b64encode(json_text.encode("utf-8")).decode("utf-8")

    # Preparamos el commit
    payload = {
        "message": "Update products.json from Streamlit app",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    # Enviamos el cambio a GitHub
    r = requests.put(API, headers=headers, json=payload, timeout=30)
    r.raise_for_status()


# ---------------------------------------------------
# EXTRAER PRECIO DESDE JSON-LD
# ---------------------------------------------------

def extract_price_from_jsonld(soup):
    # Busca scripts con datos estructurados del producto
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

            # Si offers es un diccionario
            if isinstance(offers, dict):
                price = offers.get("price")
                if price is not None:
                    try:
                        return float(str(price).replace(",", "."))
                    except:
                        pass

            # Si offers es una lista
            elif isinstance(offers, list):
                for offer in offers:
                    if isinstance(offer, dict) and offer.get("price") is not None:
                        try:
                            return float(str(offer["price"]).replace(",", "."))
                        except:
                            pass

    return None


# ---------------------------------------------------
# EXTRAER PRECIO DESDE TEXTO VISIBLE
# ---------------------------------------------------

def extract_price_from_text(soup):
    # Coge todo el texto visible de la página
    text = soup.get_text(" ", strip=True)

    # Busca patrones tipo 79,99 € o 79.99 €
    matches = re.findall(r"(\d+[.,]\d{2})\s*€", text)

    if not matches:
        return None

    try:
        return float(matches[0].replace(",", "."))
    except:
        return None


# ---------------------------------------------------
# OBTENER PRECIO ACTUAL
# ---------------------------------------------------

def get_current_price(url):
    try:
        # Descargamos la página
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        r.raise_for_status()

        # Parseamos el HTML
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

# Usamos form con clear_on_submit=True
# Así, al enviar, los campos se vacían automáticamente
with st.form("add_product_form", clear_on_submit=True):
    name = st.text_input("Nombre del producto")
    url = st.text_input("URL del producto")

    submitted = st.form_submit_button("Añadir producto")

    if submitted:
        if not name.strip() or not url.strip():
            st.error("Debes introducir nombre y URL.")

        elif not valid_url(url):
            st.error("URL no válida.")

        elif any(p["url"] == url for p in products):
            st.warning("Este producto ya está monitorizado.")

        else:
            # Añadimos el nuevo producto
            products.append({
                "name": name.strip(),
                "url": url.strip()
            })

            # Guardamos en GitHub
            save_products(products, sha)

            st.success("Producto añadido")
            st.rerun()


# ---------------------------------------------------
# LISTA DE PRODUCTOS MONITORIZADOS
# ---------------------------------------------------

st.subheader("Productos monitorizados")

if len(products) == 0:
    st.info("No hay productos aún.")

for i, p in enumerate(products):
    # Intentamos obtener precio actual
    price = get_current_price(p["url"])

    col1, col2 = st.columns([6, 1])

    # Mostramos nombre y precio si se pudo leer
    if price is not None:
        col1.write(f"**{p['name']}** — **{price:.2f} €**")
    else:
        col1.write(f"**{p['name']}** — Precio no disponible")

    # Mostramos la URL debajo
    col1.caption(p["url"])

    # Botón para eliminar
    if col2.button("Eliminar", key=f"del_{i}"):
        new_products = products[:i] + products[i + 1:]
        save_products(new_products, sha)
        st.success("Producto eliminado")
        st.rerun()
