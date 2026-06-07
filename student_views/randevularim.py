import streamlit as st
import pandas as pd
from database import fetch_query, execute_query
def show_randevularim():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("📅 Randevularım")
    st.markdown("---")

    # 1. ÖĞRENCİ ID'SİNİ ÇEKME
    query_ogrenci = "SELECT OgrenciID FROM OGRENCILER WHERE OgrenciNo = ?"
    df_ogrenci = fetch_query(query_ogrenci, (ogrenci_no,))

    if df_ogrenci.empty:
        st.error("Öğrenci bilgisi bulunamadı.")
        return

    ogrenci_id = int(df_ogrenci.iloc[0]['OgrenciID'])

    # 2. TÜM RANDEVULARI ÇEKME
    # R.RandevuID'yi çekiyoruz ki iptal işlemi yapabilelim
    query_randevular = """
        SELECT R.RandevuID, R.Tarih, R.Saat, R.Konu, R.Durum, D.AdSoyad AS DanismanAd
        FROM RANDEVULAR R
        INNER JOIN DANISMANLAR D ON R.DanismanID = D.DanismanID
        WHERE R.OgrenciID = ?
        ORDER BY R.Tarih DESC, R.Saat DESC
    """
    df_randevular = fetch_query(query_randevular, (ogrenci_id,))

    if df_randevular.empty:
        st.info("Sistemde henüz bir randevu kaydınız bulunmamaktadır.")
        return

    # 3. ARAYÜZ TASARIMI
    tab1, tab2 = st.tabs(["📌 Aktif & Yaklaşan Randevular", "📂 Tüm Randevu Geçmişi"])

    with tab1:
        st.subheader("İşlem Bekleyen ve Onaylanan Görüşmeler")

        # Sadece Bekleyen ve Onaylananları filtrele
        aktif_randevular = df_randevular[df_randevular['Durum'].isin(['Bekliyor', 'Onaylandı'])]

        if aktif_randevular.empty:
            st.success("Şu anda aktif veya yaklaşan bir randevunuz bulunmuyor.")
        else:
            # Her bir randevu için  açılır kart Expander oluşturuyoruz
            for index, row in aktif_randevular.iterrows():
                r_id = row['RandevuID']
                tarih = row['Tarih']
                saat = str(row['Saat'])[:5]
                durum = row['Durum']
                danisman = row['DanismanAd']
                konu = row['Konu']

                # Duruma göre renkli emoji
                if durum == 'Onaylandı':
                    baslik = f"🟢 {tarih} | {saat} - {danisman} (Onaylandı)"
                else:
                    baslik = f"🟠 {tarih} | {saat} - {danisman} (Onay Bekliyor)"

                with st.expander(baslik):
                    col_detay, col_islem = st.columns([3, 1])

                    with col_detay:
                        st.write(f"**Görüşülecek Kişi:** {danisman}")
                        st.write(f"**Tarih ve Saat:** {tarih} - {saat}")
                        st.write(f"**Durum:** {durum}")
                        st.write(f"**Görüşme Konusu:** {konu}")

                    with col_islem:
                        st.write("")  # Boşluk
                        st.write("")  # Boşluk
                        # İptal Et Butonu (Her randevu için benzersiz bir key veriyoruz ki hata olmasın)
                        iptal_btn = st.button("❌ İptal Et", key=f"iptal_{r_id}", use_container_width=True,
                                              type="secondary")

                        if iptal_btn:
                            update_query = "UPDATE RANDEVULAR SET Durum = 'İptal Edildi' WHERE RandevuID = ?"
                            success = execute_query(update_query, (int(r_id),))
                            if success:
                                st.success("Randevu başarıyla iptal edildi.")
                                st.rerun()  # liste güncellensin diye
                            else:
                                st.error("İptal işlemi sırasında hata oluştu.")

    with tab2:
        st.subheader("Tüm Randevular (Liste Görünümü)")
        st.write("Geçmişte tamamlanan, iptal edilen veya aktif olan tüm randevularınızın özet tablosu.")

        # Tabloda gösterilecek sütunları temizleyip düzenleyelim
        df_gosterim = df_randevular.copy()
        df_gosterim['Saat'] = df_gosterim['Saat'].astype(str).str[:5]  # Saniyeleri gizle
        df_gosterim = df_gosterim[['DanismanAd', 'Tarih', 'Saat', 'Konu', 'Durum']]
        df_gosterim.columns = ['Danışman', 'Tarih', 'Saat', 'Konu', 'Durum']  # başlıklar

        st.dataframe(df_gosterim, use_container_width=True, hide_index=True)