import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Conciliación Financiera y Presupuestal")

# Subir archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer archivo
    df = pd.read_excel(uploaded_file, dtype=str)

    # -------------------------
    # PROCESO 1
    # -------------------------
    proceso1 = df[df["mayor"].str.startswith(("5", "4"), na=False)].copy()
    proceso1["mayor_subcta"] = proceso1["mayor"] + "-" + proceso1["sub_cta"]
    proceso1 = proceso1[["mayor_subcta", "clasificador"]]

    # -------------------------
    # PROCESO 2
    # -------------------------
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
        & (df["mayor"].str.startswith(("8501", "8601"), na=False))
    ]

    # Filtro 3
    filtro3 = df[
        (df["ciclo"] == "C")
        & (df["fase"] == "C")
        & (
            df["mayor"].str.startswith(("5", "4", "8501", "8601"), na=False)
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

    # -------------------------
    # PROCESO 3 (mejorado: codigo_unido en columnas horizontales)
    # -------------------------
    conciliacion_data = []

    for _, row in proceso1.iterrows():
        mayor_subcta = str(row["mayor_subcta"])
        clasificador = str(row["clasificador"])

        mask = (
            proceso2["codigo_unido"].astype(str).str.contains(mayor_subcta, na=False)
            | proceso2["codigo_unido"].astype(str).str.contains(clasificador, na=False)
        )
        filtro = proceso2[mask].copy()

        if not filtro.empty:
            # Agrupar por los datos fijos
            agrupado = (
                filtro.groupby(
                    [
                        "nro_not_exp",
                        "desc_documento",
                        "nro_doc",
                        "Fecha Contable",
                        "desc_proveedor",
                        "saldo",
                    ]
                )["codigo_unido"]
                .apply(list)
                .reset_index()
            )

            # Expandir codigo_unido en columnas horizontales
            max_codigos = agrupado["codigo_unido"].apply(len).max()
            for i in range(max_codigos):
                agrupado[f"codigo_unido_{i+1}"] = agrupado["codigo_unido"].apply(
                    lambda x: x[i] if i < len(x) else None
                )

            agrupado = agrupado.drop(columns=["codigo_unido"])

            conciliacion_data.append(agrupado)
            conciliacion_data.append(
                pd.DataFrame([[""] * agrupado.shape[1]] * 5, columns=agrupado.columns)
            )

    if conciliacion_data:
        conciliacion_final = pd.concat(conciliacion_data, ignore_index=True)
    else:
        conciliacion_final = pd.DataFrame()

    # -------------------------
    # EXPORTAR EXCEL
    # -------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)
        proceso2.to_excel(writer, sheet_name="Proceso 2", index=False)
        conciliacion_final.to_excel(writer, sheet_name="Conciliacion", index=False)

    st.success("✅ Procesos generados correctamente")

    st.download_button(
        label="📥 Descargar Excel",
        data=output.getvalue(),
        file_name="procesos_conciliacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
