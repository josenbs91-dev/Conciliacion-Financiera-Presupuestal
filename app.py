import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Conciliación Financiera y Presupuestal (Procesos 1,2,3)")

uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # --- Leer manteniendo tipos originales ---
        df = pd.read_excel(uploaded_file, dtype=object)

        # Helpers: series seguras
        def safe_series(df, col):
            return df[col].astype(str) if col in df.columns else pd.Series([""] * len(df), index=df.index)

        # Series numéricas auxiliares
        haber_num = pd.to_numeric(df.get("haber"), errors="coerce").fillna(0)
        debe_num  = pd.to_numeric(df.get("debe"),  errors="coerce").fillna(0)

        # -------------------------
        # PROCESO 1
        # -------------------------
        mayor_s = safe_series(df, "mayor")
        sub_cta_s = safe_series(df, "sub_cta")
        clasif_s = safe_series(df, "clasificador")

        p1_mask = mayor_s.str.startswith(("5", "4"), na=False)
        for c in ["mayor", "sub_cta", "clasificador"]:
            if c not in df.columns:
                df[c] = ""
        proceso1 = df.loc[p1_mask, ["mayor", "sub_cta", "clasificador"]].copy()
        proceso1["mayor_subcta"] = proceso1["mayor"].astype(str) + "-" + proceso1["sub_cta"].astype(str)
        proceso1 = proceso1[["mayor_subcta", "clasificador"]].drop_duplicates().reset_index(drop=True)

        # -------------------------
        # PROCESO 2
        # -------------------------
        for c in ["mayor", "sub_cta", "clasificador", "tipo_ctb", "ciclo", "fase",
                  "nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor", "saldo"]:
            if c not in df.columns:
                df[c] = ""

        df["codigo_unido"] = df["mayor"].astype(str) + "-" + df["sub_cta"].astype(str) + "-" + df["clasificador"].astype(str)

        tipo_ctb_s = safe_series(df, "tipo_ctb")
        ciclo_s = safe_series(df, "ciclo")
        fase_s = safe_series(df, "fase")

        # Filtro1
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

        # Filtro2
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

        # Filtro3
        f3_mask = (
            (ciclo_s == "C") &
            (fase_s == "C") &
            (mayor_s_full.str.startswith(("5", "4", "8501", "8601"), na=False))
        )
        f3 = df.loc[f3_mask].copy()
        if not f3.empty:
            f3["saldo"] = (
                pd.to_numeric(f3.get("haber"), errors="coerce").fillna(0)
                - pd.to_numeric(f3.get("debe"), errors="coerce").fillna(0)
            )

        # Concatenar
        filtrados = [d for d in (f1, f2, f3) if (d is not None) and (not d.empty)]
        if filtrados:
            filtrado = pd.concat(filtrados, ignore_index=True)
        else:
            filtrado = pd.DataFrame(columns=df.columns)

        columnas_finales = ["codigo_unido", "nro_not_exp", "desc_documento", "nro_doc",
                            "Fecha Contable", "desc_proveedor", "saldo"]
        columnas_existentes = [c for c in columnas_finales if c in filtrado.columns]
        proceso2 = filtrado[columnas_existentes].copy() if not filtrado.empty else pd.DataFrame(columns=columnas_existentes)

        # -------------------------
        # PROCESO 3
        # -------------------------
        conciliacion_bloques = []
        group_base = ["nro_not_exp", "desc_documento", "nro_doc", "Fecha Contable", "desc_proveedor"]

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

            # Pivot: filas = nro_not_exp y datos base; columnas = codigo_unido; valores = sum saldo
            pivot = subset.pivot_table(
                index=[c for c in group_base if c in subset.columns],
                columns="codigo_unido",
                values="saldo",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            pivot.insert(0, "grupo_mayor_subcta", mayor_subcta)
            pivot.insert(1, "grupo_clasificador", clasificador)

            conciliacion_bloques.append(pivot)
            empty_block = pd.DataFrame({c: [None] * 5 for c in pivot.columns})
            conciliacion_bloques.append(empty_block)

        if conciliacion_bloques:
            conciliacion = pd.concat(conciliacion_bloques, ignore_index=True)
        else:
            conciliacion = pd.DataFrame(columns=["grupo_mayor_subcta", "grupo_clasificador"] + group_base)

        # -------------------------
        # EXPORTAR
        # -------------------------
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
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
