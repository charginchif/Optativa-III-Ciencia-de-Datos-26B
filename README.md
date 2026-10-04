# Optativa III: Ciencia de Datos 26B

Repositorio de prácticas del curso **Optativa III: Ciencia de Datos** (UNE Plantel Centro — Ingeniería en Computación, 9.º semestre).

## 📁 Contenido

### Semana 6 — Fundamentos de ingeniería de datos
| Carpeta | Descripción |
|---|---|
| [`Semana 6/ETL desde API`](Semana%206/ETL%20desde%20API) | Pipeline ETL en Python que consume la API pública DummyJSON, limpia y enriquece los datos y los carga a SQLite con un esquema estrella (`fact_productos` + `dim_categoria` + `dim_marca`). |
| [`Semana 6/Pipeline cafeterias`](Semana%206/Pipeline%20cafeterias) | Diseño de un pipeline ETL para una cadena de cafeterías: fuentes, transformaciones, destino y justificación ETL/ELT y batch/streaming. |

## 🚀 Requisitos

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install pandas requests
```
