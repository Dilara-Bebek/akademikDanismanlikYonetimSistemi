import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query


# GÖRÜŞME NOTU DETAYI
@st.dialog("📄 Görüşme Tutanağı Detayı")
def show_note_detail(note_id, df):
    note = df[df["NotID"] == note_id].iloc[0]

    st.subheader(f"🎓 Öğrenci: {note['Öğrenci']}")
    st.caption(f"📅 Not Tarihi: {note['OlusturulmaTarihi']} | 🔗 İlişkili Randevu: #{note['RandevuID']}")

    st.divider()

    st.markdown("### 📝 Görüşme Özeti")
    st.info(note['Ozet'])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚠️ Karşılaşılan Sorunlar")
        st.warning(note['Sorunlar'] if pd.notna(note['Sorunlar']) else "Belirtilmedi.")
    with col2:
        st.markdown("### 💡 Verilen Tavsiyeler")
        st.success(note['Tavsiyeler'] if pd.notna(note['Tavsiyeler']) else "Belirtilmedi.")

    st.divider()

    # Performans Skoru Görselleştirmesi
    st.markdown("### 📊 Öğrenci Performans Değerlendirmesi")
    performans = note['Performans'] if pd.notna(note['Performans']) else "Orta"

    if performans == "Çok İyi":
        st.metric("Genel Değerlendirme", "⭐⭐⭐⭐⭐ Çok İyi", "Beklentilerin Üzerinde")
    elif performans == "İyi":
        st.metric("Genel Değerlendirme", "⭐⭐⭐⭐ İyi", "Gelişim Gösteriyor")
    elif performans == "Orta":
        st.metric("Genel Değerlendirme", "⭐⭐⭐ Orta", "Takip Edilmeli", delta_color="off")
    else:
        st.metric("Genel Değerlendirme", "⭐⭐ Zayıf", "Kritik Müdahale Gerekiyor", delta_color="inverse")

    st.divider()

    # Öğrenci tarafında yazdığımız kodla uyumlu olması için DanismanNotu kısmını da gösterelim
    st.markdown("### 👨‍🏫 Öğrenci Paneline Düşecek Kısa Not")
    st.write(note['DanismanNotu'] if pd.notna(note['DanismanNotu']) else "Öğrenciye özel kısa not eklenmemiş.")


def show_gorusme_notlari():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    danisman_kullanici_adi = st.session_state['username']

    st.header("📝 Görüşme Notları ve Öğrenci Arşivi")
    st.markdown(
        "Randevularınızın ardından öğrenci gelişimini takip etmek için resmi kayıtları (tutanakları) buradan oluşturabilir ve geçmiş notları inceleyebilirsiniz.")

    # 1. DANIŞMAN ID'SİNİ ÇEKME
    query_danisman = """
        SELECT D.DanismanID FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df_danisman = fetch_query(query_danisman, (danisman_kullanici_adi,))
    if df_danisman.empty:
        st.error("Danışman profili bulunamadı.")
        return
    danisman_id = int(df_danisman.iloc[0]['DanismanID'])

    tab_ekle, tab_arsiv = st.tabs(["➕ Yeni Görüşme Notu Ekle", "📂 Geçmiş Görüşme Kayıtları (Arşiv)"])

    # 1. YENİ NOT EKLEME FORMU
    with tab_ekle:
        # Sadece bu danışmana ait olan ve "Tamamlandı" durumundaki randevuları çekiyoruz
        # Biz burada "Onaylandı" ve "Tamamlandı" olanları çekiyoruz
        query_randevular = """
            SELECT R.RandevuID, O.AdSoyad, R.Tarih, R.Saat
            FROM RANDEVULAR R
            INNER JOIN OGRENCILER O ON R.OgrenciID = O.OgrenciID
            WHERE R.DanismanID = ? AND R.Durum IN ('Onaylandı', 'Tamamlandı')
            ORDER BY R.Tarih DESC
        """
        df_randevular = fetch_query(query_randevular, (danisman_id,))

        with st.container(border=True):
            st.subheader("Yeni Tutanak Oluştur")
            st.caption(
                "Lütfen not girmek istediğiniz randevuyu seçin. (Sadece onaylanmış veya tamamlanmış randevular listelenir)")

            if df_randevular.empty:
                st.warning(
                    "Not girebileceğiniz aktif bir randevunuz bulunmamaktadır. Önce 'Randevularım' sayfasından randevu onaylamanız veya oluşturmanız gerekir.")
            else:
                with st.form("yeni_not_form"):
                    # Randevuları Selectbox'a veriyoruz
                    randevu_dict = {}
                    for index, row in df_randevular.iterrows():
                        isim = row['AdSoyad'] if pd.notna(row['AdSoyad']) else "İsimsiz"
                        saat_kisa = str(row['Saat'])[:5]
                        formatli_metin = f"#{row['RandevuID']} - {isim} ({row['Tarih']} {saat_kisa})"
                        randevu_dict[formatli_metin] = row['RandevuID']

                    secilen_randevu_metni = st.selectbox("🔗 İlişkili Randevu Seçin", list(randevu_dict.keys()))
                    secilen_r_id = randevu_dict[secilen_randevu_metni]

                    st.write("")
                    ozet = st.text_area("📝 Görüşme Özeti (Zorunlu)",
                                        placeholder="Görüşmenin genel amacı ve konuşulan ana başlıklar...", height=100)

                    col_text1, col_text2 = st.columns(2)
                    with col_text1:
                        sorunlar = st.text_area("⚠️ Sorunlar / Eksikler",
                                                placeholder="Öğrencinin zorlandığı konular, devamsızlık veya akademik sorunlar...",
                                                height=100)
                    with col_text2:
                        tavsiyeler = st.text_area("💡 Tavsiyeler / Hedefler",
                                                  placeholder="Bir sonraki görüşmeye kadar yapması gerekenler...",
                                                  height=100)

                    performans = st.select_slider("📊 Öğrenci Katılımı ve Performansı",
                                                  options=["Zayıf", "Orta", "İyi", "Çok İyi"], value="İyi")

                    danisman_notu = st.text_input("👨‍🏫 Öğrenciye Kısa Not (Öğrenci Paneline Düşer)",
                                                  placeholder="Örn: Algoritma dersine ağırlık vermelisin.")

                    st.write("")
                    if st.form_submit_button("💾 Görüşme Notunu Kaydet ve Randevuyu Tamamla", type="primary",
                                             use_container_width=True):
                        if len(ozet) < 5:
                            st.error("Lütfen en azından kısa bir görüşme özeti giriniz.")
                        else:
                            # 1. GORUSME_NOTLARI tablosuna kayıt at (Önce bu randevu için not var mı kontrol et, varsa Update, yoksa Insert yapalım)
                            check_query = "SELECT COUNT(*) as sayi FROM GORUSME_NOTLARI WHERE RandevuID = ?"
                            df_check = fetch_query(check_query, (secilen_r_id,))

                            is_exists = df_check.iloc[0]['sayi'] > 0 if not df_check.empty else False

                            if is_exists:
                                update_not_query = """
                                    UPDATE GORUSME_NOTLARI 
                                    SET Ozet = ?, Sorunlar = ?, Tavsiyeler = ?, Performans = ?, DanismanNotu = ?
                                    WHERE RandevuID = ?
                                """
                                success_not = execute_query(update_not_query,
                                                            (ozet, sorunlar, tavsiyeler, performans, danisman_notu,
                                                             secilen_r_id))
                            else:
                                insert_not_query = """
                                    INSERT INTO GORUSME_NOTLARI (RandevuID, Ozet, Sorunlar, Tavsiyeler, Performans, DanismanNotu)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """
                                success_not = execute_query(insert_not_query,
                                                            (secilen_r_id, ozet, sorunlar, tavsiyeler, performans,
                                                             danisman_notu))

                            # 2.RANDEVULAR tablosunda durumu "Tamamlandı" yap
                            update_randevu = "UPDATE RANDEVULAR SET Durum = 'Tamamlandı' WHERE RandevuID = ?"
                            success_randevu = execute_query(update_randevu, (secilen_r_id,))

                            if success_not and success_randevu:
                                st.success(
                                    f"Görüşme tutanağı kaydedildi ve #{secilen_r_id} numaralı randevu 'Tamamlandı' olarak işaretlendi!")

                            else:
                                st.error("Veritabanına kaydedilirken bir hata oluştu.")

    #2. GÖRÜŞME GEÇMİŞİ VE ARŞİV LİSTESİ
    with tab_arsiv:
        st.subheader("📂 Sistemdeki Geçmiş Notlar")

        # Danışmanın girdiği tüm notları veritabanından çekelim
        query_arsiv = """
            SELECT GN.NotID, GN.RandevuID, O.AdSoyad AS Öğrenci, GN.OlusturulmaTarihi, GN.Ozet, GN.Performans, GN.Sorunlar, GN.Tavsiyeler, GN.DanismanNotu
            FROM GORUSME_NOTLARI GN
            INNER JOIN RANDEVULAR R ON GN.RandevuID = R.RandevuID
            INNER JOIN OGRENCILER O ON R.OgrenciID = O.OgrenciID
            WHERE R.DanismanID = ?
            ORDER BY GN.OlusturulmaTarihi DESC
        """
        df_arsiv = fetch_query(query_arsiv, (danisman_id,))

        if df_arsiv.empty:
            st.info("Sistemde henüz oluşturulmuş bir görüşme tutanağı bulunmuyor.")
            return

        # Tarihi string formatına çevir
        df_arsiv['OlusturulmaTarihi'] = df_arsiv['OlusturulmaTarihi'].astype(str).str[:16]

        # Filtreleme Alanı
        with st.container(border=True):
            f_col1, f_col2 = st.columns([2, 1])
            with f_col1:
                arama = st.text_input("🔍 Öğrenci Adı veya Görüşme Özeti ile Ara")
            with f_col2:
                siralama = st.selectbox("↕️ Sırala", ["En Yeniler Önce", "En Eskiler Önce"])

        filtered_notes = df_arsiv.copy()

        # Boşluk hatalarını engelle
        filtered_notes['Öğrenci'] = filtered_notes['Öğrenci'].astype(str)
        filtered_notes['Ozet'] = filtered_notes['Ozet'].astype(str)

        if arama:
            filtered_notes = filtered_notes[
                filtered_notes["Öğrenci"].str.contains(arama, case=False) |
                filtered_notes["Ozet"].str.contains(arama, case=False)
                ]

        if siralama == "En Eskiler Önce":
            filtered_notes = filtered_notes.sort_values(by="OlusturulmaTarihi", ascending=True)

        st.write("")
        if filtered_notes.empty:
            st.warning("Aranan kritere uygun arşiv bulunamadı.")
        else:
            # Görüntülenecek tablo
            tablo_kolonlari = ["NotID", "Öğrenci", "OlusturulmaTarihi", "Ozet", "Performans"]
            # Tablo başlıkları
            gosterim_df = filtered_notes[tablo_kolonlari].rename(columns={'OlusturulmaTarihi': 'Tarih', 'Ozet': 'Özet'})

            st.dataframe(gosterim_df, use_container_width=True, hide_index=True)

            st.write("")
            with st.container(border=True):
                detay_col1, detay_col2 = st.columns([2, 1])
                with detay_col1:
                    # Selectbox formatı
                    format_func = lambda \
                        x: f"Not #{x} - {filtered_notes[filtered_notes['NotID'] == x].iloc[0]['Öğrenci']}"
                    secilen_not_id = st.selectbox("Tamamını okumak istediğiniz görüşme tutanağını seçin:",
                                                  filtered_notes["NotID"].tolist(), format_func=format_func)
                with detay_col2:
                    st.write("")
                    st.write("")
                    if st.button("👁️ Tutanak Detayını Aç", type="primary", use_container_width=True):
                        show_note_detail(secilen_not_id, filtered_notes)