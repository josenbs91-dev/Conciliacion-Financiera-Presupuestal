# Conciliacion-Financiera-Presupuestal

Aplicación en **Streamlit** para procesar archivos Excel con reglas de conciliación financiera y presupuestal.

## 🚀 Funcionalidad

1. **Subida de Excel**: Se requiere un archivo que contenga la hoja `conciliacion1`.
2. **Procesos automáticos**:
   - **Proceso 1**: Crea hoja `proceso1` uniendo `mayor.sub_cta` (si empieza con 4 o 5) y mostrando su clasificador.
   - **Proceso 2**: Crea hoja `proceso2` con `codigo_unido` (`mayor.sub_cta-clasificador`) y columnas seleccionadas.
   - **Proceso 3**: Crea hoja `conciliacion1_new` aplicando filtros según reglas de ciclo, fase, tipo_ctb y montos.
   - **Proceso 4**: Aplica filtros por dos valores escritos por el usuario en `codigo_unido`, generando la hoja `resultado_filtro`.

3. **Descarga de resultados**: El archivo procesado se descarga con todas las hojas originales y las nuevas (`proceso1`, `proceso2`, `conciliacion1_new`, `resultado_filtro`).

## 📦 Requisitos

- Python 3.9 o superior  
- Librerías indicadas en `requirements.txt`

Instalación de dependencias:
```bash
pip install -r requirements.txt
