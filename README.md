# Conciliación Financiera Presupuestal

App en **Streamlit** que filtra un archivo Excel aplicando tres filtros específicos.

## 🚀 Filtros aplicados
1. **Filtro 1**:  
   - `tipo_ctb = 1`  
   - `haber ≠ 0`  
   - `(ciclo = G y fase = D) o (ciclo = I y fase = D)`  
   - `saldo = haber`

2. **Filtro 2**:  
   - `tipo_ctb = 2`  
   - `debe ≠ 0`  
   - `(ciclo = G y fase = D) o (ciclo = I y fase = R)`  
   - `saldo = debe`

3. **Filtro 3**:  
   - `ciclo = C y fase = C`  
   - `mayor` inicia con `5`, `4`, `8501` o `8601`  
   - `saldo = haber - debe`

Los tres filtros se concatenan en orden en la hoja **Filtrado**.

## 📂 Columnas en el resultado
- `codigo_unido` → unión de (`mayor-sub_cta-clasificador`)  
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
