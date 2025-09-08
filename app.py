import streamlit as st
import pandas as pd

st.title("Conciliación Financiera Presupuestal - Procesos 1 y 2")

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer archivo Excel como objetos (mantiene texto, fechas, números)
    df = pd.read_excel(uploaded_file, dtype=object)

    # Normalizar numéricos
    for col in ["haber", "debe"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    st.subheader("👀 Vista previa datos originales")
    st.dataframe(df.head())

    # --------------------------
    # PROCESO 1
    # --------------------------
    proceso1 = df[
        df["mayor"].astype(str).str.startswith(("5", "4"))
    ].copy()

    proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
    proceso1 = proceso1[["mayor_subcta", "clasificador"]].drop_duplicates()

    # --------------------------
    # PROCESO 2 (Filtros anteriores)
    # --------------------------
    # Filtro 1
    filtro1 = df[
        (df["tipo_ctb"].astype(str) == "1") &
        (df["haber"] != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "D"))
        )
    ].copy()
    filtro1["saldo"] = filtro1["haber"]

    # Filtro 2
    filtro2 = df[
        (df["tipo_ctb"].astype(str) == "2") &
        (df["debe"] != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "R"))
        )
    ].copy()
    filtro2["saldo"] = filtro2["debe"]

    # Filtro 3
    filtro3 = df[
        (df["ciclo"] == "C") & (df["fase"] == "C") &
        (
            df["mayor"].astype(str).str.s
