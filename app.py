import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Leer archivo con formatos originales
        df = pd.read_excel(uploaded_file, dtype=str)

        # Convertir columnas numéricas donde aplique (pero mantener formato original en exportación)
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
        # 📌 FILTRO ADICIONAL POR BUSQUEDA (ANTES DEL PROCESO 2)
        # ==============================
        st.subheader("🔍 Filtro adicional")
        dato1 = st.text_input("Dato a buscar 1 (en columna codigo_unido):")
        dato2 = st.text_input("Dato a buscar 2 (en columna codigo_unido):")

        # Crear columna codigo_unido antes del Proceso 2
        df["codigo_unido"] = df["mayor"].astype(str) + "-" + df["sub_cta"].astype(str) + "-" + df["clasificador"].astype(str)

        if dato1 or dato2:
            condiciones = []
            if dato1:
                condiciones.append(df["codigo_unido"].str.contains(dato1, na=False))
            if dato2:
                condiciones.append(df["codigo_unido"].str.contains(dato2, na=False))
            if condiciones:
                mask = condiciones[0]
                for cond in condiciones[1:]:
                    mask |= cond
                df = df[mask]

        # ==============================
        # 📌 PROCESO 2
        # ==============================
        # Filtro 1
        filtro1 = df[
            (df["tipo_ctb"] == "1") &
            (
                ((df["debe"].fillna(0) != 0) & (df["ciclo"] == "G") & (df["fase"] == "D")) |
                ((df["haber"].fillna(0) != 0) & (df["ciclo"] == "I") & (df["fase"] == "D"))
            )
        ][[
            "codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
            "Fecha Contable", "desc_proveedor", "saldo"
        ]].copy()
        filtro1["Origen"] = "Filtro 1"

        # Filtro 2
        filtro2 = df[
            (df["tipo_ctb"] == "2") &
            (df["saldo"].fillna(0) != 0) &
            (
                ((df["ciclo"] == "G") & (df["fase"] == "D")) |
                ((df["ciclo"] == "I") & (df["fase"] == "R"))
            ) &
            (df["mayor"].astype(str).str.startswith(("8501", "8601"), na=False))
        ][[
            "codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
            "Fecha Contable", "desc_proveedor", "saldo"
        ]].copy()
        filtro2["Origen"] = "Filtro 2"

        # Unir resultados → filtro1 seguido de filtro2
        proceso2 = pd.concat([filtro1, filtro2], ignore_index=True)

        # ==============================
        # 📌 EXPORTAR
        # ==============================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
            proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)

            # Guardar proceso2 en Excel
            proceso2.to_excel(writer, sheet_name="Proceso 2", index=False)

            # Escribir manualmente en L1, L2, M2
            workbook  = writer.book
            worksheet = writer.sheets["Proceso 2"]
            worksheet.write("L1", "Datos a buscar")
            worksheet.write("L2", dato1 if dato1 else "")
            worksheet.write("M2", dato2 if dato2 else "")

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
