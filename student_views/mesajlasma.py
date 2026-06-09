import streamlit as st
import pandas as pd
import os
import datetime
from database import fetch_query, execute_query

# Dosyaların kaydedileceği klasör
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def show_student_mesajlasma():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    ogrenci_no = st.session_state['username']

    st.title("💬 Danışman Mesajlaşma")
    st.markdown("---")

    # 1. GEREKLİ ID BİLGİLERİNİ ÇEKME
    query_ids = """
        SELECT O.KullaniciID AS OgrenciKID, O.OgrenciID, D.KullaniciID AS DanismanKID, D.AdSoyad AS DanismanAd
        FROM OGRENCILER O
        INNER JOIN DANISMANLAR D ON O.DanismanID = D.DanismanID
        WHERE O.OgrenciNo = ?
    """
    df_ids = fetch_query(query_ids, (ogrenci_no,))

    if df_ids.empty:
        st.warning("⚠️ Danışmanınız atanmadığı için mesajlaşma başlatılamıyor.")
        return

    ogrenci_kid = int(df_ids.iloc[0]['OgrenciKID'])
    ogrenci_id = int(df_ids.iloc[0]['OgrenciID'])
    danisman_kid = int(df_ids.iloc[0]['DanismanKID'])
    danisman_ad = df_ids.iloc[0]['DanismanAd']

    st.write(f"🗨️ **Danışman:** {danisman_ad} ile sohbet ediyorsunuz.")

    # 2. MESAJ GEÇMİŞİNİ ÇEKME VE GÖRÜNTÜLEME
    query_mesajlar = """
        SELECT GonderenID, MesajMetni, Tarih, DosyaYolu
        FROM MESAJLAR
        WHERE (GonderenID = ? AND AliciID = ?) OR (GonderenID = ? AND AliciID = ?)
        ORDER BY Tarih ASC
    """
    df_mesajlar = fetch_query(query_mesajlar, (ogrenci_kid, danisman_kid, danisman_kid, ogrenci_kid))

    chat_container = st.container(height=400, border=True)

    with chat_container:
        if df_mesajlar.empty:
            st.info("Henüz bir mesajlaşma geçmişiniz bulunmuyor. İlk mesajı siz gönderin!")
        else:
            for index, row in df_mesajlar.iterrows():
                role = "user" if row['GonderenID'] == ogrenci_kid else "assistant"
                label = "Siz" if role == "user" else danisman_ad
                # ogrenci danisman gorsel
                avatar = "👨‍🎓" if role == "user" else "👨‍🏫"

                with st.chat_message(role, avatar=avatar):
                    st.write(f"**{label}**")
                    if row['MesajMetni']:
                        st.write(row['MesajMetni'])

                    # Eğer mesajda dosya eklentisi varsa indirme butonu koy
                    if pd.notna(row['DosyaYolu']) and row['DosyaYolu']:
                        file_path = row['DosyaYolu']
                        if os.path.exists(file_path):
                            file_name = os.path.basename(file_path)
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"📎 {file_name} İndir",
                                    data=f,
                                    file_name=file_name,
                                    key=f"dl_{index}"
                                )

                    # SAAT VE TARİH
                    aylar = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 7: "Tem", 8: "Ağu", 9: "Eyl",
                             10: "Eki", 11: "Kas", 12: "Ara"}
                    zaman = pd.to_datetime(row['Tarih']) + pd.Timedelta(hours=3)
                    tarih_str = f"{zaman.day:02d} {aylar[zaman.month]} {zaman.strftime('%H:%M')}"
                    st.caption(tarih_str)

    # 3. YENİ MESAJ VE DOSYA GÖNDERME
    st.write("")
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            mesaj_input = st.text_area("Mesajınızı yazın...", height=68, label_visibility="collapsed",
                                       placeholder="Mesajınız...")
            uploaded_file = st.file_uploader("📎 Belge veya Rapor Ekle (Opsiyonel)",
                                             type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "xlsx"])

        with col2:
            st.write("")
            st.write("")
            if st.button("📤 Gönder", use_container_width=True, type="primary"):
                if not mesaj_input and not uploaded_file:
                    st.warning("Boş mesaj gönderilemez.")
                else:
                    saved_path = None
                    if uploaded_file is not None:
                        # Benzersiz bir dosya adı oluştur
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        file_name = f"{timestamp}_{uploaded_file.name}"
                        saved_path = os.path.join(UPLOAD_DIR, file_name)
                        with open(saved_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                    # SQL Kayıt
                    insert_msg = "INSERT INTO MESAJLAR (GonderenID, AliciID, MesajMetni, DosyaYolu) VALUES (?, ?, ?, ?)"
                    success = execute_query(insert_msg, (ogrenci_kid, danisman_kid, mesaj_input, saved_path))

                    if success:
                        st.rerun()
                    else:
                        st.error("Mesaj gönderilirken bir hata oluştu.")