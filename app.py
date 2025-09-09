import streamlit as st
import pandas as pd
import io

st.title("📊 Conciliación Financiera Presupuestal")

# Cargar archivo
archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])

# Entradas de texto para filtros
dato1 = st.text_input("🔍 Dato filtro 1 (buscar en codigo_unido)")
dato2 = st.text_input("🔍 Dato filtro 2 (buscar en codigo_unido)")

if archivo:
    try:
        # Leer todas las hojas del Excel
        xls = pd.ExcelFile(archivo)
        df = pd.read_excel(xls, xls.sheet_names[0], dtype=str)

        # Mantener también los numéricos en su formato original (saldo, debe, haber)
        numeric_cols = ["saldo", "debe", "haber"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # -------------------------
        # PROCESO 1
        # -------------------------
        proceso1 = df[df["mayor"].astype(str).str.startswith(("5", "4"))][
            ["mayor", "sub_cta", "clasificador"]
        ].copy()
        proceso1["mayor_subcta"] = proceso1["mayor"] + "-" + proceso1["sub_cta"]
        proceso1 = proceso1[["mayor_subcta", "clasificador"]]

        # -------------------------
        # PROCESO 2 - base_conc
        # -------------------------
        proceso2 = df.copy()
        proceso2["codigo_unido"] = (
            proceso2["mayor"].astype(str) + "-" +
            proceso2["sub_cta"].astype(str) + "-" +
            proceso2["clasificador"].astype(str)
        )
        base_conc = proceso2[
            ["codigo_unido", "nro_not_exp", "desc_documento",
             "nro_doc", "Fecha Contable", "desc_proveedor", "saldo",
             "tipo_ctb", "ciclo", "fase", "mayor", "debe", "haber"]
        ].copy()

        # -------------------------
        # FILTRO OR por dato1/dato2
        # -------------------------
        if dato1 or dato2:
            col = base_conc["codigo_unido"].astype(str)
            base_conc = base_conc[
                (col.str.contains(dato1, case=False, na=False) if dato1 else False) |
                (col.str.contains(dato2, case=False, na=False) if dato2 else False)
            ]

        # -------------------------
        # CONCILIACION (Filtros 1,2,3)
        # -------------------------
        conciliacion = pd.DataFrame()

        # Filtro 1
        filtro1 = base_conc[
            (base_conc["tipo_ctb"] == "1") &
            (base_conc["ciclo"] == "G") &
            (base_conc["fase"] == "D") &
            (base_conc["debe"] != 0)
        ]
        conciliacion = pd.concat([conciliacion, filtro1])

        # Filtro 2
        filtro2 = base_conc[
            (base_conc["tipo_ctb"] == "1") &
            (base_conc["ciclo"] == "I") &
            (base_conc["fase"] == "D") &
            (base_conc["haber"] != 0)
        ]
        conciliacion = pd.concat([conciliacion, filtro2])

        # Filtro 3
        filtro3 = base_conc[
            (base_conc["tipo_ctb"] == "2") &
            (base_conc["saldo"] != 0) &
            (
                (base_conc["ciclo"] == "G") & (base_conc["fase"] == "D") |
                (base_conc["ciclo"] == "I") & (base_conc["fase"] == "R")
            ) &
            (
                base_conc["mayor"].astype(str).str.startswith("8501") |
                base_conc["mayor"].astype(str).str.startswith("8601")
            )
        ]
        conciliacion = pd.concat([conciliacion, filtro3])

        # -------------------------
        # EXPORTAR EXCEL
        # -------------------------
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter",
                            datetime_format="yyyy-mm-dd") as writer:
            proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)
            base_conc.to_excel(writer, sheet_name="base_conc", index=False)

            # Agregar referencia en base_conc
            workbook = writer.book
            worksheet = writer.sheets["base_conc"]
            worksheet.write("L1", "Datos a buscar")
            worksheet.write("L2", dato1 if dato1 else "")
            worksheet.write("M2", dato2 if dato2 else "")

            conciliacion.to_excel(writer, sheet_name="conciliacion", index=False)

        st.success("✅ Archivo procesado correctamente")
        st.download_button(
            label="⬇️ Descargar Excel procesado",
            data=output.getvalue(),
            file_name="conciliacion_financiera.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
