import streamlit as st
import pandas as pd
from database import fetch_query

def show_dashboard():
    # Başlık
    st.header("📊 Genel Bakış")

    #  VERİTABANINDAN VERİLERİ ÇEKME
    # Toplam Öğrenci
    df_ogr = fetch_query("SELECT COUNT(*) as sayi FROM OGRENCILER")
    toplam_ogrenci = df_ogr.iloc[0]['sayi'] if not df_ogr.empty else 0

    # Aktif Danışman
    df_dan = fetch_query("SELECT COUNT(*) as sayi FROM DANISMANLAR")
    toplam_danisman = df_dan.iloc[0]['sayi'] if not df_dan.empty else 0

    # Bekleyen Atamalar (Danışmanı atanmamış öğrenciler)
    df_bekleyen = fetch_query("SELECT COUNT(*) as sayi FROM OGRENCILER WHERE DanismanID IS NULL")
    bekleyen_atama = df_bekleyen.iloc[0]['sayi'] if not df_bekleyen.empty else 0

    # Kritik Uyarılar (GNO'su 2.0'ın altında olan öğrenciler)
    df_kritik = fetch_query("SELECT COUNT(*) as sayi FROM OGRENCILER WHERE GNO < 2.0")
    kritik_ogrenci = df_kritik.iloc[0]['sayi'] if not df_kritik.empty else 0

    # METRİKLERİ EKRANA BASMA
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Toplam Öğrenci", value=toplam_ogrenci)
    with col2:
        st.metric(label="Aktif Danışman", value=toplam_danisman)
    with col3:
        st.metric(label="Bekleyen Atamalar", value=bekleyen_atama, delta="Acil" if bekleyen_atama > 0 else "Tamam",
                  delta_color="inverse" if bekleyen_atama > 0 else "normal")
    with col4:
        st.metric(label="Kritik Uyarılar (GNO)", value=kritik_ogrenci,
                  delta="Riskli" if kritik_ogrenci > 0 else "Güvenli",
                  delta_color="inverse" if kritik_ogrenci > 0 else "normal")

    st.divider()

    # GRAFİK VE HIZLI AKSİYONLAR
    col_chart, col_actions = st.columns([2, 1])

    with col_chart:
        st.subheader("📈 Danışmanların Öğrenci Yükü Dağılımı")
        # SQL'den hangi hocada kaç öğrenci var onu çekiyoruz (JOIN işlemi ile)
        query_chart = """
            SELECT d.AdSoyad as Danisman, COUNT(o.OgrenciID) as OgrenciSayisi
            FROM DANISMANLAR d
            LEFT JOIN OGRENCILER o ON d.DanismanID = o.DanismanID
            GROUP BY d.AdSoyad
        """
        df_chart = fetch_query(query_chart)

        if not df_chart.empty and df_chart['OgrenciSayisi'].sum() > 0:
            df_chart.set_index("Danisman", inplace=True)
            st.bar_chart(df_chart, color="#ffaa00")
        else:
            st.info("Henüz danışmanlara atanmış öğrenci verisi bulunmuyor.")

    with col_actions:
        st.subheader("⚡ Hızlı İşlemler")

        if st.button("➕ Yeni Kullanıcı Ekle", use_container_width=True, type="primary"):
            st.info("💡 Lütfen sol menüden 'Kullanıcı Yönetimi' sayfasına geçiş yapın.")

        if st.button("🔔 Kritik Uyarıları İncele", use_container_width=True):
            if kritik_ogrenci > 0:
                st.warning(
                    f"Sistemde GNO'su 2.0 altında olan {kritik_ogrenci} öğrenci var. Raporlar sekmesinden detayları inceleyebilirsiniz.")
            else:
                st.success("Şu an sistemde riskli (GNO < 2.0) öğrenci bulunmuyor.")

        st.write("")
        st.subheader("🕒 Son Aktiviteler")
        with st.container(border=True):
            # Sistem loglarından en son 2 işlemi çekiyoruz
            df_logs = fetch_query("SELECT TOP 2 Aciklama, Durum FROM SISTEM_LOGLARI ORDER BY LogID DESC")

            if not df_logs.empty:
                for index, row in df_logs.iterrows():
                    if row['Durum'] == 'Hata':
                        st.error(f"🚨 {row['Aciklama']}")
                    elif row['Durum'] == 'Güncelleme':
                        st.warning(f"🔄 {row['Aciklama']}")
                    else:
                        st.success(f"✔️ {row['Aciklama']}")
            else:
                st.caption("Henüz kaydedilmiş bir sistem aktivitesi yok.")