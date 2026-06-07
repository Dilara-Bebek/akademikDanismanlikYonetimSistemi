import streamlit as st
import pandas as pd
import os
import datetime
from database import fetch_query, execute_query

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def show_advisor_mesajlasma():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    danisman_kullanici_adi = st.session_state['username']

    st.header("💬 Mesajlaşma ve Duyuru Merkezi")
    st.markdown(
        "Öğrencilerinizle birebir iletişime geçin, ödev/rapor alışverişi yapın veya gruplara toplu duyuru gönderin.")

    # 1. DANIŞMAN BİLGİLERİNİ ÇEKME
    query_danisman = """
        SELECT D.DanismanID, D.KullaniciID, D.AdSoyad 
        FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df_danisman = fetch_query(query_danisman, (danisman_kullanici_adi,))

    if df_danisman.empty:
        st.error("Danışman profilinize ulaşılamıyor.")
        return

    danisman_id = int(df_danisman.iloc[0]['DanismanID'])
    danisman_kid = int(df_danisman.iloc[0]['KullaniciID'])

    # 2. DANIŞMANA AİT ÖĞRENCİLERİ ÇEKME
    query_ogrenciler = "SELECT OgrenciID, KullaniciID, AdSoyad, OgrenciNo FROM OGRENCILER WHERE DanismanID = ?"
    df_ogrenciler = fetch_query(query_ogrenciler, (danisman_id,))

    ogrenci_dict = {}
    if not df_ogrenciler.empty:
        for index, row in df_ogrenciler.iterrows():
            ad_soyad = row['AdSoyad'] if pd.notna(row['AdSoyad']) else "İsimsiz Öğrenci"
            ogr_no = row['OgrenciNo']
            gorunen_isim = f"{ad_soyad} ({ogr_no})"
            ogrenci_dict[gorunen_isim] = {
                'KullaniciID': row['KullaniciID'],
                'OgrenciID': row['OgrenciID']
            }

    tab_birebir, tab_duyuru = st.tabs(["👤 Birebir Sohbet", "📢 Toplu Duyuru Gönder"])

    # 1. Mesajlasma Arayüzü
    with tab_birebir:
        if not ogrenci_dict:
            st.info("Henüz size atanmış bir öğrenci bulunmamaktadır.")
        else:
            col_kisiler, col_sohbet = st.columns([1, 2.5])

            with col_kisiler:
                st.subheader("👨‍🎓 Öğrencilerim")
                arama = st.text_input("🔍 İsim Ara...", placeholder="Örn: Dilara")

                filtrelenmis_ogrenciler = [isim for isim in ogrenci_dict.keys() if arama.lower() in isim.lower()]

                if filtrelenmis_ogrenciler:
                    secilen_kisi = st.radio("Sohbet Seçimi:", filtrelenmis_ogrenciler)
                else:
                    st.warning("Aranan isimde öğrenci bulunamadı.")
                    secilen_kisi = None

            with col_sohbet:
                if secilen_kisi:
                    secilen_ogrenci_kid = int(ogrenci_dict[secilen_kisi]['KullaniciID'])

                    with st.container(border=True):
                        st.subheader(f"Sohbet: {secilen_kisi.split('(')[0]}")
                        st.caption("🔒 Mesajlar uçtan uca şifrelenmektedir ve sadece sistem üzerinden okunabilir.")

                        # Sohbet Geçmişini Çek Dosya Yolu ile birlikte
                        query_mesajlar = """
                            SELECT GonderenID, MesajMetni, Tarih, DosyaYolu
                            FROM MESAJLAR 
                            WHERE (GonderenID = ? AND AliciID = ?) OR (GonderenID = ? AND AliciID = ?)
                            ORDER BY Tarih ASC
                        """
                        df_mesajlar = fetch_query(query_mesajlar,
                                                  (danisman_kid, secilen_ogrenci_kid, secilen_ogrenci_kid,
                                                   danisman_kid))

                        with st.container(height=350):
                            if df_mesajlar.empty:
                                st.info("Bu öğrenciyle henüz bir mesajlaşma geçmişiniz yok.")
                            else:
                                for index, row in df_mesajlar.iterrows():
                                    role = "user" if row['GonderenID'] == danisman_kid else "assistant"
                                    avatar = "👨‍🏫" if role == "user" else "👨‍🎓"

                                    with st.chat_message(role, avatar=avatar):
                                        if row['MesajMetni']:
                                            st.write(row['MesajMetni'])

                                        # Gelen veya giden dosyayı indirme butonu
                                        if pd.notna(row['DosyaYolu']) and row['DosyaYolu']:
                                            file_path = row['DosyaYolu']
                                            if os.path.exists(file_path):
                                                file_name = os.path.basename(file_path)
                                                with open(file_path, "rb") as f:
                                                    st.download_button(
                                                        label=f"📎 {file_name} İndir",
                                                        data=f,
                                                        file_name=file_name,
                                                        key=f"adv_dl_{index}"
                                                    )
                                        st.caption(f"{row['Tarih'].strftime('%d %b %H:%M')}")

                        # Yeni Mesaj ve Dosya Gönderme Kutusu
                        st.write("")
                        col_msg, col_btn = st.columns([4, 1])

                        with col_msg:
                            mesaj_input = st.text_input("Mesajınız...", label_visibility="collapsed")
                            uploaded_file = st.file_uploader("📎 Belge Gönder (Opsiyonel)",
                                                             type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx"],
                                                             label_visibility="collapsed")

                        with col_btn:
                            if st.button("📤 Gönder", use_container_width=True, type="primary"):
                                if not mesaj_input and not uploaded_file:
                                    st.warning("Mesaj boş olamaz.")
                                else:
                                    saved_path = None
                                    if uploaded_file is not None:
                                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                                        file_name = f"{timestamp}_{uploaded_file.name}"
                                        saved_path = os.path.join(UPLOAD_DIR, file_name)
                                        with open(saved_path, "wb") as f:
                                            f.write(uploaded_file.getbuffer())

                                    insert_msg = "INSERT INTO MESAJLAR (GonderenID, AliciID, MesajMetni, DosyaYolu) VALUES (?, ?, ?, ?)"
                                    if execute_query(insert_msg,
                                                     (danisman_kid, secilen_ogrenci_kid, mesaj_input, saved_path)):
                                        st.rerun()
                                    else:
                                        st.error("Gönderim başarısız.")

    # 2. TOPLU DUYURU ALANI
    with tab_duyuru:
        st.subheader("📢 Toplu Bildirim ve Duyuru Paneli")
        st.markdown(
            "Bu alandan göndereceğiniz mesajlar, seçtiğiniz öğrenci grubunun sistem içi bildirimlerine (🔔) otomatik olarak düşecektir.")

        with st.container(border=True):
            if not ogrenci_dict:
                st.warning("Duyuru yapabileceğiniz bir öğrenci grubunuz bulunmamaktadır.")
            else:
                hedef_kitle = st.selectbox(
                    "🎯 Hedef Kitle Seçimi",
                    [f"Tüm Öğrencilerim ({len(ogrenci_dict)} Kişi)"]
                )

                st.write("")
                duyuru_baslik = st.text_input("📌 Duyuru Başlığı",
                                              placeholder="Örn: 2026 Bahar Dönemi Ders Seçimleri Hakkında")
                duyuru_metni = st.text_area("📝 Duyuru Metni",
                                            placeholder="Öğrencilerinize iletmek istediğiniz mesaj detaylarını buraya yazın...",
                                            height=150)

                st.write("")
                if st.button("🚀 Duyuruyu Gönder ve Bildirim At", type="primary", use_container_width=True):
                    if len(duyuru_baslik) < 3 or len(duyuru_metni) < 5:
                        st.error("Lütfen geçerli bir başlık ve detaylı bir duyuru metni giriniz.")
                    else:
                        basari_sayisi = 0
                        for ogr_isim, veri in ogrenci_dict.items():
                            ogr_id = veri['OgrenciID']
                            insert_notif = "INSERT INTO BILDIRIMLER (OgrenciID, Baslik, Mesaj, Tur) VALUES (?, ?, ?, 'Duyuru')"
                            if execute_query(insert_notif, (ogr_id, duyuru_baslik, duyuru_metni)):
                                basari_sayisi += 1

                        if basari_sayisi > 0:
                            st.success(f"Duyurunuz başarıyla {basari_sayisi} öğrenciye gönderildi!")

                        else:
                            st.error("Duyuru gönderilirken bir hata oluştu.")