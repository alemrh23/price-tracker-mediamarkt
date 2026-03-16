# Importamos librerías necesarias
import streamlit as st
import json
import requests
import base64
from urllib.parse import urlparse


# ---------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------

# Título de la aplicación
st.title("Price Tracker")

# Token de GitHub guardado como secreto en Streamlit
TOKEN = st.secrets["GITHUB_TOKEN"]

# Repositorio en formato usuario/repositorio
REPO = st.secrets["REPO"]

# Archivo donde guardamos los productos
FILE = "products.json"

# Rama principal del repositorio
BRANCH = "main"

# Endpoint de la API de GitHub para ese archivo
API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

# Cabeceras necesarias para autenticarnos
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
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

    # Pedimos el archivo a GitHub
    r = requests.get(API, headers=headers)

    # Si hay error (token mal, archivo inexistente, etc)
    r.raise_for_status()

    # Convertimos la respuesta en JSON
    data = r.json()

    # GitHub envía el contenido codificado en base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    # Convertimos el texto JSON en lista Python
    products = json.loads(content)

    # Devolvemos lista y SHA del archivo
    return products, data["sha"]


# ---------------------------------------------------
# FUNCIÓN PARA GUARDAR PRODUCTOS EN GITHUB
# ---------------------------------------------------
def save_products(products, sha):

    # Convertimos la lista a texto JSON
    json_text = json.dumps(products, ensure_ascii=False, indent=2)

    # GitHub exige enviarlo en base64
    encoded = base64.b64encode(json_text.encode()).decode()

    # Datos para el commit
    payload = {
        "message": "Update products.json from Streamlit app",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    # Enviamos actualización a GitHub
    r = requests.put(API, headers=headers, json=payload)

    r.raise_for_status()


# ---------------------------------------------------
# CARGA INICIAL
# ---------------------------------------------------

products, sha = load_products()


# ---------------------------------------------------
# FORMULARIO PARA AÑADIR PRODUCTO
# ---------------------------------------------------

st.subheader("Añadir producto")

# Campo para nombre
name = st.text_input("Nombre del producto")

# Campo para URL
url = st.text_input("URL del producto")


# Botón añadir
if st.button("Añadir producto"):

    # Validación campos vacíos
    if not name.strip() or not url.strip():
        st.error("Debes introducir nombre y URL.")

    # Validación URL correcta
    elif not valid_url(url):
        st.error("URL no válida.")

    # Evitar productos duplicados
    elif any(p["url"] == url for p in products):
        st.warning("Este producto ya está monitorizado.")

    else:

        # Añadimos el producto
        products.append({
            "name": name.strip(),
            "url": url.strip()
        })

        # Guardamos cambios
        save_products(products, sha)

        st.success("Producto añadido")

        # Recarga automática de la página
        st.rerun()


# ---------------------------------------------------
# LISTA DE PRODUCTOS
# ---------------------------------------------------

st.subheader("Productos monitorizados")

if len(products) == 0:
    st.info("No hay productos aún.")


for i, p in enumerate(products):

    # Dos columnas: info + botón eliminar
    col1, col2 = st.columns([6,1])

    col1.write(f"**{p['name']}**")
    col1.caption(p["url"])

    # Botón eliminar
    if col2.button("Eliminar", key=i):

        # Eliminamos producto
        new_products = products[:i] + products[i+1:]

        # Guardamos cambios
        save_products(new_products, sha)

        st.success("Producto eliminado")

        # Recarga automática
        st.rerun()
