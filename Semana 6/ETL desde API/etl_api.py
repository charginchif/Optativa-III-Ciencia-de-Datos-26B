"""
Tarea integradora — Semana 6: Pipeline ETL que consume una API pública
Optativa III: Ciencia de Datos · UNE Plantel Centro

Fuente:  API pública DummyJSON (catálogo de productos de una tienda)
Destino: base SQLite "catalogo.db" con un esquema estrella
"""
import json
import os
import sqlite3

import pandas as pd
import requests

URL_API = "https://dummyjson.com/products"
CARPETA_CRUDOS = "datos_crudos"
BASE_DESTINO = "catalogo.db"

# ===== EXTRACT: consumir la API y guardar la respuesta cruda =====
# limit=0 pide todos los productos en una sola llamada.
# El User-Agent evita que el servidor rechace la petición (HTTP 403).
respuesta = requests.get(URL_API, params={"limit": 0},
                         headers={"User-Agent": "Mozilla/5.0 (etl-practica-une)"}, timeout=30)
respuesta.raise_for_status()
datos = respuesta.json()

# Se guarda el JSON tal como llegó (zona "cruda", como en un data lake) para
# poder reprocesarlo sin volver a llamar a la API.
os.makedirs(CARPETA_CRUDOS, exist_ok=True)
with open(os.path.join(CARPETA_CRUDOS, "productos_raw.json"), "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)

df = pd.json_normalize(datos["products"])
print("Extraídos", len(df), "productos de", URL_API)

# ===== TRANSFORM: seleccionar, limpiar y crear features nuevas =====
# 1) Quedarse solo con las columnas útiles para el análisis y traducirlas
df = df[["id", "title", "category", "brand", "price", "discountPercentage", "rating", "stock"]]
df = df.rename(columns={
    "id": "producto_id", "title": "titulo", "category": "categoria", "brand": "marca",
    "price": "precio", "discountPercentage": "descuento_pct",
})

# 2) Limpieza: marcas faltantes, texto uniforme y duplicados
sin_marca = df["marca"].isna().sum()
df["marca"] = df["marca"].fillna("Sin marca").str.strip()
df["categoria"] = df["categoria"].str.strip().str.replace("-", " ").str.capitalize()
df = df.drop_duplicates(subset="producto_id")
print("Limpieza:", sin_marca, "productos sin marca -> 'Sin marca'")

# 3) Features nuevas
df["precio_final"] = (df["precio"] * (1 - df["descuento_pct"] / 100)).round(2)
df["valor_inventario"] = (df["precio_final"] * df["stock"]).round(2)

# Modelado dimensional: esquema estrella (1 hecho + 2 dimensiones)
dim_categoria = pd.DataFrame({"categoria": sorted(df["categoria"].unique())})
dim_categoria["cat_id"] = range(1, len(dim_categoria) + 1)

dim_marca = pd.DataFrame({"marca": sorted(df["marca"].unique())})
dim_marca["marca_id"] = range(1, len(dim_marca) + 1)

fact = df.merge(dim_categoria, on="categoria").merge(dim_marca, on="marca")
fact_productos = fact[["producto_id", "titulo", "cat_id", "marca_id", "precio", "descuento_pct",
                       "precio_final", "stock", "valor_inventario", "rating"]]

# ===== LOAD: cargar a SQLite =====
conn = sqlite3.connect(BASE_DESTINO)
dim_categoria.to_sql("dim_categoria", conn, if_exists="replace", index=False)
dim_marca.to_sql("dim_marca", conn, if_exists="replace", index=False)
fact_productos.to_sql("fact_productos", conn, if_exists="replace", index=False)
print(f"Cargadas: dim_categoria={len(dim_categoria)}, dim_marca={len(dim_marca)}, "
      f"fact_productos={len(fact_productos)} -> {BASE_DESTINO}")

# ===== Validación: ningún hecho sin dimensión =====
huerfanos = pd.read_sql("""
SELECT COUNT(*) AS n FROM fact_productos f
LEFT JOIN dim_categoria c ON f.cat_id = c.cat_id
LEFT JOIN dim_marca m     ON f.marca_id = m.marca_id
WHERE c.cat_id IS NULL OR m.marca_id IS NULL
""", conn)["n"][0]
print("Validación: productos sin categoría o marca en las dimensiones =", huerfanos)

# ===== Consulta analítica: valor del inventario por categoría =====
query = """
SELECT c.categoria,
       COUNT(*)                         AS productos,
       ROUND(AVG(f.rating), 2)          AS rating_prom,
       CAST(ROUND(SUM(f.valor_inventario)) AS INTEGER) AS valor_inventario
FROM fact_productos f
JOIN dim_categoria c ON f.cat_id = c.cat_id
GROUP BY c.categoria
ORDER BY valor_inventario DESC
LIMIT 8
"""
print("\nTop 8 categorías por valor de inventario (USD):")
print(pd.read_sql(query, conn).to_string(index=False))
conn.close()
