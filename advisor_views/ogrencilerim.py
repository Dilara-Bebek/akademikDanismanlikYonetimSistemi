import streamlit as st
import pandas as pd
from database import fetch_query, execute_query

#ÖĞRENCİ DETAY, ÖZEL DURUM VE HEDEF TAKİBİ
@st.dialog("👨‍🎓 Öğrenci Detay Kartı", width="large")
def show_student_profile(ogr_id, df):
    # Seçilen öğrencinin verilerini Dataframe'den çekiyoruz
    ogr = df[df["ÖğrenciID"] == ogr_id].iloc[0]

    st.subheader(f"🎓 {ogr['Ad Soyad']}")
    st.caption(f"🆔 No: {ogr['Öğrenci No']} | 🏢 Bölüm: {ogr['Bölüm']} | 📧 İletişim: {ogr['İletişim']}")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Akademik Durum", "🕒 Geçmiş Randevular", "🎯 Hedef Yönetimi", "📚 Ders ve Not Durumu"])

    with tab1:
        st.markdown("### 📌 Özel Durum Takibi")
        col1, col2 = st.columns(2)

        gno_degeri = float(ogr['GNO']) if pd.notna(ogr['GNO']) else 0.0
        devamsizlik_degeri = int(ogr['Devamsızlık']) if pd.notna(ogr['Devamsızlık']) else 0

        # Risk analizine göre dinamik renklenen metrikler
        col1.metric("Genel Not Ortalaması (GNO)", f"{gno_degeri:.2f}",
                    "Dikkat!" if gno_degeri < 2.0 else "Normal",
                    delta_color="inverse" if gno_degeri < 2.0 else "normal")

        col2.metric("Devamsızlık Oranı", f"%{devamsizlik_degeri}",
                    "Sınırda" if ogr['Risk'] == "Yüksek" else "Güvenli",
                    delta_color="inverse" if ogr['Risk'] == "Yüksek" else "off")

        st.write("")
        if ogr['Risk'] == "Yüksek":
            st.error("🚨 **Kritik Uyarı:** Bu öğrenci akademik risk altındadır (GNO < 2.0 veya yüksek devamsızlık).")
        elif ogr['Risk'] == "Orta":
            st.warning("⚠️ **Uyarı:** Öğrencinin akademik durumu sınırda. Yakından takip edilmeli.")
        else:
            st.success("✅ Öğrencinin akademik durumu stabil.")

    with tab2:
        st.markdown("### 📅 Geçmiş Görüşme Kayıtları")
        query_gecmis = """
            SELECT Tarih, Konu, Durum 
            FROM RANDEVULAR 
            WHERE OgrenciID = ? AND Durum IN ('Tamamlandı', 'Onaylandı')
            ORDER BY Tarih DESC
        """
        df_gecmis = fetch_query(query_gecmis, (int(ogr_id),))

        if df_gecmis.empty:
            st.info("Bu öğrenciyle henüz kayıtlı bir görüşme veya randevu bulunmamaktadır.")
        else:
            st.dataframe(df_gecmis, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### 🎯 Öğrenciye Yeni Hedef Ata")

        yeni_hedef = st.text_input("Hedef / Görev Tanımı",
                                   placeholder="Örn: TÜBİTAK 2209-A literatür taramasını tamamla...")

        if st.button("➕ Hedefi Ata", type="primary", use_container_width=True):
            if len(yeni_hedef) > 3:
                insert_query = "INSERT INTO AKADEMIK_HEDEFLER (OgrenciID, HedefMetni, Durum, EklenmeTarihi) VALUES (?, ?, 'Devam Ediyor', GETDATE())"
                if execute_query(insert_query, (int(ogr_id), yeni_hedef)):
                    st.toast("Yeni hedef başarıyla atandı!", icon="🎯")
                    st.rerun()
                else:
                    st.error("Hedef atanırken veritabanı hatası oluştu.")
            else:
                st.warning("Lütfen geçerli bir hedef tanımı girin.")

        st.divider()
        st.markdown("### 📋 Öğrencinin Mevcut Hedefleri")
        query_hedefler = """
            SELECT 
                HedefMetni as [Görev / Hedef], 
                Durum, 
                FORMAT(EklenmeTarihi, 'yyyy-MM-dd') as [Veriliş Tarihi] 
            FROM AKADEMIK_HEDEFLER 
            WHERE OgrenciID = ? 
            ORDER BY HedefID DESC
        """
        df_hedefler = fetch_query(query_hedefler, (int(ogr_id),))

        if not df_hedefler.empty:
            st.dataframe(df_hedefler, use_container_width=True, hide_index=True)
        else:
            st.info("Bu öğrenciye henüz bir hedef atanmamış.")

    with tab4:
        st.markdown("### 📚 Transkript Ders ve Not Durumu (AI Destekli)")

        query_dersler = "SELECT DersAdi, Performans FROM DERS_DURUMLARI WHERE OgrenciID = ?"
        df_dersler = fetch_query(query_dersler, (int(ogr_id),))

        if df_dersler.empty:
            st.info("Öğrenci henüz transkript verilerini sisteme senkronize etmemiş.")
        else:
            zayif_dersler = df_dersler[df_dersler["Performans"] == "Zayıf"]
            zayif_sayisi = len(zayif_dersler)

            if zayif_sayisi > 0:
                st.error(
                    f"🚨 **Erken Akademik Uyarı:** Bu öğrencinin transkriptinde **{zayif_sayisi} adet** zayıf performanslı (FF/FD/Başarısız) ders tespit edilmiştir! Dönem kaybını engellemek için akademik müdahale önerilir.")
            else:
                st.success(
                    "✅ **Akademik Durum Başarılı:** Öğrencinin transkriptinde kritik düzeyde zayıf veya başarısız ders bulunmamaktadır.")

            st.write("")
            st.markdown("**📋 Transkript Ders Dağılım Detayları:**")

            c_iyi, c_orta, c_zayif = st.columns(3)

            with c_iyi:
                st.markdown("🍏 **Başarılı Olanlar**")
                iyi_dersler = df_dersler[df_dersler["Performans"] == "İyi"]["DersAdi"].tolist()
                if iyi_dersler:
                    for d in iyi_dersler:
                        st.caption(f"🟢 {d}")
                else:
                    st.write("*Kayıt yok.*")

            with c_orta:
                st.markdown("🟡 **Orta Seviye**")
                orta_dersler = df_dersler[df_dersler["Performans"] == "Orta"]["DersAdi"].tolist()
                if orta_dersler:
                    for d in orta_dersler:
                        st.caption(f"🟡 {d}")
                else:
                    st.write("*Kayıt yok.*")

            with c_zayif:
                st.markdown("🔴 **Zayıf / Riskli Olanlar**")
                if zayif_sayisi > 0:
                    for d in zayif_dersler["DersAdi"].tolist():
                        st.caption(f"🔴 {d}")
                else:
                    st.write("*Kayıt yok.*")


def show_ogrencilerim():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    danisman_kullanici_adi = st.session_state['username']

    st.header("👨‍🎓 Sorumlu Olduğum Öğrenciler")
    st.markdown(
        "Danışmanlığını yürüttüğünüz öğrencilerin listesini, iletişim bilgilerini ve **özel akademik durumlarını (Risk Takibi)** buradan yönetebilirsiniz.")

    # 1. DANIŞMAN ID'SİNİ ÇEKME
    query_danisman = """
        SELECT D.DanismanID FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df_danisman = fetch_query(query_danisman, (danisman_kullanici_adi,))

    if df_danisman.empty:
        st.error("Sisteme kayıtlı bir danışman profiliniz bulunamadı.")
        return

    danisman_id = int(df_danisman.iloc[0]['DanismanID'])

    # 2. ÖĞRENCİ VERİLERİNİ ÇEKME
    query_ogrenciler = """
        SELECT O.OgrenciID, O.OgrenciNo, O.AdSoyad, O.Bolum, O.Email, O.GNO, O.DevamsizlikOrani,
               COUNT(R.RandevuID) AS ToplamRandevu
        FROM OGRENCILER O
        LEFT JOIN RANDEVULAR R ON O.OgrenciID = R.OgrenciID AND R.DanismanID = O.DanismanID
        WHERE O.DanismanID = ?
        GROUP BY O.OgrenciID, O.OgrenciNo, O.AdSoyad, O.Bolum, O.Email, O.GNO, O.DevamsizlikOrani
    """
    df_raw = fetch_query(query_ogrenciler, (danisman_id,))

    if df_raw.empty:
        st.info("Sisteme kayıtlı öğrenciniz bulunmamaktadır.")
        return

    ogr_list = []
    risk_sayisi = 0

    for index, row in df_raw.iterrows():
        gno = float(row['GNO']) if pd.notna(row['GNO']) else 0.0
        devamsizlik = int(row['DevamsizlikOrani']) if pd.notna(row['DevamsizlikOrani']) else 0

        if gno < 2.0 or devamsizlik > 20:
            risk = "Yüksek"
            risk_sayisi += 1
        elif gno < 2.5 or devamsizlik > 10:
            risk = "Orta"
        else:
            risk = "Düşük"

        ogr_list.append({
            "ÖğrenciID": row['OgrenciID'],
            "Öğrenci No": row['OgrenciNo'],
            "Ad Soyad": row['AdSoyad'] if pd.notna(row['AdSoyad']) else "İsimsiz",
            "Bölüm": row['Bolum'] if pd.notna(row['Bolum']) else "Bölüm Belirtilmemiş",
            "İletişim": row['Email'] if pd.notna(row['Email']) else "E-posta Yok",
            "Randevu Sayısı": int(row['ToplamRandevu']),
            "GNO": gno,
            "Devamsızlık": devamsizlik,
            "Risk": risk
        })

    ogr_df = pd.DataFrame(ogr_list)

    #3. ÜST METRİKLER
    c1, c2, c3 = st.columns(3)
    c1.metric("Sorumlu Olunan Öğrenci", len(ogr_df), "Aktif Dönem")
    c2.metric("Riskli Öğrenci Sayısı", risk_sayisi, "GNO < 2.0", delta_color="inverse" if risk_sayisi > 0 else "off")

    ort_randevu = round(ogr_df['Randevu Sayısı'].mean(), 1) if not ogr_df.empty else 0
    c3.metric("Ortalama Görüşme Oranı", ort_randevu, "Kişi Başı")

    st.divider()

    #4. FİLTRELEME VE ARAMA
    with st.container(border=True):
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            arama = st.text_input("🔍 İsim, Okul No veya E-Posta ile Ara", placeholder="Örn: Dilara...")
        with f2:
            risk_filtre = st.selectbox("⚠️ Risk Durumuna Göre Filtrele", ["Tümü", "Yüksek", "Orta", "Düşük"])
        with f3:
            siralama = st.selectbox("↕️ Tabloyu Sırala", ["GNO (Azalan)", "GNO (Artan)", "En Çok Randevu"])

    filtered_df = ogr_df.copy()

    filtered_df['Ad Soyad'] = filtered_df['Ad Soyad'].astype(str)
    filtered_df['İletişim'] = filtered_df['İletişim'].astype(str)

    if arama:
        filtered_df = filtered_df[filtered_df["Ad Soyad"].str.contains(arama, case=False) |
                                  filtered_df["Öğrenci No"].str.contains(arama, case=False) |
                                  filtered_df["İletişim"].str.contains(arama, case=False)]
    if risk_filtre != "Tümü":
        filtered_df = filtered_df[filtered_df["Risk"] == risk_filtre]

    if siralama == "GNO (Azalan)":
        filtered_df = filtered_df.sort_values(by="GNO", ascending=False)
    elif siralama == "GNO (Artan)":
        filtered_df = filtered_df.sort_values(by="GNO", ascending=True)
    elif siralama == "En Çok Randevu":
        filtered_df = filtered_df.sort_values(by="Randevu Sayısı", ascending=False)

    # 5. ANA LİSTE
    st.write("")
    st.subheader("📋 Öğrenci Listesi")
    if filtered_df.empty:
        st.warning("Filtrelerinize uygun öğrenci bulunamadı.")
    else:
        gosterilecek_kolonlar = ["Öğrenci No", "Ad Soyad", "Bölüm", "İletişim", "Randevu Sayısı", "Risk"]
        st.dataframe(filtered_df[gosterilecek_kolonlar], use_container_width=True, hide_index=True)

        #6. İŞLEMLER
        st.write("")
        st.subheader("⚡ Hızlı Öğrenci İşlemleri")
        with st.container(border=True):
            col_sel, col_btn = st.columns([2, 1])
            with col_sel:
                secenekler = filtered_df["ÖğrenciID"].tolist()
                formatla = lambda \
                        x: f"{filtered_df[filtered_df['ÖğrenciID'] == x].iloc[0]['Ad Soyad']} ({filtered_df[filtered_df['ÖğrenciID'] == x].iloc[0]['Öğrenci No']})"

                secilen_ogr_id = st.selectbox("İncelemek veya işlem yapmak istediğiniz öğrenciyi seçin:", secenekler,
                                              format_func=formatla)

            with col_btn:
                st.write("")
                st.write("")
                if st.button("👁️ Profili Görüntüle", use_container_width=True, type="primary"):
                    if secilen_ogr_id:
                        show_student_profile(secilen_ogr_id, filtered_df)