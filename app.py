import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Conciliación Financiera y Presupuestal - Procesos 1,2,3")

uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # --- Leer manteniendo tipos originales ---
    df = pd.read_excel(uploaded_file, dtype=object)

    # Series numéricas auxiliares (no modifican df)
    haber_num = pd.to_numeric(df.get("haber"), errors="coerce").fillna(0)
    debe_num  = pd.to_numeric(df.get("debe"),  errors="coerce").fillna(0)

    # -------------------------
    # PROCESO 1: mayor-sub_cta y clasificador (mayor que empiece con 5 o 4)
    # -------------------------
    p1_mask = df["mayor"].astype(str).str.startswith(("5", "4"), na=False)
    proceso1 = df.loc[p1_mask, ["mayor", "sub_cta", "clasificador"]].copy()
    proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
    proceso1 = proceso1[["mayor_subcta", "clasificador"]].drop_duplicates().reset_index(drop=True)

    # -------------------------
    # PROCESO 2: aplicar 3 filtros y crear codigo_unido
    # -------------------------
    # crear codigo_unido en df (no altera otros tipos)
    df["codigo_unido"] = df["mayor"].astype(str) + "-" + df["sub_cta"].astype(str) + "-" + df["clasificador"].astype(str)

    # Filtro 1: tipo_ctb=1, haber != 0, (ciclo G & fase D) o (ciclo I & fase D)
    f1 = df[
        (df["tipo_ctb"].astype(str) == "1") &
        (haber_num != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "D"))
        )
    ].copy()
    f1["saldo"] = pd.to_numeric(f1.get("haber"), errors="coerce").fillna(0)

    # Filtro 2: tipo_ctb=2, debe != 0, (ciclo G & fase D) o (ciclo I & fase R), mayor empieza 8501|8601
    f2 = df[
        (df["tipo_ctb"].astype(str) == "2") &
        (debe_num != 0) &
        (
            ((df["ciclo"] == "G") & (df["fase"] == "D")) |
            ((df["ciclo"] == "I") & (df["fase"] == "R"))
        ) &
        (df["mayor"].astype(str).str.startswith(("8501", "8601"), na=False))
    ].copy()
    f2["saldo"] = pd.to_numeric(f2.get("debe"), errors="coerce").fillna(0)

    # Filtro 3: ciclo C & fase C & mayor empieza con 5|4|8501|8601
    f3 = df[
        (df["ciclo"] == "C") &
        (df["fase"] == "C") &
        (df["mayor"].astype(str).str.startswith(("5", "4", "8501", "8601"), na=False))
    ].copy()
    f3["saldo"] = pd.to_numeric(f3.get("haber"), errors="coerce").fillna(0) - pd.to_numeric(f3.get("debe"), errors="coerce").fillna(0)

    # Concatenar en orden
    filtrados_list = [x for x in (f1, f2, f3) if x is not None and not x.empty]
    if filtrados_list:
        filtrado = pd.concat(filtrados_list, ignore_index=True)
    else:
        filtrado = pd.DataFrame()

    # Asegurar codigo_unido en filtrado
    if not filtrado.empty and "codigo_unido" not in filtrado.columns:
        filtrado["codigo_unido"] = filtrado["mayor"].astype(str) + "-" + filtrado["sub_cta"].astype(str) + "-" + filtrado["clasificador"].astype(str)

    # Columnas finales deseadas para Proceso2 (mantener solo las que existan)
    columnas_finales = ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]
    columnas_existentes = [c for c in columnas_finales if c in filtrado.columns]
    if not filtrado.empty:
        proceso2 = filtrado[columnas_existentes].copy()
    else:
        proceso2 = pd.DataFrame(columns=columnas_existentes)

    # Mostrar previsualizaciones
    st.subheader("Proceso 1 (muestra)")
    st.dataframe(proceso1.head())
    st.subheader("Proceso 2 (muestra)")
    st.dataframe(proceso2.head())

    # -------------------------
    # PROCESO 3: Conciliación - pivotear codigo_unido horizontal por nro_not_exp
    # -------------------------
    conciliacion_bloques = []
    # Columnas fijas que usaremos para agrupar (si existen)
    group_base = ["nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]

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

        # determinar columnas de agrupamiento realmente presentes
        group_cols = [c for c in group_base if c in subset.columns]
        if not group_cols:
            # si no hay columnas fijas, agrupar solo por codigo_unido (pero esto es raro)
            subset = subset.reset_index(drop=True)
            group_cols = []

        # agrupar y coleccionar los codigo_unido por grupo
        if group_cols:
            agrupado = subset.groupby(group_cols, dropna=False)["codigo_unido"].apply(
                lambda s: list(dict.fromkeys([str(x) for x in s.tolist()]))
            ).reset_index()
        else:
            # si no hay group_cols, crear tabla simple con listas
            agrupado = subset.groupby("codigo_unido", dropna=False)["codigo_unido"].apply(lambda s: list(dict.fromkeys([str(x) for x in s.tolist()]))).reset_index()
            agrupado.rename(columns={0: "codigo_unido"}, inplace=True)

        # calcular máximo seguro de códigos por fila
        if "codigo_unido" in agrupado.columns:
            lengths = agrupado["codigo_unido"].apply(lambda x: len(x) if isinstance(x, list) else 0)
            max_len_val = lengths.max() if not lengths.empty else 0
            try:
                max_len = int(max_len_val) if pd.notna(max_len_val) else 0
            except Exception:
                max_len = 0
        else:
            max_len = 0

        # expandir en columnas horizontales
        for i in range(max_len):
            agrupado[f"codigo_unido_{i+1}"] = agrupado["codigo_unido"].apply(
                lambda x: x[i] if isinstance(x, list) and i < len(x) else None
            )

        if "codigo_unido" in agrupado.columns:
            agrupado = agrupado.drop(columns=["codigo_unido"])

        # insertar columnas identificadoras del bloque
        agrupado.insert(0, "grupo_mayor_subcta", mayor_subcta)
        agrupado.insert(1, "grupo_clasificador", clasificador)

        # añadir bloque y luego 5 filas vacías con las mismas columnas
        conciliacion_bloques.append(agrupado)
        empty_block = pd.DataFrame({col: [None] * 5 for col in agrupado.columns})
        conciliacion_bloques.append(empty_block)

    if conciliacion_bloques:
        conciliacion = pd.concat(conciliacion_bloques, ignore_index=True)
    else:
        # crear DataFrame vacío con columnas esperadas
        conciliacion_cols = ["grupo_mayor_subcta", "grupo_clasificador"] + [c for c in group_base if c in proceso2.columns]
        conciliacion = pd.DataFrame(columns=conciliacion_cols)

    # -------------------------
    # EXPORTAR TODO A EXCEL (openpyxl)
    # -------------------------
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        # opcional: incluir original si lo deseas
        df.to_excel(writer, sheet_name="Original", index=False)
        proceso1.to_excel(writer, sheet_name="Proceso 1", index=False)
        proceso2.to_excel(writer, sheet_name="Proceso 2", index=False)
        conciliacion.to_excel(writer, sheet_name="Conciliacion", index=False)

    out.seek(0)
    st.success("✅ Procesos generados correctamente")
    st.download_button(
        "📥 Descargar Excel con Procesos",
        data=out.getvalue(),
        file_name="Conciliacion_Financiera_Procesos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
