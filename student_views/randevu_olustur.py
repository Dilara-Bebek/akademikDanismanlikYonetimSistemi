import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query


def show_randevu_olustur():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("➕ Yeni Randevu Talebi")
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

                #  ÇAKIŞMA  KONTROLÜ
                check_student_query = """
                    SELECT COUNT(*) FROM RANDEVULAR 
                    WHERE DanismanID = ? AND Tarih = ? AND Saat = ? AND Durum IN ('Bekliyor', 'Onaylandı', 'Onaylandi')
                """
                df_s_check = fetch_query(check_student_query, (danisman_id, tarih_talep_str, saat_talep_str))
                cakisma_var_mi = df_s_check.iloc[0, 0] > 0 if not df_s_check.empty else False

                if cakisma_var_mi:
                    st.error(
                        "❌ TALEP REDDEDİLDİ: Danışman hocanızın bu tarih ve saatte başka bir randevusu bulunmaktadır. Lütfen farklı bir saat seçiniz.")
                else:
                    insert_talep = """
                        INSERT INTO RANDEVULAR (OgrenciID, DanismanID, Tarih, Saat, Konu, Durum)
                        VALUES (?, ?, ?, ?, ?, 'Bekliyor')
                    """
                    if execute_query(insert_talep, (ogrenci_id, danisman_id, tarih_talep_str, saat_talep_str, t_konu)):
                        st.success("✅ Randevu talebiniz başarıyla hocanıza iletildi! Onay bekliyor.")
                    else:
                        st.error("Sistem hatası oluştu.")