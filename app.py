import streamlit as st
import pandas as pd

st.title("Conciliación Financiera Presupuestal - Filtros Excel")

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer archivo Excel conservando formatos
    df = pd.read_excel(uploaded_file, dtype=str)
    
    # Convertir columnas numéricas de forma segura
    for col in ["haber", "debe"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    st.subheader("👀 Vista previa datos originales")
    st.dataframe(df.head())

    # --------------------------
    # FILTRO 1
    # --------------------------
    filtro1 = df[
        (df["tipo_ctb"] == "1") &
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
        (df["tipo_ctb"] == "2") &
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
    # UNIR FILTR
