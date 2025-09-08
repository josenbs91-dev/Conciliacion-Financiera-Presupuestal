import streamlit as st
import pandas as pd

st.title("Conciliación Financiera Presupuestal - Filtrado Excel")

# Subir archivo
uploaded_file = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer Excel
    df = pd.read_excel(uploaded_file)

    st.subheader("👀 Vista previa de los datos originales")
    st.dataframe(df.head())

    # --- FILTROS ---
    # tipo_ctb = 1 con haber ≠ 0
    filtro1 = df[(df["tipo_ctb"] == 1) & (df["haber"] != 0)]

    # tipo_ctb = 2 con debe ≠ 0
    filtro2 = df[(df["tipo_ctb"] == 2) & (df["debe"] != 0)]

    # Unir ambos filtros
    filtrado = pd.concat([filtro1, filtro2])

    # Crear columna saldo
    filtrado["saldo"] = filtrado.apply(
        lambda x: x["haber"] if x["tipo_ctb"] == 1 else x["debe"], axis=1
    )

    # Crear columna unida mayor-sub_cta-clasificador
    filtrado["codigo_unido"] = (
        filtrado["mayor"].astype(str) + "-" +
        filtrado["sub_cta"].astype(str) + "-" +
        filtrado["clasificador"].astype(str)
    )

    # --- FILTRO EXTRA CICLO/FASE ---
    condiciones = (
        ((filtrado["ciclo"] == "G") & (filtrado["fase"] == "D")) |
        ((filtrado["ciclo"] == "I") & (filtrado["fase"] == "R")) |
        ((filtrado["ciclo"] == "C") & (filtrado["fase"] == "C"))
    )
    filtrado = filtrado[condiciones]

    # Seleccionar columnas finales
    resultado = filtrado[
        ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
         "Fecha Contable", "desc_proveedor", "saldo"]
    ]

    st.subheader("📊 Datos filtrados")
    st.dataframe(resultado)

    # Guardar en nueva hoja de Excel
    output_file = "resultado_filtrado.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Original", index=False)
        resultado.to_excel(writer, sheet_name="Filtrado", index=False)

    with open(output_file, "rb") as f:
        st.download_button(
            "⬇️ Descargar Excel con hoja filtrada",
            f,
            file_name="resultado_filtrado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
