import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import json
from fpdf import FPDF
from google import genai
import plotly.express as px
import streamlit.components.v1 as components

st.set_page_config(page_title="Gelişmiş Oran Analiz Sistemi (Çoklu Bahisçi)", layout="wide")

# =====================================================
# ŞİFRE KALDIRILDI - DOĞRUDAN GİRİŞ
# =====================================================
if True:

    # =====================================================
    # GEMINI İSTEMCİSİ
    # =====================================================
    try:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_aktif = True
    except Exception as e:
        gemini_aktif = False
        gemini_client = None
        st.sidebar.warning(f"⚠️ Gemini API anahtarı bulunamadı. Yapay zeka yorumu devre dışı. Hata: {e}")

    st.title("📊 ORAN KUTBU (Çoklu Bahisçi - Açılış + Kapanış)")
    st.markdown("---")

    def tr_to_ascii(text):
        replacements = {
            'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
            'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c',
            '🔥': ''
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text


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


    def generate_summary_dashboard(total_matches, tolerans, mod_metni, oran_metni):
        html = (
            f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 25px;">'
            f'<div style="background-color: #1a202c; border: 1px solid #3b82f6; border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(59, 130, 246, 0.15);">'
            f'<div style="color: #93c5fd; font-weight: 600; font-size: 15px; margin-bottom: 8px;">📋 Eşleşen Maç Sayısı</div>'
            f'<div style="font-size: 36px; color: #3b82f6; font-weight: bold;">{total_matches} Adet</div>'
            f'<div style="color: #64748b; font-size: 12px; margin-top: 5px;">Tolerans: ±{tolerans}</div>'
            f'<div style="color: #94a3b8; font-size: 11px; margin-top: 3px;">{oran_metni} • {mod_metni}</div>'
            f'</div>'
            f'</div>'
        )
        return html


    # =====================================================
    # ANİMASYONLU SKOR GRAFİĞİ FONKSİYONU
    # =====================================================
    def generate_animated_score_chart(df, skor_kolonu='MS', max_mac=60, title='Animasyonlu Skor Dağılımı'):
        if skor_kolonu not in df.columns or len(df) == 0:
            return None

        anim_kaynak = df.head(min(len(df), max_mac)).reset_index(drop=True)
        
        if len(anim_kaynak) == 1:
            kum = anim_kaynak[skor_kolonu].value_counts().reset_index()
            kum.columns = ['Skor', 'Adet']
            fig = px.bar(
                kum, x='Skor', y='Adet', 
                title=f"{title} (Tek Maç Verisi)", 
                text='Adet',
                template='plotly_dark'
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=450,
            )
            return fig

        frames_list = []
        for i in range(1, len(anim_kaynak) + 1):
            kum = anim_kaynak.head(i)[skor_kolonu].value_counts().reset_index()
            kum.columns = ['Skor', 'Adet']
            kum['Mac_Sayisi'] = i
            frames_list.append(kum)

        if not frames_list:
            return None

        anim_df = pd.concat(frames_list, ignore_index=True)

        fig = px.bar(
            anim_df,
            x='Skor',
            y='Adet',
            color='Skor',
            animation_frame='Mac_Sayisi',
            range_y=[0, anim_df['Adet'].max() * 1.15 + 1],
            title=title,
            labels={'Skor': 'Skor', 'Adet': 'Görülme Sayısı'},
            template='plotly_dark'
        )

        fig.update_layout(
            transition={'duration': 200},
            showlegend=False,
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

        if fig.layout.updatemenus:
            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 150
            fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 150

        return fig

    # =====================================================
    # ÇARPIŞMA SİMÜLASYONU (HTML5 CANVAS)
    # =====================================================
    def render_bouncing_balls_animation(df, skor_kolonu='MS'):
        if skor_kolonu not in df.columns or len(df) == 0:
            return
            
        scores = df[skor_kolonu].tolist()
        scores_json = json.dumps(scores)
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
          body {{ margin: 0; display: flex; justify-content: center; align-items: center; background-color: transparent; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
          #container {{ position: relative; width: 400px; height: 400px; margin: 20px auto; }}
          canvas {{ border-radius: 50%; border: 4px solid #3b82f6; box-shadow: 0 0 30px rgba(59, 130, 246, 0.3); background: #0f172a; }}
          #scoreboard {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: #fff; font-size: 64px; font-weight: 800; pointer-events: none;
            text-shadow: 0 0 20px rgba(0,0,0,1), 0 0 10px rgba(0,0,0,0.8); z-index: 10;
            display: flex; gap: 20px; transition: color 0.15s ease;
          }}
          .score-text {{ background: rgba(30, 41, 59, 0.8); padding: 10px 20px; border-radius: 12px; border: 1px solid #334155; }}
          .subtitle {{ position: absolute; bottom: -30px; width: 100%; text-align: center; color: #94a3b8; font-size: 14px; }}
        </style>
        </head>
        <body>
        <div id="container">
          <div id="scoreboard"><span class="score-text" id="score">0 - 0</span></div>
          <canvas id="canvas" width="400" height="400"></canvas>
          <div class="subtitle">⚽ Toplar çarpıştıkça eşleşen maçların gerçek skorları görünür.</div>
        </div>

        <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const scoreEl = document.getElementById('score');

        const scores = {scores_json};
        let scoreIndex = 0;

        const radius = 18;
        const center = {{ x: 200, y: 200 }};
        const bounds = 200;

        const ball1 = {{ x: 150, y: 200, vx: 4, vy: 2.5, color: '#ef4444' }}; // Ev Sahibi (Kırmızı)
        const ball2 = {{ x: 250, y: 200, vx: -3.5, vy: -4, color: '#10b981' }}; // Deplasman (Yeşil)

        function updateScore() {{
            if (scores.length === 0) return;
            scoreEl.innerText = scores[scoreIndex];
            scoreIndex = (scoreIndex + 1) % scores.length;
            
            // Çarpışma anında parlama efekti
            scoreEl.style.color = '#fbbf24';
            setTimeout(() => scoreEl.style.color = '#fff', 150);
        }}

        function drawBall(ball) {{
            ctx.beginPath();
            ctx.arc(ball.x, ball.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = ball.color;
            ctx.fill();
            ctx.shadowColor = ball.color;
            ctx.shadowBlur = 15;
            ctx.fill();
            ctx.shadowBlur = 0;
            ctx.closePath();
            
            // İç parlama (3D efekti)
            ctx.beginPath();
            ctx.arc(ball.x - 4, ball.y - 4, radius/3, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.fill();
            ctx.closePath();
        }}

        function checkCollision(b1, b2) {{
            const dx = b1.x - b2.x;
            const dy = b1.y - b2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < radius * 2) {{
                updateScore();

                const angle = Math.atan2(dy, dx);
                const sin = Math.sin(angle);
                const cos = Math.cos(angle);

                const vx1 = b1.vx * cos + b1.vy * sin;
                const vy1 = b1.vy * cos - b1.vx * sin;
                const vx2 = b2.vx * cos + b2.vy * sin;
                const vy2 = b2.vy * cos - b2.vx * sin;

                b1.vx = vx2 * cos - vy1 * sin;
                b1.vy = vy1 * cos + vx2 * sin;
                b2.vx = vx1 * cos - vy2 * sin;
                b2.vy = vy2 * cos + vx1 * sin;

                const overlap = radius * 2 - dist;
                b1.x += (dx / dist) * overlap / 2;
                b1.y += (dy / dist) * overlap / 2;
                b2.x -= (dx / dist) * overlap / 2;
                b2.y -= (dy / dist) * overlap / 2;
            }}
        }}

        function animate() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ball1.x += ball1.vx;
            ball1.y += ball1.vy;
            ball2.x += ball2.vx;
            ball2.y += ball2.vy;

            [ball1, ball2].forEach(ball => {{
                const dx = ball.x - center.x;
                const dy = ball.y - center.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist > bounds - radius) {{
                    const nx = dx / dist;
                    const ny = dy / dist;
                    const dot = ball.vx * nx + ball.vy * ny;
                    ball.vx -= 2 * dot * nx;
                    ball.vy -= 2 * dot * ny;

                    ball.x = center.x + nx * (bounds - radius);
                    ball.y = center.y + ny * (bounds - radius);
                }}
            }});

            checkCollision(ball1, ball2);

            drawBall(ball1);
            drawBall(ball2);

            requestAnimationFrame(animate);
        }}

        updateScore();
        animate();
        </script>
        </body>
        </html>
        """
        
        components.html(html_code, height=480, scrolling=False)


    # =====================================================
    # BAHİSÇİ SÜTUN EŞLEŞTİRMELERİ (AÇILIŞ + KAPANIŞ)
    # =====================================================
    BAHISCILER = {
        "Pinnacle": {
            "acilis":  {"H": "PSH",    "D": "PSD",    "A": "PSA"},
            "kapanis": {"H": "PSCH",   "D": "PSCD",   "A": "PSCA"},
        },
        "Bet365": {
            "acilis":  {"H": "B365H",  "D": "B365D",  "A": "B365A"},
            "kapanis": {"H": "B365CH", "D": "B365CD", "A": "B365CA"},
        },
        "Bwin": {
            "acilis":  {"H": "BWH",    "D": "BWD",    "A": "BWA"},
            "kapanis": {"H": "BWCH",   "D": "BWCD",   "A": "BWCA"},
        },
        "Interwetten": {
            "acilis":  {"H": "IWH",    "D": "IWD",    "A": "IWA"},
            "kapanis": {"H": "IWCH",   "D": "IWCD",   "A": "IWCA"},
        },
        "William Hill": {
            "acilis":  {"H": "WHH",    "D": "WHD",    "A": "WHA"},
            "kapanis": {"H": "WHCH",   "D": "WHCD",   "A": "WHCA"},
        },
        "VC Bet": {
            "acilis":  {"H": "VCH",    "D": "VCD",    "A": "VCA"},
            "kapanis": {"H": "VCCH",   "D": "VCCD",   "A": "VCCA"},
        },
        "Betvictor": {
            "acilis":  {"H": "BVH",    "D": "BVD",    "A": "BVA"},
            "kapanis": {"H": "BVCH",   "D": "BVCD",   "A": "BVCA"},
        },
        "Ortalama (Betbrain)": {
            "acilis":  {"H": "BbAvH",  "D": "BbAvD",  "A": "BbAvA"},
            "kapanis": {"H": "BbAvCH", "D": "BbAvCD", "A": "BbAvCA"},
        },
        "Maksimum (Betbrain)": {
            "acilis":  {"H": "BbMxH",  "D": "BbMxD",  "A": "BbMxA"},
            "kapanis": {"H": "BbMxCH", "D": "BbMxCD", "A": "BbMxCA"},
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


    # =====================================================
    # GEMINI YORUM FONKSİYONU (Otomatik Model Fallback)
    # =====================================================
    def gemini_ile_mac_yorumu_uret(ev_takim, dep_takim, ms_dagilim, iy_dagilim, iyms_dagilim):
        if not gemini_aktif:
            return "Yapay zeka yorumu için Gemini API anahtarı tanımlı değil. Streamlit Secrets'a 'GEMINI_API_KEY' ekleyin."

        ms_ozet = ", ".join([f"{row['MS Skoru']} ({row['Adet']} kez)" for _, row in ms_dagilim.head(5).iterrows()])
        iy_ozet = ", ".join([f"{row['İY Skoru']} ({row['Adet']} kez)" for _, row in iy_dagilim.head(5).iterrows()])
        iyms_ozet = ", ".join([f"{row['İY/MS']} ({row['Adet']} kez)" for _, row in iyms_dagilim.head(5).iterrows()])

        prompt = f"""
        Sen deneyimli bir futbol analistisin. Aşağıdaki geçmiş maç verilerine dayanarak,
        {ev_takim} - {dep_takim} maçı için Türkçe, akıcı ve profesyonel bir bahis yorumu yaz.
        Yorum, 3-4 cümleyi geçmesin ve şu verileri korusun:

        - En sık görülen Maç Sonu (MS) skorları: {ms_ozet}
        - En sık görülen İlk Yarı (İY) skorları: {iy_ozet}
        - En sık görülen İY/MS kombinasyonları: {iyms_ozet}

        Yorumda, bu istatistiklerin maçın olası gidişatı hakkında ne ima ettiğini belirt.
        """

        denenecek_modeller = [
            'gemini-3.8-flash',
            'gemini-2.5-flash',
            'gemini-1.5-flash',
            'gemini-flash-latest',
        ]

        son_hata = None
        for model_adi in denenecek_modeller:
            try:
                response = gemini_client.models.generate_content(
                    model=model_adi,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                son_hata = e
                continue

        return (
            f"Yapay zeka yorumu oluşturulamadı. Denenen modeller: "
            f"{', '.join(denenecek_modeller)}. Son hata: {son_hata}"
        )


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
    # ANALİZ MODU SEÇİMİ
    # =====================================================
    st.markdown("### 🎯 Analiz Modu")

    mod = st.radio(
        "Hangi modda arama yapmak istiyorsun?",
        options=["Tek Bahisçi", "Herhangi Biri (Tüm Bahisçiler)"],
        horizontal=True,
        help=(
            "Tek Bahisçi: Sadece seçtiğin bahisçinin oranları taranır.\n"
            "Herhangi Biri: Tüm bahisçilerin oranları taranır; bir tanesi bile toleransa uyuyorsa maç listeye girer."
        )
    )

    st.markdown("### 📊 Oran Tipi")
    oran_tipi = st.radio(
        "Hangi oran setini aramak istiyorsun?",
        options=[MODE_ACILIS, MODE_KAPANIS, MODE_VEYA, MODE_VE],
        horizontal=True,
        help=(
            "Sadece Açılış: Yalnızca açılış oranları taranır.\n"
            "Sadece Kapanış: Yalnızca kapanış oranları taranır.\n"
            "Her İkisi (VEYA): Açılış veya kapanış oranlarından biri toleransa uyuyorsa maç listeye girer.\n"
            "Her İkisi (VE): Hem açılış hem kapanış toleransa uyuyorsa maç listeye girer."
        )
    )

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

        if oran_tipi == MODE_ACILIS:
            return ac_ok
        elif oran_tipi == MODE_KAPANIS:
            return kc_ok
        elif oran_tipi == MODE_VEYA:
            return ac_ok or kc_ok
        elif oran_tipi == MODE_VE:
            return ac_ok and kc_ok
        return False

    mevcut_bahisciler = [isim for isim in BAHISCILER if bahisci_uygun_mu(isim, oran_tipi)]

    if not mevcut_bahisciler:
        st.error(f"⚠️ '{oran_tipi}' modu için uygun bahisçi/veri bulunamadı. Lütfen farklı bir oran tipi seçin veya veri yükleyin.")
        st.stop()

    if mod == "Tek Bahisçi":
        secilen_bahisci = st.selectbox(
            "Bahisçi Seç",
            options=mevcut_bahisciler,
            index=mevcut_bahisciler.index("Pinnacle") if "Pinnacle" in mevcut_bahisciler else 0,
            help="Sadece bu bahisçinin oranları taranacak."
        )
        aranacak_bahisciler = [secilen_bahisci]
    else:
        aranacak_bahisciler = st.multiselect(
            "Taranacak Bahisçiler (boş bırakırsan tümü taranır)",
            options=mevcut_bahisciler,
            default=mevcut_bahisciler,
            help="Tüm bahisçilerin oranları taranır, bir tanesi bile toleransa uyuyorsa maç listeye girer."
        )
        if not aranacak_bahisciler:
            aranacak_bahisciler = mevcut_bahisciler
        secilen_bahisci = "Herhangi Biri"

    # =====================================================
    # ORAN GİRİŞ ALANLARI
    # =====================================================
    ps_h = ps_d = ps_a = None
    ps_h_k = ps_d_k = ps_a_k = None

    if acilis_kullan:
        st.markdown("### 📈 Açılış Oranlarını Girin")
        col1, col2, col3 = st.columns(3)
        with col1:
            ps_h = st.number_input("Ev Sahibi (Açılış)", min_value=1.0, max_value=20.0, value=2.60, step=0.01, key="in_psh_ac")
        with col2:
            ps_d = st.number_input("Beraberlik (Açılış)", min_value=1.0, max_value=20.0, value=3.75, step=0.01, key="in_psd_ac")
        with col3:
            ps_a = st.number_input("Deplasman (Açılış)", min_value=1.0, max_value=20.0, value=2.37, step=0.01, key="in_psa_ac")

    if kapanis_kullan:
        st.markdown("### 📉 Kapanış Oranlarını Girin")
        col1, col2, col3 = st.columns(3)
        with col1:
            ps_h_k = st.number_input("Ev Sahibi (Kapanış)", min_value=1.0, max_value=20.0, value=2.60, step=0.01, key="in_psh_kc")
        with col2:
            ps_d_k = st.number_input("Beraberlik (Kapanış)", min_value=1.0, max_value=20.0, value=3.75, step=0.01, key="in_psd_kc")
        with col3:
            ps_a_k = st.number_input("Deplasman (Kapanış)", min_value=1.0, max_value=20.0, value=2.37, step=0.01, key="in_psa_kc")

    st.caption(f"Seçili bahisçi(ler): **{', '.join(aranacak_bahisciler)}** | Mod: **{oran_tipi}**")

    # TOLERANS SLIDER (0.30'a kadar)
    st.markdown("### ⚙️ Eşleşme Toleransı")
    tolerans = st.slider(
        "Oran Toleransı (±)",
        min_value=0.0, max_value=0.30, value=0.05, step=0.01,
        help="0 = Birebir tam eşleşme, 0.05 = ±0.05 toleranslı eşleşme, 0.30 = ±0.30 toleranslı eşleşme"
    )

    if tolerans == 0:
        st.caption("🔒 Şu an **birebir tam eşleşme** modundasınız.")
    else:
        info_parts = []
        if acilis_kullan:
            info_parts.append(
                f"Açılış → Ev [{ps_h - tolerans:.2f}–{ps_h + tolerans:.2f}], "
                f"Ber [{ps_d - tolerans:.2f}–{ps_d + tolerans:.2f}], "
                f"Dep [{ps_a - tolerans:.2f}–{ps_a + tolerans:.2f}]"
            )
        if kapanis_kullan:
            info_parts.append(
                f"Kapanış → Ev [{ps_h_k - tolerans:.2f}–{ps_h_k + tolerans:.2f}], "
                f"Ber [{ps_d_k - tolerans:.2f}–{ps_d_k + tolerans:.2f}], "
                f"Dep [{ps_a_k - tolerans:.2f}–{ps_a_k + tolerans:.2f}]"
            )
        st.caption(f"📏 **±{tolerans}** tolerans aktif. " + " | ".join(info_parts))

    # Lig Filtresi
    st.sidebar.header("🌍 Filtreler")
    benzersiz_ligler = sorted(df_all_leagues['Source_Sheet'].dropna().unique().tolist()) if not df_all_leagues.empty else []
    secilen_ligler = st.sidebar.multiselect("Lig Filtrele", benzersiz_ligler)

    if "analiz_yapildi" not in st.session_state:
        st.session_state.analiz_yapildi = False

    if st.button("⚡ Analizi Başlat", use_container_width=True):
        df_temp = df_all_leagues.copy()

        if secilen_ligler:
            df_temp = df_temp[df_temp['Source_Sheet'].isin(secilen_ligler)]

        eslesen_satirlar = []

        for bahisci in aranacak_bahisciler:
            if bahisci not in BAHISCILER:
                continue
            sut = BAHISCILER[bahisci]
            ac_cols = sut["acilis"]
            kc_cols = sut["kapanis"]

            tmp = df_temp.copy()
            mask_ac = None
            mask_kc = None

            if acilis_kullan:
                ac_h, ac_d, ac_a = ac_cols["H"], ac_cols["D"], ac_cols["A"]
                if all(c in tmp.columns for c in [ac_h, ac_d, ac_a]):
                    for c in [ac_h, ac_d, ac_a]:
                        tmp[c] = pd.to_numeric(tmp[c], errors='coerce')
                    mask_ac = (
                        tmp[ac_h].between(ps_h - tolerans, ps_h + tolerans) &
                        tmp[ac_d].between(ps_d - tolerans, ps_d + tolerans) &
                        tmp[ac_a].between(ps_a - tolerans, ps_a + tolerans)
                    )

            if kapanis_kullan:
                kc_h, kc_d, kc_a = kc_cols["H"], kc_cols["D"], kc_cols["A"]
                if all(c in tmp.columns for c in [kc_h, kc_d, kc_a]):
                    for c in [kc_h, kc_d, kc_a]:
                        tmp[c] = pd.to_numeric(tmp[c], errors='coerce')
                    mask_kc = (
                        tmp[kc_h].between(ps_h_k - tolerans, ps_h_k + tolerans) &
                        tmp[kc_d].between(ps_d_k - tolerans, ps_d_k + tolerans) &
                        tmp[kc_a].between(ps_a_k - tolerans, ps_a_k + tolerans)
                    )

            if oran_tipi == MODE_ACILIS:
                final_mask = mask_ac
            elif oran_tipi == MODE_KAPANIS:
                final_mask = mask_kc
            elif oran_tipi == MODE_VEYA:
                if mask_ac is not None and mask_kc is not None:
                    final_mask = mask_ac | mask_kc
                else:
                    final_mask = mask_ac if mask_ac is not None else mask_kc
            elif oran_tipi == MODE_VE:
                if mask_ac is not None and mask_kc is not None:
                    final_mask = mask_ac & mask_kc
                else:
                    final_mask = None
            else:
                final_mask = None

            if final_mask is None:
                continue

            matched = tmp[final_mask].copy()
            if matched.empty:
                continue

            if oran_tipi == MODE_ACILIS:
                tip_series = pd.Series(['Aç'] * len(matched), index=matched.index)
            elif oran_tipi == MODE_KAPANIS:
                tip_series = pd.Series(['Kap'] * len(matched), index=matched.index)
            else:
                ac_bool = (mask_ac.reindex(matched.index, fill_value=False)
                           if mask_ac is not None else pd.Series(False, index=matched.index))
                kc_bool = (mask_kc.reindex(matched.index, fill_value=False)
                           if mask_kc is not None else pd.Series(False, index=matched.index))

                def get_tip(a, k):
                    if a and k: return 'Aç+Kap'
                    elif a: return 'Aç'
                    elif k: return 'Kap'
                    return '-'
                tip_series = pd.Series([get_tip(a, k) for a, k in zip(ac_bool, kc_bool)], index=matched.index)

            matched['Eslesen_Bahisci'] = bahisci + ' (' + tip_series + ')'

            ac_h, ac_d, ac_a = ac_cols["H"], ac_cols["D"], ac_cols["A"]
            if all(c in matched.columns for c in [ac_h, ac_d, ac_a]):
                matched['AC_H'] = matched[ac_h]
                matched['AC_D'] = matched[ac_d]
                matched['AC_A'] = matched[ac_a]
                if acilis_kullan:
                    matched['Fark_AC_H'] = (matched[ac_h] - ps_h).round(2)
                    matched['Fark_AC_D'] = (matched[ac_d] - ps_d).round(2)
                    matched['Fark_AC_A'] = (matched[ac_a] - ps_a).round(2)

            kc_h, kc_d, kc_a = kc_cols["H"], kc_cols["D"], kc_cols["A"]
            if all(c in matched.columns for c in [kc_h, kc_d, kc_a]):
                matched['KC_H'] = matched[kc_h]
                matched['KC_D'] = matched[kc_d]
                matched['KC_A'] = matched[kc_a]
                if kapanis_kullan:
                    matched['Fark_KC_H'] = (matched[kc_h] - ps_h_k).round(2)
                    matched['Fark_KC_D'] = (matched[kc_d] - ps_d_k).round(2)
                    matched['Fark_KC_A'] = (matched[kc_a] - ps_a_k).round(2)

            eslesen_satirlar.append(matched)

        if not eslesen_satirlar:
            if tolerans == 0:
                st.warning("Seçilen kriterlerle birebir tam eşleşen hiçbir maç bulunamadı.")
            else:
                st.warning(f"±{tolerans} toleransında eşleşen hiçbir maç bulunamadı.")
            st.session_state.analiz_yapildi = False
        else:
            birlesik = pd.concat(eslesen_satirlar, ignore_index=True)

            grup_kolonlari = [c for c in ['Date', 'HomeTeam', 'AwayTeam', 'Source_Sheet'] if c in birlesik.columns]

            if grup_kolonlari:
                birlesik['Eslesen_Bahisci_Str'] = birlesik['Eslesen_Bahisci']
                agg_dict = {
                    'Eslesen_Bahisci_Str': lambda x: ', '.join(sorted(set(x))),
                }
                for c in ['AC_H', 'AC_D', 'AC_A', 'KC_H', 'KC_D', 'KC_A',
                          'Fark_AC_H', 'Fark_AC_D', 'Fark_AC_A',
                          'Fark_KC_H', 'Fark_KC_D', 'Fark_KC_A']:
                    if c in birlesik.columns:
                        agg_dict[c] = 'first'
                for c in ['HTHG', 'HTAG', 'FTHG', 'FTAG']:
                    if c in birlesik.columns:
                        agg_dict[c] = 'first'

                ozet = birlesik.groupby(grup_kolonlari, as_index=False).agg(agg_dict)
                ozet = ozet.rename(columns={'Eslesen_Bahisci_Str': 'Eslesen_Bahisci'})
            else:
                ozet = birlesik.copy()

            for col in ['HTHG', 'HTAG', 'FTHG', 'FTAG']:
                if col in ozet.columns:
                    ozet[col] = pd.to_numeric(ozet[col], errors='coerce').fillna(0).astype(int)
                else:
                    ozet[col] = 0

            ozet['İY'] = ozet['HTHG'].astype(str) + '-' + ozet['HTAG'].astype(str)
            ozet['MS'] = ozet['FTHG'].astype(str) + '-' + ozet['FTAG'].astype(str)

            temel_kolonlar = ['Date', 'Source_Sheet', 'HomeTeam', 'AwayTeam', 'Eslesen_Bahisci']
            ac_kolonlar = ['AC_H', 'AC_D', 'AC_A']
            kc_kolonlar = ['KC_H', 'KC_D', 'KC_A']
            fark_ac_kolonlar = ['Fark_AC_H', 'Fark_AC_D', 'Fark_AC_A']
            fark_kc_kolonlar = ['Fark_KC_H', 'Fark_KC_D', 'Fark_KC_A']
            skor_kolonlar = ['İY', 'MS']

            gosterilecek_kolonlar = temel_kolonlar[:]
            if acilis_kullan:
                gosterilecek_kolonlar += [c for c in ac_kolonlar if c in ozet.columns]
                gosterilecek_kolonlar += [c for c in fark_ac_kolonlar if c in ozet.columns]
            if kapanis_kullan:
                gosterilecek_kolonlar += [c for c in kc_kolonlar if c in ozet.columns]
                gosterilecek_kolonlar += [c for c in fark_kc_kolonlar if c in ozet.columns]
            gosterilecek_kolonlar += skor_kolonlar

            final_tablo = ozet[[c for c in gosterilecek_kolonlar if c in ozet.columns]].copy()

            final_tablo = final_tablo.rename(columns={
                'AC_H': 'Aç_Ev', 'AC_D': 'Aç_Ber', 'AC_A': 'Aç_Dep',
                'KC_H': 'Kap_Ev', 'KC_D': 'Kap_Ber', 'KC_A': 'Kap_Dep',
                'Fark_AC_H': 'F_Aç_Ev', 'Fark_AC_D': 'F_Aç_Ber', 'Fark_AC_A': 'F_Aç_Dep',
                'Fark_KC_H': 'F_Kap_Ev', 'Fark_KC_D': 'F_Kap_Ber', 'Fark_KC_A': 'F_Kap_Dep',
            })

            st.session_state.final_tablo = final_tablo
            st.session_state.analiz_yapildi = True
            st.session_state.kullanilan_tolerans = tolerans
            st.session_state.kullanilan_psh = ps_h
            st.session_state.kullanilan_psd = ps_d
            st.session_state.kullanilan_psa = ps_a
            st.session_state.kullanilan_psh_k = ps_h_k
            st.session_state.kullanilan_psd_k = ps_d_k
            st.session_state.kullanilan_psa_k = ps_a_k
            st.session_state.kullanilan_mod = mod
            st.session_state.kullanilan_oran_tipi = oran_tipi
            st.session_state.kullanilan_bahisciler = aranacak_bahisciler
            st.session_state.pop('gemini_yorum', None)

    if st.session_state.analiz_yapildi:
        final_tablo = st.session_state.final_tablo
        tolerans_aktif = st.session_state.get('kullanilan_tolerans', tolerans)
        mod_aktif = st.session_state.get('kullanilan_mod', mod)
        oran_tipi_aktif = st.session_state.get('kullanilan_oran_tipi', oran_tipi)
        bahisciler_aktif = st.session_state.get('kullanilan_bahisciler', aranacak_bahisciler)

        mod_metni = mod_aktif if mod_aktif == "Herhangi Biri (Tüm Bahisçiler)" else f"Tek Bahisçi: {bahisciler_aktif[0]}"

        st.markdown(generate_summary_dashboard(len(final_tablo), tolerans_aktif, mod_metni, oran_tipi_aktif), unsafe_allow_html=True)

        st.subheader(f"🎯 {len(final_tablo)} Maç Eşleşti")
        st.dataframe(final_tablo, use_container_width=True)

        st.markdown("### 📊 Skor ve İstatistiki Dağılımlar")

        col_stat1, col_stat2, col_stat3 = st.columns(3)

        iy_dagilim = final_tablo['İY'].value_counts().reset_index().rename(columns={'index': 'İY Skoru', 'İY': 'Adet'})
        iy_dagilim.columns = ['İY Skoru', 'Adet']

        ms_dagilim = final_tablo['MS'].value_counts().reset_index().rename(columns={'index': 'MS Skoru', 'MS': 'Adet'})
        ms_dagilim.columns = ['MS Skoru', 'Adet']

        temp_copy = final_tablo.copy()
        temp_copy['İY/MS'] = temp_copy['İY'].apply(taraf_belirle) + '/' + temp_copy['MS'].apply(taraf_belirle)
        iyms_dagilim = temp_copy['İY/MS'].value_counts().reset_index().rename(columns={'index': 'İY/MS', 'İY/MS': 'Adet'})
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

        st.markdown("---")
        st.markdown("### 🔥 Maç Sonu (MS) Özel Bahis Dağılımı")
        st.caption(f"Son {len(final_tablo)} maç üzerinden hesaplanmıştır. (Alevler: 10-14 maç=1, 15-16 maç=2, 17+ maç=3)")

        temp_gol = final_tablo.copy()
        temp_gol['Toplam_Gol'] = temp_gol['MS'].apply(lambda s: sum(int(x.strip()) for x in s.split('-')) if isinstance(s, str) else 0)
        temp_gol['KG_Var'] = temp_gol['MS'].apply(lambda s: all(int(x) > 0 for x in s.split('-')) if isinstance(s, str) and '-' in s else False)

        if len(temp_gol) > 0:
            toplam_mac = len(temp_gol)
            html_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'

            ust_25_adet = int((temp_gol['Toplam_Gol'] >= 3).sum())
            alev_25 = "".join(["🔥" for _ in range(3 if ust_25_adet >= 17 else 2 if ust_25_adet >= 15 else 1 if ust_25_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS 2.5 Üst", ust_25_adet, toplam_mac, alev_25)
            if alev_25:
                ideal_tercihler.append(f"2.5 Ust - {ust_25_adet} Mac {alev_25}")

            alt_25_adet = int((temp_gol['Toplam_Gol'] <= 2).sum())
            alev_alt_25 = "".join(["🔥" for _ in range(3 if alt_25_adet >= 17 else 2 if alt_25_adet >= 15 else 1 if alt_25_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS 2.5 Alt", alt_25_adet, toplam_mac, alev_alt_25)
            if alev_alt_25:
                ideal_tercihler.append(f"2.5 Alt - {alt_25_adet} Mac {alev_alt_25}")

            ust_55_adet = int((temp_gol['Toplam_Gol'] >= 6).sum())
            alev_55 = "".join(["🔥" for _ in range(3 if ust_55_adet >= 17 else 2 if ust_55_adet >= 15 else 1 if ust_55_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS 5.5 Üst", ust_55_adet, toplam_mac, alev_55)
            if alev_55:
                ideal_tercihler.append(f"5.5 Ust - {ust_55_adet} Mac {alev_55}")

            kg_adet = int(temp_gol['KG_Var'].sum())
            alev_kg = "".join(["🔥" for _ in range(3 if kg_adet >= 17 else 2 if kg_adet >= 15 else 1 if kg_adet >= 10 else 0)])
            html_cards += generate_modern_card("MS KG Var", kg_adet, toplam_mac, alev_kg)
            if alev_kg:
                ideal_tercihler.append(f"KG Var - {kg_adet} Mac {alev_kg}")

            html_cards += '</div>'
            st.markdown(html_cards, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### ⚽ İlk Yarı (İY) Özel Bahis Dağılımı")
            st.caption(f"İlk yarı skorlarına göre hesaplanmıştır.")

            temp_gol['IY_Toplam_Gol'] = temp_gol['İY'].apply(lambda s: sum(int(x.strip()) for x in s.split('-')) if isinstance(s, str) else 0)
            temp_gol['IY_KG_Var'] = temp_gol['İY'].apply(lambda s: all(int(x) > 0 for x in s.split('-')) if isinstance(s, str) and '-' in s else False)
            temp_gol['IY_Taraf'] = temp_gol['İY'].apply(taraf_belirle)

            html_iy_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
            for baslik, adet in [
                ("İY 0.5 Üst", int((temp_gol['IY_Toplam_Gol'] >= 1).sum())),
                ("İY 1.5 Üst", int((temp_gol['IY_Toplam_Gol'] >= 2).sum())),
                ("İY KG Var", int(temp_gol['IY_KG_Var'].sum()))
            ]:
                alev = 3 if adet >= 17 else 2 if adet >= 15 else 1 if adet >= 10 else 0
                alev_str = "".join(["🔥" for _ in range(alev)])
                html_iy_cards += generate_modern_card(baslik, adet, toplam_mac, alev_str)
                if alev > 0:
                    ideal_tercihler.append(f"{baslik} - {adet} Mac {alev_str}")
            html_iy_cards += '</div>'
            st.markdown(html_iy_cards, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🎯 İlk Yarı (İY) Sonuç Dağılımı (1 - X - 2)")

            html_iy_sonuc_cards = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; margin-top: 15px;">'
            for baslik, adet in [
                ("İY Ev Sahibi (1)", int((temp_gol['IY_Taraf'] == '1').sum())),
                ("İY Beraberlik (X)", int((temp_gol['IY_Taraf'] == 'X').sum())),
                ("İY Deplasman (2)", int((temp_gol['IY_Taraf'] == '2').sum()))
            ]:
                alev = 3 if adet >= 17 else 2 if adet >= 15 else 1 if adet >= 10 else 0
                alev_str = "".join(["🔥" for _ in range(alev)])
                html_iy_sonuc_cards += generate_modern_card(baslik, adet, toplam_mac, alev_str)
                if alev > 0:
                    ideal_tercihler.append(f"{baslik} - {adet} Mac {alev_str}")
            html_iy_sonuc_cards += '</div>'
            st.markdown(html_iy_sonuc_cards, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🔄 İY/MS Özel Sonuç Dağılımı")

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
                if alev_sayisi > 0:
                    surpriz_tercihler.append(f"{baslik} - {adet} Mac {alev_gosterim}")

            html_ters_cards += '</div>'
            st.markdown(html_ters_cards, unsafe_allow_html=True)

            # ==========================================
            # ANİMASYONLU SKOR GRAFİKLERİ VE SİMÜLASYON
            # ==========================================
            st.markdown("---")
            st.markdown("### 🎬 Animasyonlu Skor Dağılımları")
            st.caption("▶️ Oynat butonuna basarak veya kaydırıcıyı oynatarak skor dağılımını görebilirsin.")

            tab_ms, tab_iy, tab_carpisma = st.tabs(["🏆 MS Skor Animasyonu", "⚽ İY Skor Animasyonu", "🎱 Çarpışma Simülasyonu"])

            with tab_ms:
                fig_ms_anim = generate_animated_score_chart(
                    temp_gol, skor_kolonu='MS', max_mac=60,
                    title='⚽ Maç Sonu (MS) Skor Dağılımı — Animasyon'
                )
                if fig_ms_anim is not None:
                    st.plotly_chart(fig_ms_anim, use_container_width=True)
                else:
                    st.warning("MS skor verisi bulunamadı.")

            with tab_iy:
                fig_iy_anim = generate_animated_score_chart(
                    temp_gol, skor_kolonu='İY', max_mac=60,
                    title='⚽ İlk Yarı (İY) Skor Dağılımı — Animasyon'
                )
                if fig_iy_anim is not None:
                    st.plotly_chart(fig_iy_anim, use_container_width=True)
                else:
                    st.warning("İY skor verisi bulunamadı.")

            with tab_carpisma:
                render_bouncing_balls_animation(temp_gol, skor_kolonu='MS')

            # ==========================================
            # YAPAY ZEKA YORUMU (UI)
            # ==========================================
            st.markdown("---")
            st.subheader("🤖 Yapay Zeka Maç Yorumu (Gemini)")

            if not gemini_aktif:
                st.warning("⚠️ Gemini API anahtarı tanımlı değil. Streamlit Secrets'a `GEMINI_API_KEY` ekleyin.")
            else:
                if 'HomeTeam' in final_tablo.columns and 'AwayTeam' in final_tablo.columns and len(final_tablo) > 0:
                    ev_takim = str(final_tablo['HomeTeam'].iloc[0])
                    dep_takim = str(final_tablo['AwayTeam'].iloc[0])
                else:
                    ev_takim = "Ev Sahibi"
                    dep_takim = "Deplasman"

                if st.button("✨ Yorumu Oluştur", use_container_width=True):
                    with st.spinner("Yapay zeka maçı analiz ediyor..."):
                        yorum = gemini_ile_mac_yorumu_uret(
                            ev_takim, dep_takim,
                            ms_dagilim, iy_dagilim, iyms_dagilim
                        )
                        st.session_state.gemini_yorum = yorum

                if 'gemini_yorum' in st.session_state:
                    st.info(st.session_state.gemini_yorum)

            # ==========================================
            # PDF RAPORU
            # ==========================================
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
            pdf.cell(180, 26, txt="", ln=False, fill=True)
            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.set_xy(20, 45)
            pdf.cell(85, 5, txt=tr_to_ascii(f"Analiz Edilen Mac Sayisi: {len(final_tablo)} Adet"), ln=False)
            pdf.cell(85, 5, txt=tr_to_ascii(f"Tarih: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"), ln=True)
            pdf.set_xy(20, 50)
            pdf.set_font("Helvetica", '', 9)
            pdf.set_text_color(*color_text_muted)
            tolerans_metni = "Birebir" if tolerans_aktif == 0 else f"±{tolerans_aktif}"

            oran_satirlari = [f"Oran Tipi: {oran_tipi_aktif} | Tolerans: {tolerans_metni}"]
            if oran_tipi_aktif in [MODE_ACILIS, MODE_VEYA, MODE_VE]:
                oran_satirlari.append(
                    f"Acilis Giris: Ev: {st.session_state.get('kullanilan_psh')} | "
                    f"Ber: {st.session_state.get('kullanilan_psd')} | "
                    f"Dep: {st.session_state.get('kullanilan_psa')}"
                )
            if oran_tipi_aktif in [MODE_KAPANIS, MODE_VEYA, MODE_VE]:
                oran_satirlari.append(
                    f"Kapanis Giris: Ev: {st.session_state.get('kullanilan_psh_k')} | "
                    f"Ber: {st.session_state.get('kullanilan_psd_k')} | "
                    f"Dep: {st.session_state.get('kullanilan_psa_k')}"
                )

            y_pos = 50
            for satir in oran_satirlari:
                pdf.set_xy(20, y_pos)
                pdf.cell(170, 4, txt=tr_to_ascii(satir), ln=True)
                y_pos += 4

            pdf.set_xy(20, y_pos + 1)
            pdf.cell(170, 4, txt=tr_to_ascii(
                f"Mod: {mod_aktif} | Bahisciler: {', '.join(bahisciler_aktif)}"
            ), ln=True)
            pdf.ln(14)

            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(180, 8, txt=tr_to_ascii("1. IDEAL TERCIHLER (Banko Adaylari)"), ln=True)

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
                    pdf.cell(120, 8, txt=tr_to_ascii(f" {temiz_metin}"), ln=False)
                    if alev_sayisi > 0:
                        pdf.set_text_color(220, 38, 38)
                        pdf.set_font("Helvetica", 'B', 9)
                        pdf.cell(50, 8, txt=tr_to_ascii(f" {alev_sayisi} ALEVLI POTANSIYEL"), ln=True, align='R')
                    else:
                        pdf.ln(8)
                    pdf.set_y(current_y + 12)
            else:
                pdf.set_font("Helvetica", 'I', 10)
                pdf.set_text_color(*color_text_muted)
                pdf.cell(0, 8, txt=tr_to_ascii(" Bu analiz kriterlerine uyan aktif ideal tahmin bulunmuyor."), ln=True)
            pdf.ln(6)

            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(180, 8, txt=tr_to_ascii("2. SURPRIZ TERCIHLER (Degerli & Yuksek Oranlar)"), ln=True)

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
                    pdf.cell(120, 8, txt=tr_to_ascii(f" {temiz_metin}"), ln=False)
                    if alev_sayisi > 0:
                        pdf.set_text_color(220, 38, 38)
                        pdf.set_font("Helvetica", 'B', 9)
                        pdf.cell(50, 8, txt=tr_to_ascii(f" {alev_sayisi} ALEVLI SURPRIZ"), ln=True, align='R')
                    else:
                        pdf.ln(8)
                    pdf.set_y(current_y + 12)
            else:
                pdf.set_font("Helvetica", 'I', 10)
                pdf.set_text_color(*color_text_muted)
                pdf.cell(0, 8, txt=tr_to_ascii(" Bu analiz kriterlerine uyan aktif surpriz tahmin bulunmuyor."), ln=True)
            pdf.ln(6)

            pdf.set_text_color(*color_text_dark)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.cell(180, 8, txt=tr_to_ascii("3. SKOR VE ISTATISTIKSEL DAGILIMLAR"), ln=True)
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

            # YAPAY ZEKA YORUMU (PDF)
            if 'gemini_yorum' in st.session_state and st.session_state.gemini_yorum:
                pdf.set_text_color(*color_text_dark)
                pdf.set_font("Helvetica", 'B', 12)
                pdf.cell(180, 8, txt=tr_to_ascii("4. YAPAY ZEKA MAC YORUMU (GEMINI)"), ln=True)
                pdf.set_draw_color(139, 92, 246)
                pdf.set_line_width(0.8)
                pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                pdf.ln(4)
                pdf.set_fill_color(*color_sec_bg)
                pdf.set_font("Helvetica", '', 10)
                pdf.set_text_color(*color_text_dark)
                pdf.set_x(15)
                yorum_pdf_metni = tr_to_ascii(st.session_state.gemini_yorum)
                pdf.multi_cell(180, 6, txt=yorum_pdf_metni, fill=True)
                pdf.ln(6)

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
                    <div style="background-color: #ef4444; color: white; padding: 12px 20px; text-align: center; border-radius: 8px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; margin-top: 10px; display: block;">
                        🚀 Mobil Doğrudan İndir (Telefon)
                    </div>
                </a>
                '''
                st.markdown(pdf_link_html, unsafe_allow_html=True)

            except Exception as pdf_error:
                st.error(f"PDF oluşturulurken bir hata oluştu: {pdf_error}")
