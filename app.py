import streamlit as st
import pandas as pd
import io

st.title("📊 Conciliación Financiera Presupuestal")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

# Interfaz para ingresar hasta 50 pares de filtros
st.markdown("Ingresa hasta 50 pares de filtros para buscar en 'codigo_unido'.")
num_filas = 50
filtros = []
for i in range(num_filas):
    col1, col2 = st.columns(2)
    dato1 = col1.text_input(f"Primer dato fila {i+1}")
    dato2 = col2.text_input(f"Segundo dato fila {i+1}")
    filtros.append((dato1.strip(), dato2.strip()))

# Botón para ejecutar
ejecutar = st.button("Ejecutar procesos y generar Excel")

if uploaded_file and ejecutar:
    try:
        # Leer archivo Excel manteniendo formatos originales
        xls = pd.ExcelFile(uploaded_file)
        df_all = pd.concat([xls.parse(sheet, dtype=str) for sheet in xls.sheet_names])

        # Convertir a numérico solo debe, haber y saldo
        for col in ['debe', 'haber', 'saldo']:
            if col in df_all.columns:
                df_all[col] = pd.to_numeric(df_all[col], errors='coerce').fillna(0)

        # --- Proceso 1 ---
        if {'mayor', 'sub_cta', 'clasificador'}.issubset(df_all.columns):
            df_proceso1 = df_all[df_all['mayor'].astype(str).str.startswith(('4','5'))].copy()
            df_proceso1["mayor_subcta"] = df_proceso1['mayor'].astype(str) + "." + df_proceso1['sub_cta'].astype(str)
            df_proceso1 = df_proceso1[['mayor_subcta','clasificador']]
        else:
            df_proceso1 = pd.DataFrame()

        # --- Proceso 2 ---
        required_cols = ['mayor','sub_cta','clasificador','nro_not_exp','desc_documento','nro_doc',
                         'Fecha Contable','desc_proveedor','debe','haber','saldo','tipo_ctb','ciclo','fase']
        if set(required_cols).issubset(df_all.columns):
            df_proceso2 = df_all.copy()
            for col in ['mayor','sub_cta','clasificador']:
                df_proceso2[col] = df_proceso2[col].fillna("").astype(str)
            df_proceso2["codigo_unido"] = df_proceso2['mayor']+"."+df_proceso2['sub_cta']+"-"+df_proceso2['clasificador']
            df_proceso2 = df_proceso2[['codigo_unido','nro_not_exp','desc_documento','nro_doc','Fecha Contable',
                                       'desc_proveedor','debe','haber','saldo','tipo_ctb','ciclo','fase','mayor']]
        else:
            df_proceso2 = pd.DataFrame()

        # --- Proceso 3 --- Crear conciliacion1_new
        condiciones = []
        if not df_proceso2.empty:
            cond1 = (df_proceso2['tipo_ctb'].astype(str) == '1') & (df_proceso2['ciclo'] == 'G') & (df_proceso2['fase'] == 'D') & (df_proceso2['debe'] != 0)
            cond2 = (df_proceso2['tipo_ctb'].astype(str) == '1') & (df_proceso2['ciclo'] == 'I') & (df_proceso2['fase'] == 'D') & (df_proceso2['haber'] != 0)
            cond3 = (df_proceso2['tipo_ctb'].astype(str) == '2') & (df_proceso2['saldo'] != 0) & \
                    (((df_proceso2['ciclo'] == 'G') & (df_proceso2['fase'] == 'D')) | ((df_proceso2['ciclo'] == 'I') & (df_proceso2['fase'] == 'R'))) & \
                    (df_proceso2['mayor'].astype(str).str.startswith(('8501','8601')))
            cond4 = (df_proceso2['ciclo'] == 'C') & (df_proceso2['fase'] == 'C') & \
                    (df_proceso2['mayor'].astype(str).str.startswith(('4','5','8501','8601')))
            condiciones.extend([df_proceso2[cond1], df_proceso2[cond2], df_proceso2[cond3], df_proceso2[cond4]])
            df_conciliacion1_new = pd.concat(condiciones, ignore_index=True)
        else:
            df_conciliacion1_new = pd.DataFrame()

        # --- Proceso 4 --- Filtro por todos los pares de filtros
        df_filtro_final = pd.DataFrame()
        if not df_conciliacion1_new.empty:
            row_offset = 0
            for f1, f2 in filtros:
                if f1 or f2:
                    df_temp = df_conciliacion1_new[
                        df_conciliacion1_new['codigo_unido'].str.contains(f1, na=False, regex=False) |
                        df_conciliacion1_new['codigo_unido'].str.contains(f2, na=False, regex=False)
                    ]
                    if not df_temp.empty:
                        df_temp.insert(0, 'Filtro1', f1)
                        df_temp.insert(1, 'Filtro2', f2)
                        # Añadir filas vacías si no es la primera tabla
                        if row_offset > 0:
                            df_filtro_final = pd.concat([df_filtro_final, pd.DataFrame([['']*len(df_temp.columns)]*5, columns=df_temp.columns)], ignore_index=True)
                        df_filtro_final = pd.concat([df_filtro_final, df_temp], ignore_index=True)
                        row_offset += len(df_temp) + 5

        # Guardar todo en Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet in xls.sheet_names:
                xls.parse(sheet).to_excel(writer, sheet_name=sheet, index=False)
            df_proceso1.to_excel(writer, sheet_name='proceso1', index=False)
            df_proceso2.to_excel(writer, sheet_name='proceso2', index=False)
            df_conciliacion1_new.to_excel(writer, sheet_name='conciliacion1_new', index=False)
            df_filtro_final.to_excel(writer, sheet_name='resultado_filtro', index=False)

        st.success("Procesos ejecutados correctamente ✅")
        st.download_button(
            label="⬇️ Descargar Excel procesado",
            data=output.getvalue(),
            file_name="conciliacion_procesada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error durante el procesamiento: {e}")
