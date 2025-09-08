import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Conciliación Financiera y Presupuestal (Procesos 1,2,3)")

uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # --- Leer manteniendo tipos originales ---
        df = pd.read_excel(uploaded_file, dtype=object)

        # Helpers: series seguras (devuelven Series de longitud correcta aunque falte la columna)
        def safe_series(df, col):
            return df[col].astype(str) if col in df.columns else pd.Series([""] * len(df), index=df.index)

        # Series numéricas auxiliares (no modifican df original)
        haber_num = pd.to_numeric(df.get("haber"), errors="coerce").fillna(0)
        debe_num  = pd.to_numeric(df.get("debe"),  errors="coerce").fillna(0)

        # -------------------------
        # PROCESO 1: mayor_subcta + clasificador (mayor que empiece con 5 o 4)
        # -------------------------
        mayor_s = safe_series(df, "mayor")
        sub_cta_s = safe_series(df, "sub_cta")
        clasif_s = safe_series(df, "clasificador")

        p1_mask = mayor_s.str.startswith(("5", "4"), na=False)
        cols_p1 = []
        for c in ["mayor", "sub_cta", "clasificador"]:
            if c in df.columns:
                cols_p1.append(c)
            else:
                # Si falta, crear columna vacía temporal para seleccionar
                df[c] = ""
                cols_p1.append(c)

        proceso1 = df.loc[p1_mask, cols_p1].copy()
        proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
        proceso1 = proceso1[["mayor_subcta", "clasificador"]].drop_duplicates().reset_index(drop=True)

        # -------------------------
        # PROCESO 2: crear codigo_unido y aplicar filtros
        # -------------------------
        # Asegurar columnas necesarias existen (si faltan, se crean vacías para no romper)
        for c in ["mayor", "sub_cta", "clasificador", "tipo_ctb", "ciclo", "fase", "nro_not_exp",
                  "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]:
            if c not in df.columns:
                df[c] = ""

        # crear codigo_unido (no altera formatos originales de otras columnas)
        df["codigo_unido"] = df["mayor"].astype(str) + "-" + df["sub_cta"].astype(str) + "-" + df["clasificador"].astype(str)

        tipo_ctb_s = safe_series(df, "tipo_ctb")
        ciclo_s = safe_series(df, "ciclo")
        fase_s = safe_series(df, "fase")

        # Filtro1: tipo_ctb=1, haber !=0, (ciclo G & fase D) o (ciclo I & fase D)
        f1_mask = (
            (tipo_ctb_s == "1") &
            (haber_num != 0) &
            (
                ((ciclo_s == "G") & (fase_s == "D")) |
                ((ciclo_s == "I") & (fase_s == "D"))
            )
        )
        f1 = df.loc[f1_mask].copy()
        if not f1.empty:
            f1["saldo"] = pd.to_numeric(f1.get("haber"), errors="coerce").fillna(0)

        # Filtro2: tipo_ctb=2, debe !=0, (ciclo G & fase D) o (ciclo I & fase R), mayor empieza 8501|8601
        mayor_s_full = safe_series(df, "mayor")
        f2_mask = (
            (tipo_ctb_s == "2") &
            (debe_num != 0) &
            (
                ((ciclo_s == "G") & (fase_s == "D")) |
                ((ciclo_s == "I") & (fase_s == "R"))
            ) &
            (mayor_s_full.str.startswith(("8501", "8601"), na=False))
        )
        f2 = df.loc[f2_mask].copy()
        if not f2.empty:
            f2["saldo"] = pd.to_numeric(f2.get("debe"), errors="coerce").fillna(0)

        # Filtro3: ciclo C & fase C & mayor empieza con 5|4|8501|8601
        f3_mask = (
            (ciclo_s == "C") &
            (fase_s == "C") &
            (mayor_s_full.str.startswith(("5", "4", "8501", "8601"), na=False))
        )
        f3 = df.loc[f3_mask].copy()
        if not f3.empty:
            f3["saldo"] = pd.to_numeric(f3.get("haber"), errors="coerce").fillna(0) - pd.to_numeric(f3.get("debe"), errors="coerce").fillna(0)

        # Concatenar filtros en orden 1,2,3
        filtrados = [d for d in (f1, f2, f3) if (d is not None) and (not d.empty)]
        if filtrados:
            filtrado = pd.concat(filtrados, ignore_index=True)
        else:
            filtrado = pd.DataFrame(columns=df.columns)

        # Seleccionar columnas finales manteniendo existencia
        columnas_finales = ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]
        columnas_existentes = [c for c in columnas_finales if c in filtrado.columns]
        proceso2 = filtrado[columnas_existentes].copy() if not filtrado.empty else pd.DataFrame(columns=columnas_existentes)

        # -------------------------
        # PROCESO 3: convertir codigo_unido en encabezados (marcar con 1)
        # -------------------------
        conciliacion_bloques = []
        group_base = ["nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]

        # si Proceso1 vacío no iteramos
        for _, fila in proceso1.iterrows():
            mayor_subcta = str(fila.get("mayor_subcta", ""))
            clasificador = str(fila.get("clasificador", ""))

            if proceso2.empty:
                continue

            mask = (
                proceso2["codigo_unido"].astype(str).str.contains(mayor_subcta, na=False, regex=False)
                | proceso2["codigo_unido"].astype(str).str.contains(clasificador, na=False, regex=False)
            )
            subset = proceso2.loc[mask].copy()
            if subset.empty:
                continue

            # columnas de agrupamiento existentes
            group_cols = [c for c in group_base if c in subset.columns]
            if not group_cols:
                # si no hay columnas fijas, saltamos este bloque
                continue

            # pivotear: cada codigo_unido -> columna, valor 1 si existe
            # Primero, para asegurar una única fila por grupo, agregamos una columna auxiliar con 1
            subset["_flag"] = 1
            pivot = subset.pivot_table(
                index=group_cols,
                columns="codigo_unido",
                values="_flag",
                aggfunc="max",
                fill_value=0
            ).reset_index()

            # Aplanar nombres de columnas (pivot crea MultiIndex en columnas si hay nombres)
            pivot.columns = [str(col) if not isinstance(col, tuple) else str(col[1]) for col in pivot.columns]

            # Insertar columnas de identificación del bloque al inicio
            pivot.insert(0, "grupo_mayor_subcta", mayor_subcta)
            pivot.insert(1, "grupo_clasificador", clasificador)

            conciliacion_bloques.append(pivot)
            # agregar 5 filas vacías (misma estructura de columnas)
            empty_block = pd.DataFrame({c: [None] * 5 for c in pivot.columns})
            conciliacion_bloques.append(empty_block)

        if conciliacion_bloques:
            conciliacion = pd.concat(conciliacion_bloques, ignore_index=True)
        else:
            conciliacion = pd.DataFrame(columns=["grupo_mayor_subcta", "grupo_clasificador"] + [c for c in group_base if c in proceso2.columns])

        # -------------------------
        # EXPORTAR A EXCEL (openpyxl)
        # -------------------------
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
            # opcional: incluir original si quieres
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

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo:")
        st.exception(e)
