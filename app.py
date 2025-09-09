import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='Conciliación - Procesos Excel', layout='wide')
st.title('App de conciliación - subir Excel y ejecutar procesos')

st.markdown('Regla general: los datos se leen inicialmente como texto para preservar formatos. '
            'Cuando se necesite comparar importes se convierten temporalmente a numéricos; nunca se sobrescribe la copia textual original.')

uploaded_file = st.file_uploader('Sube tu archivo Excel (.xls / .xlsx)', type=['xls', 'xlsx'])

col1, col2 = st.columns(2)
with col1:
    filtro_1 = st.text_input('Filtro 1 — texto a buscar en codigo_unido')
with col2:
    filtro_2 = st.text_input('Filtro 2 — texto a buscar en codigo_unido')

st.write('Pulsa el botón para ejecutar el filtro y los procesos pedidos. Se creará un nuevo archivo Excel con las hojas generadas.')

if uploaded_file is None:
    st.info('Por favor sube un archivo Excel para continuar.')
    st.stop()

if st.button('Ejecutar procesos y generar Excel'):
    try:
        xls = pd.read_excel(uploaded_file, sheet_name=None, dtype=str, engine='openpyxl')
    except Exception as e:
        st.error(f'Error al leer el Excel: {e}')
        st.stop()

    sheet_names = {name.lower(): name for name in xls.keys()}
    if 'conciliacion1' not in sheet_names:
        st.error("El archivo debe contener una hoja llamada 'conciliacion1' (verifica nombre de hoja).")
        st.stop()

    conciliacion_raw = xls[sheet_names['conciliacion1']].copy()
    conciliacion_txt = conciliacion_raw.astype(object).where(pd.notnull(conciliacion_raw), '')

    def safe_col(df, colname):
        for c in df.columns:
            if c.strip().lower() == colname.strip().lower():
                return c
        return None

    getcol = lambda df, name: safe_col(df, name)

    mayor_col = getcol(conciliacion_txt, 'mayor')
    subcta_col = getcol(conciliacion_txt, 'sub_cta') or getcol(conciliacion_txt, 'subcta')
    clas_col = getcol(conciliacion_txt, 'clasificador') or getcol(conciliacion_txt, 'clasificadores')

    proceso1 = pd.DataFrame()
    if mayor_col and subcta_col:
        df_temp = conciliacion_txt[[mayor_col, subcta_col]].copy()
        if clas_col:
            df_temp['clasificador'] = conciliacion_txt[clas_col].fillna('')
        else:
            df_temp['clasificador'] = ''

        def join_may_sub(row):
            mayor = str(row[mayor_col]).strip()
            sub = str(row[subcta_col]).strip()
            if mayor.startswith(('5', '4')):
                return f"{mayor}.{sub}"
            else:
                return None

        df_temp['mayor_subcta'] = df_temp.apply(join_may_sub, axis=1)
        proceso1 = df_temp[['mayor_subcta', 'clasificador']].dropna(subset=['mayor_subcta']).copy()
        proceso1.columns = ['mayor_subcta', 'clasificador']
    else:
        proceso1 = pd.DataFrame(columns=['mayor_subcta', 'clasificador'])

    col_map = {
        'nro_not_exp': ['nro_not_exp', 'nro_not', 'nro_notificacion'],
        'desc_documento': ['desc_documento', 'descripcion_documento', 'desc_doc'],
        'nro_doc': ['nro_doc', 'numero_doc', 'nro_documento'],
        'Fecha Contable': ['Fecha Contable', 'fecha contable', 'fecha_contable'],
        'desc_proveedor': ['desc_proveedor', 'proveedor', 'desc_prov'],
        'debe': ['debe', 'debitos'],
        'haber': ['haber', 'creditos'],
        'saldo': ['saldo']
    }

    proceso2 = conciliacion_txt.copy()
    if not clas_col:
        proceso2['clasificador'] = ''
        clas_col = 'clasificador'

    if mayor_col and subcta_col:
        proceso2['mayor'] = proceso2[mayor_col].astype(str).fillna('')
        proceso2['sub_cta'] = proceso2[subcta_col].astype(str).fillna('')
        proceso2['clasificador'] = proceso2[clas_col].astype(str).fillna('')
        proceso2['codigo_unido'] = proceso2['mayor'].str.strip() + '.' + proceso2['sub_cta'].str.strip() + '-' + proceso2['clasificador'].str.strip()
    else:
        proceso2['codigo_unido'] = ''

    out_cols = ['codigo_unido', 'nro_not_exp', 'desc_documento', 'nro_doc', 'Fecha Contable', 'desc_proveedor', 'debe', 'haber', 'saldo']
    proceso2_out = pd.DataFrame()
    proceso2_out['codigo_unido'] = proceso2['codigo_unido']

    for out in out_cols[1:]:
        candidates = col_map.get(out, [out])
        found = None
        for cand in candidates:
            c = getcol(conciliacion_txt, cand)
            if c:
                found = c
                break
        if found:
            proceso2_out[out] = proceso2[found].astype(object)
        else:
            proceso2_out[out] = ''

    proc2 = proceso2_out.copy()

    def to_numeric_col(df, col):
        return pd.to_numeric(df[col].replace('', '0').astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce').fillna(0)

    proc2['debe_num'] = to_numeric_col(proc2, 'debe')
    proc2['haber_num'] = to_numeric_col(proc2, 'haber')
    proc2['saldo_num'] = to_numeric_col(proc2, 'saldo')

    tipo_ctb_col = getcol(conciliacion_txt, 'tipo_ctb')
    ciclo_col = getcol(conciliacion_txt, 'ciclo')
    fase_col = getcol(conciliacion_txt, 'fase')

    try:
        mayor_orig = conciliacion_txt[mayor_col].astype(str) if mayor_col else pd.Series(['']*len(proc2), index=proc2.index)
        tipo_ctb_orig = conciliacion_txt[tipo_ctb_col] if tipo_ctb_col else pd.Series(['']*len(proc2), index=proc2.index)
        ciclo_orig = conciliacion_txt[ciclo_col] if ciclo_col else pd.Series(['']*len(proc2), index=proc2.index)
        fase_orig = conciliacion_txt[fase_col] if fase_col else pd.Series(['']*len(proc2), index=proc2.index)
    except Exception:
        mayor_orig = pd.Series(['']*len(proc2), index=proc2.index)
        tipo_ctb_orig = pd.Series(['']*len(proc2), index=proc2.index)
        ciclo_orig = pd.Series(['']*len(proc2), index=proc2.index)
        fase_orig = pd.Series(['']*len(proc2), index=proc2.index)

    proc2['_mayor_orig'] = mayor_orig.astype(str).fillna('')
    proc2['_tipo_ctb'] = tipo_ctb_orig.astype(str).fillna('')
    proc2['_ciclo'] = ciclo_orig.astype(str).fillna('')
    proc2['_fase'] = fase_orig.astype(str).fillna('')

    r1 = proc2[(proc2['_tipo_ctb'].str.strip() == '1') &
               (proc2['_ciclo'].str.strip().str.upper() == 'G') &
               (proc2['_fase'].str.strip().str.upper() == 'D') &
               (proc2['debe_num'] != 0)].copy()

    r2 = proc2[(proc2['_tipo_ctb'].str.strip() == '1') &
               (proc2['_ciclo'].str.strip().str.upper() == 'I') &
               (proc2['_fase'].str.strip().str.upper() == 'D') &
               (proc2['haber_num'] != 0)].copy()

    r3 = proc2[(proc2['_tipo_ctb'].str.strip() == '2') &
               (proc2['saldo_num'] != 0) &
               (((proc2['_ciclo'].str.strip().str.upper() == 'G') & (proc2['_fase'].str.strip().str.upper() == 'D')) |
                ((proc2['_ciclo'].str.strip().str.upper() == 'I') & (proc2['_fase'].str.strip().str.upper() == 'R'))) &
               (proc2['_mayor_orig'].str.strip().str.startswith(('8501', '8601')))].copy()

    mayor_starts_mask = proc2['_mayor_orig'].str.strip().str.startswith(('5', '4', '8501', '8601'))
    r4 = proc2[(proc2['_ciclo'].str.strip().str.upper() == 'C') &
               (proc2['_fase'].str.strip().str.upper() == 'C') &
               (mayor_starts_mask)].copy()

    tablafinal = pd.concat([r1, r2, r3, r4], ignore_index=True, sort=False)

    for col in ['debe_num', 'haber_num', 'saldo_num', '_mayor_orig', '_tipo_ctb', '_ciclo', '_fase']:
        if col in tablafinal.columns:
            tablafinal.drop(columns=[col], inplace=True)

    conciliacion1_df = tablafinal.copy()

    if (filtro_1 or filtro_2):
        mask = pd.Series([False]*len(conciliacion1_df))
        if filtro_1:
            mask = mask | conciliacion1_df['codigo_unido'].astype(str).str.contains(filtro_1, case=False, na=False)
        if filtro_2:
            mask = mask | conciliacion1_df['codigo_unido'].astype(str).str.contains(filtro_2, case=False, na=False)
        resultado_filtro = conciliacion1_df[mask].copy()
    else:
        resultado_filtro = conciliacion1_df.copy()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for name, df in xls.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)

        proceso1.to_excel(writer, sheet_name='proceso1'[:31], index=False)
        proceso2_out.to_excel(writer, sheet_name='proceso2'[:31], index=False)
        conciliacion1_df.to_excel(writer, sheet_name='conciliacion1_new'[:31], index=False)
        resultado_filtro.to_excel(writer, sheet_name='resultado_filtro'[:31], index=False)

        writer.save()
        processed_data = output.getvalue()

    st.success('Procesos completados. Descarga el archivo generado con las nuevas hojas.')
    st.download_button('Descargar Excel procesado', data=processed_data, file_name='conciliacion_procesada.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    st.markdown('**Notas:**\n- Se preservan los formatos de entrada leyendo inicialmente todo como texto.\n- Para comparaciones numéricas se convierten columnas temporalmente.\n- Si tus nombres de columnas difieren, el app intenta encontrarlos de forma insensible a mayúsculas/minúsculas.\n- Si falta alguna columna revisa el nombre en la hoja `conciliacion1`.')
