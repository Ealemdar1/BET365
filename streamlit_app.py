import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from fpdf import FPDF

st.set_page_config(page_title="Gelişmiş Oran Analiz Sistemi", layout="wide")

# =====================================================
# GÜVENLİK VE GİRİŞ ŞİFRESİ SİSTEMİ
# =====================================================
def check_password():
    """Kullanıcı doğru şifre girene kadar True dönmez."""
    if "authorized" not in st.session_state:
        st.session_state.authorized = False

    if st.session_state.authorized:
        return True

    st.markdown("""
    <style>
        .login-box {
            background-color: #1a202c;
            padding: 30px;
            border-radius: 12px;
            border: 1px solid #2d3748;
            max-width: 400px;
            margin: 100px auto;
            text-align: center;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        }
    </style>
    """)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.subheader("🔒 Sefin Kuponu Portal Girişi")
    st.write("Devam etmek için lütfen giriş şifresini giriniz.")

    # Şifre girdi alanı
    password_input = st.text_input("Şifre", type="password", key="portal_pass_input")

    # Şifre kontrolü (Kullanıcı tarafından belirlenen şifre: "225960")
    if st.button("Giriş Yap", use_container_width=True):
        if password_input == "225960":
            st.session_state.authorized = True
            st.rerun()
        else:
            st.error("❌ Hatalı şifre girdiniz!")

    st.markdown('</div>', unsafe_allow_html=True)
    return False

# Şifre kontrolünü çalıştır
if check_password():
    st.title("📊 ORAN KUTBU (Bet365)")
    st.markdown("---")

    # PDF için Türkçe karakter dönüştürücü
    def tr_to_ascii(text):
        replacements = {
            'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
            'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c',
            '🔥': ''
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    # MODERN KART TASARIMI
    def generate_modern_card(title, count, total, flames):
        yuzde = (count / total) * 100 if total > 0 else 0
        flame_display = flames if flames else "-"

        html = (
            f'<div style="background-color: #1a202c; border: 1px solid #2d3748; border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">'
            f'<div style="display: flex; justify-content: space-between; align-items: center;">'
            f'<span style="color: #a0aec0; font-weight: 600; font-size: 14px;">{title}</span>'
            f'<span style="color: #718096; font-size: 13px;">{count}/{total}</span>'
            f'</div>'
            f'<div style="font-size: 28px; line-height: 1; min-height: 32px; color: #10b981; font-weight: bold;">'
            f'{flame_display}'
            f'</div>'
            f'<div style="width: 100%; height: 6px; background-color: #2d3748; border-radius: 3px; overflow: hidden;">'
            f'<div style="width: {yuzde}%; height: 100%; background-color: #10b981; border-radius: 3px;"></div>'
            f'</div>'
            f'</div>'
        )
        return html

    # ÖZET DASHBOARD KARTLARI
    def generate_summary_dashboard(total_matches, avg_distance):
        html = (
            f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 25px;">'
            f'<div style="background-color: #1a202c; border: 1px solid #3b82f6; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.15);">'
            f'<div style="color: #93c5fd; font-weight: 600; font-size: 15px; margin-bottom: 8px;">📋 Analiz Edilen Maç Sayısı</div>'
            f'<div style="font-size: 36px; color: #3b82f6; font-weight: bold;">{total_matches} Adet</div>'
            f'<div style="color: #64748b; font-size: 12px; margin-top: 5px;">En yakın oran eşleşmesine sahip toplam maç</div>'
            f'</div>'
            f'<div style="background-color: #1a202c; border: 1px solid #f59e0b; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(245, 158, 11, 0.15);">'
            f'<div style="color: #fde047; font-weight: 600; font-size: 15px; margin-bottom: 8px;">📏 Ortalama Yakınlık Derecesi (Mesafe)</div>'
            f'<div style="font-size: 36px; color: #f59e0b; font-weight: bold;">{avg_distance:.4f}</div>'
            f'<div style="color: #64748b; font-size: 12px; margin-top: 5px;">Sıfıra yakın değerler daha iyi bir eşleşmeyi gösterir</div>'
            f'</div>'
            f'</div>'
        )
        return html

    # Tüm 2010-2027 Excel Verileri ve Yeni Eklenen Liglerin excel dosyası
    uploaded_files = [
        "new_leagues_data.xlsx",
        "all-euro-data-2010-2011.xlsx",
        "all-euro-data-2011-2012.xlsx",
        "all-euro-data-2012-2013.xlsx",
        "all-euro-data-2013-2014.xlsx",
        "all-euro-data-2014-2015.xlsx",
        "all-euro-data-2015-2016.xlsx",
        "all-euro-data-2016-2017.xlsx",
        "all-euro-data-2017-2018.xlsx",
        "all-euro-data-2018-2019.xlsx",
        "all-euro-data-2019-2020.xlsx",
        "all-euro-data-2020-2021.xlsx",
        "all-euro-data-2021-2022.xlsx",
        "all-euro-data-2022-2023.xlsx",
        "all-euro-data-2023-2024.xlsx",
        "all-euro-data-2024-2025.xlsx",
        "all-euro-data-2025-2026.xlsx",
        "all-euro-data-2026-2027.xlsx"
    ]

    # Tüm Avrupa ve Yeni Eklenen Dünya Ligleri Açıklama Sözlüğü
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
        # Yeni Eklenen Ligler
        "ARG": "ARG (Arjantin Liga Profesional)",
        "AUT": "AUT (Avusturya Bundesliga)",
        "BRA": "BRA (Brezilya Serie A)",
        "CHN": "CHN (Çin Süper Ligi)",
        "DNK": "DNK (Danimarka Superliga)",
        "FIN": "FIN (Finlandiya Veikkausliiga)",
        "IRL": "IRL (İrlanda Premier Division)",
        "JPN": "JPN (Japonya J1 League)",
        "MEX": "MEX (Meksika Liga MX)",
        "NOR": "NOR (Norveç Eliteserien)",
        "POL": "POL (Polonya Ekstraklasa)",
        "ROU": "ROU (Romanya Liga I)",
        "RUS": "RUS (Rusya Premier Lig)",
        "SWE": "SWE (İsveç Allsvenskan)",
        "SWZ": "SWZ (İsviçre Süper Lig)",
        "USA": "USA (Amerika MLS)"
    }

    def taraf_belirle(skor_str):
        try:
            ev, dep = map(int, skor_str.split('-'))
            if ev > dep: return '1'
            elif ev < dep: return '2'
            else: return 'X'
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
            st.success(f"✅ {len(uploaded_files)} kaynak dosyası başarıyla tarandı ve toplam {len(df_all_leagues)} arşiv kaydı birleştirildi!")
        else:
            st.warning("Sistemde okunacak arşiv dosyaları bulunamadı ya da dosyalar boş.")
    else:
        st.info("💡 Lütfen analize başlamak için Excel dosyalarınızı hazırlayın.")
        st.stop()

    # =====================================================
    # MOBİL UYUMLU KOMPAKT YAN YANA ORAN GİRİŞ ALANI (Bet365)
    # =====================================================
    st.markdown("### 🎯 Bet365 Hedef Oranlarını Girin")

    # Başlık Sütunları
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("**📥 Açılış Oranları (Bet365)**")
    with col_h2:
        st.markdown("**📤 Kapanış Oranları (Bet365)**")

    # 1. Ev Sahibi Oranları
    col1, col2 = st.columns(2)
    with col1:
        b365h = st.number_input("Ev Sahibi (B365H)", min_value=1.0, max_value=20.0, value=2.60, step=0.01)
    with col2:
        b365ch = st.number_input("Ev Sahibi (B365CH)", min_value=1.0, max_value=20.0, value=2.75, step=0.01)

    st.markdown("<hr style='margin: 8px 0px; border-color: rgba(49, 51, 63, 0.2);'>", unsafe_allow_html=True)

    # 2. Beraberlik Oranları
    col3, col4 = st.columns(2)
    with col3:
        b365d = st.number_input("Beraberlik (B365D)", min_value=1.0, max_value=20.0, value=3.75, step=0.01)
    with col4:
        b365cd = st.number_input("Beraberlik (B365CD)", min_value=1.0, max_value=20.0, value=3.75, step=0.01)

    st.markdown("<hr style='margin: 8px 0px; border-color: rgba(49, 51, 63, 0.2);'>", unsafe_allow_html=True)

    # 3. Deplasman Oranları
    col5, col6 = st.columns(2)
    with col5:
        b365a = st.number_input("Deplasman (B365A)", min_value=1.0, max_value=20.0, value=2.37, step=0.01)
    with col6:
        b365ca = st.number_input("Deplasman (B365CA)", min_value=1.0, max_value=20.0, value=2.35, step=0.01)

    # Lig ve Limit Filtreleri (Sol Panel)
    st.sidebar.header("🌍 Filtreler")
    benzersiz_ligler = sorted(df_all_leagues['Source_Sheet'].dropna().unique().tolist()) if not df_all_leagues.empty else []
    secilen_ligler = st.sidebar.multiselect("Lig Filtrele", benzersiz_ligler)
    limit_val = st.sidebar.slider("📋 En Yakın Maç Sayısı", min_value=5, max_value=50, value=20)

    # ANALİZ YAP BUTONU TETİKLEME VE SEANS HAFIZASI
    if "analiz_yapildi" not in st.session_state:
        st.session_state.analiz_yapildi = False

    if st.button("⚡ Analizi Başlat", use_container_width=True):
        df_temp = df_all_leagues.copy()

        if secilen_ligler:
            df_temp = df_temp[df_temp['Source_Sheet'].isin(secilen_ligler)]

        # Bet365 Oran Sütunları
        oran_sutunlari = ['B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA']
        for col in oran_sutunlari:
            df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce')
        df_temp = df_temp.dropna(subset=oran_sutunlari)

        if df_temp.empty:
            st.warning("Seçilen kriterlere uygun Bet365 oran verisi bulunan maç kalmadı.")
        else:
            hedef = np.array([b365h, b365d, b365a, b365ch, b365cd, b365ca])
            mesafeler = []
            progress_bar = st.progress(0)
            total_rows = len(df_temp)

            for i, (idx, row) in enumerate(df_temp.iterrows()):
                mevcut = np.array([row['B365H'], row['B365D'], row['B365A'], row['B365CH'], row['B365CD'], row['B365CA']])
                mesafe = np.linalg.norm(mevcut - hedef)
                mesafeler.append((idx, round(mesafe, 4)))
                if i % 1000 == 0 or i == total_rows - 1:
                    progress_bar.progress(min((i + 1) / total_rows, 1.0))
            progress_bar.empty()

            mesafeler.sort(key=lambda x: x[1])
            en_yakin_indeksler = [x[0] for x in mesafeler[:limit_val]]
            en_yakin_mesafeler = [x[1] for x in mesafeler[:limit_val]]

            sonuc_df = df_temp.loc[en_yakin_indeksler].copy()
            sonuc_df['Oran_Farki_Mesafe'] = en_yakin_mesafeler

            for col in ['HTHG', 'HTAG', 'FTHG', 'FTAG']:
                if col in sonuc_df.columns:
                    sonuc_df[col] = pd.to_numeric(sonuc_df[col], errors='coerce').fillna(0).astype(int)

            sonuc_df['İY'] = sonuc_df['HTHG'].astype(str) + '-' + sonuc_df['HTAG'].astype(str)
            sonuc_df['MS'] = sonuc_df['FTHG'].astype(str) + '-' + sonuc_df['FTAG'].astype(str)

            gosterilecek_kolonlar = ['Date', 'Source_Sheet', 'HomeTeam', 'AwayTeam', 'B365H', 'B365D', 'B365A', 'B365CH', 'B365CD', 'B365CA', 'Oran_Farki_Mesafe', 'İY', 'MS']
            final_tablo = sonuc_df[[c for c in gosterilecek_kolonlar if c in sonuc_df.columns]]

            st.session_state.final_tablo = final_tablo
            st.session_state.analiz_yapildi = True

    # Eğer analiz yapılmışsa sonuçları session_state'den okuyup çiziyoruz
    if st.session_state.analiz_yapildi:
        final_tablo = st.session_state.final_tablo

        # --- ÖZET DASHBOARD KARTLARI ---
        avg_dist_val = final_tablo['Oran_Farki_Mesafe'].mean() if 'Oran_Farki_Mesafe' in final_tablo.columns else 0.0
        st.markdown(generate_summary_dashboard(len(final_tablo), avg_dist_val), unsafe_allow_html=True)

        st.subheader(f"🎯 En Yakın {len(final_tablo)} Maç")
        st.dataframe(final_tablo, use_container_width=True)

        st.markdown("### 📊 Skor ve İstatistiki Dağılımlar")
        col_stat1, col_stat2, col_stat3 = st.columns(3)

        iy_dagilim = final_tablo['İY'].value_counts().reset_index().rename(columns={'İY': 'Adet'})
        iy_dagilim.columns = ['İY Skoru', 'Adet']

        ms_dagilim = final_tablo['MS'].value_counts().reset_index().rename(columns={'MS': 'Adet'})
        ms_dagilim.columns = ['MS Skoru', 'Adet']

        temp_copy = final_tablo.copy()
        temp_copy['İY/MS'] = temp_copy['İY'].apply(taraf_belirle) + '/' + temp_copy['MS'].apply(taraf_belirle)
        iyms_dagilim = temp_copy['İY/MS'].value_counts().reset_index().rename(columns={'İY/MS': 'Adet'})
        iyms_dagilim.columns = ['İY/MS', 'Adet']

        with col_stat1:
            st.markdown("⚽ İY Skor Dağılımı")
            st.dataframe(iy_dagilim, use_container_width=True)
        with col_stat2:
            st.markdown("🏆 MS Skor Dağılımı")
            st.dataframe(ms_dagilim, use_container_width=True)
        with col_stat3:
            st.markdown("📈 İY/MS Kombinasyonu")
            st.dataframe(iyms_dagilim, use_container_width=True)

        ideal_tercihler = []
        surpriz_tercihler = []

        # MS ÖZEL BAHİS
        st.markdown("---")
        st.markdown("### 🔥 Maç Sonu (MS) Özel Bahis Dağılımı")
        st.caption(f"Son {len(final_tablo)} maç üzerinden hesaplanmıştır. (Alevler: 10-14 maç=1, 15-16 maç=2, 17+ maç=3)")
        temp_gol = final_tablo.copy()
        temp_gol['Toplam_Gol'] = temp_gol['MS'].apply(lambda s: sum(int(x.strip()) for x in s.split('-')) if isinstance(s, str) else 0)
        temp_gol['KG_Var'] = temp_gol['MS'].apply(lambda s: all(int(x)>0 for x in s.split('-')) if isinstance(s, str) and '-' in s else False)

        if len(temp_gol) > 0:
            toplam_mac = len(temp_gol)
            html_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'

            ust_25_adet = int((temp_gol['Toplam_Gol'] >= 3).sum())
            alev_25 = "".join(["🔥" for _ in range(3 if ust_25_adet >= 17 else 2 if ust_25_adet >= 15 else 1 if ust_25_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS 2.5 Üst", ust_25_adet, toplam_mac, alev_25)
            if alev_25: ideal_tercihler.append(f"2.5 Ust - {ust_25_adet} Mac {alev_25}")

            alt_25_adet = int((temp_gol['Toplam_Gol'] <= 2).sum())
            alev_alt_25 = "".join(["🔥" for _ in range(3 if alt_25_adet >= 17 else 2 if alt_25_adet >= 15 else 1 if alt_25_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS 2.5 Alt", alt_25_adet, toplam_mac, alev_alt_25)
            if alev_alt_25: ideal_tercihler.append(f"2.5 Alt - {alt_25_adet} Mac {alev_alt_25}")

            ust_55_adet = int((temp_gol['Toplam_Gol'] >= 6).sum())
            alev_55 = "".join(["🔥" for _ in range(3 if ust_55_adet >= 17 else 2 if ust_55_adet >= 15 else 1 if ust_55_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS 5.5 Üst", ust_55_adet, toplam_mac, alev_55)
            if alev_55: ideal_tercihler.append(f"5.5 Ust - {ust_55_adet} Mac {alev_55}")

            kg_adet = int(temp_gol['KG_Var'].sum())
            alev_kg = "".join(["🔥" for _ in range(3 if kg_adet >= 17 else 2 if kg_adet >= 15 else 1 if kg_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS KG Var", kg_adet, toplam_mac, alev_kg)
            if alev_kg: ideal_tercihler.append(f"KG Var - {kg_adet} Mac {alev_kg}")

            html_cards += '</div>'
            st.markdown(html_cards, unsafe_allow_html=True)

        # İY ÖZEL BAHİS
        st.markdown("---")
        st.markdown("### ⚽ İlk Yarı (İY) Özel Bahis Dağılımı")
        st.caption(f"İlk yarı skorlarına göre hesaplanmıştır. (Alevler: 10-14 maç=1, 15-16 maç=2, 17+ maç=3)")
        temp_gol['IY_Toplam_Gol'] = temp_gol['İY'].apply(lambda s: sum(int(x.strip()) for x in s.split('-')) if isinstance(s, str) else 0)
        temp_gol['IY_KG_Var'] = temp_gol['İY'].apply(lambda s: all(int(x)>0 for x in s.split('-')) if isinstance(s, str) and '-' in s else False)
        temp_gol['IY_Taraf'] = temp_gol['İY'].apply(taraf_belirle)

        html_iy_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
        for baslik, adet in [("İY 0.5 Üst", int((temp_gol['IY_Toplam_Gol'] >= 1).sum())), ("İY 1.5 Üst", int((temp_gol['IY_Toplam_Gol'] >= 2).sum())), ("İY KG Var", int(temp_gol['IY_KG_Var'].sum()))]:
            alev = 3 if adet >= 17 else 2 if adet >= 15 else 1 if adet >= 10 else 0
            alev_str = "".join(["🔥" for _ in range(alev)])
            html_iy_cards += generate_modern_card(baslik, adet, toplam_mac, alev_str)
            if alev > 0: ideal_tercihler.append(f"{baslik} - {adet} Mac {alev_str}")
        html_iy_cards += '</div>'
        st.markdown(html_iy_cards, unsafe_allow_html=True)

        # İY SONUÇ DAĞILIMI
        st.markdown("---")
        st.markdown("### 🎯 İlk Yarı (İY) Sonuç Dağılımı (1 - X - 2)")
        st.caption(f"İlk yarı skorlarına göre hesaplanmıştır. (Alevler: 10-14 maç=1, 15-16 maç=2, 17+ maç=3)")
        html_iy_sonuc_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
        for baslik, adet in [("İY Ev Sahibi (1)", int((temp_gol['IY_Taraf'] == '1').sum())), ("İY Beraberlik (X)", int((temp_gol['IY_Taraf'] == 'X').sum())), ("İY Deplasman (2)", int((temp_gol['IY_Taraf'] == '2').sum()))]:
            alev = 3 if adet >= 17 else 2 if adet >= 15 else 1 if adet >= 10 else 0
            alev_str = "".join(["🔥" for _ in range(alev)])
            html_iy_sonuc_cards += generate_modern_card(baslik, adet, toplam_mac, alev_str)
            if alev > 0: ideal_tercihler.append(f"{baslik} - {adet} Mac {alev_str}")
        html_iy_sonuc_cards += '</div>'
        st.markdown(html_iy_sonuc_cards, unsafe_allow_html=True)

        # İY/MS ÖZEL SONUÇ DAĞILIMI
        st.markdown("---")
        st.markdown("### 🔄 İY/MS Özel Sonuç Dağılımı")
        st.caption(f"Ters (2/1, 1/2): 2 maç=1, 3 maç=2, 4+ maç=3 Alev | Dönüşler (X/X, 1/X, 2/X): 7+ maç Alevli (7-9=1, 10-12=2, 13+=3)")
        temp_gol['IY_MS'] = temp_gol['IY_Taraf'] + '/' + temp_gol['MS'].apply(taraf_belirle)
        kart_verileri = [
            ("İY/MS 2/1", int((temp_gol['IY_MS'] == '2/1').sum()), 'ters'),
            ("İY/MS 1/2", int((temp_gol['IY_MS'] == '1/2').sum()), 'ters'),
            ("İY/MS X/X", int((temp_gol['IY_MS'] == 'X/X').sum()), 'standart'),
            ("İY/MS 1/X", int((temp_gol['IY_MS'] == '1/X').sum()), 'standart'),
            ("İY/MS 2/X", int((temp_gol['IY_MS'] == '2/X').sum()), 'standart')
        ]
        html_ters_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
        for baslik, adet, tip in kart_verileri:
            alev_sayisi = 0
            if tip == 'ters':
                if adet >= 4: alev_sayisi = 3
                elif adet == 3: alev_sayisi = 2
                elif adet == 2: alev_sayisi = 1
            elif tip == 'standart':
                if adet >= 13: alev_sayisi = 3
                elif adet >= 10: alev_sayisi = 2
                elif adet >= 7: alev_sayisi = 1
            alev_gosterim = "".join(["🔥" for _ in range(alev_sayisi)])
            html_ters_cards += generate_modern_card(baslik, adet, toplam_mac, alev_gosterim)
            if alev_sayisi > 0: surpriz_tercihler.append(f"{baslik} - {adet} Mac {alev_gosterim}")
        html_ters_cards += '</div>'
        st.markdown(html_ters_cards, unsafe_allow_html=True)

        # PDF TERCİHLER VE BAŞLIK AYARLARI
        st.markdown("---")
        st.subheader("📄 Analiz Sonucu Raporu")

        # Maç Adı Giriş Alanı
        mac_adi_girisi = st.text_input("⚽ Maç Adı (PDF Başlığı ve Dosya Adı Olacaktır)", value="Fenerbahce - Galatasaray", key="mac_adi_input")
        temiz_dosya_adi = "".join([c for c in mac_adi_girisi if c.isalpha() or c.isdigit() or c in ' -_']).strip().replace(' ', '_').lower()
        if not temiz_dosya_adi:
            temiz_dosya_adi = "sefin_kuponu_rapor"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(15, 15, 15)

        # Renk Paleti Tanımlamaları
        color_header_bg = (24, 28, 36)      # Koyu Gece Mavisi
        color_sec_bg = (241, 245, 249)      # Açık Mat Gri
        color_ideal_left = (16, 185, 129)    # Canlı Yeşil (Sol Sütun Şeridi)
        color_surp_left = (245, 158, 11)     # Canlı Turuncu
        color_text_dark = (15, 23, 42)       # Koyu Karbon
        color_text_muted = (100, 116, 139)   # Slate Gri

        # 1. Şık Rapor Başlığı (Header Banner)
        pdf.set_fill_color(*color_header_bg)
        pdf.rect(15, 15, 180, 24, 'F')

        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_xy(20, 19)
        pdf.cell(170, 8, txt=tr_to_ascii(f"SEFIN KUPONU | {mac_adi_girisi.upper()}"), ln=True, align='L')
        pdf.set_font("Helvetica", 'I', 9)
        pdf.set_x(20)
        pdf.cell(170, 4, txt=tr_to_ascii("Gelismis Oran Analiz Sistemi Raporu"), ln=True, align='L')

        # Bilgi Paneli
        pdf.set_xy(15, 43)
        pdf.set_fill_color(*color_sec_bg)
        pdf.cell(180, 15, txt="", ln=False, fill=True)

        pdf.set_text_color(*color_text_dark)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_xy(20, 45)
        pdf.cell(85, 5, txt=tr_to_ascii(f"Analiz Edilen Mac Sayisi:  {len(final_tablo)} Adet"), ln=False)
        pdf.cell(85, 5, txt=tr_to_ascii(f"Olusturma Tarihi:  {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"), ln=True)
        pdf.set_xy(20, 50)
        pdf.set_font("Helvetica", '', 9)
        pdf.set_text_color(*color_text_muted)
        pdf.cell(170, 4, txt=tr_to_ascii(f"Giris Oranlari (Bet365):  Ev: {b365h} / {b365ch}   |   Ber: {b365d} / {b365cd}   |   Dep: {b365a} / {b365ca}"), ln=True)

        pdf.ln(10)

        # --- IDEAL TERCİHLER BÖLÜMÜ ---
        pdf.set_text_color(*color_text_dark)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(180, 8, txt=tr_to_ascii("1. IDEAL TERCIHLER (Banko Adaylari)"), ln=True)

        # Dekoratif ince çizgi
        pdf.set_draw_color(*color_ideal_left)
        pdf.set_line_width(0.8)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

        if ideal_tercihler:
            for t in ideal_tercihler:
                alev_sayisi = t.count('🔥')
                temiz_metin = t.replace('🔥', '').strip()

                current_y = pdf.get_y()
                # Sol yeşil şerit
                pdf.set_fill_color(*color_ideal_left)
                pdf.rect(15, current_y, 3, 10, 'F')

                # Arka plan dolgusu
                pdf.set_fill_color(*color_sec_bg)
                pdf.rect(18, current_y, 177, 10, 'F')

                # Yazı
                pdf.set_xy(23, current_y + 1)
                pdf.set_text_color(*color_text_dark)
                pdf.set_font("Helvetica", 'B', 10)
                pdf.cell(120, 8, txt=tr_to_ascii(f"  {temiz_metin}"), ln=False)

                if alev_sayisi > 0:
                    pdf.set_text_color(220, 38, 38) # Koyu Kırmızı
                    pdf.set_font("Helvetica", 'B', 9)
                    pdf.cell(50, 8, txt=tr_to_ascii(f"  {alev_sayisi} ALEVLI POTANSIYEL"), ln=True, align='R')
                else:
                    pdf.ln(8)

                pdf.set_y(current_y + 12)
        else:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.set_text_color(*color_text_muted)
            pdf.cell(0, 8, txt=tr_to_ascii("  Bu analiz kriterlerine uyan aktif ideal tahmin bulunmuyor."), ln=True)

        pdf.ln(6)

        # --- SÜRPRİZ TERCİHLER BÖLÜMÜ ---
        pdf.set_text_color(*color_text_dark)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(180, 8, txt=tr_to_ascii("2. SURPRIZ TERCIHLER (Degerli & Yuksek Oranlar)"), ln=True)

        # Dekoratif ince çizgi
        pdf.set_draw_color(*color_surp_left)
        pdf.set_line_width(0.8)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

        if surpriz_tercihler:
            for t in surpriz_tercihler:
                alev_sayisi = t.count('🔥')
                temiz_metin = t.replace('🔥', '').strip()

                current_y = pdf.get_y()
                # Sol turuncu şerit
                pdf.set_fill_color(*color_surp_left)
                pdf.rect(15, current_y, 3, 10, 'F')

                # Arka plan dolgusu
                pdf.set_fill_color(*color_sec_bg)
                pdf.rect(18, current_y, 177, 10, 'F')

                # Yazı
                pdf.set_xy(23, current_y + 1)
                pdf.set_text_color(*color_text_dark)
                pdf.set_font("Helvetica", 'B', 10)
                pdf.cell(120, 8, txt=tr_to_ascii(f"  {temiz_metin}"), ln=False)

                if alev_sayisi > 0:
                    pdf.set_text_color(220, 38, 38) # Koyu Kırmızı
                    pdf.set_font("Helvetica", 'B', 9)
                    pdf.cell(50, 8, txt=tr_to_ascii(f"  {alev_sayisi} ALEVLI SURPRIZ"), ln=True, align='R')
                else:
                    pdf.ln(8)

                pdf.set_y(current_y + 12)
        else:
            pdf.set_font("Helvetica", 'I', 10)
            pdf.set_text_color(*color_text_muted)
            pdf.cell(0, 8, txt=tr_to_ascii("  Bu analiz kriterlerine uyan aktif surpriz tahmin bulunmuyor."), ln=True)

        pdf.ln(6)

        # --- İSTATİSTİKSEL DAĞILIM TABLOLARI BÖLÜMÜ ---
        pdf.set_text_color(*color_text_dark)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(180, 8, txt=tr_to_ascii("3. SKOR VE ISTATISTIKSEL DAGILIMLAR (Ozet Tablolar)"), ln=True)

        pdf.set_draw_color(100, 116, 139)
        pdf.set_line_width(0.8)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)

        def draw_pdf_table(pdf_obj, title, dataframe, col_names, start_x, start_y):
            pdf_obj.set_xy(start_x, start_y)
            pdf_obj.set_font("Helvetica", 'B', 9)
            pdf_obj.set_fill_color(200, 220, 255)
            pdf_obj.cell(55, 6, txt=tr_to_ascii(title), ln=True, align='L', fill=True)
            
            pdf_obj.set_xy(start_x, start_y + 6)
            pdf_obj.set_fill_color(240, 240, 240)
            pdf_obj.set_font("Helvetica", 'B', 8)
            pdf_obj.cell(35, 5, txt=tr_to_ascii(col_names[0]), border=1, ln=False, fill=True)
            pdf_obj.cell(20, 5, txt=tr_to_ascii(col_names[1]), border=1, ln=True, fill=True)
            
            current_row_y = start_y + 11
            pdf_obj.set_font("Helvetica", '', 8)
            for index, row in dataframe.head(15).iterrows():
                pdf_obj.set_xy(start_x, current_row_y)
                pdf_obj.cell(35, 5, txt=tr_to_ascii(str(row.iloc[0])), border=1, ln=False)
                pdf_obj.cell(20, 5, txt=tr_to_ascii(str(row.iloc[1])), border=1, ln=True)
                current_row_y += 5

        table_start_y = pdf.get_y()
        
        draw_pdf_table(pdf, "IY Skor Dagilimi", iy_dagilim, ["IY Skoru", "Adet"], 15, table_start_y)
        draw_pdf_table(pdf, "MS Skor Dagilimi", ms_dagilim, ["MS Skoru", "Adet"], 75, table_start_y)
        draw_pdf_table(pdf, "IY/MS Kombinasyonu", iyms_dagilim, ["IY/MS", "Adet"], 135, table_start_y)

        pdf.set_y(table_start_y + 90)
        pdf.ln(5)

        try:
            pdf_output = pdf.output(dest='S').encode('latin-1')
            b64_pdf = base64.b64encode(pdf_output).decode('utf-8')

            st.download_button( 
                label="⬇️ Klasik İndirme (Bilgisayar/Tablet)",
                data=pdf_output,
                file_name=f"{temiz_dosya_adi}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            pdf_link_html = f'''
            <a href="data:application/pdf;base64,{b64_pdf}" download="{temiz_dosya_adi}.pdf" style="text-decoration:none;">
                <div style="
                    background-color: #ef4444;
                    color: white;
                    padding: 12px 20px;
                    text-align: center;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    cursor: pointer;
                    margin-top: 10px;
                    display: block;
                ">
                    🚀 Mobil Doğrudan İndir (Telefon)
                </div>
            </a>
            '''
            st.markdown(pdf_link_html, unsafe_allow_html=True)

        except Exception as pdf_error:
            st.error(f"PDF oluşturulurken bir hata oluştu: {pdf_error}")
