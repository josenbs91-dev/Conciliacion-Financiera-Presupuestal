import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Leer archivo
        df = pd.read_excel(uploaded_file, dtype=str)

        # Convertir columnas numéricas donde aplique
        for col in ["haber", "debe", "saldo"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # ==============================
        # 📌 PROCESO 1
        # ==============================
        proceso1 = df[df["mayor"].str.startswith(("5", "4"), na=False)].copy()
        proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
        proceso1 = proceso1[["mayor_subcta", "clasificador"]]

        # ==============================
        # 📌 PROCESO 2
        # ==============================
        df["codigo_unido"] = df["mayor"].astype(str) + "-" + df["sub_cta"].astype(str) + "-" + df["clasificador"].astype(str)

        # Filtro 1
        filtro1 = df[
            (df["tipo_ctb"] == "1") &
            (df["haber"].fillna(0) != 0) &
            (((df["ciclo"] == "G") & (df["fase"] == "D")) |
             ((df["ciclo"] == "I") & (df["fase"] == "D")))
        ]

        # Filtro 2
        filtro2 = df[
            (df["tipo_ctb"] == "2") &
            (df["debe"].fillna(0) != 0) &
            (((df["ciclo"] == "G") & (df["fase"] == "D")) |
             ((df["ciclo"] == "I") & (df["fase"] == "R"))) &
            (df["mayor"].astype(str).str.startswith(("8501", "8601"), na=False))
        ]

        # Filtro 3
        filtro3 = df[
            (df["ciclo"] == "C") & (df["fase"] == "C") &
            (df["mayor"].astype(str).str.startswith(("5", "4", "8501", "8601"), na=False))
        ]

        proceso2 = pd.concat([filtro1, filtro2, filtro3], ignore_index=True)
        proceso2 = proceso2[[
            "codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
            "Fecha Contable", "desc_proveedor", "saldo"
        ]]

        # ==============================
        # 📌 PROCESO 3 → Conciliación
        # ==============================
        conciliacion_tables = []
        for _, row in proceso1.iterrows():
            mayor_subcta = str(row["mayor_subcta"])
            clasificador = str(row["clasificador"])

            # Filtrar filas que contengan mayor_subcta o clasificador
            subset = proceso2[
                proceso2["codigo_unido"].astype(str).str.contains(mayor_subcta, na=False) |
                proceso2["codigo_unido"].astype(str).str.contains(clasificador, na=False)
            ].copy()

            if not subset.empty:
                # Pivot dinámico → cada codigo_unido se vuelve encabezado
                pivot = subset.pivot_table(
                    index=["nro_not_exp", "desc_documento", "nro_doc",
                           "Fecha Contable", "desc_proveedor"],
                    columns="codigo_unido",
                    values="saldo",
                    aggfunc="sum",
                    fill_value=""
                ).reset_index()

                conciliacion_tables.append((f"{mayor_subcta}-{clasificador}", pivot))

        # ==============================
        # 📌 Exportar resultados
        # ==============================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
            proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)
            proceso2.to_excel(writer, sheet_name="Proceso 2", index=False)

            # Conciliación → varias tablas con espacio de 5 filas
            if conciliacion_tables:
                workbook = writer.book
                worksheet = workbook.add_worksheet("Conciliacion")
                writer.sheets["Conciliacion"] = worksheet

                start_row = 0
                for name, table in conciliacion_tables:
                    worksheet.write(start_row, 0, f"Tabla: {name}")
                    table.to_excel(writer, sheet_name="Conciliacion",
                                   startrow=start_row + 1, index=False)
                    start_row += len(table) + 6  # tabla + título + 5 filas vacías

        st.success("Procesos completados correctamente ✅")

        # Botón de descarga
        st.download_button(
            label="📥 Descargar Excel Procesado",
            data=output.getvalue(),
            file_name="Procesos_Conciliacion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
