# Conciliación Financiera Presupuestal

App en **Streamlit** que procesa un Excel y aplica filtros contables.

## 🚀 Filtros aplicados

### Filtro 1
- `tipo_ctb = 1`
- `haber ≠ 0`
- `(ciclo = G y fase = D) o (ciclo = I y fase = D)`
- `saldo = haber`

### Filtro 2
- `tipo_ctb = 2`
- `debe ≠ 0`
- `(ciclo = G y fase = D) o (ciclo = I y fase = R)`
- `saldo = debe`

### Filtro 3
- `ciclo = C y fase = C`
- `mayor` inicia con `5`, `4`, `8501` o `8601`
- `saldo = haber - debe`

Los tres filtros se concatenan en orden y se guardan en la hoja **Filtrado**.

## 📂 Columnas exportadas
- `codigo_unido` (mayor-sub_cta-clasificador)
- `nro_not_exp`
- `desc_documento`
- `nro_doc`
- `Fecha Contable`
- `desc_proveedor`
- `saldo`

## 📦 Instalación local
```bash
pip install -r requirements.txt
streamlit run app.py
