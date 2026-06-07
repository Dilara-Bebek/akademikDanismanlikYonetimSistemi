import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from database import fetch_query


def show_advisor_dashboard():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    danisman_kullanici_adi = st.session_state['username']

    st.header("📊 Danışman Anasayfa")
    st.markdown("Akademik danışmanlık süreçlerinize ait günlük özet, istatistikler ve yaklaşan etkinlikler.")


    # DANIŞMAN ID VE VERİLERİ ÇEKME
    query_danisman = """
        SELECT D.DanismanID FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df_danisman = fetch_query(query_danisman, (danisman_kullanici_adi,))
    if df_danisman.empty:
        st.error("Danışman profili bulunamadı.")
        return
    danisman_id = int(df_danisman.iloc[0]['DanismanID'])

    # Bugünün tarihi ve ayı
    bugun = datetime.date.today()
    bugun_str = bugun.strftime("%Y-%m-%d")
    bu_ay = bugun.month

    # Tüm Randevuları Çek (Hesaplamalar için)
    query_randevular = "SELECT Tarih, Saat, Durum FROM RANDEVULAR WHERE DanismanID = ?"
    df_ran = fetch_query(query_randevular, (danisman_id,))

    # Tüm Öğrencileri Çek
    query_ogr = "SELECT OgrenciID FROM OGRENCILER WHERE DanismanID = ?"
    df_ogr = fetch_query(query_ogr, (danisman_id,))

    #KPI Hesaplamaları
    toplam_ogrenci = len(df_ogr)
    bekleyen_sayisi = 0
    bugunku_randevular = 0
    tamamlanan_bu_ay = 0

    if not df_ran.empty:
        df_ran['Tarih'] = pd.to_datetime(df_ran['Tarih'])
        bekleyen_sayisi = len(df_ran[df_ran['Durum'] == 'Bekliyor'])
        bugunku_randevular = len(
            df_ran[(df_ran['Tarih'].dt.date == bugun) & (df_ran['Durum'].isin(['Onaylandı', 'Bekliyor']))])
        tamamlanan_bu_ay = len(df_ran[(df_ran['Durum'] == 'Tamamlandı') & (df_ran['Tarih'].dt.month == bu_ay)])

    # ÜST METRİKLER (KPI)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="📅 Bugünkü Randevular", value=bugunku_randevular, delta="Onaylı/Bekleyen")
    with kpi2:
        st.metric(label="⏳ Bekleyen Talepler", value=bekleyen_sayisi, delta="İşlem Bekliyor",
                  delta_color="inverse" if bekleyen_sayisi > 0 else "off")
    with kpi3:
        st.metric(label="✔️ Tamamlanan (Bu Ay)", value=tamamlanan_bu_ay, delta="Arşivlendi", delta_color="normal")
    with kpi4:
        st.metric(label="👨‍🎓 Sorumlu Öğrenciler", value=toplam_ogrenci, delta="Tümü Aktif", delta_color="off")

    st.divider()

    # GRAFİKLER
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📈 Haftalık Randevu Yoğunluğu")
        st.caption("Bu hafta planlanan görüşme sayıları (Dinamik)")

        # SQL'deki randevuları haftanın günlerine göre sayalım
        gunler_map = {0: "Pzt", 1: "Sal", 2: "Çar", 3: "Per", 4: "Cum", 5: "Cmt", 6: "Paz"}
        haftalik_sayilar = {"Pzt": 0, "Sal": 0, "Çar": 0, "Per": 0, "Cum": 0}

        if not df_ran.empty:
            # Sadece bu haftanın randevularını filtrele
            df_bu_hafta = df_ran[df_ran['Tarih'].dt.isocalendar().week == bugun.isocalendar()[1]]
            for index, row in df_bu_hafta.iterrows():
                gun_idx = row['Tarih'].weekday()
                if gun_idx in gunler_map and gunler_map[gun_idx] in haftalik_sayilar:
                    haftalik_sayilar[gunler_map[gun_idx]] += 1

        haftalik_data = pd.DataFrame({
            "Günler": list(haftalik_sayilar.keys()),
            "Randevu Sayısı": list(haftalik_sayilar.values())
        })

        fig_line = px.line(haftalik_data, x="Günler", y="Randevu Sayısı", markers=True, line_shape="spline")
        fig_line.update_traces(line_color="#7B68EE", line_width=4, marker=dict(size=10))
        # Y eksenini tam sayı yap
        fig_line.update_yaxes(tickformat="d")
        st.plotly_chart(fig_line, use_container_width=True)

    with col_chart2:
        st.subheader("🥧 Randevu Durum Dağılımı")
        st.caption("Sistemdeki tüm randevularınızın anlık oranları")

        if df_ran.empty:
            st.info("Henüz randevu veriniz bulunmadığı için grafik oluşturulamadı.")
        else:
            durum_data = df_ran['Durum'].value_counts().reset_index()
            durum_data.columns = ['Durum', 'Sayi']

            # Renk haritası
            renkler = {"Tamamlandı": "#00CC96", "Bekliyor": "#FFA15A", "Onaylandı": "#3498DB",
                       "İptal Edildi": "#EF553B"}

            fig_pie = px.pie(durum_data, names="Durum", values="Sayi", hole=0.4,
                             color="Durum", color_discrete_map=renkler)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    # YAKLAŞAN RANDEVULAR VE HIZLI İŞLEMLER

    col_list, col_act = st.columns([2, 1])

    with col_list:
        st.subheader("⏳ Bugünün Randevuları")

        query_bugun = """
            SELECT R.Saat, O.AdSoyad AS Öğrenci, R.Konu, R.Durum, R.RandevuID
            FROM RANDEVULAR R
            INNER JOIN OGRENCILER O ON R.OgrenciID = O.OgrenciID
            WHERE R.DanismanID = ? AND R.Tarih = ?
            ORDER BY R.Saat ASC
        """
        df_bugun = fetch_query(query_bugun, (danisman_id, bugun_str))

        if df_bugun.empty:
            st.success(" Bugün için planlanmış bir randevunuz bulunmamaktadır.")
        else:
            # Saatlerin saniyelerini kırp
            df_bugun['Saat'] = df_bugun['Saat'].astype(str).str[:5]

            # Durum emojileri
            emoji_map = {"Onaylandı": "🟢 Onaylandı", "Bekliyor": "🟡 Bekliyor", "Tamamlandı": "✔️ Tamamlandı",
                         "İptal Edildi": "🔴 İptal"}
            df_bugun['Durum'] = df_bugun['Durum'].map(emoji_map).fillna(df_bugun['Durum'])

            st.dataframe(df_bugun[['Saat', 'Öğrenci', 'Konu', 'Durum']], use_container_width=True, hide_index=True)

    with col_act:
        st.subheader("⚡ Hızlı İşlemler")

        # 1. Randevulara Geçiş
        if st.button("📅 Tüm Randevuları Yönet", use_container_width=True, type="primary"):
            st.session_state['menu_selection'] = "📅 Randevularım"
            st.rerun()

        # 2. Öğrenci Listesine Geçiş
        if st.button("👨‍🎓 Öğrenci Listesini Aç", use_container_width=True):
            st.session_state['menu_selection'] = "👨‍🎓 Öğrencilerim"
            st.rerun()

        # 3. Görüşme Notlarına Geçiş
        if st.button("📝 Yeni Görüşme Notu Ekle", use_container_width=True):
            st.session_state['menu_selection'] = "📝 Görüşme Notları"
            st.rerun()

        st.write("")
        with st.container(border=True):
            if bekleyen_sayisi > 0:
                st.warning(f"💡 **Sistem Asistanı:** {bekleyen_sayisi} adet randevu onayınızı bekliyor.")
            else:
                st.info("💡 **Sistem Asistanı:** Şu an için acil bir durum yok. Harika bir gün dilerim!")