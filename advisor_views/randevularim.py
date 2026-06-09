import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query

@st.dialog("🔍 Randevu Detay ve İşlem Geçmişi")
def show_appointment_detail(r_id, df):
    detay = df[df["RandevuID"] == r_id].iloc[0]

    st.markdown(f"### Öğrenci: {detay['Öğrenci Adı']}")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📅 **Tarih:** {detay['Tarih']}")
        st.write(f"⏰ **Saat:** {detay['Saat']}")
    with col2:
        st.write(f"📌 **Mevcut Durum:** {detay['Durum']}")
        st.write(f"🆔 **Randevu ID:** {detay['RandevuID']}")

    st.divider()
    st.write(f"📝 **Öğrenci Notu / Açıklama:**\n\n{detay['Açıklama']}")

    st.divider()
    st.subheader("⚙️ Hızlı İşlemler")

    mevcut_durum = detay['Durum']

    if mevcut_durum == 'Bekliyor':
        c1, c2 = st.columns(2)
        if c1.button("✅ Onayla", use_container_width=True, type="primary"):
            success = execute_query("UPDATE RANDEVULAR SET Durum = 'Onaylandı' WHERE RandevuID = ?", (int(r_id),))
            if success:
                execute_query("INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Randevu Onayı', ?, 0, GETDATE())",
                              (f"ID: {r_id} numaralı randevu danışman tarafından onaylandı.",))
                st.success("Randevu başarıyla onaylandı!")
                st.rerun()

        if c2.button("❌ İptal Et", use_container_width=True):
            success = execute_query("UPDATE RANDEVULAR SET Durum = 'İptal Edildi' WHERE RandevuID = ?", (int(r_id),))
            if success:
                execute_query("INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Randevu İptali', ?, 0, GETDATE())",
                              (f"ID: {r_id} numaralı randevu danışman tarafından iptal edildi.",))
                st.success("Randevu iptal edildi.")
                st.rerun()

    elif mevcut_durum == 'Onaylandı':
        c1, c2, c3 = st.columns(3)
        if c1.button("🔵 Tamamlandı", use_container_width=True, type="primary"):
            success = execute_query("UPDATE RANDEVULAR SET Durum = 'Tamamlandı' WHERE RandevuID = ?", (int(r_id),))
            if success:
                execute_query("INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem: Randevu Tamamlandı', ?, 0, GETDATE())",
                              (f"ID: {r_id} numaralı randevu başarıyla tamamlandı olarak işaretlendi.",))
                st.success("Randevu başarıyla 'Tamamlandı' olarak işaretlendi!")
                st.rerun()

        if c2.button("⚠️ Gerçekleşmedi", use_container_width=True):
            success = execute_query("UPDATE RANDEVULAR SET Durum = 'Gerçekleşmedi' WHERE RandevuID = ?", (int(r_id),))
            if success:
                execute_query("INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem Uyarı', ?, 0, GETDATE())",
                              (f"ID: {r_id} numaralı randevu danışman tarafından gerçekleşmedi olarak işaretlendi.",))
                st.warning("Görüşme sağlanamadığı için 'Gerçekleşmedi' olarak işaretlendi.")
                st.rerun()

        if c3.button("❌ İptal Et", use_container_width=True):
            success = execute_query("UPDATE RANDEVULAR SET Durum = 'İptal Edildi' WHERE RandevuID = ?", (int(r_id),))
            if success:
                execute_query("INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Randevu İptali', ?, 0, GETDATE())",
                              (f"ID: {r_id} numaralı onaylı randevu danışman tarafından iptal edildi.",))
                st.error("Randevu iptal edildi.")
                st.rerun()

    # KİLİTLENMEYİ ENGELLEYEN GERİ ALMA SEÇENEĞİ
    elif mevcut_durum in ['Tamamlandı', 'Gerçekleşmedi']:
        if st.button("🔄 İşlemi Geri Al (Yeniden 'Onaylandı' Yap)", use_container_width=True, type="secondary"):
            success = execute_query("UPDATE RANDEVULAR SET Durum = 'Onaylandı' WHERE RandevuID = ?", (int(r_id),))
            if success:
                st.success("Randevu durumu başarıyla geri alındı, takvimde yeniden aktif!")
                st.rerun()
    else:
        st.info(f"Bu randevu '{mevcut_durum}' statüsünde olduğu için yeni bir işlem yapılamaz.")


def show_randevularim():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    danisman_kullanici_adi = st.session_state['username']

    st.header("📅 Randevu Yönetim Merkezi")
    st.markdown("Öğrencilerinizden gelen talepleri onaylayabilir veya takviminizi yönetebilirsiniz.")

    query_danisman = """
        SELECT D.DanismanID FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df_danisman = fetch_query(query_danisman, (danisman_kullanici_adi,))
    if df_danisman.empty:
        st.error("Danışman bilgisi çekilemedi.")
        return
    danisman_id = int(df_danisman.iloc[0]['DanismanID'])

    query_randevular = """
        SELECT R.RandevuID, O.AdSoyad AS [Öğrenci Adı], R.Tarih, R.Saat, R.Durum, R.Konu AS [Açıklama]
        FROM RANDEVULAR R
        INNER JOIN OGRENCILER O ON R.OgrenciID = O.OgrenciID
        WHERE R.DanismanID = ?
        ORDER BY R.Tarih ASC, R.Saat ASC
    """
    df_randevular = fetch_query(query_randevular, (danisman_id,))

    if df_randevular.empty:
        st.info("Sistemde henüz size ait bir randevu kaydı bulunmamaktadır.")
        manuel_randevu_formu(danisman_id)
        return

    df_randevular['Saat'] = df_randevular['Saat'].astype(str).str[:5]

    with st.container(border=True):
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search = st.text_input("🔍 Öğrenci Adı ile Ara", placeholder="Örn: Dilara...")
        with f_col2:
            status_filter = st.selectbox("📌 Durum Filtresi",
                                         ["Tümü", "Bekliyor", "Onaylandı", "Tamamlandı", "Gerçekleşmedi",
                                          "İptal Edildi"])
        with f_col3:
            view_mode = st.radio("🖼️ Görünüm", ["Tablo", "Takvim"], horizontal=True)

    filtered_df = df_randevular.copy()
    if search:
        filtered_df = filtered_df[filtered_df["Öğrenci Adı"].fillna("").str.contains(search, case=False)]
    if status_filter != "Tümü":
        filtered_df = filtered_df[filtered_df["Durum"] == status_filter]

    if view_mode == "Tablo":
        st.subheader("📋 Randevu Listesi")
        if filtered_df.empty:
            st.warning("Arama kriterlerinize uygun randevu bulunamadı.")
        else:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            with st.container(border=True):
                act_col1, act_col2 = st.columns([2, 2])
                with act_col1:
                    format_func = lambda \
                            x: f"ID:{x} - {filtered_df[filtered_df['RandevuID'] == x].iloc[0]['Öğrenci Adı']} ({filtered_df[filtered_df['RandevuID'] == x].iloc[0]['Tarih']})"
                    secilen_r = st.selectbox("İşlem yapmak istediğiniz randevuyu seçin:",
                                             filtered_df["RandevuID"].tolist(), format_func=format_func)
                with act_col2:
                    st.write("")
                    st.write("")
                    if st.button("👁️ Randevu Detayını Gör", type="primary", use_container_width=True):
                        show_appointment_detail(secilen_r, filtered_df)

    else:
        st.subheader("📅 Yaklaşan Randevularınız (Liste Takvimi)")
        st.info("💡 Sadece 'Onaylandı' ve 'Bekliyor' durumundaki randevular gösterilmektedir.")

        takvim_df = df_randevular[df_randevular['Durum'].isin(['Onaylandı', 'Bekliyor'])]

        if takvim_df.empty:
            st.success("Planlanmış bir randevunuz bulunmuyor.")
        else:
            for index, row in takvim_df.iterrows():
                renk = "🟢" if row['Durum'] == 'Onaylandı' else "🟠"
                st.markdown(
                    f"**{row['Tarih']} | {row['Saat']}** ➔ {renk} {row['Öğrenci Adı']} *(Konu: {row['Açıklama']})*")

    st.divider()
    manuel_randevu_formu(danisman_id)


def manuel_randevu_formu(danisman_id):
    query_ogr = "SELECT OgrenciID, AdSoyad, OgrenciNo FROM OGRENCILER WHERE DanismanID = ?"
    df_ogr = fetch_query(query_ogr, (danisman_id,))

    ogr_dict = {}
    if not df_ogr.empty:
        for index, row in df_ogr.iterrows():
            isim = row['AdSoyad'] if pd.notna(row['AdSoyad']) else "İsimsiz"
            ogr_dict[f"{isim} ({row['OgrenciNo']})"] = row['OgrenciID']

    with st.expander("➕ Manuel Randevu Oluştur (Öğrenci Adına)"):
        with st.form("manual_randevu"):
            if not ogr_dict:
                st.warning("Sisteme kayıtlı öğrenciniz bulunmuyor.")
                m_ogr_isim = None
            else:
                m_ogr_isim = st.selectbox("Öğrenci Seçin", list(ogr_dict.keys()))

            m_col1, m_col2 = st.columns(2)
            m_tarih = m_col1.date_input("Tarih", value=datetime.date.today() + datetime.timedelta(days=1))
            m_saat = m_col2.time_input("Saat", value=datetime.time(13, 0))
            m_not = st.text_area("Randevu Notu (Konu)", placeholder="Hoca tarafından manuel oluşturuldu.")

            if st.form_submit_button("Randevuyu Takvime Ekle", type="primary"):
                if m_ogr_isim:
                    secilen_ogr_id = ogr_dict[m_ogr_isim]
                    saat_str = f"{m_saat.hour:02d}:{m_saat.minute:02d}:00"
                    tarih_str = m_tarih.strftime("%Y-%m-%d")

                    #1. ÇAKIŞMA KONTROLÜ
                    check_query = """
                        SELECT COUNT(*) FROM RANDEVULAR 
                        WHERE DanismanID = ? AND Tarih = ? AND Saat = ? AND Durum IN ('Bekliyor', 'Onaylandı')
                    """
                    df_check = fetch_query(check_query, (danisman_id, tarih_str, saat_str))
                    cakisma_var_mi = df_check.iloc[0][0] > 0 if not df_check.empty else False

                    if cakisma_var_mi:
                        st.error("🚨 SİSTEM ENGELİ: Seçtiğiniz tarih ve saatte zaten onaylı veya bekleyen başka bir randevunuz bulunuyor! Lütfen saati değiştirin.")
                    else:
                        insert_query = """
                            INSERT INTO RANDEVULAR (OgrenciID, DanismanID, Tarih, Saat, Konu, Durum)
                            VALUES (?, ?, ?, ?, ?, 'Onaylandı')
                        """
                        success = execute_query(insert_query, (secilen_ogr_id, danisman_id, tarih_str, saat_str, m_not))
                        if success:
                            execute_query("INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Yeni Randevu Planlandı', ?, 0, GETDATE())",
                                          (f"Danışmanınız, sizin adınıza {tarih_str} saat {saat_str[:5]} için yeni bir randevu oluşturdu.",))
                            st.success(f"{m_ogr_isim} için randevu başarıyla eklendi.")
                            st.rerun()
                        else:
                            st.error("Veritabanına kaydedilirken hata oluştu.")