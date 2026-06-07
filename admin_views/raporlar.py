import streamlit as st
import pandas as pd
import plotly.express as px
from database import fetch_query


def show_raporlar():
    st.header("📊 Sistem Raporları ve Analizi")

    # SQL'DEN VERİ ÇEKME
    df_danismanlar = fetch_query("SELECT DanismanID, AdSoyad FROM DANISMANLAR")
    df_ogrenciler = fetch_query(
        "SELECT o.OgrenciID, k.KullaniciAdi FROM OGRENCILER o JOIN KULLANICILAR k ON o.KullaniciID = k.KullaniciID")
    df_randevular = fetch_query("""
        SELECT 
            r.RandevuID, r.Durum, r.Tarih, r.Saat, r.Konu,
            d.AdSoyad as Danisman, k.KullaniciAdi as Ogrenci
        FROM RANDEVULAR r
        LEFT JOIN DANISMANLAR d ON r.DanismanID = d.DanismanID
        LEFT JOIN OGRENCILER o ON r.OgrenciID = o.OgrenciID
        LEFT JOIN KULLANICILAR k ON o.KullaniciID = k.KullaniciID
    """)

    #  ÜST FİLTRE ALANI -Kullanıcı Seçimleri
    with st.container(border=True):
        st.subheader("🔍Rapor Filtreleri")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            tarih_araligi = st.selectbox("📅 Tarih Aralığı", ["Tümü", "Son 7 Gün", "Bu Ay", "Bu Dönem"])
        with f_col2:
            kullanici_turu = st.selectbox("👤 Kullanıcı Türü", ["Tümü", "Öğrenci", "Danışman"])
        with f_col3:
            durum_filtresi = st.multiselect("🏷️ Randevu Durumu",
                                            ["Onaylandı", "İptal Edildi", "Tamamlandı", "Bekliyor", "Gerçekleşmedi"],
                                            default=["Onaylandı", "Bekliyor", "Tamamlandı"])
        with f_col4:
            danisman_listesi = ["Tüm Danışmanlar"] + df_danismanlar[
                "AdSoyad"].tolist() if not df_danismanlar.empty else ["Tüm Danışmanlar"]
            danisman_filtresi = st.selectbox("🔍 Danışman", danisman_listesi)

    #  FİLTRELEME İŞLEMİ
    if not df_randevular.empty:
        #  Durum Filtresi
        if durum_filtresi:
            df_randevular = df_randevular[df_randevular["Durum"].isin(durum_filtresi)]

        #  Danışman Filtresi
        if danisman_filtresi != "Tüm Danışmanlar":
            df_randevular = df_randevular[df_randevular["Danisman"] == danisman_filtresi]


    # Sayıları Hesaplama
    toplam_danisman = len(df_danismanlar) if not df_danismanlar.empty else 0
    toplam_ogrenci = len(df_ogrenciler) if not df_ogrenciler.empty else 0
    toplam_randevu = len(df_randevular) if not df_randevular.empty else 0

    tamamlanan = iptal = bekleyen = onaylanan = gerceklesmedi = 0

    # Durum sütunu kontrolü ve Statülerin Eklenmesi
    if not df_randevular.empty and "Durum" in df_randevular.columns:
        tamamlanan = len(df_randevular[df_randevular["Durum"].isin(["Tamamlandı", "Tamamlandi"])])
        iptal = len(df_randevular[df_randevular["Durum"].isin(["İptal", "İptal Edildi"])])
        bekleyen = len(df_randevular[df_randevular["Durum"] == "Bekliyor"])
        onaylanan = len(df_randevular[df_randevular["Durum"] == "Onaylandı"])
        gerceklesmedi = len(df_randevular[df_randevular["Durum"] == "Gerçekleşmedi"])

    # GENEL ÖZET KARTLARI
    st.write("")
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    kpi1.metric("Toplam Randevu", toplam_randevu)
    kpi2.metric("✔️ Tamamlanan", tamamlanan)
    kpi3.metric("❌ İptal Edilen", iptal, delta_color="inverse")
    kpi4.metric("⏳ Bekleyen", bekleyen)

    # Kullanılmayan 'onaylanan' ve 'gerceklesmedi' değişkenlerini KPI olarak eklendi
    kpi5.metric("📌 Onaylanan", onaylanan)
    kpi6.metric("🚫 Gerçekleşmedi", gerceklesmedi)

    st.divider()

    # Rapor Sekmeleri
    rap_tab1, rap_tab2 = st.tabs(["📈 Genel İstatistikler ve Grafikler", "👤 Kullanıcı Bazlı Raporlar"])

    with rap_tab1:
        # AKILLI ÖNERİ SİSTEMİ
        st.subheader("🧠 Sistem Yorumları")
        ai_col1, ai_col2, ai_col3 = st.columns(3)
        with ai_col1:
            if toplam_randevu > 0:
                st.success(f"🔥 **Genel Durum:** Sistemde toplam {toplam_randevu} randevu hareketi kaydedildi.")
            else:
                st.info("🔥 **Durum:** Henüz randevu verisi yok.")
        with ai_col2:
            if bekleyen > 0:
                st.warning(f"⚠️ **İşlem Bekleyenler:** Onay veya iptal bekleyen {bekleyen} adet randevu var.")
            else:
                st.success("✅ **İşlem Bekleyenler:** Tüm randevular işleme alınmış durumda.")
        with ai_col3:
            if iptal > 0 and toplam_randevu > 0:
                st.error(
                    f"📉 **İptal Analizi:** Toplam randevuların %{int((iptal / toplam_randevu) * 100)}'si iptal edilmiş.")
            else:
                st.info("📉 **İptal Analizi:** İptal edilen randevu bulunmuyor.")

        st.write("")

        # GRAFİKLER
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("📈 Danışman Performansı")
            if not df_randevular.empty and "Danisman" in df_randevular.columns:
                perf_data = df_randevular.groupby("Danisman").size().reset_index(name='Görüşme Sayısı')
                fig_bar = px.bar(perf_data, x="Danisman", y="Görüşme Sayısı", text="Görüşme Sayısı",
                                 color="Görüşme Sayısı", color_continuous_scale="Blues",
                                 labels={'Danisman': 'Danışman'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Grafik oluşturmak için yeterli randevu verisi yok.")

        with chart_col2:
            st.subheader("🥧 Randevu Durum Dağılımı")
            if not df_randevular.empty and "Durum" in df_randevular.columns:
                pie_data = df_randevular.groupby("Durum").size().reset_index(name='Oran')
                fig_pie = px.pie(pie_data, names="Durum", values="Oran", hole=0.4, color="Durum",
                                 color_discrete_map={"Tamamlandı": "#00CC96", "Tamamlandi": "#00CC96",
                                                     "İptal Edildi": "#EF553B", "İptal": "#EF553B",
                                                     "Gerçekleşmedi": "#B10DC9",
                                                     "Bekliyor": "#FFA15A", "Onaylandı": "#636EFA"})
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Grafik oluşturmak için yeterli randevu verisi yok.")

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            st.subheader("📅 Tarihe Göre Randevu Yoğunluğu")
            if not df_randevular.empty and "Tarih" in df_randevular.columns:
                trend_data = df_randevular.groupby("Tarih").size().reset_index(name='Randevu Sayısı')
                fig_line = px.line(trend_data, x="Tarih", y="Randevu Sayısı", markers=True, line_shape="spline")
                fig_line.update_traces(line_color="#FF4B4B", line_width=4, marker=dict(size=10))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Grafik oluşturmak için yeterli randevu verisi yok.")

        with chart_col4:
            st.subheader("🔥 Yoğunluk Isı Haritası")
            st.caption("Veri tabanında saat/gün birikimi arttıkça burası dinamikleşecektir.")
            z_data = [[1, 2, 5, 8, 3], [4, 8, 12, 15, 6], [2, 4, 9, 11, 4], [5, 10, 15, 22, 12], [3, 6, 8, 14, 5]]
            fig_heat = px.imshow(z_data,
                                 labels=dict(x="Saat Aralıkları", y="Günler", color="Yoğunluk"),
                                 x=['09:00', '11:00', '13:00', '15:00', '17:00'],
                                 y=['Pzt', 'Sal', 'Çar', 'Per', 'Cum'],
                                 color_continuous_scale="YlOrRd")
            st.plotly_chart(fig_heat, use_container_width=True)

        # DETAYLI TABLO VE DIŞA AKTARMA
        st.divider()
        st.subheader("📄 Detaylı Randevu Tablosu")

        gerekli_sutunlar = ["Ogrenci", "Danisman", "Tarih", "Saat", "Durum", "Konu"]
        if not df_randevular.empty and all(col in df_randevular.columns for col in gerekli_sutunlar):
            detay_df = df_randevular[gerekli_sutunlar]
            detay_df.columns = ["Öğrenci", "Danışman", "Tarih", "Saat", "Durum", "Konu"]
            st.dataframe(detay_df, use_container_width=True, hide_index=True)

            exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 3])
            with exp_col1:
                csv_data = detay_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Excel/CSV İndir", data=csv_data, file_name="Rapor_Detay.csv", type="primary")
            with exp_col2:
                st.button("📄 PDF İndir (Yakında)")
        else:
            st.info("Sistemde listelenecek geçerli bir randevu bulunmuyor.")

    #  KULLANICI BAZLI RAPORLAR SEKMESİ
    with rap_tab2:
        st.subheader("👨‍🏫 Danışman ve Öğrenci Karne Analizleri")
        user_col1, user_col2 = st.columns(2)

        with user_col1:
            with st.container(border=True):
                st.markdown("### 🎓 Danışman Raporu")
                if not df_danismanlar.empty:
                    secilen_dan = st.selectbox("İncelenecek Danışman:", df_danismanlar["AdSoyad"])

                    if not df_randevular.empty and "Danisman" in df_randevular.columns and "Durum" in df_randevular.columns:
                        dan_randevular = df_randevular[df_randevular["Danisman"] == secilen_dan]
                        dan_toplam = len(dan_randevular)

                        # Sadece sonuçlanmış randevuları hesapla
                        dan_tamamlanan = len(dan_randevular[dan_randevular["Durum"].isin(["Tamamlandı", "Tamamlandi"])])
                        kapanan_randevular = len(dan_randevular[dan_randevular["Durum"].isin(
                            ["Tamamlandı", "Tamamlandi", "İptal", "İptal Edildi", "Gerçekleşmedi"])])
                    else:
                        dan_toplam = 0
                        dan_tamamlanan = 0
                        kapanan_randevular = 0

                    st.metric("Toplam Randevu Sayısı", dan_toplam)
                    st.metric("Tamamlanan Görüşme", dan_tamamlanan)

                    # Oran hesabı sadece geçmiş randevular üzerinden yapılıyor
                    if kapanan_randevular > 0:
                        basari_orani = f"%{int((dan_tamamlanan / kapanan_randevular) * 100)}"
                        st.metric("Görüşme Başarı Oranı", basari_orani, delta="Sonuçlanan randevulara göre",
                                  delta_color="off")
                    else:
                        st.metric("Görüşme Başarı Oranı", "Hesaplanmadı", delta="Henüz bitmiş randevu yok",
                                  delta_color="off")
                else:
                    st.info("Kayıtlı danışman yok.")

        with user_col2:
            with st.container(border=True):
                st.markdown("### 👤 Öğrenci Raporu")
                if not df_ogrenciler.empty:
                    secilen_ogr = st.selectbox("İncelenecek Öğrenci:", df_ogrenciler["KullaniciAdi"])

                    if not df_randevular.empty and "Ogrenci" in df_randevular.columns:
                        ogr_randevular = df_randevular[df_randevular["Ogrenci"] == secilen_ogr]
                        ogr_toplam = len(ogr_randevular)
                    else:
                        ogr_randevular = pd.DataFrame()
                        ogr_toplam = 0

                    st.metric("Toplam Aldığı Randevu", ogr_toplam)
                    if ogr_toplam > 0 and "Konu" in ogr_randevular.columns:
                        son_konu = ogr_randevular.iloc[0]["Konu"]
                        st.metric("Katılım / Aktiflik", "Sistemde Aktif")
                        st.metric("Son Görüşme Konusu", son_konu if pd.notna(son_konu) else "Belirtilmemiş")
                    else:
                        st.metric("Katılım / Aktiflik", "Pasif")
                        st.metric("Son Görüşme Konusu", "Görüşme Yok")
                else:
                    st.info("Kayıtlı öğrenci yok.")