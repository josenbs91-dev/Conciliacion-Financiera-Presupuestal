import streamlit as st
import pandas as pd
import io

st.title("Conciliación Financiera Presupuestal")

uploaded_file = st.file_uploader("📂 Sube el archivo Excel", type=["xlsx"])

if uploaded_file:
    # Leer conservando tipos originales (texto, fechas, números)
    df = pd.read_excel(uploaded_file, dtype=object)

    # Series numéricas para cálculos (no alteran el df original)
    haber_num = pd.to_numeric(df.get("haber"), errors="coerce").fillna(0)
    debe_num  = pd.to_numeric(df.get("debe"),  errors="coerce").fillna(0)

    # ---------------- PROCESO 1 ----------------
    p1_mask = df["mayor"].astype(str).str.startswith(("5", "4"), na=False)
    proceso1 = df.loc[p1_mask, ["mayor", "sub_cta", "clasificador"]].copy()
    proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
    proceso1 = proceso1[["mayor_subcta", "clasificador"]].drop_duplicates()

    # ---------------- PROCESO 2 ----------------
    # construir codigo_unido sin alterar formatos del resto
    df["codigo_unido"] = (
        df["mayor"].astype(str) + "-" +
        df["sub_cta"].astype(str) + "-" +
        df["clasificador"].astype(str)
    )

    # Filtro 1
    f1 = df[
        (df["tipo_ctb"].astype(str) == "1") &
        (haber_num != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "D"))
        )
    ].copy()
    f1["saldo"] = pd.to_numeric(f1.get("haber"), errors="coerce").fillna(0)

    # Filtro 2 (con mayor iniciando en 8501 o 8601)
    f2 = df[
        (df["tipo_ctb"].astype(str) == "2") &
        (debe_num != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "R"))
        ) &
        (
            df["mayor"].astype(str).str.startswith(("8501", "8601"), na=False)
        )
    ].copy()
    f2["saldo"] = pd.to_numeric(f2.get("debe"), errors="coerce").fillna(0)

    # Filtro 3
    f3 = df[
        (df["ciclo"] == "C") & (df["fase"] == "C") &
        (
            df["mayor"].astype(str).str.startswith(("5", "4", "8501", "8601"), na=False)
        )
    ].copy()
    f3["saldo"] = (
        pd.to_numeric(f3.get("haber"), errors="coerce").fillna(0) -
        pd.to_numeric(f3.get("debe"),  errors="coerce").fillna(0)
    )

    filtrado = pd.concat([f1, f2, f3], ignore_index=True)

    # Asegurar codigo_unido en filtrado (por si algún filtro no lo arrastra)
    if "codigo_unido" not in filtrado.columns:
        filtrado["codigo_unido"] = (
            filtrado["mayor"].astype(str) + "-" +
            filtrado["sub_cta"].astype(str) + "-" +
            filtrado["clasificador"].astype(str)
        )

    columnas_finales = [
        "codigo_unido",
        "nro_not_exp",
        "desc_documento",
        "nro_doc",
        "Fecha Contable",
        "desc_proveedor",
        "saldo",
    ]
    # Mantener solo columnas existentes para evitar KeyError si alguna faltase
    columnas_existentes = [c for c in columnas_finales if c in filtrado.columns]
    proceso2 = filtrado[columnas_existentes].copy()

    st.subheader("✅ Vistas previas")
    st.write("**Proceso 1**")
    st.dataframe(proceso1.head())
    st.write("**Proceso 2**")
    st.dataframe(proceso2.head())

    # ---------------- PROCESO 3 (Conciliación) ----------------
    conciliacion_bloques = []

    for _, fila in proceso1.iterrows():
        mayor_subcta = str(fila.get("mayor_subcta", ""))
        clasificador = str(fila.get("clasificador", ""))

        # Filtrar Proceso 2 por coincidencia en codigo_unido (regex desactivado)
        subset = proceso2[
            proceso2["codigo_unido"].astype(str).str.contains(mayor_subcta, na=False, regex=False) |
            proceso2["codigo_unido"].astype(str).str.contains(clasificador, na=False, regex=False)
        ].copy()

        if not subset.empty:
            # Agrupar por nro_not_exp (y demás columnas de contexto si existen)
            group_cols = [c for c in ["nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"] if c in subset.columns]

            # Listar todos los codigo_unido por grupo
            pivoted = (
                subset.groupby(group_cols, dropna=False)["codigo_unido"]
                .apply(lambda s: list(dict.fromkeys(s.tolist())))  # quita duplicados preservando orden
                .reset_index()
            )

            # Expandir en columnas horizontales
            if not pivoted.empty:
                lengths = pivoted["codigo_unido"].apply(lambda x: len(x) if isinstance(x, list) else 0)
                max_len_val = lengths.max() if not lengths.empty else 0
                max_len = int(max_len_val) if pd.notna(max_len_val) else 0

                for i in range(max_len):
                    pivoted[f"codigo_unido_{i+1}"] = pivoted["codigo_unido"].apply(
                        lambda x: x[i] if isinstance(x, list) and i < len(x) else None
                    )
                pivoted.drop(columns=["codigo_unido"], inplace=True)

                # Añadir columnas de referencia del grupo
                pivoted.insert(0, "grupo_mayor_subcta", mayor_subcta)
                pivoted.insert(1, "grupo_clasificador", clasificador)

                # Agregar bloque + 5 filas vacías
                conciliacion_bloques.append(pivoted)
                # 5 filas vacías (todas columnas del bloque)
                conciliacion_bloques.append(pd.DataFrame({col: [None]*5 for col in pivoted.columns}))

    if conciliacion_bloques:
        conciliacion = pd.concat(conciliacion_bloques, ignore_index=True)
    else:
        conciliacion = pd.DataFrame(columns=["grupo_mayor_subcta", "grupo_clasificador"] + columnas_existentes)

    # ---------------- EXPORTAR ----------------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
        # Original (opcional): si quieres incluirla, descomenta la línea siguiente:
        # df.to_excel(writer, sheet_name="Original", index=False)
        proceso1.to_excel(writer, sheet_name="Proceso1", index=False)
        proceso2.to_excel(writer, sheet_name="Proceso2", index=False)
        conciliacion.to_excel(writer, sheet_name="Conciliacion", index=False)

    st.download_button(
        label="📥 Descargar Excel Procesado",
        data=output.getvalue(),
        file_name="Conciliacion_Financiera.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
