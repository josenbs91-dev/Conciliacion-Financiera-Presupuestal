# Conciliación Financiera Presupuestal

App en **Streamlit** para filtrar datos de un archivo Excel según reglas de conciliación financiera.

## 🚀 Uso en Streamlit Cloud
1. Sube este repositorio a GitHub.
2. Conéctalo con [Streamlit Cloud](https://share.streamlit.io).
3. Selecciona el archivo `app.py` como entrada de la app.

## 📂 Cómo funciona
- Sube un archivo Excel con las columnas:  
  `tipo_ctb, haber, debe, nro_not_exp, desc_documento, nro_doc, Fecha Contable, desc_proveedor, mayor, sub_cta, clasificador`.
- La app:
  - Filtra `tipo_ctb = 1` → solo si `haber ≠ 0`.  
  - Filtra `tipo_ctb = 2` → solo si `debe ≠ 0`.  
  - Crea una nueva columna `saldo` con el valor correspondiente.  
  - Une `mayor-sub_cta-clasificador` en una sola columna llamada `codigo_unido`.  
- Genera un nuevo Excel con dos hojas:
  - **Original** → todos los datos.
  - **Filtrado** → los registros procesados.

## 📦 Instalación local
```bash
pip install -r requirements.txt
streamlit run app.py
