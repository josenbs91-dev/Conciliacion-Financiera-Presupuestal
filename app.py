import streamlit as st
import pandas as pd

st.title("Conciliación Financiera Presupuestal - Filtros Personalizados")

# Subir archivo
uploaded_file = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer Excel
    df = pd.read_excel(uploaded_file)

    st.subheader("👀 Vista previa de los datos originales")
    st.dataframe(df.head())

    # --- FILTRO 1 ---
    filtro1 = df[
        (df["tipo_ctb"] == 1) &
        (df["haber"] != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "D"))
        )
    ]
    filtro1 = filtro1.copy()
    filtro1["saldo"] = filtro1["haber"]

    # --- FILTRO 2 ---
    filtro2 = df[
        (df["tipo_ctb"] == 2) &
        (df["debe"] != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "R"))
        )
    ]
    filtro2 = filtro2.copy()
    filtro2["saldo"] = filtro2["debe"]

    # --- FILTRO 3 ---
    filtro3 = df[
        (df["ciclo"] == "C") & (df["fase"] == "C") &
        (
            df["mayor"].astype(str).str.startswith("5") |
            df["mayor"].astype(str).str.startswith("4") |
            df["mayor"].astype(str).str.startswith("8501") |
            df["mayor"].astype(str).str.startswith("8601")
        )
    ]
    filtro3 = filtro3.copy()
    # Para este caso saldo puede ser haber - debe, ajusta según lo que requieras
    filtro3["saldo"] = filtro3["haber"] - filtro3["debe"]

    # Unir los tres filtros en orden
    filtrado = pd.concat([filtro1, filtro2, filtro3])

    # Crear columna unida mayor-sub_cta-clasificador
    filtrado["codigo_unido"] = (
        filtrado["mayor"].astype(str) + "-" +
        filtrado["sub_cta"].astype(str) + "-" +
        filtrado["clasificador"].astype(str)
    )

    # Seleccionar columnas finales
    resultado = filtrado[
        ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
         "Fecha Contable", "desc_proveedor", "saldo"]
    ]

    st.subheader("📊 Datos filtrados")
    st.dataframe(resultado)

    st.write(f"✅ Registros filtrados: {len(resultado)}")

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
