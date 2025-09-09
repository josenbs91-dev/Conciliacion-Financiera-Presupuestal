import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

# Inputs para filtros adicionales (columna codigo_unido en conciliacion)
dato1 = st.text_input("Dato filtro 1 (columna codigo_unido)")
dato2 = st.text_input("Dato filtro 2 (columna codigo_unido)")

if uploaded_file:
    try:
        # Cargar archivo Excel manteniendo formatos originales como texto
        df = pd.read_excel(uploaded_file, dtype=str)

        # -------------------------
        # PROCESO 1
        # -------------------------
        df_proceso1 = df[df["mayor"].astype(str).str.startswith(("5", "4"))].copy()
        df_proceso1["mayor_subcta"] = df_proceso1["mayor"].astype(str) + "-" + df_proceso1["sub_cta"].astype(str)
        df_proceso1 = df_proceso1[["mayor_subcta", "clasificador"]]

        # -------------------------
        # PROCESO 2 → base_conc
        # -------------------------
        df_base = df.copy()
        df_base["codigo_unido"] = (
            df_base["mayor"].astype(str) + "-" +
            df_base["sub_cta"].astype(str) + "-" +
            df_base["clasificador"].astype(str)
        )

        df_base_conc = df_base[
            ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
             "Fecha Contable", "desc_proveedor", "saldo",
             "tipo_ctb", "ciclo", "fase", "debe", "haber", "mayor"]
        ].copy()

        # -------------------------
        # FILTROS → conciliacion
        # -------------------------
        # Filtro 1: tipo_ctb = 1, ciclo G, fase D, debe ≠ 0
        filtro1 = df_base_conc[
            (df_base_conc["tipo_ctb"] == "1") &
            (df_base_conc["ciclo"] == "G") &
            (df_base_conc["fase"] == "D") &
            (df_base_conc["debe"].astype(float) != 0)
        ]

        # Filtro 2: tipo_ctb = 1, ciclo G, fase D, haber ≠ 0
        filtro2 = df_base_conc[
            (df_base_conc["tipo_ctb"] == "1") &
            (df_base_conc["ciclo"] == "G") &
            (df_base_conc["fase"] == "D") &
            (df_base_conc["haber"].astype(float) != 0)
        ]

        # Filtro 3: tipo_ctb = 2, saldo ≠ 0, ciclo G fase D o ciclo I fase R, mayor = 8501/8601
        filtro3 = df_base_conc[
            (df_base_conc["tipo_ctb"] == "2") &
            (df_base_conc["saldo"].astype(float) != 0) &
            (
                ((df_base_conc["ciclo"] == "G") & (df_base_conc["fase"] == "D")) |
                ((df_base_conc["ciclo"] == "I") & (df_base_conc["fase"] == "R"))
            ) &
            (df_base_conc["mayor"].astype(str).str.startswith(("8501", "8601")))
        ]

        # Concatenar todos los filtros en orden
        df_conciliacion = pd.concat([filtro1, filtro2, filtro3], ignore_index=True)

        # -------------------------
        # FILTRO ADICIONAL en conciliacion (columna codigo_unido)
        # -------------------------
        if dato1 or dato2:
            condiciones = []
            if dato1:
                condiciones.append(df_conciliacion["codigo_unido"].str.contains(str(dato1), na=False))
            if dato2:
                condiciones.append(df_conciliacion["codigo_unido"].str.contains(str(dato2), na=False))
            if condiciones:
                df_conciliacion = df_conciliacion[pd.concat(condiciones, axis=1).any(axis=1)]

        # -------------------------
        # EXPORTACIÓN A EXCEL
        # -------------------------
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
            df_proceso1.to_excel(writer, index=False, sheet_name="Proceso 1")
            df_base_conc.to_excel(writer, index=False, sheet_name="base_conc")

            # Exportar conciliacion y agregar datos buscados en Q1:R2
            df_conciliacion.to_excel(writer, index=False, sheet_name="conciliacion")

            workbook = writer.book
            worksheet = writer.sheets["conciliacion"]
            worksheet.write("Q1", "Datos a buscar")
            worksheet.write("Q2", dato1 if dato1 else "")
            worksheet.write("R2", dato2 if dato2 else "")

        # Botón de descarga
        st.download_button(
            label="📥 Descargar Excel procesado",
            data=output.getvalue(),
            file_name="conciliacion_procesada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
