import streamlit as st
import pandas as pd
import io

st.title("📊 Conciliación Financiera Presupuestal")

# Subir archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

# Entradas para los dos datos de filtro
filtro1 = st.text_input("Primer dato para filtro (se buscará en codigo_unido)")
filtro2 = st.text_input("Segundo dato para filtro (se buscará en codigo_unido)")

ejecutar = st.button("Ejecutar procesos y generar Excel")

if uploaded_file and ejecutar:
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)

        # Concatenar todas las hojas para procesos iniciales
        df_all = pd.concat([xls.parse(sheet) for sheet in xls.sheet_names])

        # Forzar que las columnas numéricas sean de tipo número
        for col in ['debe', 'haber', 'saldo']:
            if col in df_all.columns:
                df_all[col] = pd.to_numeric(df_all[col], errors='coerce').fillna(0)

        # --- Proceso 1 ---
        if {'mayor', 'sub_cta', 'clasificador'}.issubset(df_all.columns):
            df_proceso1 = df_all[
                df_all['mayor'].astype(str).str.startswith(('4','5'))
            ].copy()
            df_proceso1["mayor_subcta"] = df_proceso1['mayor'].astype(str) + "." + df_proceso1['sub_cta'].astype(str)
            df_proceso1 = df_proceso1[['mayor_subcta','clasificador']]
        else:
            df_proceso1 = pd.DataFrame()

        # --- Proceso 2 ---
        required_cols = ['mayor','sub_cta','clasificador','nro_not_exp','desc_documento','nro_doc','Fecha Contable','desc_proveedor','debe','haber','saldo','tipo_ctb','ciclo','fase']
        if set(required_cols).issubset(df_all.columns):
            df_proceso2 = df_all.copy()
            df_proceso2["codigo_unido"] = df_proceso2['mayor'].astype(str)+"."+df_proceso2['sub_cta'].astype(str)+"-"+df_proceso2['clasificador'].astype(str)
            df_proceso2 = df_proceso2[['codigo_unido','nro_not_exp','desc_documento','nro_doc','Fecha Contable','desc_proveedor','debe','haber','saldo','tipo_ctb','ciclo','fase','mayor']]
        else:
            df_proceso2 = pd.DataFrame()

        # --- Proceso 3 --- Crear conciliacion1_new
        condiciones = []

        if not df_proceso2.empty:
            # Condición 1
            cond1 = (df_proceso2['tipo_ctb'].astype(str) == '1') & \
                    (df_proceso2['ciclo'] == 'G') & \
                    (df_proceso2['fase'] == 'D') & \
                    (df_proceso2['debe'] != 0)
            condiciones.append(df_proceso2[cond1])

            # Condición 2
            cond2 = (df_proceso2['tipo_ctb'].astype(str) == '1') & \
                    (df_proceso2['ciclo'] == 'I') & \
                    (df_proceso2['fase'] == 'D') & \
                    (df_proceso2['haber'] != 0)
            condiciones.append(df_proceso2[cond2])

            # Condición 3
            cond3 = (df_proceso2['tipo_ctb'].astype(str) == '2') & \
                    (df_proceso2['saldo'] != 0) & \
                    (((df_proceso2['ciclo'] == 'G') & (df_proceso2['fase'] == 'D')) | ((df_proceso2['ciclo'] == 'I') & (df_proceso2['fase'] == 'R'))) & \
                    (df_proceso2['mayor'].astype(str).str.startswith(('8501','8601')))
            condiciones.append(df_proceso2[cond3])

            # Condición 4
            cond4 = (df_proceso2['ciclo'] == 'C') & (df_proceso2['fase'] == 'C') & \
                    (df_proceso2['mayor'].astype(str).str.startswith(('4','5','8501','8601')))
            condiciones.append(df_proceso2[cond4])

            df_conciliacion1_new = pd.concat(condiciones, ignore_index=True)
        else:
            df_conciliacion1_new = pd.DataFrame()

        # --- Proceso 4 --- Filtro sobre conciliacion1_new
        if not df_conciliacion1_new.empty:
            df_filtro = df_conciliacion1_new[
                df_conciliacion1_new['codigo_unido'].str.contains(filtro1, na=False) |
                df_conciliacion1_new['codigo_unido'].str.contains(filtro2, na=False)
            ]
        else:
            df_filtro = pd.DataFrame()

        # Guardar todo en un nuevo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet in xls.sheet_names:
                xls.parse(sheet).to_excel(writer, sheet_name=sheet, index=False)
            df_proceso1.to_excel(writer, sheet_name='proceso1', index=False)
            df_proceso2.to_excel(writer, sheet_name='proceso2', index=False)
            df_conciliacion1_new.to_excel(writer, sheet_name='conciliacion1_new', index=False)
            df_filtro.to_excel(writer, sheet_name='resultado_filtro', index=False)

        st.success("Procesos ejecutados correctamente ✅")
        st.download_button(
            label="⬇️ Descargar Excel procesado",
            data=output.getvalue(),
            file_name="conciliacion_procesada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error durante el procesamiento: {e}")
