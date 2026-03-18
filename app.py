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
    .stApp {
        background-color: #f6f8fb;
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
    }

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

    /* Contador */
    .counter-box {
        background: #eef4ff;
        color: #1d4ed8;
        border-radius: 12px;
        padding: 0.7rem 1rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 1rem;
    }

    /* TABLA */
    .table-header {
        font-weight: 800;
        color: #475569;
        font-size: 0.9rem;
    }

    .table-row {
        background: white;
        border-radius: 14px;
        padding: 0.9rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 5px 14px rgba(0,0,0,0.05);
    }

    .name-cell {
        font-size: 1.05rem;
        font-weight: 800;
    }

    .url-cell {
        font-size: 0.98rem;
        color: #475569;
        word-break: break-word;
    }

    .price-cell {
        font-weight: 900;
        color: #059669;
        font-size: 1.2rem;
    }

    .price-unavailable {
        color: #b45309;
        font-weight: 700;
    }

    /* BOTÓN AÑADIR */
    .stForm button[kind="primary"] {
        background: #2563eb !important;
        border: 1px solid #2563eb !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
    }

    .stForm button[kind="primary"]:hover {
        background: #1d4ed8 !important;
    }

    /* BOTÓN ELIMINAR */
    .stButton button[kind="secondary"] {
        background: #fff5f5 !important;
        border: 1px solid #fecaca !important;
        color: #dc2626 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
    }

    hr {display:none;}
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
# FUNCIONES AUXILIARES
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


# ===================================================
# GITHUB LOAD / SAVE
# ===================================================

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
        "message": "update products",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH
    }

    requests.put(API, headers=headers, json=payload)


# ===================================================
# SCRAPING PRECIO
# ===================================================

def get_price(url):
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text()
        match = re.search(r"(\d+[.,]\d{2})\s*€", text)

        if match:
            return float(match.group(1).replace(",", "."))

        return None
    except:
        return None


# ===================================================
# BORRADO
# ===================================================

@st.dialog("Confirmar")
def confirm_delete(i, name, products, sha):
    st.write(f"Eliminar {name}?")

    if st.button("Sí"):
        new = products[:i] + products[i+1:]
        save_products(new, sha)
        st.rerun()

    if st.button("Cancelar"):
        st.rerun()


# ===================================================
# LOAD
# ===================================================

products, sha = load_products()


# ===================================================
# AÑADIR PRODUCTO
# ===================================================

st.markdown('<div class="section-title">Añadir producto</div>', unsafe_allow_html=True)

with st.container(border=True):

    st.markdown(
        f'<div class="counter-box">{len(products)} / 10 productos</div>',
        unsafe_allow_html=True
    )

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
# LISTADO TIPO TABLA
# ===================================================

st.markdown('<div class="section-title">Productos monitorizados</div>', unsafe_allow_html=True)

# CABECERA
cols = st.columns([2,1.5,1,3,1])

cols[0].markdown('<div class="table-header">Nombre</div>', unsafe_allow_html=True)
cols[1].markdown('<div class="table-header">Fecha</div>', unsafe_allow_html=True)
cols[2].markdown('<div class="table-header">Precio</div>', unsafe_allow_html=True)
cols[3].markdown('<div class="table-header">URL</div>', unsafe_allow_html=True)
cols[4].markdown('<div class="table-header">Acción</div>', unsafe_allow_html=True)

# FILAS
for i, p in enumerate(products):

    price = get_price(p["url"])

    cols = st.columns([2,1.5,1,3,1])

    # Nombre
    cols[0].markdown(f'<div class="table-row name-cell">{p["name"]}</div>', unsafe_allow_html=True)

    # Fecha
    cols[1].markdown(f'<div class="table-row">{format_date(p["added_at"])}</div>', unsafe_allow_html=True)

    # Precio
    if price:
        cols[2].markdown(f'<div class="table-row price-cell">{price} €</div>', unsafe_allow_html=True)
    else:
        cols[2].markdown('<div class="table-row price-unavailable">—</div>', unsafe_allow_html=True)

    # URL
    cols[3].markdown(f'<div class="table-row url-cell">{p["url"]}</div>', unsafe_allow_html=True)

    # Botón eliminar
    if cols[4].button("Eliminar", key=i):
        confirm_delete(i, p["name"], products, sha)
