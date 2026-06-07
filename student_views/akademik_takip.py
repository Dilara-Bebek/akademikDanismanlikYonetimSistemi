import streamlit as st
import pandas as pd
import plotly.express as px
import pypdf
import time
import json
import google.generativeai as genai
from database import fetch_query, execute_query
from datetime import datetime

try:
    GEMINI_API_KEY = st.secrets["gemini"]["api_key"]
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"Yapay zeka yapılandırma hatası: {e}")

def show_akademik_takip():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    ogrenci_no = st.session_state['username']

    st.title("📈 Akademik Takip ve Gelişim")
    st.markdown("---")

    query_student = "SELECT OgrenciID FROM OGRENCILER WHERE OgrenciNo = ?"
    df_student = fetch_query(query_student, (ogrenci_no,))
    if df_student.empty:
        return
    ogrenci_id = int(df_student.iloc[0]['OgrenciID'])

    query_son_randevu = """
        SELECT TOP 1 Tarih 
        FROM RANDEVULAR 
        WHERE OgrenciID = ? AND Durum = 'Tamamlandı' 
        ORDER BY Tarih DESC
    """
    df_son_randevu = fetch_query(query_son_randevu, (ogrenci_id,))

    uyari_mesajlari = []

    if not df_son_randevu.empty:
        son_tarih = pd.to_datetime(df_son_randevu.iloc[0]['Tarih']).date()
        bugun = datetime.now().date()
        fark = (bugun - son_tarih).days

        if fark > 14:
            uyari_mesajlari.append(
                f"⚠️ **Uyarı:** Son görüşmenizin üzerinden {fark} gün geçmiş. Durumunuzu değerlendirmek için yeni bir randevu almanız önerilir.")
    else:
        uyari_mesajlari.append("⚠️ **Bilgi:** Sisteme kayıtlı tamamlanmış bir danışman görüşmeniz bulunmuyor.")

    if uyari_mesajlari:
        for uyari in uyari_mesajlari:
            st.warning(uyari)
    else:
        st.success("✅ Harika gidiyorsunuz! Danışman görüşmelerinizi düzenli olarak gerçekleştiriyorsunuz.")

    st.markdown("---")

    st.subheader("🤖 Yapay Zeka ile Transkript Eşitleme")
    with st.expander("PDF Transkript Yükle ve AI ile Analiz Et", expanded=True):
        st.info(
            "E-Devlet üzerinden aldığınız güncel transkriptinizi PDF formatında yükleyin. **Google Gemini Yapay Zeka Modeli** belgeyi okuyarak derslerinizi ve GNO'nuzu %100 doğrulukla sisteme aktaracaktır.")

        uploaded_file = st.file_uploader("Transkript Yükle (PDF)", type="pdf")

        if uploaded_file is not None:
            if st.button("🧠 Yapay Zeka Analizini Başlat", type="primary", use_container_width=True):
                if uploaded_file.size == 0:
                    st.error(
                        "🚨 Yüklediğiniz dosya 0 Byte (Boş veya Bozuk). Lütfen içi dolu, geçerli bir PDF dosyası yüklediğinizden emin olun.")
                elif "gemini" not in st.secrets or "api_key" not in st.secrets["gemini"]:
                    st.error(
                        "🚨 Geliştirici Uyarısı: Lütfen secrets.toml dosyasına geçerli bir API anahtarı girin.")
                else:
                    with st.spinner(
                            "Yapay Zeka belgenizi okuyor ve karmaşık verileri çözümlüyor. Bu işlem birkaç saniye sürebilir..."):
                        try:
                            reader = pypdf.PdfReader(uploaded_file)
                            raw_text = ""
                            for page in reader.pages:
                                raw_text += page.extract_text() + "\n"

                            if not raw_text.strip():
                                st.error(
                                    "🚨 Yüklenen PDF dosyasından metin okunamadı (Dosya şifreli veya resim formatında olabilir).")
                                st.stop()

                            prompt = f"""
                            Sen kıdemli bir akademik veri analiz asistanısın. Aşağıda bir Türk üniversite öğrencisine ait E-Devlet transkript metni bulunuyor. 
                            Görevlerin:
                            1. Belgenin genelindeki güncel 'Genel Not Ortalamasını' (GNO/GANO) bul.
                            2. Öğrencinin aldığı tüm dersleri (Ders Kodu, Ders Adı ve Harf Notu) listele.
                            3. Yanıtını SADECE aşağıdaki JSON formatında ver. JSON dışında hiçbir açıklama, yorum veya markdown kodu (```json) ekleme. Doğrudan süslü parantez ile başla.

                            Örnek Format:
                            {{
                                "gno": 2.85,
                                "dersler": [
                                    {{"kod": "BIL101", "ad": "Programlama", "not": "AA"}},
                                    {{"kod": "MAT101", "ad": "Matematik", "not": "CB"}}
                                ]
                            }}

                            İşte analiz etmen gereken Transkript Metni:
                            {raw_text}
                            """

                            response = ai_model.generate_content(prompt)
                            ai_response = response.text.strip()

                            if ai_response.startswith("```json"):
                                ai_response = ai_response[7:-3].strip()
                            elif ai_response.startswith("```"):
                                ai_response = ai_response[3:-3].strip()

                            parsed_data = json.loads(ai_response)
                            gno_val = float(parsed_data.get("gno", 0.0))
                            dersler = parsed_data.get("dersler", [])

                            if len(dersler) > 0:
                                execute_query("UPDATE OGRENCILER SET GNO = ? WHERE OgrenciID = ?",
                                              (gno_val, ogrenci_id))
                                execute_query("DELETE FROM DERS_DURUMLARI WHERE OgrenciID = ?", (ogrenci_id,))

                                eklenen_ders = 0
                                for ders in dersler:
                                    kod = ders.get("kod", "BİLİNMİYOR")
                                    ad = ders.get("ad", "İsimsiz Ders")
                                    harf = str(ders.get("not", "FF")).upper()

                                    if harf in ['AA', 'BA', 'BB', 'YT']:
                                        perf = 'İyi'
                                    elif harf in ['CB', 'CC', 'DC']:
                                        perf = 'Orta'
                                    else:
                                        perf = 'Zayıf'

                                    execute_query(
                                        "INSERT INTO DERS_DURUMLARI (OgrenciID, DersAdi, Performans) VALUES (?, ?, ?)",
                                        (ogrenci_id, f"{kod} {ad}", perf))
                                    eklenen_ders += 1

                                log_msg = f"{ogrenci_no} numaralı öğrenci Yapay Zeka ile transkriptini eşitledi."
                                execute_query(
                                    "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('AI Transkript Senkronizasyonu', ?, 'Başarılı')",
                                    (log_msg,))

                                st.success(
                                    f"✅ Yapay Zeka Analizi Başarılı! Sisteme **{eklenen_ders}** ders işlendi. Yeni GNO: **{gno_val}**")
                                time.sleep(3)
                                st.rerun()
                            else:
                                st.error(
                                    "Yapay zeka belgede herhangi bir ders verisi bulamadı. Lütfen geçerli bir transkript yüklediğinizden emin olun.")

                        except Exception as e:
                            st.error(f"Yapay Zeka analizi sırasında beklenmeyen bir hata oluştu: {e}")

    st.markdown("---")

    st.subheader("📊 Performans Analizi")

    query_ders = "SELECT DersAdi, Performans FROM DERS_DURUMLARI WHERE OgrenciID = ?"
    df_ders = fetch_query(query_ders, (ogrenci_id,))

    if not df_ders.empty:
        performans_puan = {'İyi': 3, 'Orta': 2, 'Zayıf': 1}
        df_ders['Puan'] = df_ders['Performans'].map(performans_puan)

        fig = px.bar(df_ders, x='DersAdi', y='Puan', color='Performans',
                     color_discrete_map={'İyi': '#2ecc71', 'Orta': '#f1c40f', 'Zayıf': '#e74c3c'},
                     title="Akademik Gelişim Grafiği (Tüm Dersler)",
                     labels={'Puan': 'Performans Seviyesi', 'DersAdi': 'Dersler'})
        fig.update_yaxes(tickvals=[1, 2, 3], ticktext=['Zayıf', 'Orta', 'İyi'])
        fig.update_layout(xaxis_tickangle=-45)

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📚 Tüm Derslerin Detaylı Listesini Gör"):
            col1, col2, col3 = st.columns(3)
            for i, (index, row) in enumerate(df_ders.iterrows()):
                ders = row['DersAdi']
                perf = row['Performans']

                if i % 3 == 0:
                    col1.markdown(
                        f"**{ders}** : {'🟢 İyi' if perf == 'İyi' else '🟡 Orta' if perf == 'Orta' else '🔴 Zayıf'}")
                elif i % 3 == 1:
                    col2.markdown(
                        f"**{ders}** : {'🟢 İyi' if perf == 'İyi' else '🟡 Orta' if perf == 'Orta' else '🔴 Zayıf'}")
                else:
                    col3.markdown(
                        f"**{ders}** : {'🟢 İyi' if perf == 'İyi' else '🟡 Orta' if perf == 'Orta' else '🔴 Zayıf'}")
    else:
        st.info("Yapay Zeka ile transkriptinizi yüklediğinizde grafikler bu alanda otomatik oluşturulacaktır.")

    st.markdown("---")

    col_hedef, col_notlar = st.columns(2)

    with col_hedef:
        st.subheader("🎯 Size Verilen Hedefler")
        query_hedef = "SELECT HedefID, HedefMetni, Durum, FORMAT(EklenmeTarihi, 'yyyy-MM-dd') as Tarih FROM AKADEMIK_HEDEFLER WHERE OgrenciID = ? ORDER BY HedefID DESC"
        df_hedef = fetch_query(query_hedef, (ogrenci_id,))

        if not df_hedef.empty:
            for index, row in df_hedef.iterrows():
                h_id = row['HedefID']
                h_metin = row['HedefMetni']
                durum = row['Durum']
                tarih = row['Tarih']

                is_checked = True if durum == 'Tamamlandı' else False

                metin_gosterimi = f"{h_metin} *(Veriliş: {tarih})*"

                if st.checkbox(metin_gosterimi, value=is_checked, key=f"hedef_{h_id}"):
                    if not is_checked:
                        execute_query("UPDATE AKADEMIK_HEDEFLER SET Durum = 'Tamamlandı' WHERE HedefID = ?", (h_id,))
                        st.toast("Tebrikler, bir hedefi daha tamamladınız!", icon="✅")
                        st.rerun()
                else:
                    if is_checked:
                        execute_query("UPDATE AKADEMIK_HEDEFLER SET Durum = 'Devam Ediyor' WHERE HedefID = ?", (h_id,))
                        st.rerun()
        else:
            st.info("Şu an için atanmış aktif bir hedefiniz bulunmamaktadır.")

    with col_notlar:
        st.subheader("📝 Son Görüşme Notları")
        query_ozet = """
            SELECT TOP 3 R.Tarih, R.Konu, GN.DanismanNotu
            FROM RANDEVULAR R
            INNER JOIN GORUSME_NOTLARI GN ON R.RandevuID = GN.RandevuID
            WHERE R.OgrenciID = ? AND R.Durum = 'Tamamlandı'
            ORDER BY R.Tarih DESC
        """
        df_ozet = fetch_query(query_ozet, (ogrenci_id,))

        if not df_ozet.empty:
            for index, row in df_ozet.iterrows():
                tarih = str(row['Tarih'])
                konu = row['Konu']
                not_metni = row['DanismanNotu'] if pd.notna(row['DanismanNotu']) else "Not girilmemiş."

                with st.container(border=True):
                    st.caption(f"📅 {tarih} | **Konu:** {konu}")
                    st.write(f"*{not_metni}*")
        else:
            st.info("Sistemde değerlendirilmiş görüşme notu bulunmamaktadır.")