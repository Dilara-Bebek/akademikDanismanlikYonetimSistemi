import streamlit as st
import pandas as pd
import plotly.express as px
from database import fetch_query


def show_advisor_raporlar():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    kullanici_adi = st.session_state['username']

    st.header("📈 Akademik Danışmanlık Raporları")
    st.markdown(
        "Kendi danışmanlık performansınızı, takvim yoğunluğunuzu ve öğrencileriniz üzerindeki akademik etkinizi buradan analiz edebilirsiniz.")

    # DANIŞMAN IDSİNİ ÇEKME
    query_danisman = """
        SELECT D.DanismanID FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df_dan = fetch_query(query_danisman, (kullanici_adi,))
    if df_dan.empty:
        st.warning("Danışman profilinize ulaşılamadı.")
        return

    danisman_id = int(df_dan.iloc[0]['DanismanID'])

    #1. RANDEVU VERİLERİNİ ÇEKME VE KPI HESAPLAMA
    query_randevular = "SELECT Durum, Tarih FROM RANDEVULAR WHERE DanismanID = ?"
    df_randevular = fetch_query(query_randevular, (danisman_id,))

    toplam_randevu = len(df_randevular)
    tamamlanan = 0
    iptal_edilen = 0
    en_yogun_gun_adi = "Bilinmiyor"

    if not df_randevular.empty:
        # Durumları normalize et Büyük/Küçük harf duyarlılığını kaldırmak için
        df_randevular['Durum'] = df_randevular['Durum'].astype(str).str.upper()
        tamamlanan = len(df_randevular[df_randevular['Durum'].str.contains('TAMAMLANDI')])
        iptal_edilen = len(df_randevular[df_randevular['Durum'].str.contains('İPTAL|IPTAL')])

        # Gün analizleri için tarih formatını pandas datetime'a çevir
        df_randevular['Tarih'] = pd.to_datetime(df_randevular['Tarih'])
        df_randevular['Gun_Ing'] = df_randevular['Tarih'].dt.day_name()

        # İngilizce gün isimlerini Türkçeye çevir
        gunler_tr = {
            'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
            'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
        }
        df_randevular['Gün'] = df_randevular['Gun_Ing'].map(gunler_tr)

        if not df_randevular['Gün'].dropna().empty:
            en_yogun_gun_adi = df_randevular['Gün'].mode()[0]

    basari_orani = int((tamamlanan / toplam_randevu) * 100) if toplam_randevu > 0 else 0
    iptal_orani = int((iptal_edilen / toplam_randevu) * 100) if toplam_randevu > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Toplam Randevu", str(toplam_randevu), "Bu Dönem")
    col2.metric("✔️ Tamamlanan Görüşme", str(tamamlanan), f"%{basari_orani} Başarı Oranı")
    col3.metric("❌ İptal Oranı", f"%{iptal_orani}", "Gerçek Veri", delta_color="inverse")
    col4.metric("⏱️ Ort. Görüşme Süresi", "25 dk", "Tahmini Süre")

    st.divider()

    # SİSTEM ASİSTANI
    st.subheader("💡 Sistem Asistanı Yorumları")
    with st.container(border=True):
        ai1, ai2 = st.columns(2)
        if toplam_randevu > 0:
            ai1.info(
                f"🔥 **En Yoğun Günler:** Randevularınızın büyük çoğunluğu **{en_yogun_gun_adi}** günlerinde yoğunlaşıyor. Bu günlerde yorgunluğu önlemek için mola sürelerini artırmanız önerilir.")
        else:
            ai1.info("📌 **Sistem Notu:** Henüz yeterli randevu verisi oluşmadığı için yoğunluk analizi yapılamıyor.")

        ai2.success(
            "✅ **Sistem Takibi:** Öğrencilerle gerçekleştirdiğiniz görüşmeler, veritabanına anlık olarak işlenmekte ve akademik raporlara yansıtılmaktadır.")

    st.write("")

    # GRAFİKLER
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Tarihlere Göre Dağılım")
        st.caption("Veritabanındaki randevuların tarihsel yoğunluğu.")

        if not df_randevular.empty:
            # Tarihlere göre grupla
            gunluk_sayi = df_randevular.groupby(df_randevular['Tarih'].dt.date).size().reset_index(
                name='Randevu Sayısı')
            gunluk_sayi.rename(columns={'Tarih': 'Tarih'}, inplace=True)

            fig_bar = px.bar(gunluk_sayi, x="Tarih", y="Randevu Sayısı", text="Randevu Sayısı",
                             color="Randevu Sayısı", color_continuous_scale="Purples")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Grafik oluşturulacak randevu kaydı bulunamadı.")

    with chart_col2:
        st.subheader("🥧 Günlük Görüşme Dağılımı")
        st.caption("Hangi gün daha çok görüşme yaptığınızın oransal dağılımı.")

        if not df_randevular.empty and not df_randevular['Gün'].dropna().empty:
            gun_oran = df_randevular['Gün'].value_counts().reset_index()
            gun_oran.columns = ['Gün', 'Sayi']

            fig_pie = px.pie(gun_oran, names="Gün", values="Sayi", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Dağılım pastası için yeterli veri yok.")

    st.divider()

    # ÖĞRENCİ BAZLI PERFORMANS ANALİZİ
    st.subheader("👨‍🎓 Öğrenci Bazlı Detaylı Analiz")
    st.markdown("Veritabanına kayıtlı öğrencilerinizin sizinle olan görüşme geçmişi.")

    # SQL'den Danışmana ait öğrencileri ve randevu istatistiklerini çekiyoruz
    query_ogr_analiz = """
        SELECT 
            O.AdSoyad,
            O.OgrenciNo,
            COALESCE(O.GNO, 0.0) as GNO,
            COUNT(R.RandevuID) as ToplamGorusme,
            MAX(CASE WHEN R.Durum = 'Tamamlandı' THEN R.Tarih END) as SonGorusme
        FROM OGRENCILER O
        LEFT JOIN RANDEVULAR R ON O.OgrenciID = R.OgrenciID AND R.DanismanID = ?
        WHERE O.DanismanID = ?
        GROUP BY O.AdSoyad, O.OgrenciNo, O.GNO
    """
    df_ogr = fetch_query(query_ogr_analiz, (danisman_id, danisman_id))

    if df_ogr.empty:
        st.warning("Sisteme kayıtlı öğrenciniz bulunmamaktadır.")
        return

    ogr_col, detay_col = st.columns([1, 2])

    # İsimsiz öğrencileri filtrele ve listeyi hazırla
    df_ogr['AdSoyad'] = df_ogr['AdSoyad'].fillna(df_ogr['OgrenciNo'])
    ogr_isimleri = df_ogr["AdSoyad"].tolist()

    with ogr_col:
        secilen_ogr = st.selectbox("İncelenecek Öğrenciyi Seçin:", ogr_isimleri)
        st.write("")

        # Seçili öğrencinin verilerini alıyoruz
        secili_detay = df_ogr[df_ogr["AdSoyad"] == secilen_ogr].iloc[0]

        son_gorusme = secili_detay['SonGorusme']
        if pd.isna(son_gorusme):
            son_gorusme = "Hiç Görüşülmedi"
        else:
            son_gorusme = pd.to_datetime(son_gorusme).strftime('%Y-%m-%d')

        # İndirilecek dosyanın içeriğini hazırlıyoruz
        rapor_icerik = f"""
        ========================================
        AKADEMIK DANISMANLIK OGRENCI RAPORU
        ========================================
        Ogrenci: {secili_detay['AdSoyad']}
        Okul No: {secili_detay['OgrenciNo']}
        Genel Not Ortalamasi (GNO): {secili_detay['GNO']}
        Toplam Planlanan Randevu: {secili_detay['ToplamGorusme']}
        Son Tamamlanan Gorusme: {son_gorusme}
        ========================================
        Cikti Tarihi: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}
        """

        st.download_button(
            label="📄 Detaylı Raporu İndir (TXT)",
            data=rapor_icerik,
            file_name=f"{secilen_ogr.replace(' ', '_')}_Raporu.txt",
            mime="text/plain",
            use_container_width=True
        )

    with detay_col:
        with st.container(border=True):
            st.markdown(f"#### 📊 **{secilen_ogr}** - Danışmanlık Karnesi")
            st.write("")
            d_c1, d_c2, d_c3 = st.columns(3)
            d_c1.metric("Toplam Randevu Talebi", int(secili_detay["ToplamGorusme"]))
            d_c2.metric("Son Görüşme", str(son_gorusme))

            gno_val = float(secili_detay["GNO"])
            d_c3.metric("Mevcut GNO", f"{gno_val:.2f}",
                        "Kritik" if gno_val < 2.0 else "Normal",
                        delta_color="inverse" if gno_val < 2.0 else "normal")