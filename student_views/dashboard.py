import streamlit as st
import pandas as pd
from database import fetch_query

def show_student_dashboard():
    # Güvenlik kontrolü
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("🎓 Öğrenci Kontrol Paneli")
    st.markdown("---")

    # 1. VERİTABANINDAN VERİLERİ ÇEKME
    # 1.1 Öğrenci ID'sini, Adını ve Danışman Bilgilerini Çek
    query_info = """
        SELECT O.OgrenciID, O.OgrenciNo, O.AdSoyad AS OgrenciAd, D.AdSoyad AS DanismanAd
        FROM OGRENCILER O
        LEFT JOIN DANISMANLAR D ON O.DanismanID = D.DanismanID
        WHERE O.OgrenciNo = ?
    """
    df_info = fetch_query(query_info, (ogrenci_no,))

    # Eğer öğrenci tablosunda bu numara yoksa hata vermemesi için kontrol edelim
    if df_info.empty:
        st.error("Öğrenci bilgileriniz sistemde eksik. Lütfen yönetici ile iletişime geçin.")
        return

    # Veritabanındaki verileri değişkene alıyoruz
    ogrenci_id = int(df_info.iloc[0]['OgrenciID'])

    # Öğrenci adı çekme ve boş olma durumuna karşı güvenlik önlemi
    ogrenci_ad = df_info.iloc[0]['OgrenciAd']
    if pd.isna(ogrenci_ad) or str(ogrenci_ad).strip() == "":
        ogrenci_ad = ogrenci_no  # Veritabanında isim yoksa okul numarasını göster

    danisman_adi = "Atanmadı"
    if pd.notna(df_info.iloc[0]['DanismanAd']):
        danisman_adi = df_info.iloc[0]['DanismanAd']

    # 1.2 Randevu İstatistiklerini Çek
    query_randevular = """
        SELECT Durum, COUNT(*) as Sayi
        FROM RANDEVULAR
        WHERE OgrenciID = ?
        GROUP BY Durum
    """
    df_randevular = fetch_query(query_randevular, (ogrenci_id,))

    bekleyen_sayisi = 0
    onaylanan_sayisi = 0
    tamamlanan_sayisi = 0

    if not df_randevular.empty:
        for index, row in df_randevular.iterrows():
            if pd.notna(row['Durum']):
                durum = str(row['Durum']).upper()
                if "BEKLIYOR" in durum or "BEKLEYEN" in durum:
                    bekleyen_sayisi = row['Sayi']
                elif "ONAYLANDI" in durum or "YAKLAŞAN" in durum:
                    onaylanan_sayisi = row['Sayi']
                elif "TAMAMLANDI" in durum or "GEÇMİŞ" in durum:
                    tamamlanan_sayisi = row['Sayi']

    # 1.3 Yaklaşan En Yakın Randevuyu Çek
    query_son_randevu = """
        SELECT TOP 1 Tarih, Saat, Durum
        FROM RANDEVULAR
        WHERE OgrenciID = ? AND Durum = 'Onaylandı'
        ORDER BY Tarih ASC, Saat ASC
    """
    df_son_randevu = fetch_query(query_son_randevu, (ogrenci_id,))

    # 2. ARAYÜZ TASARIMI
    st.subheader(f"Hoş Geldin, {ogrenci_ad} 👋")
    st.info(f"👩‍🏫 **Mevcut Danışmanınız:** {danisman_adi}")

    # 4 Sütunlu Metrik Alanı
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Yaklaşan Randevular", value=onaylanan_sayisi, delta="Onaylı")
    with col2:
        st.metric(label="Bekleyen Talepler", value=bekleyen_sayisi, delta="İşlem Bekliyor", delta_color="off")
    with col3:
        st.metric(label="Tamamlanan Görüşmeler", value=tamamlanan_sayisi, delta="Arşivlendi", delta_color="normal")
    with col4:
        # Son randevu bilgisini dinamik gösterme
        if not df_son_randevu.empty and pd.notna(df_son_randevu.iloc[0]['Tarih']):
            tarih = df_son_randevu.iloc[0]['Tarih']
            saat = str(df_son_randevu.iloc[0]['Saat'])[:5]  # 14:30:00 formatını 14:30 yapar
            st.metric(label="Sıradaki Randevu", value=f"{tarih}", delta=f"Saat: {saat}")
        else:
            st.metric(label="Sıradaki Randevu", value="Yok", delta="Planlanmış görüşme yok", delta_color="off")

    st.markdown("---")

    # 3. HIZLI İŞLEMLER VE ÖZET TABLOLAR
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("⏳ Onay Bekleyen Taleplerim")

        query_bekleyen_liste = """
            SELECT Tarih, Saat, Konu
            FROM RANDEVULAR
            WHERE OgrenciID = ? AND Durum = 'Bekliyor'
            ORDER BY Tarih ASC
        """
        df_bekleyen_liste = fetch_query(query_bekleyen_liste, (ogrenci_id,))

        if not df_bekleyen_liste.empty:
            st.dataframe(df_bekleyen_liste, use_container_width=True, hide_index=True)
        else:
            st.success("Şu anda onay bekleyen randevu talebiniz bulunmamaktadır.")

    with col_right:
        st.subheader("⚡ Hızlı İşlemler")
        with st.container(border=True):
            st.write("Danışmanınızdan hemen yeni bir görüşme talep edebilirsiniz.")

            if st.button("➕ Hızlı Randevu Oluştur", use_container_width=True, type="primary"):
                st.session_state['menu_selection'] = "➕ Randevu Oluştur"
                st.rerun()