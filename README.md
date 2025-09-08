# Conciliación Financiera Presupuestal

App en **Streamlit** que procesa un Excel y aplica dos procesos:

## 🚀 Procesos

### Proceso 1
- Une `mayor-sub_cta` en una columna.
- Filtra solo `mayor` que comiencen con **5** o **4**.
- Muestra junto al `clasificador`.

### Proceso 2
- Aplica tres filtros contables:
  1. `tipo_ctb = 1` con `haber ≠ 0` y `(ciclo = G, fase = D) o (ciclo = I, fase = D)`.
  2. `tipo_ctb = 2` con `debe ≠ 0` y `(ciclo = G, fase = D) o (ciclo = I, fase = R)`.
  3. `ciclo = C y fase = C` y `mayor` inicia con 5, 4, 8501 o 8601.
- Crea `codigo_unido = mayor-sub_cta-clasificador`.
- Exporta: `codigo_unido, nro_not_exp, desc_documento, nro_doc, Fecha Contable, desc_proveedor, saldo`.

## 📂 Exportación
El Excel generado contiene tres hojas:
- **Original**: datos sin filtrar.
- **Proceso 1**: `mayor-sub_cta` y `clasificador`.
- **Proceso 2**: filtros contables aplicados.

## 📦 Instalación local
```bash
pip install -r requirements.txt
streamlit run app.py
