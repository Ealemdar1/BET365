import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from fpdf import FPDF

st.set_page_config(page_title="Gelişmiş Oran Analiz Sistemi (Pinnacle Toleranslı)", layout="wide")

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
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.subheader("🔐 Sefin Kuponu Analiz Paneli")
    st.write("Devam etmek için lütfen giriş şifrenizi yazın.")

    pwd_input = st.text_input("Giriş Şifresi", type="password", key="login_pwd_input")
    submit_btn = st.button("Giriş Yap", use_container_width=True)

    if submit_btn:
        if pwd_input == "225960":
            st.session_state.authorized = True
            st.success("Şifre Doğrulandı! Giriş yapılıyor...")
            st.rerun()
        else:
            st.error("Hatalı Şifre! Lütfen tekrar deneyin.")

    st.markdown('</div>', unsafe_allow_html=True)
    return False

# Şifre kontrolünü çalıştır
if check_password():
    st.title("📊 ORAN KUTBU (Pinnacle - +/- 0.05 Toleranslı Eşleşme)")
    st.markdown("---")

    # PDF için Türkçe karakter dönüştürücü
    def tr_to_ascii(text):
        if not isinstance(text, str):
            return str(text)
        mapping = {
            'ç': 'c', 'Ç': 'C',
            'ğ': 'g', 'Ğ': 'G',
            'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ü': 'u', 'Ü': 'U'
        }
        for k, v in mapping.items():
            text = text.replace(k, v)
        return text

    # Taraf sonucunu belirleyen yardımcı fonksiyon
    def taraf_belirle(skor_str):
        if not isinstance(skor_str, str) or '-' not in skor_str:
            return 'X'
        try:
            home, away = map(int, skor_str.split('-'))
            if home > away:
                return '1'
            elif away > home:
                return '2'
            return 'X'
        except:
            return 'X'

    # Modern HTML Kart Tasarım Fonksiyonu
    def generate_modern_card(title, count, total, alev_str=""):
        pct = (count / total * 100) if total > 0 else 0
        glow_style = "border: 1px solid #ef4444; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);" if "🔥" in alev_str else "border: 1px solid #2d3748;"
        bg_color = "#1e1b1b" if "🔥" in alev_str else "#111827"

        card_html = f"""
        <div style="background-color: {bg_color}; {glow_style} border-radius: 12px; padding: 18px; text-align: center; transition: transform 0.2s;">
            <div style="color: #9ca3af; font-size: 13px; font-weight: 500; margin-bottom: 6px; text-transform: uppercase;">{title}</div>
            <div style="font-size: 28px; font-weight: 800; color: #f3f4f6; margin-bottom: 4px;">{count} / {total}</div>
            <div style="font-size: 18px; font-weight: 700; color: #10b981; margin-bottom: 6px;">% {pct:.1f}</div>
            <div style="font-size: 14px; min-height: 20px;">{alev_str}</div>
        </div>
        """
        return card_html

    # Toleranslı Eşleşen Maç Sayısı Dashboard Kartı
    def generate_summary_dashboard(total_matches):
        html = (
            f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 25px;">'
            f'<div style="background-color: #1a202c; border: 1px solid #3b82f6; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.15);">'
            f'<div style="color: #93c5fd; font-weight: 600; font-size: 15px; margin-bottom: 8px;">📋 Tolerans Dahilinde Eşleşen Maç Sayısı</div>'
            f'<div style="font-size: 36px; color: #3b82f6; font-weight: bold;">{total_matches} Adet</div>'
            f'<div style="color: #64748b; font-size: 12px; margin-top: 5px;">Seçilen açılış oranlarına +/- 0.05 yakınlıktaki maç sayısı</div>'
            f'</div>'
            f'</div>'
        )
        return html

    # Veri Yükleme Fonksiyonu (Cache ile)
    @st.cache_data
    def load_excel_data():
        dosya_adi = "oranlar.xlsx"
        if not os.path.exists(dosya_adi):
            return None
        try:
            df = pd.read_excel(dosya_adi)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Excel dosyası yüklenirken hata oluştu: {e}")
            return None

    df_temp = load_excel_data()

    if df_temp is not None:
        # =====================================================
        # MOBİL UYUMLU KOMPAKT YAN YANA ORAN GİRİŞ ALANI
        # =====================================================
        st.markdown("### 🎯 Pinnacle Açılış Oranlarını Girin (+/- 0.05 Toleranslı Aranır)")

        col1, col2, col3 = st.columns(3)
        with col1:
            ps_h = st.number_input("Ev Sahibi Açılış (PSH)", min_value=1.0, max_value=20.0, value=2.60, step=0.01)
        with col2:
            ps_d = st.number_input("Beraberlik Açılış (PSD)", min_value=1.0, max_value=20.0, value=3.10, step=0.01)
        with col3:
            ps_a = st.number_input("Deplasman Açılış (PSA)", min_value=1.0, max_value=20.0, value=2.90, step=0.01)

        # +/- 0.05 toleranslı aralık filtresi
        sonuc_df = df_temp[
            (df_temp['PSH'] >= ps_h - 0.05) & (df_temp['PSH'] <= ps_h + 0.05) &
            (df_temp['PSD'] >= ps_d - 0.05) & (df_temp['PSD'] <= ps_d + 0.05) &
            (df_temp['PSA'] >= ps_a - 0.05) & (df_temp['PSA'] <= ps_a + 0.05)
        ].copy()

        if sonuc_df.empty:
            st.warning("Belirtilen tolerans aralığında (+/- 0.05) hiçbir maç bulunamadı.")
        else:
            for col in ['HTHG', 'HTAG', 'FTHG', 'FTAG']:
                if col in sonuc_df.columns:
                    sonuc_df[col] = pd.to_numeric(sonuc_df[col], errors='coerce').fillna(0).astype(int)

            sonuc_df['İY'] = sonuc_df['HTHG'].astype(str) + "-" + sonuc_df['HTAG'].astype(str)
            sonuc_df['MS'] = sonuc_df['FTHG'].astype(str) + "-" + sonuc_df['FTAG'].astype(str)

            # İstenen Sütunları Seç ve Sırala
            kolonlar = ['Home', 'Away', 'İY', 'MS', 'PSH', 'PSD', 'PSA']
            final_tablo = sonuc_df[[c for c in kolonlar if c in sonuc_df.columns]]

            # --- ÖZET DASHBOARD KARTLARI ---
            st.markdown(generate_summary_dashboard(len(final_tablo)), unsafe_allow_html=True)
            st.subheader(f"🎯 Eşleşen {len(final_tablo)} Maç (+/- 0.05 Toleranslı)")
            st.dataframe(final_tablo, use_container_width=True)

            st.markdown("### 📊 Skor ve İstatistiki Dağılımlar")
            col_stat1, col_stat2, col_stat3 = st.columns(3)

            with col_stat1:
                st.markdown("**İlk Yarı (İY) Skor Dağılımı**")
                iy_dagilim = final_tablo['İY'].value_counts().reset_index()
                iy_dagilim.columns = ['İY Skoru', 'Adet']
                st.dataframe(iy_dagilim, use_container_width=True)

            with col_stat2:
                st.markdown("**Maç Sonu (MS) Skor Dağılımı**")
                ms_dagilim = final_tablo['MS'].value_counts().reset_index()
                ms_dagilim.columns = ['MS Skoru', 'Adet']
                st.dataframe(ms_dagilim, use_container_width=True)

            with col_stat3:
                st.markdown("**İY / MS Kombinasyon Dağılımı**")
                final_tablo_temp = final_tablo.copy()
                final_tablo_temp['IY_Taraf'] = final_tablo_temp['İY'].apply(taraf_belirle)
                final_tablo_temp['MS_Taraf'] = final_tablo_temp['MS'].apply(taraf_belirle)
                final_tablo_temp['IY/MS'] = final_tablo_temp['IY_Taraf'] + "/" + final_tablo_temp['MS_Taraf']
                iyms_dagilim = final_tablo_temp['IY/MS'].value_counts().reset_index()
                iyms_dagilim.columns = ['IY/MS', 'Adet']
                st.dataframe(iyms_dagilim, use_container_width=True)

            # Bahis Tahminleri Listeleri
            ideal_tercihler = []
            surpriz_tercihler = []

            # MS ÖZEL BAHİS
            st.markdown("---")
            st.markdown("### 🔥 Maç Sonu (MS) Özel Bahis Dağılımı")
            st.caption(f"Son {len(final_tablo)} maç üzerinden hesaplanmıştır. (Alevler: 10-14 maç=1, 15-16 maç=2, 17+ maç=3)")
            temp_gol = final_tablo.copy()
            temp_gol['Toplam_Gol'] = temp_gol['MS'].apply(lambda s: sum(int(x.strip()) for x in s.split('-')) if isinstance(s, str) and '-' in s else 0)
            temp_gol['KG_Var'] = temp_gol['MS'].apply(lambda s: all(int(x)>0 for x in s.split('-')) if isinstance(s, str) and '-' in s else False)

            if len(temp_gol) > 0:
                toplam_mac = len(temp_gol)
                html_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'

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
            temp_gol['IY_Toplam_Gol'] = temp_gol['İY'].apply(lambda s: sum(int(x.strip()) for x in s.split('-')) if isinstance(s, str) and '-' in s else 0)
            temp_gol['IY_KG_Var'] = temp_gol['İY'].apply(lambda s: all(int(x)>0 for x in s.split('-')) if isinstance(s, str) and '-' in s else False)
            temp_gol['IY_Taraf'] = temp_gol['İY'].apply(taraf_belirle)

            html_iy_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
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
            html_iy_sonuc_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
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
            html_ters_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
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

            # PDF RAPOR BÖLÜMÜ
            st.markdown("---")
            st.subheader("📄 Analiz Sonucu Raporu")
            mac_adi_girisi = st.text_input("⚽ Maç Adı (PDF Başlığı ve Dosya Adı)", value="Fenerbahce - Galatasaray", key="mac_adi_input")
            temiz_dosya_adi = "".join([c for c in mac_adi_girisi if c.isalpha() or c.isdigit() or c in ' -_']).strip().replace(' ', '_').lower()
            if not temiz_dosya_adi:
                temiz_dosya_adi = "sefin_kuponu_rapor"

            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_margins(15, 15, 15)

            color_header_bg = (24, 28, 36)
            color_sec_bg = (241, 245, 249)
            color_ideal_left = (16, 185, 129)
            color_surp_left = (245, 158, 11)
            color_text_dark = (15, 23, 42)
            color_text_muted = (100, 116, 139)

            pdf.set_fill_color(*color_header_bg)
            pdf.rect(15, 15, 180, 24, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", 'B', 14)
            pdf.set_xy(20, 19)
            pdf.cell(170, 8, txt=tr_to_ascii(f"SEFIN KUPONU | {mac_adi_girisi.upper()}"), ln=True, align='L')
            pdf.set_font("Helvetica", 'I', 9)
            pdf.set_x(20)
            pdf.cell(170, 4, txt=tr_to_ascii("Gelismis Oran Analiz Sistemi Raporu"), ln=True, align='L')

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
            pdf.cell(170, 4, txt=tr_to_ascii(f"Giris Oranlari:  Ev: {ps_h}  |  Ber: {ps_d}  |  Dep: {ps_a}"), ln=True)
            pdf.ln(10)

            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(180, 8, txt=tr_to_ascii("1. IDEAL TERCİHLER (Banko Adayları)"), ln=True)
            pdf.set_draw_color(*color_ideal_left)
            pdf.set_line_width(0.8)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(4)

            if ideal_tercihler:
                for t in ideal_tercihler:
                    alev_sayisi = t.count('🔥')
                    temiz_metin = t.replace('🔥', '').strip()
                    current_y = pdf.get_y()
                    pdf.set_fill_color(*color_ideal_left)
                    pdf.rect(15, current_y, 3, 10, 'F')
                    pdf.set_fill_color(*color_sec_bg)
                    pdf.rect(18, current_y, 177, 10, 'F')
                    pdf.set_xy(23, current_y + 1)
                    pdf.set_text_color(*color_text_dark)
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.cell(120, 8, txt=tr_to_ascii(f"  {temiz_metin}"), ln=False)
                    if alev_sayisi > 0:
                        pdf.set_text_color(220, 38, 38)
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
            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(180, 8, txt=tr_to_ascii("2. SURPRIZ TERCİHLER (Değerli & Yüksek Oranlar)"), ln=True)
            pdf.set_draw_color(*color_surp_left)
            pdf.set_line_width(0.8)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(4)

            if surpriz_tercihler:
                for t in surpriz_tercihler:
                    alev_sayisi = t.count('🔥')
                    temiz_metin = t.replace('🔥', '').strip()
                    current_y = pdf.get_y()
                    pdf.set_fill_color(*color_surp_left)
                    pdf.rect(15, current_y, 3, 10, 'F')
                    pdf.set_fill_color(*color_sec_bg)
                    pdf.rect(18, current_y, 177, 10, 'F')
                    pdf.set_xy(23, current_y + 1)
                    pdf.set_text_color(*color_text_dark)
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.cell(120, 8, txt=tr_to_ascii(f"  {temiz_metin}"), ln=False)
                    if alev_sayisi > 0:
                        pdf.set_text_color(220, 38, 38)
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
            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(180, 8, txt=tr_to_ascii("3. SKOR VE ISTATISTIKSEL DAGILIMLAR (Özet Tablolar)"), ln=True)
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
    else:
        st.warning("Lütfen 'oranlar.xlsx' dosyasını çalışma alanına yükleyin.")
