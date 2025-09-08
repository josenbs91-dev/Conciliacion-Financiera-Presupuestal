import streamlit as st
import pandas as pd

st.title("Conciliación Financiera Presupuestal - Filtros Excel")

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer archivo Excel sin forzar tipos
    df = pd.read_excel(uploaded_file, dtype=object)

    # Normalizar columnas numéricas (haber y debe)
    for col in ["haber", "debe"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    st.subheader("👀 Vista previa datos originales")
    st.dataframe(df.head())

    # --------------------------
    # FILTRO 1
    # --------------------------
    filtro1 = df[
        (df["tipo_ctb"].astype(str) == "1") &
        (df["haber"] != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "D"))
        )
    ].copy()
    filtro1["saldo"] = filtro1["haber"]

    # --------------------------
    # FILTRO 2
    # --------------------------
    filtro2 = df[
        (df["tipo_ctb"].astype(str) == "2") &
        (df["debe"] != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "R"))
        )
    ].copy()
    filtro2["saldo"] = filtro2["debe"]

    # --------------------------
    # FILTRO 3
    # --------------------------
    filtro3 = df[
        (df["ciclo"] == "C") & (df["fase"] == "C") &
        (
            df["mayor"].astype(str).str.startswith("5") |
            df["mayor"].astype(str).str.startswith("4") |
            df["mayor"].astype(str).str.startswith("8501") |
            df["mayor"].astype(str).str.startswith("8601")
        )
    ].copy()
    filtro3["saldo"] = pd.to_numeric(filtro3["haber"], errors="coerce").fillna(0) - \
                       pd.to_numeric(filtro3["debe"], errors="coerce").fillna(0)

    # --------------------------
    # UNIR FILTROS EN ORDEN
    # --------------------------
    filtrado = pd.concat([filtro1, filtro2, filtro3])

    # Crear columna unida mayor-sub_cta-clasificador
    filtrado["codigo_unido"] = (
        filtrado["mayor"].astype(str) + "-" +
        filtrado["sub_cta"].astype(str) + "-" +
        filtrado["clasificador"].astype(str)
    )

    # Selección final de columnas
    columnas_finales = [
        "codigo_unido", "nro_not_exp", "desc_documento",
        "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"
    ]
    resultado = filtrado[columnas_finales]

    st.subheader("📊 Datos filtrados")
    st.dataframe(resultado)

    st.write(f"✅ Total registros exportados: {len(resultado)}")

    # --------------------------
    # EXPORTAR A EXCEL
    # --------------------------
    output_file = "resultado_filtrado.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Original", index=False)
        resultado.to_excel(writer, sheet_name="Filtrado", index=False)

    # Botón de descarga
    if not resultado.empty:
        with open(output_file, "rb") as f:
            st.download_button(
                "⬇️ Descargar Excel filtrado",
                f,
                file_name="resultado_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.warning("⚠️ No se encontraron registros que cumplan los filtros.")
