import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query


def show_randevularim():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("📅 Randevu Yönetim Paneli")
    st.markdown("---")

    # 1. ÖĞRENCİ VE DANIŞMAN BİLGİLERİNİ ÇEKME
    query_ogrenci = """
        SELECT O.OgrenciID, O.DanismanID, D.AdSoyad AS DanismanAd 
        FROM OGRENCILER O
        LEFT JOIN DANISMANLAR D ON O.DanismanID = D.DanismanID
        WHERE O.OgrenciNo = ?
    """
    df_ogrenci = fetch_query(query_ogrenci, (ogrenci_no,))

    if df_ogrenci.empty:
        st.error("Öğrenci bilgisi bulunamadı.")
        return

    ogrenci_id = int(df_ogrenci.iloc[0]['OgrenciID'])

    if pd.isna(df_ogrenci.iloc[0]['DanismanID']):
        st.warning("⚠️ Henüz size atanmış bir danışman hoca bulunmadığı için randevu alamazsınız.")
        return

    danisman_id = int(df_ogrenci.iloc[0]['DanismanID'])
    danisman_ad = df_ogrenci.iloc[0]['DanismanAd']

    # 2. TÜM RANDEVULARI ÇEKME
    query_randevular = """
        SELECT R.RandevuID, R.Tarih, R.Saat, R.Konu, R.Durum, D.AdSoyad AS DanismanAd
        FROM RANDEVULAR R
        INNER JOIN DANISMANLAR D ON R.DanismanID = D.DanismanID
        WHERE R.OgrenciID = ?
        ORDER BY R.Tarih DESC, R.Saat DESC
    """
    df_randevular = fetch_query(query_randevular, (ogrenci_id,))

    # 3. ARAYÜZ TASARIMI
    tab1, tab2, tab3 = st.tabs(["📌 Aktif & Yaklaşan Randevular", "➕ Yeni Randevu Talebi", "📂 Tüm Randevu Geçmişi"])

    with tab1:
        st.subheader("İşlem Bekleyen ve Onaylanan Görüşmeler")
        if df_randevular.empty:
            aktif_randevular = pd.DataFrame()
        else:
            aktif_randevular = df_randevular[df_randevular['Durum'].isin(['Bekliyor', 'Onaylandı'])]

        if aktif_randevular.empty:
            st.success("Şu anda aktif veya yaklaşan bir randevunuz bulunmuyor.")
        else:
            for index, row in aktif_randevular.iterrows():
                r_id = row['RandevuID']
                tarih = row['Tarih']
                saat = str(row['Saat'])[:5]
                durum = row['Durum']
                danisman = row['DanismanAd']
                konu = row['Konu']

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
                        st.write("")
                        st.write("")
                        iptal_btn = st.button("❌ İptal Et", key=f"iptal_{r_id}", use_container_width=True)

                        if iptal_btn:
                            update_query = "UPDATE RANDEVULAR SET Durum = 'İptal Edildi' WHERE RandevuID = ?"
                            success = execute_query(update_query, (int(r_id),))
                            if success:
                                st.success("Randevu başarıyla iptal edildi.")
                                st.rerun()
                            else:
                                st.error("İptal işlemi sırasında hata oluştu.")

    # ÖĞRENCİ TARAFINDAN RANDEVU TALEBİ OLUŞTURMA VE ÇAKIŞMA KONTROLÜ
    with tab2:
        st.subheader(f"👨‍🏫 Danışman: {danisman_ad}")
        st.caption("Hocanızın takviminde çakışma olmaması için uygun bir tarih ve saat seçiniz.")

        with st.form("ogrenci_randevu_talep_form"):
            t_tarih = st.date_input("Talep Edilen Tarih", value=datetime.date.today() + datetime.timedelta(days=1))
            t_saat = st.time_input("Talep Edilen Saat", value=datetime.time(10, 0))
            t_konu = st.text_area("Görüşme Amacı / Konusu",
                                  placeholder="Örn: Proje veritabanı şeması hakkında görüşme talebi.")

            submit_talep = st.form_submit_button("🚀 Randevu Talebini Gönder", type="primary", use_container_width=True)

            if submit_talep:
                if not t_konu.strip():
                    st.warning("⚠️ Lütfen görüşme konusunu belirtiniz.")
                else:
                    saat_talep_str = f"{t_saat.hour:02d}:{t_saat.minute:02d}:00"
                    tarih_talep_str = t_tarih.strftime("%Y-%m-%d")

                    #  ÇAKIŞMA KONTROLÜ
                    check_student_query = """
                        SELECT COUNT(*) FROM RANDEVULAR 
                        WHERE DanismanID = ? AND Tarih = ? AND Saat = ? AND Durum IN ('Bekliyor', 'Onaylandı')
                    """
                    df_s_check = fetch_query(check_student_query, (danisman_id, tarih_talep_str, saat_talep_str))
                    cakisma_var_mi = df_s_check.iloc[0][0] > 0 if not df_s_check.empty else False

                    if cakisma_var_mi:
                        st.error(
                            "❌ TALEP REDDEDİLDİ: Danışman hocanızın bu tarih ve saatte başka bir randevusu bulunmaktadır. Lütfen farklı bir saat seçiniz.")
                    else:
                        insert_talep = """
                            INSERT INTO RANDEVULAR (OgrenciID, DanismanID, Tarih, Saat, Konu, Durum)
                            VALUES (?, ?, ?, ?, ?, 'Bekliyor')
                        """
                        if execute_query(insert_talep,
                                         (ogrenci_id, danisman_id, tarih_talep_str, saat_talep_str, t_konu)):
                            st.success("✅ Randevu talebiniz başarıyla hocanıza iletildi! Onay bekliyor.")
                            st.rerun()
                        else:
                            st.error("Sistem hatası oluştu.")

    with tab3:
        st.subheader("Tüm Randevular (Liste Görünümü)")
        if df_randevular.empty:
            st.info("Geçmiş randevu kaydı bulunmuyor.")
        else:
            df_gosterim = df_randevular.copy()
            df_gosterim['Saat'] = df_gosterim['Saat'].astype(str).str[:5]
            df_gosterim = df_gosterim[['DanismanAd', 'Tarih', 'Saat', 'Konu', 'Durum']]
            df_gosterim.columns = ['Danışman', 'Tarih', 'Saat', 'Konu', 'Durum']
            st.dataframe(df_gosterim, use_container_width=True, hide_index=True)