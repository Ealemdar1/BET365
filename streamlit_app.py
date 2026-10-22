import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Gelişmiş Oran Analiz Sistemi", layout="wide")

st.title("📊 ORAN KUTBU (Sadeleştirilmiş Analiz Paneli)")
st.markdown("---")

BAHISCILER = {
    "Pinnacle": {
        "acilis":  {"H": "PSH",    "D": "PSD",    "A": "PSA"},
        "kapanis": {
            "H": "PSCH",
            "D": "PSCD",
            "A": "PSCA",
        },
    },
    "Bet365": {
        "acilis":  {"H": "B365H",  "D": "B365D",  "A": "B365A"},
        "kapanis": {
            "H": "B365CH",
            "D": "B365CD",
            "A": "B365CA",
        },
    },
    "Bwin": {
        "acilis":  {"H": "BWH",    "D": "BWD",    "A": "BWA"},
        "kapanis": {
            "H": "BWCH",
            "D": "BWCD",
            "A": "BWCA",
        },
    },
    "Interwetten": {
        "acilis":  {"H": "IWH",    "D": "IWD",    "A": "IWA"},
        "kapanis": {
            "H": "IWCH",
            "D": "IWCD",
            "A": "IWCA",
        },
    },
    "William Hill": {
        "acilis":  {"H": "WHH",    "D": "WHD",    "A": "WHA"},
        "kapanis": {
            "H": "WHCH",
            "D": "WHCD",
            "A": "WHCA",
        },
    },
    "VC Bet": {
        "acilis":  {"H": "VCH",    "D": "VCD",    "A": "VCA"},
        "kapanis": {
            "H": "VCCH",
            "D": "VCCD",
            "A": "VCCA",
        },
    },
    "Betvictor": {
        "acilis":  {"H": "BVH",    "D": "BVD",    "A": "BVA"},
        "kapanis": {
            "H": "BVCH",
            "D": "BVCD",
            "A": "BVCA",
        },
    },
    "Ortalama (Betbrain)": {
        "acilis":  {"H": "BbAvH",  "D": "BbAvD",  "A": "BbAvA"},
        "kapanis": {
            "H": "BbAvCH",
            "D": "BbAvCD",
            "A": "BbAvCA",
        },
    },
    "Maksimum (Betbrain)": {
        "acilis":  {"H": "BbMxH",  "D": "BbMxD",  "A": "BbMxA"},
        "kapanis": {
            "H": "BbMxCH",
            "D": "BbMxCD",
            "A": "BbMxCA",
        },
    },
}

MODE_ACILIS = "Sadece Açılış"
MODE_KAPANIS = "Sadece Kapanış"
MODE_VEYA = "Her İkisi (VEYA - biri yeterli)"
MODE_VE = "Her İkisi (VE - ikisi de uyumlu)"

uploaded_files = [
    "new_leagues_data.xlsx",
    "all-euro-data-2010-2011.xlsx", "all-euro-data-2011-2012.xlsx",
    "all-euro-data-2012-2013.xlsx", "all-euro-data-2013-2014.xlsx",
    "all-euro-data-2014-2015.xlsx", "all-euro-data-2015-2016.xlsx",
    "all-euro-data-2016-2017.xlsx", "all-euro-data-2017-2018.xlsx",
    "all-euro-data-2018-2019.xlsx", "all-euro-data-2019-2020.xlsx",
    "all-euro-data-2020-2021.xlsx", "all-euro-data-2021-2022.xlsx",
    "all-euro-data-2022-2023.xlsx", "all-euro-data-2023-2024.xlsx",
    "all-euro-data-2024-2025.xlsx", "all-euro-data-2025-2026.xlsx",
    "all-euro-data-2026-2027.xlsx"
]

lig_aciklamalari = {
    "D1": "D1 (Almanya Bundesliga)", "D2": "D2 (Almanya Bundesliga 2)",
    "E0": "E0 (İngiltere Premier Lig)", "E1": "E1 (İngiltere Championship)",
    "E2": "E2 (İngiltere League One)", "E3": "E3 (İngiltere League Two)",
    "SP1": "SP1 (İspanya La Liga)", "SP2": "SP2 (İspanya Segunda Division)",
    "I1": "I1 (İtalya Serie A)", "I2": "I2 (İtalya Serie B)",
    "F1": "F1 (Fransa Ligue 1)", "F2": "F2 (Fransa Ligue 2)",
    "N1": "N1 (Hollanda Eredivisie)", "B1": "B1 (Belçika Pro League)",
    "P1": "P1 (Portekiz Liga NOS)", "T1": "T1 (Türkiye Süper Ligi)",
    "SC0": "SC0 (İskoçya Premiership)", "SC1": "SC1 (İskoçya Championship)",
    "SC2": "SC2 (İskoçya League One)", "SC3": "SC3 (İskoçya League Two)",
    "G1": "G1 (Yunanistan Super League)", "EC": "EC (Avrupa Kupaları)",
    "CL": "CL (Şampiyonlar Ligi)",
    "ARG": "ARG (Arjantin Liga Profesional)", "AUT": "AUT (Avusturya Bundesliga)",
    "BRA": "BRA (Brezilya Serie A)", "CHN": "CHN (Çin Süper Ligi)",
    "DNK": "DNK (Danimarka Superliga)", "FIN": "FIN (Finlandiya Veikkausliiga)",
    "IRL": "IRL (İrlanda Premier Division)", "JPN": "JPN (Japonya J1 League)",
    "MEX": "MEX (Meksika Liga MX)", "NOR": "NOR (Norveç Eliteserien)",
    "POL": "POL (Polonya Ekstraklasa)", "ROU": "ROU (Romanya Liga I)",
    "RUS": "RUS (Rusya Premier Lig)", "SWE": "SWE (İsveç Allsvenskan)",
    "SWZ": "SWZ (İsviçre Süper Lig)", "USA": "USA (Amerika MLS)"
}

def taraf_belirle(skor_str):
    try:
        ev, dep = map(int, skor_str.split('-'))
        if ev > dep:
            return '1'
        elif ev < dep:
            return '2'
        else:
            return 'X'
    except:
        return '?'

@st.cache_data
def verileri_yukle_ve_birlestir(files):
    tum_veriler = []
    for file in files:
        if os.path.exists(file):
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                df_sheet = pd.read_excel(file, sheet_name=sheet_name)
                if not df_sheet.empty:
                    df_sheet['Source_File'] = file
                    temiz_kod = str(sheet_name).strip()
                    df_sheet['Source_Sheet'] = lig_aciklamalari.get(temiz_kod, temiz_kod)
                    tum_veriler.append(df_sheet)
    if tum_veriler:
        return pd.concat(tum_veriler, ignore_index=True, sort=False)
    return pd.DataFrame()

if uploaded_files:
    df_all_leagues = verileri_yukle_ve_birlestir(uploaded_files)
    if not df_all_leagues.empty:
        st.success(f"✅ {len(df_all_leagues)} arşiv kaydı birleştirildi!")
    else:
        st.warning("Sistemde okunacak arşiv dosyaları bulunamadı ya da dosyalar boş.")
        st.stop()
else:
    st.stop()

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    mod = st.radio("Analiz Modu", options=["Tek Bahisçi", "Herhangi Biri (Tüm Bahisçiler)"], horizontal=True)
with col_opt2:
    oran_tipi = st.radio("Oran Tipi", options=[MODE_ACILIS, MODE_KAPANIS, MODE_VEYA, MODE_VE], horizontal=True)

acilis_kullan = oran_tipi in [MODE_ACILIS, MODE_VEYA, MODE_VE]
kapanis_kullan = oran_tipi in [MODE_KAPANIS, MODE_VEYA, MODE_VE]

def bahisci_uygun_mu(isim, oran_tipi):
    sut = BAHISCILER[isim]
    ac_cols = list(sut["acilis"].values())
    kc_cols = list(sut["kapanis"].values())
    ac_exists = all(c in df_all_leagues.columns for c in ac_cols)
    kc_exists = all(c in df_all_leagues.columns for c in kc_cols)
    ac_ok = ac_exists and df_all_leagues[ac_cols].notna().any().any()
    kc_ok = kc_exists and df_all_leagues[kc_cols].notna().any().any()
    if oran_tipi == MODE_ACILIS: return ac_ok
    elif oran_tipi == MODE_KAPANIS: return kc_ok
    elif oran_tipi == MODE_VEYA: return ac_ok or kc_ok
    elif oran_tipi == MODE_VE: return ac_ok and kc_ok
    return False

mevcut_bahisciler = [isim for isim in BAHISCILER if bahisci_uygun_mu(isim, oran_tipi)]
if not mevcut_bahisciler:
    st.error("Seçilen kriterlere uygun veri seti bulunamadı.")
    st.stop()

if mod == "Tek Bahisçi":
    secilen_bahisci = st.selectbox("Bahisçi Seç", options=mevcut_bahisciler)
    aranacak_bahisciler = [secilen_bahisci]
else:
    aranacak_bahisciler = st.multiselect("Taranacak Bahisçiler", options=mevcut_bahisciler, default=mevcut_bahisciler)
    if not aranacak_bahisciler:
        aranacak_bahisciler = mevcut_bahisciler

ps_h = ps_d = ps_a = None
ps_h_k = ps_d_k = ps_a_k = None

if acilis_kullan:
    st.markdown("### 📈 Açılış Oranları")
    col1, col2, col3 = st.columns(3)
    with col1: ps_h = st.number_input("Ev (Açılış)", min_value=1.0, max_value=20.0, value=2.60, step=0.01)
    with col2: ps_d = st.number_input("Beraberlik (Açılış)", min_value=1.0, max_value=20.0, value=3.75, step=0.01)
    with col3: ps_a = st.number_input("Deplasman (Açılış)", min_value=1.0, max_value=20.0, value=2.37, step=0.01)

if kapanis_kullan:
    st.markdown("### 📉 Kapanış Oranları")
    col1, col2, col3 = st.columns(3)
    with col1: ps_h_k = st.number_input("Ev (Kapanış)", min_value=1.0, max_value=20.0, value=2.60, step=0.01)
    with col2: ps_d_k = st.number_input("Beraberlik (Kapanış)", min_value=1.0, max_value=20.0, value=3.75, step=0.01)
    with col3: ps_a_k = st.number_input("Deplasman (Kapanış)", min_value=1.0, max_value=20.0, value=2.37, step=0.01)

tolerans = st.slider("Oran Toleransı (±)", min_value=0.0, max_value=0.30, value=0.05, step=0.01)
mac_limiti = st.select_slider("Maksimum Maç Sınırı", options=[10, 20, 50, 100, 200, 500, 1000], value=100)

benzersiz_ligler = sorted(df_all_leagues['Source_Sheet'].dropna().unique().tolist())
secilen_ligler = st.sidebar.multiselect("Lig Filtrele", benzersiz_ligler)

if st.button("⚡ Analizi Başlat", use_container_width=True):
    df_temp = df_all_leagues.copy()
    if secilen_ligler:
        df_temp = df_temp[df_temp['Source_Sheet'].isin(secilen_ligler)]

    eslesen_satirlar = []
    for bahisci in aranacak_bahisciler:
        if bahisci not in BAHISCILER: continue
        sut = BAHISCILER[bahisci]
        ac_cols, kc_cols = sut["acilis"], sut["kapanis"]

        tmp = df_temp.copy()
        mask_ac = mask_kc = None

        if acilis_kullan:
            ac_h, ac_d, ac_a = ac_cols["H"], ac_cols["D"], ac_cols["A"]
            if all(c in tmp.columns for c in [ac_h, ac_d, ac_a]):
                for c in [ac_h, ac_d, ac_a]: tmp[c] = pd.to_numeric(tmp[c], errors='coerce')
                mask_ac = (tmp[ac_h].between(ps_h - tolerans, ps_h + tolerans) &
                           tmp[ac_d].between(ps_d - tolerans, ps_d + tolerans) &
                           tmp[ac_a].between(ps_a - tolerans, ps_a + tolerans))

        if kapanis_kullan:
            kc_h, kc_d, kc_a = kc_cols["H"], kc_cols["D"], kc_cols["A"]
            if all(c in tmp.columns for c in [kc_h, kc_d, kc_a]):
                for c in [kc_h, kc_d, kc_a]: tmp[c] = pd.to_numeric(tmp[c], errors='coerce')
                mask_kc = (tmp[kc_h].between(ps_h_k - tolerans, ps_h_k + tolerans) &
                           tmp[kc_d].between(ps_d_k - tolerans, ps_d_k + tolerans) &
                           tmp[kc_a].between(ps_a_k - tolerans, ps_a_k + tolerans))

        if oran_tipi == MODE_ACILIS: final_mask = mask_ac
        elif oran_tipi == MODE_KAPANIS: final_mask = mask_kc
        elif oran_tipi == MODE_VEYA:
            final_mask = (mask_ac | mask_kc) if (mask_ac is not None and mask_kc is not None) else (mask_ac if mask_ac is not None else mask_kc)
        elif oran_tipi == MODE_VE:
            final_mask = (mask_ac & mask_kc) if (mask_ac is not None and mask_kc is not None) else None
        else: final_mask = None

        if final_mask is None: continue
        matched = tmp[final_mask].copy()
        if not matched.empty:
            matched['Eslesen_Bahisci'] = bahisci
            eslesen_satirlar.append(matched)

    if not eslesen_satirlar:
        st.warning("Eşleşen hiçbir maç bulunamadı.")
    else: 
        birlesik = pd.concat(eslesen_satirlar, ignore_index=True)
        grup_kolonlari = [c for c in ['Date', 'HomeTeam', 'AwayTeam', 'Source_Sheet'] if c in birlesik.columns]

        if grup_kolonlari:
            agg_dict = {'Eslesen_Bahisci': lambda x: ', '.join(sorted(set(x)))}
            for c in ['HTHG', 'HTAG', 'FTHG', 'FTAG']:
                if c in birlesik.columns:
                    agg_dict[c] = 'first'
            final_tablo = birlesik.groupby(grup_kolonlari, as_index=False).agg(agg_dict)
        else:
            final_tablo = birlesik.copy()

        for col in ['HTHG', 'HTAG', 'FTHG', 'FTAG']:
            if col in final_tablo.columns:
                final_tablo[col] = pd.to_numeric(final_tablo[col], errors='coerce').fillna(0).astype(int)
            else:
                final_tablo[col] = 0

        final_tablo['İY'] = final_tablo['HTHG'].astype(str) + '-' + final_tablo['HTAG'].astype(str)
        final_tablo['MS'] = final_tablo['FTHG'].astype(str) + '-' + final_tablo['FTAG'].astype(str)

        if len(final_tablo) > mac_limiti:
            final_tablo = final_tablo.head(mac_limiti)

        st.subheader(f"🎯 {len(final_tablo)} Maç Gösteriliyor")
        st.dataframe(final_tablo, use_container_width=True)

        st.markdown("### 📊 Skor ve İstatistiki Dağılımlar")
        col_stat1, col_stat2, col_stat3 = st.columns(3)

        iy_dagilim = final_tablo['İY'].value_counts().reset_index()
        iy_dagilim.columns = ['İY Skoru', 'Adet']

        ms_dagilim = final_tablo['MS'].value_counts().reset_index()
        ms_dagilim.columns = ['MS Skoru', 'Adet']

        temp_copy = final_tablo.copy()
        temp_copy['İY/MS'] = temp_copy['İY'].apply(taraf_belirle) + '/' + temp_copy['MS'].apply(taraf_belirle)
        iyms_dagilim = temp_copy['İY/MS'].value_counts().reset_index()
        iyms_dagilim.columns = ['İY/MS', 'Adet']

        with col_stat1:
            st.markdown("⚽ **İY Skor Dağılımı**")
            st.dataframe(iy_dagilim, use_container_width=True)
        with col_stat2:
            st.markdown("🏆 **MS Skor Dağılımı**")
            st.dataframe(ms_dagilim, use_container_width=True)
        with col_stat3:
            st.markdown("📈 **İY/MS Kombinasyonu (Taraf)**")
            st.dataframe(iyms_dagilim, use_container_width=True)
