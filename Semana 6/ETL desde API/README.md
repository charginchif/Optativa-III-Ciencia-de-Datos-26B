# Tarea integradora Semana 6 — Pipeline ETL desde una API pública

Práctica de **Optativa III: Ciencia de Datos** (UNE Plantel Centro — Ingeniería en Computación, 9.º semestre).

Pipeline ETL documentado que **consume la API pública [DummyJSON](https://dummyjson.com/products)** (catálogo de una tienda en línea), limpia y enriquece los datos, los modela en un **esquema estrella** y los guarda en **SQLite**.

```text
DummyJSON API ──► EXTRACT ──────────► TRANSFORM ─────────────► LOAD ──► catalogo.db
 (JSON, HTTP)     requests +           limpieza + features +    to_sql   dim_categoria
                  copia cruda (.json)  esquema estrella                  dim_marca
                                                                         fact_productos
```

## 📁 Estructura

```text
├── etl_api.py                    # Pipeline con las tres fases comentadas
├── datos_crudos/productos_raw.json  # Respuesta original de la API (se genera al ejecutar)
├── catalogo.db                   # Base SQLite resultante
├── salida.txt / captura_salida.png  # Evidencia de la ejecución
├── requirements.txt
└── README.md
```

## 🚀 Ejecución

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python etl_api.py
```

---

## 🔄 Fases

### 1. EXTRACT
* `requests.get("https://dummyjson.com/products", params={"limit": 0})` descarga los **194 productos** en una sola llamada.
* Se envía un `User-Agent`, porque sin él el servidor responde **HTTP 403**. `raise_for_status()` detiene el pipeline si la API falla, para no cargar datos incompletos.
* La respuesta se guarda **sin modificar** en `datos_crudos/productos_raw.json`. Es la "zona cruda", la misma idea de un data lake: si cambia la transformación, se reprocesa sin volver a llamar a la API.
* `pd.json_normalize()` convierte el JSON anidado en un DataFrame.

### 2. TRANSFORM
| Paso | Detalle |
|---|---|
| Selección | De 22 campos se conservan 8: id, título, categoría, marca, precio, descuento, rating y stock |
| Traducción | Columnas renombradas al español (`price` → `precio`, …) |
| Valores faltantes | **92 productos sin marca** → `"Sin marca"` (no se descartan, porque sí tienen precio y stock) |
| Texto uniforme | Categorías `home-decoration` → `Home decoration` |
| Duplicados | `drop_duplicates(subset="producto_id")` |
| **Features nuevas** | `precio_final = precio × (1 − descuento/100)` y `valor_inventario = precio_final × stock` |

### 3. LOAD
Tres tablas en `catalogo.db` con `if_exists="replace"`, para que el pipeline se pueda volver a ejecutar sin duplicar datos. Después de cargar se **valida** que ningún hecho quede sin su dimensión (resultado: 0 huérfanos).

---

## ⭐ Esquema estrella

```text
 ┌───────────────┐        ┌──────────────────────┐        ┌───────────────┐
 │ dim_categoria │        │    fact_productos    │        │   dim_marca   │
 │───────────────│        │──────────────────────│        │───────────────│
 │ cat_id (PK)   │◄───────┤ cat_id   (FK)        ├───────►│ marca_id (PK) │
 │ categoria     │        │ marca_id (FK)        │        │ marca         │
 └───────────────┘        │ producto_id, titulo  │        └───────────────┘
      24 filas            │ precio, descuento_pct│             64 filas
                          │ precio_final, stock  │
                          │ valor_inventario     │
                          │ rating               │
                          └──────────────────────┘
                                 194 filas
```

## 📊 Resultado

```text
Top 8 categorías por valor de inventario (USD):
     categoria  productos  rating_prom  valor_inventario
       Vehicle          5         3.39           9608753
  Mens watches          6         3.66           2482712
Womens watches          5         3.48           1243628
    Motorcycle          5         3.67            917638
       Laptops          5         3.62            351794
     Furniture          5         4.01            314649
   Smartphones         16         3.70            244575
       Tablets          3         3.86             81231
```

**Interpretación:** con solo 5 productos, *Vehicle* concentra la mayor parte del capital inmovilizado en inventario, porque son artículos muy caros. *Smartphones* tiene más variedad (16 productos) pero mucho menos valor. Para la gerencia, esto indica dónde un exceso de stock cuesta más dinero.

> Los datos de DummyJSON son de prueba y pueden cambiar con el tiempo, así que los números de otra ejecución pueden variar un poco.
