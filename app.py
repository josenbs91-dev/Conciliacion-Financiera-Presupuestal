import streamlit as st
import pandas as pd
from io import BytesIO

st.title("Conciliación Financiera Presupuestal")

# Subir archivo
archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

# Cajas de texto para filtros
dato1 = st.text_input("Dato filtro 1 (para conciliacion)")
dato2 = st.text_input("Dato filtro 2 (para conciliacion)")

if archivo:
    try:
        # Leer Excel
        df = pd.read_excel(archivo, dtype=str)

        # -------------------
        # PROCESO 1
        # -------------------
        proceso1 = df[df["mayor"].str.startswith(("5", "4"), na=False)].copy()
        proceso1["mayor_subcta"] = proceso1["mayor"] + "-" + proceso1["sub_cta"]
        proceso1 = proceso1[["mayor_subcta", "clasificador"]]

        # -------------------
        # PROCESO 2 (base_conc)
        # -------------------
        proceso2 = df.copy()
        proceso2["codigo_unido"] = (
            proceso2["mayor"].fillna("") + "-" +
            proceso2["sub_cta"].fillna("") + "-" +
            proceso2["clasificador"].fillna("")
        )

        base_conc = proceso2[
            ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
             "Fecha Contable", "desc_proveedor", "saldo",
             "tipo_ctb", "ciclo", "fase", "mayor", "debe", "haber"]
        ].copy()

        # -------------------
        # PROCESO 2 (conciliacion con filtros)
        # -------------------
        conciliacion = pd.DataFrame()

        # Filtro 1
        filtro1 = base_conc[
            (base_conc["tipo_ctb"] == "1") &
            (base_conc["ciclo"] == "G") & (base_conc["fase"] == "D") &
            (base_conc["debe"].astype(float) != 0)
        ]
        conciliacion = pd.concat([conciliacion, filtro1])

        # Filtro 2
        filtro2 = base_conc[
            (base_conc["tipo_ctb"] == "1") &
            (base_conc["ciclo"] == "G") & (base_conc["fase"] == "D") &
            (base_conc["haber"].astype(float) != 0)
        ]
        conciliacion = pd.concat([conciliacion, filtro2])

        # Filtro 3
        filtro3 = base_conc[
            (base_conc["tipo_ctb"] == "2") &
            (base_conc["saldo"].astype(float) != 0) &
            (
                ((base_conc["ciclo"] == "G") & (base_conc["fase"] == "D")) |
                ((base_conc["ciclo"] == "I") & (base_conc["fase"] == "R"))
            ) &
            (base_conc["mayor"].str.startswith(("8501", "8601"), na=False))
        ]
        conciliacion = pd.concat([conciliacion, filtro3])

        # Filtro 4
        filtro4 = base_conc[
            (base_conc["ciclo"] == "C") & (base_conc["fase"] == "C") &
            (base_conc["mayor"].str.startswith(("5", "4"), na=False))
        ]
        conciliacion = pd.concat([conciliacion, filtro4])

        # -------------------
        # APLICAR FILTRO DATO1 / DATO2 SOLO A conciliacion
        # -------------------
        if dato1 or dato2:
            mask = pd.Series(False, index=conciliacion.index)
            if dato1:
                mask |= conciliacion["codigo_unido"].str.contains(dato1, na=False)
            if dato2:
                mask |= conciliacion["codigo_unido"].str.contains(dato2, na=False)
            conciliacion = conciliacion[mask]

        # -------------------
        # Exportar Excel
        # -------------------
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
            proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)
            base_conc.to_excel(writer, sheet_name="base_conc", index=False)

            # Agregar etiquetas de referencia en base_conc (L1, L2, M2)
            workbook  = writer.book
            worksheet = writer.sheets["base_conc"]
            worksheet.write("L1", "Datos a buscar")
            worksheet.write("L2", dato1)
            worksheet.write("M2", dato2)

            conciliacion.to_excel(writer, sheet_name="conciliacion", index=False)

        st.download_button(
            label="Descargar Excel procesado",
            data=output.getvalue(),
            file_name="conciliacion_resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
