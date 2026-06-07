import streamlit as st
import pandas as pd
from database import fetch_query, execute_query
def show_bildirimler():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("🔔 Bildirimler")
    st.markdown("---")

    # 1. ÖĞRENCİ ID'SİNİ ÇEKME
    query_student = "SELECT OgrenciID FROM OGRENCILER WHERE OgrenciNo = ?"
    df_student = fetch_query(query_student, (ogrenci_no,))

    if df_student.empty:
        st.error("Öğrenci bilgisi bulunamadı.")
        return

    ogrenci_id = int(df_student.iloc[0]['OgrenciID'])

    # 2. BİLDİRİMLERİ ÇEKME
    query_notif = """
        SELECT BildirimID, Baslik, Mesaj, Tarih, OkunduMu, Tur
        FROM BILDIRIMLER
        WHERE OgrenciID = ?
        ORDER BY OkunduMu ASC, Tarih DESC
    """
    df_notif = fetch_query(query_notif, (ogrenci_id,))

    if df_notif.empty:
        st.info("Sistemde henüz size ait bir bildirim bulunmamaktadır.")
        return

    # Bildirim İstatistikleri
    okunmamis_sayisi = len(df_notif[df_notif['OkunduMu'] == False])

    col_baslik, col_buton = st.columns([3, 1])
    with col_baslik:
        if okunmamis_sayisi > 0:
            st.warning(f"📬 **{okunmamis_sayisi}** adet okunmamış bildiriminiz var.")
        else:
            st.success("Tüm bildirimleri okudunuz.")

    with col_buton:
        if okunmamis_sayisi > 0:
            if st.button("Tümünü Okundu İşaretle", use_container_width=True):
                update_all_query = "UPDATE BILDIRIMLER SET OkunduMu = 1 WHERE OgrenciID = ? AND OkunduMu = 0"
                execute_query(update_all_query, (ogrenci_id,))
                st.rerun()

    st.markdown("---")

    # 3. BİLDİRİMLERİ LİSTELEME
    for index, row in df_notif.iterrows():
        b_id = row['BildirimID']
        baslik = row['Baslik']
        mesaj = row['Mesaj']
        tarih = str(row['Tarih'])[:16]  # YYYY-MM-DD HH:MM formatı
        okundu_mu = row['OkunduMu']
        tur = row['Tur']

        # Bildirim türüne göre renkli kutular ve ikonlar belirliyoruz
        if tur == 'Onay':
            icon = "🟢"
            bg_color = "success"
        elif tur == 'Iptal':
            icon = "🔴"
            bg_color = "error"
        elif tur == 'Hatirlatma':
            icon = "⏳"
            bg_color = "warning"
        else:
            icon = "📫"
            bg_color = "info"

        # Okunmamış bildirimleri göster
        if not okundu_mu:
            with st.container(border=True):
                col_icerik, col_aksiyon = st.columns([4, 1])

                with col_icerik:
                    st.markdown(f"**{icon} {baslik}** *(Yeni)*")
                    st.write(mesaj)
                    st.caption(f"📅 {tarih}")

                with col_aksiyon:
                    st.write("")  # Boşluk
                    if st.button("✔️ Okundu", key=f"okundu_{b_id}", use_container_width=True):
                        update_query = "UPDATE BILDIRIMLER SET OkunduMu = 1 WHERE BildirimID = ?"
                        execute_query(update_query, (int(b_id),))
                        st.rerun()

                    # İlgili sayfaya yönlendirme
                    if st.button("🔗 Detaya Git", key=f"git_{b_id}", use_container_width=True):
                        st.info("Lütfen detayları görmek için sol menüden '📅 Randevularım' sekmesine geçiniz.")

        else:
            # Okunmuş bildirimler kapalı bir kutuda görünür
            with st.expander(f"✉️ {baslik} ({tarih})"):
                st.write(mesaj)