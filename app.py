import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

# Cargar archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Leer todas las hojas
        xls = pd.ExcelFile(uploaded_file)
        hoja = xls.sheet_names[0]
        df = pd.read_excel(xls, hoja, dtype=str)

        # Asegurar que numéricos se lean con su formato
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass

        # -------------------------
        # PROCESO 1
        # -------------------------
        proceso1 = df.copy()
        proceso1 = proceso1[(proceso1["mayor"].str.startswith(("5", "4")))].copy()
        proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
        proceso1 = proceso1[["mayor_subcta", "clasificador"]]

        # -------------------------
        # PROCESO 2
        # -------------------------
        df["codigo_unido"] = (
            df["mayor"].astype(str) + "-" +
            df["sub_cta"].astype(str) + "-" +
            df["clasificador"].astype(str)
        )

        # Filtro 1
        filtro1 = df[
            (df["tipo_ctb"] == "1") &
            (pd.to_numeric(df["haber"], errors="coerce") != 0) &
            (
                ((df["ciclo"] == "G") & (df["fase"] == "D")) |
                ((df["ciclo"] == "I") & (df["fase"] == "D"))
            )
        ]

        # Filtro 2
        filtro2 = df[
            (df["tipo_ctb"] == "2") &
            (pd.to_numeric(df["debe"], errors="coerce") != 0) &
            (
                ((df["ciclo"] == "G") & (df["fase"] == "D")) |
                ((df["ciclo"] == "I") & (df["fase"] == "R"))
            ) &
            (df["mayor"].str.startswith(("8501", "8601")))
        ]

        # Filtro 3
        filtro3 = df[
            (df["ciclo"] == "C") & (df["fase"] == "C") &
            (
                df["mayor"].str.startswith(("5", "4", "8501", "8601"))
            )
        ]

        # Unir resultados
        proceso2 = pd.concat([filtro1, filtro2, filtro3], ignore_index=True)
        proceso2 = proceso2[
            ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
             "Fecha Contable", "desc_proveedor", "saldo"]
        ]

        # -------------------------
        # PROCESO 3
        # -------------------------
        conciliacion_bloques = []
        group_base = ["nro_not_exp", "desc_documento", "nro_doc",
                      "Fecha Contable", "desc_proveedor", "saldo"]

        for _, fila in proceso1.iterrows():
            mayor_subcta = str(fila.get("mayor_subcta", ""))
            clasificador = str(fila.get("clasificador", ""))

            if proceso2.empty:
                continue

            mask = (
                proceso2["codigo_unido"].astype(str).str.contains(mayor_subcta, na=False, regex=False)
                | proceso2["codigo_unido"].astype(str).str.contains(clasificador, na=False, regex=False)
            )
            subset = proceso2[mask].copy()

            if subset.empty:
                continue

            # Pivotear: codigo_unido como columnas
            pivoted = subset.pivot_table(
                index=[c for c in group_base if c in subset.columns],
                columns="codigo_unido",
                values="codigo_unido",
                aggfunc=lambda x: 1  # marcar con 1 en vez de repetir el código
            ).reset_index()

            # Insertar columnas de identificación del bloque
            pivoted.insert(0, "grupo_mayor_subcta", mayor_subcta)
            pivoted.insert(1, "grupo_clasificador", clasificador)

            conciliacion_bloques.append(pivoted)

            # 5 filas vacías para separación
            empty_block = pd.DataFrame({col: [None] * 5 for col in pivoted.columns})
            conciliacion_bloques.append(empty_block)

        if conciliacion_bloques:
            conciliacion = pd.concat(conciliacion_bloques, ignore_index=True)
        else:
            conciliacion = pd.DataFrame(columns=["grupo_mayor_subcta", "grupo_clasificador"] + group_base)

        # -------------------------
        # Exportar a Excel
        # -------------------------
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
            proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)
            proceso2.to_excel(writer, sheet_name="Proceso 2", index=False)
            conciliacion.to_excel(writer, sheet_name="Conciliacion", index=False)

        st.download_button(
            label="📥 Descargar resultados en Excel",
            data=output.getvalue(),
            file_name="procesos_conciliacion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
