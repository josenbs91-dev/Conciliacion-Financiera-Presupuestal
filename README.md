# Conciliación Financiera Presupuestal

Esta aplicación en **Streamlit** permite procesar archivos Excel de conciliación financiera y presupuestal siguiendo varios procesos definidos y generar resultados filtrados según múltiples criterios.

## Funcionalidades

1. **Subida de Excel:**
   - El usuario puede subir cualquier archivo Excel.
   - Mantiene los formatos originales de todas las columnas.
   - Las columnas `debe`, `haber` y `saldo` se convierten automáticamente a números.

2. **Procesos automáticos:**
   - **Proceso 1:** Genera la hoja `proceso1` combinando `mayor` y `sub_cta` con un punto (`mayor.sub_cta`) para registros que comienzan con 4 o 5, incluyendo sus `clasificador` si existe.
   - **Proceso 2:** Genera la hoja `proceso2` con `codigo_unido = mayor.sub_cta-clasificador` y otras columnas relevantes.
   - **Proceso 3:** Crea la hoja `conciliacion1_new` aplicando condiciones específicas sobre `tipo_ctb`, `ciclo`, `fase` y los importes de `debe`, `haber` y `saldo`.
   - **Proceso 4:** Permite filtrar `conciliacion1_new` según múltiples pares de datos proporcionados por el usuario.

3. **Filtros múltiples:**
   - Se pueden ingresar hasta 50 pares de filtros.
   - Cada par genera una tabla separada en la hoja `resultado_filtro`.
   - Las tablas se separan con 5 filas en blanco para mayor claridad.
   - Se muestran en la hoja `resultado_filtro` con columnas adicionales indicando `Filtro1` y `Filtro2` que originaron los resultados.

## Uso

1. Ejecutar la app en Streamlit con:
   ```bash
   streamlit run app.py
