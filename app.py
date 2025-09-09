import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

# Entradas de búsqueda
dato1 = st.text_input("Dato a buscar 1")
dato2 = st.text_input("Dato a buscar 2")

if uploaded_file:
    try:
        # Cargar el archivo Excel
        df = pd.read_excel(uploaded_file, dtype=str)  # mantener formatos originales como texto

        # -------------------------
        # PROCESO 1
        # -------------------------
        df_proceso1 = df[df["mayor"].astype(str).str.startswith(("5", "4"))].copy()
        df_proceso1["mayor_subcta"] = df_proceso1["mayor"].astype(str) + "-" + df_proceso1["sub_cta"].astype(str)
        df_proceso1 = df_proceso1[["mayor_subcta", "clasificador"]]

        # -------------------------
        # PROCESO 2 (con filtro búsqueda antes)
        # -------------------------
        df["codigo_unido"] = df["mayor"].astype(str) + "-" + df["sub_cta"].astype(str) + "-" + df["clasificador"].astype(str)

        # Aplicar filtro búsqueda (Dato1 o Dato2)
        if dato1 or dato2:
            mask = pd.Series(False, index=df.index)
            if dato1:
                mask |= df["codigo_unido"].str.contains(str(dato1), na=False)
            if dato2:
                mask |= df["codigo_unido"].str.contains(str(dato2), na=False)
            df = df[mask]

        df_proceso2 = df[
            ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
             "Fecha Contable", "desc_proveedor", "saldo", "tipo_ctb",
             "ciclo", "fase", "debe", "haber", "mayor"]
        ].copy()

        # -------------------------
        # FILTRO 1
        # -------------------------
        filtro1 = df_proceso2[
            ((df_proceso2["tipo_ctb"] == "1") &
             ((df_proceso2["debe"].astype(float) != 0) |
              ((df_proceso2["ciclo"] == "G") & (df_proceso2["fase"] == "D")) |
              ((df_proceso2["ciclo"] == "I") & (df_proceso2["fase"] == "D") & (df_proceso2["haber"].astype(float) != 0))))
        ]

        # -------------------------
        # FILTRO 2
        # -------------------------
        filtro2 = df_proceso2[
            ((df_proceso2["tipo_ctb"] == "2") &
             (df_proceso2["saldo"].astype(float) != 0) &
             (((df_proceso2["ciclo"] == "G") & (df_proceso2["fase"] == "D")) |
              ((df_proceso2["ciclo"] == "I") & (df_proceso2["fase"] == "R")))) &
            (df_proceso2["mayor"].astype(str).str.startswith(("8501", "8601")))
        ]

        # Concatenar filtros
        df_filtros = pd.concat([filtro1, filtro2], ignore_index=True)

        # -------------------------
        # EXPORTACIÓN A EXCEL
        # -------------------------
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
            df_proceso1.to_excel(writer, index=False, sheet_name="Proceso 1")
            df_proceso2.to_excel(writer, index=False, sheet_name="Proceso 2", startrow=2)

            # Escribir etiquetas de búsqueda en Proceso 2
            workbook  = writer.book
            worksheet = writer.sheets["Proceso 2"]
            worksheet.write("L1", "Datos a buscar")
            worksheet.write("L2", str(dato1) if dato1 else "")
            worksheet.write("M2", str(dato2) if dato2 else "")

            df_filtros.to_excel(writer, index=False, sheet_name="Filtros")

        st.download_button(
            label="📥 Descargar Excel procesado",
            data=output.getvalue(),
            file_name="conciliacion_procesada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
