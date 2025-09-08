import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

uploaded_file = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer archivo original
    df = pd.read_excel(uploaded_file, dtype=str)  # Mantener formato como texto
    st.success("Archivo cargado correctamente")

    # ---------------- PROCESO 1 ----------------
    proceso1 = df[df["mayor"].str.startswith(("5", "4"))].copy()
    proceso1["mayor_subcta"] = proceso1["mayor"] + "-" + proceso1["sub_cta"]
    proceso1 = proceso1[["mayor_subcta", "clasificador"]]

    # ---------------- PROCESO 2 ----------------
    df["codigo_unido"] = df["mayor"] + "-" + df["sub_cta"] + "-" + df["clasificador"]

    # Filtro 1
    filtro1 = df[
        (df["tipo_ctb"] == "1")
        & (df["haber"].astype(float) != 0)
        & (
            ((df["ciclo"] == "G") & (df["fase"] == "D"))
            | ((df["ciclo"] == "I") & (df["fase"] == "D"))
        )
    ]

    # Filtro 2
    filtro2 = df[
        (df["tipo_ctb"] == "2")
        & (df["debe"].astype(float) != 0)
        & (
            ((df["ciclo"] == "G") & (df["fase"] == "D"))
            | ((df["ciclo"] == "I") & (df["fase"] == "R"))
        )
        & (df["mayor"].str.startswith(("8501", "8601")))
    ]

    # Filtro 3
    filtro3 = df[
        (df["ciclo"] == "C")
        & (df["fase"] == "C")
        & (
            df["mayor"].str.startswith(("5", "4", "8501", "8601"))
        )
    ]

    proceso2 = pd.concat([filtro1, filtro2, filtro3], ignore_index=True)
    proceso2 = proceso2[
        [
            "codigo_unido",
            "nro_not_exp",
            "desc_documento",
            "nro_doc",
            "Fecha Contable",
            "desc_proveedor",
            "saldo",
        ]
    ]

    # ---------------- PROCESO 3 ----------------
    conciliacion_tables = []
    for _, fila in proceso1.iterrows():
        mayor_subcta = fila["mayor_subcta"]
        clasificador = fila["clasificador"]

        subset = proceso2[
            proceso2["codigo_unido"].str.contains(mayor_subcta)
            | proceso2["codigo_unido"].str.contains(clasificador)
        ].copy()

        if not subset.empty:
            # Expandir codigo_unido horizontal por nro_not_exp
            pivoted = (
                subset.groupby(
                    ["nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]
                )["codigo_unido"]
                .apply(list)
                .reset_index()
            )

            # Expandir listas en columnas
            max_len = pivoted["codigo_unido"].apply(len).max()
            for i in range(max_len):
                pivoted[f"codigo_unido_{i+1}"] = pivoted["codigo_unido"].apply(
                    lambda x: x[i] if i < len(x) else None
                )
            pivoted.drop(columns=["codigo_unido"], inplace=True)

            conciliacion_tables.append(
                pd.DataFrame(
                    {col: [""] * 5 for col in pivoted.columns}
                )
            )  # Espaciado
            conciliacion_tables.append(pivoted)

    if conciliacion_tables:
        conciliacion = pd.concat(conciliacion_tables, ignore_index=True)
    else:
        conciliacion = pd.DataFrame()

    # ---------------- EXPORTAR ----------------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        proceso1.to_excel(writer, sheet_name="Proceso1", index=False)
        proceso2.to_excel(writer, sheet_name="Proceso2", index=False)
        conciliacion.to_excel(writer, sheet_name="Conciliacion", index=False)

    st.download_button(
        label="📥 Descargar Excel Procesado",
        data=output.getvalue(),
        file_name="Conciliacion_Financiera.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
