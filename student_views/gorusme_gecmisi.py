import streamlit as st
import pandas as pd
from database import fetch_query, execute_query
def show_gorusme_gecmisi():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("⏳ Geçmiş Görüşmeler ve Notlar")
    st.markdown("---")

    # 1. ÖĞRENCİ ID'SİNİ ÇEKME
    query_ogrenci = "SELECT OgrenciID FROM OGRENCILER WHERE OgrenciNo = ?"
    df_ogrenci = fetch_query(query_ogrenci, (ogrenci_no,))

    if df_ogrenci.empty:
        st.error("Öğrenci bilgisi bulunamadı.")
        return

    ogrenci_id = int(df_ogrenci.iloc[0]['OgrenciID'])

    # 2. TAMAMLANMIŞ RANDEVULARI VE NOTLARI ÇEKME
    # GORUSME_NOTLARI tablosunu LEFT JOIN ile bağlıyoruz ki not olmasa bile randevu gelsin
    query_gecmis = """
        SELECT R.RandevuID, R.Tarih, R.Saat, R.Konu, D.AdSoyad AS DanismanAd,
               GN.DanismanNotu, GN.OgrenciNotu
        FROM RANDEVULAR R
        INNER JOIN DANISMANLAR D ON R.DanismanID = D.DanismanID
        LEFT JOIN GORUSME_NOTLARI GN ON R.RandevuID = GN.RandevuID
        WHERE R.OgrenciID = ? AND R.Durum = 'Tamamlandı'
        ORDER BY R.Tarih DESC, R.Saat DESC
    """
    df_gecmis = fetch_query(query_gecmis, (ogrenci_id,))

    if df_gecmis.empty:
        st.info("Sistemde henüz 'Tamamlandı' durumunda bir görüşmeniz bulunmamaktadır.")
        return

    st.write(
        "Danışmanınızla gerçekleştirdiğiniz geçmiş görüşmelerin detaylarını ve notlarını buradan inceleyebilirsiniz.")

    # 3. ARAYÜZ TASARIMI VE NOT EKLEME İŞLEMİ
    for index, row in df_gecmis.iterrows():
        r_id = int(row['RandevuID'])
        tarih = row['Tarih']
        saat = str(row['Saat'])[:5]
        danisman = row['DanismanAd']
        konu = row['Konu']

        # Eğer veritabanında NULL ise varsayılan değerler atıyoruz
        d_notu = row['DanismanNotu'] if pd.notna(
            row['DanismanNotu']) else "Danışman bu görüşme için henüz bir not eklememiş."
        o_notu = row['OgrenciNotu'] if pd.notna(row['OgrenciNotu']) else ""

        baslik = f"🗓️ {tarih} | {saat} - {danisman}"

        with st.expander(baslik):
            st.markdown(f"**Görüşme Konusu:** {konu}")
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.info(f"👨‍🏫 **Danışman Notu:**\n\n{d_notu}")

            with col2:
                # Öğrencinin kendi notunu girebileceği ve güncelleyebileceği alan
                st.write("📝 **Kendi Görüşme Notlarınız:**")
                yeni_not = st.text_area("Bu alana görüşmeyle ilgili kişisel notlarınızı ekleyebilirsiniz.",
                                        value=o_notu,
                                        key=f"txt_{r_id}",
                                        height=100)

                if st.button("💾 Notumu Kaydet", key=f"btn_{r_id}", type="primary"):
                    # GORUSME_NOTLARI tablosunda bu randevu için daha önce kayıt açılmış mı kontrolü
                    check_query = "SELECT COUNT(*) as sayi FROM GORUSME_NOTLARI WHERE RandevuID = ?"
                    df_check = fetch_query(check_query, (r_id,))

                    is_exists = df_check.iloc[0]['sayi'] > 0 if not df_check.empty else False

                    if is_exists:
                        # Kayıt varsa sadece Öğrenci Notunu güncelle
                        update_q = "UPDATE GORUSME_NOTLARI SET OgrenciNotu = ? WHERE RandevuID = ?"
                        success = execute_query(update_q, (yeni_not, r_id))
                    else:
                        # Kayıt yoksa yeni satır oluştur
                        insert_q = "INSERT INTO GORUSME_NOTLARI (RandevuID, OgrenciNotu) VALUES (?, ?)"
                        success = execute_query(insert_q, (r_id, yeni_not))

                    if success:
                        st.success("Notunuz başarıyla kaydedildi!")
                    else:
                        st.error("Not kaydedilirken bir hata oluştu.")