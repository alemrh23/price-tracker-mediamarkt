import streamlit as st
import json
import os

FILE = "products.json"

st.title("Price Tracker")

# cargar productos
if os.path.exists(FILE):
    with open(FILE) as f:
        products = json.load(f)
else:
    products = []

st.subheader("Añadir producto")

name = st.text_input("Nombre del producto")
url = st.text_input("URL")

if st.button("Añadir"):
    products.append({
        "name": name,
        "url": url
    })
    with open(FILE,"w") as f:
        json.dump(products,f,indent=2)
    st.success("Producto añadido")

st.subheader("Productos monitorizados")

for i,p in enumerate(products):
    col1,col2 = st.columns([4,1])

    col1.write(p["name"])

    if col2.button("Eliminar", key=i):
        products.pop(i)
        with open(FILE,"w") as f:
            json.dump(products,f,indent=2)
        st.experimental_rerun()
