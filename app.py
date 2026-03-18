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

st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #f6f8fb;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
    }

    /* Título */
    .app-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #0f172a;
    }

    .app-subtitle {
        color: #64748b;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.7rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }

    /* INPUTS BLANCOS */
    div[data-baseweb="input"] > div {
        background-color: white !important;
        border: 1px solid #cbd5f5 !important;
        border-radius: 10px !important;
    }

    input {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }

    input::placeholder {
        color: #94a3b8 !important;
    }

    /* BOTÓN AÑADIR */
    .stForm button[kind="primary"] {
        background: #0ea5e9 !important;
        border: 1px solid #0ea5e9 !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
    }

    .stForm button[kind="primary"]:hover {
        background: #0284c7 !important;
    }

    /* TABLA */
    .table-row {
        background: white;
        border-radius: 12px;
        padding: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .name-cell {
        font-size: 1.08rem;
        font-weight: 900;
    }

    .url-cell {
        font-size: 1rem;
        color: #1d4ed8;
        font-weight: 600;
    }

    .price-cell {
        font-weight: 900;
        color: #059669;
    }

    .price-unavailable {
        color: #b45309;
    }
</style>
""", unsafe_allow_html=True)


# ===================================================
# CABECERA
# ===================================================

st.markdown('<div class="app-title">💸 Rastreador de precios</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Controla tus productos fácilmente</div>', unsafe_allow_html=True)


# ===================================================
# CONFIGURACIÓN GITHUB
# ===================================================

TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = st.secrets["REPO"]

FILE = "products.json"
BRANCH = "main"

API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ===================================================
# FUNCIONES
# ===================================================

def valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def format_date(d):
    if not d:
        return "—"
    return datetime.fromisoformat(d).strftime("%d/%m/%Y")


def load_products():
    r = requests.get(API, headers=headers)
    data = r.json()

    content = base64.b64decode(data["content"]).decode()
    products = json.loads(content)

    for p in products:
        if "added_at" not in p:
            p["added_at"] = None

    return products, data["sha"]


def save_products(products, sha):
    text = json.dumps(products, indent=2)
    encoded = base64.b64encode(text.encode()).decode()

    payload = {
        "message": "update",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    requests.put(API, headers=headers, json=payload)


def get_price(url):
    try:
        r = requests.get(url, headers=REQUEST_HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text()
        match = re.search(r"(\\d+[.,]\\d{2})\\s*€", text)

        if match:
            return float(match.group(1).replace(",", "."))

        return None
    except:
        return None


# ===================================================
# LOAD
# ===================================================

products, sha = load_products()


# ===================================================
# AÑADIR PRODUCTO
# ===================================================

st.markdown('<div class="section-title">Añadir producto</div>', unsafe_allow_html=True)

with st.container(border=True):

    limit = len(products) >= 10

    with st.form("form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Nombre", disabled=limit)

        with col2:
            url = st.text_input("URL", disabled=limit)

        # BOTÓN CENTRADO
        c1, c2, c3 = st.columns([2,1,2])
        with c2:
            submit = st.form_submit_button("Añadir", use_container_width=True)

        if submit:
            if not name or not url:
                st.error("Campos vacíos")

            elif not valid_url(url):
                st.error("URL inválida")

            else:
                products.append({
                    "name": name,
                    "url": url,
                    "added_at": datetime.now().isoformat()
                })

                save_products(products, sha)
                st.rerun()


# ===================================================
# TABLA PRODUCTOS
# ===================================================

st.markdown('<div class="section-title">Productos monitorizados</div>', unsafe_allow_html=True)

cols = st.columns([2,1.5,1,3,1])

cols[0].write("Nombre")
cols[1].write("Fecha")
cols[2].write("Precio")
cols[3].write("URL")
cols[4].write("")

for i, p in enumerate(products):

    price = get_price(p["url"])

    cols = st.columns([2,1.5,1,3,1])

    cols[0].markdown(f'<div class="table-row name-cell">{p["name"]}</div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="table-row">{format_date(p["added_at"])}</div>', unsafe_allow_html=True)

    if price:
        cols[2].markdown(f'<div class="table-row price-cell">{price} €</div>', unsafe_allow_html=True)
    else:
        cols[2].markdown('<div class="table-row price-unavailable">—</div>', unsafe_allow_html=True)

    cols[3].markdown(f'<div class="table-row url-cell">{p["url"]}</div>', unsafe_allow_html=True)

    if cols[4].button("Eliminar", key=i):
        products.pop(i)
        save_products(products, sha)
        st.rerun()
