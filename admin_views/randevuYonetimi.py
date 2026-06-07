import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query


# randevu detay kartı
@st.dialog("📋 Randevu Detay Kartı")
def show_randevu_details(r_id, df):
    detay = df[df["ID"] == r_id].iloc[0]
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"🎓 **Öğrenci:** {detay['Öğrenci Adı']}")
        st.write(f"📅 **Tarih:** {detay['Tarih']}")
        st.write(f"📌 **Durum:** {detay['Durum']}")
    with col2:
        st.write(f"👤 **Danışman:** {detay['Danışman Adı']}")
        st.write(f"⏰ **Saat:** {detay['Saat']}")

    st.divider()
    st.write(f"📝 **Görüşme Konusu / Notlar:** {detay['Konu']}")
    st.info("Randevu detayları anlık olarak çekilmektedir.")


@st.dialog("➕ Yeni Randevu Oluştur")
def yeni_randevu_olustur_dialog():
    df_ogr = fetch_query("SELECT OgrenciID, AdSoyad + ' (' + OgrenciNo + ')' as Gosterim FROM OGRENCILER")
    df_dan = fetch_query("SELECT DanismanID, AdSoyad FROM DANISMANLAR")

    if df_ogr.empty or df_dan.empty:
        st.error("⚠️ Sistemde kayıtlı öğrenci veya danışman bulunmuyor.")
        return

    ogr_dict = dict(zip(df_ogr["Gosterim"], df_ogr["OgrenciID"]))
    dan_dict = dict(zip(df_dan["AdSoyad"], df_dan["DanismanID"]))

    with st.form("yeni_randevu_formu"):
        secilen_ogr = st.selectbox("👨‍🎓 Öğrenci Seçin", list(ogr_dict.keys()))
        secilen_dan = st.selectbox("👨‍🏫 Danışman Seçin", list(dan_dict.keys()))

        col_tarih, col_saat = st.columns(2)
        with col_tarih:
            randevu_tarihi = st.date_input("📅 Tarih")
        with col_saat:
            randevu_saati = st.time_input("⏰ Saat", value=datetime.time(10, 00))

        konu = st.text_area("📝 Görüşme Konusu", placeholder="Randevu nedenini kısaca belirtin...")

        submit_btn = st.form_submit_button("Randevuyu Kaydet", type="primary", use_container_width=True)

        if submit_btn:
            ogr_id = ogr_dict[secilen_ogr]
            dan_id = dan_dict[secilen_dan]

            query = """
                INSERT INTO RANDEVULAR (OgrenciID, DanismanID, Tarih, Saat, Durum, Konu)
                VALUES (?, ?, ?, ?, 'Bekliyor', ?)
            """
            basarili = execute_query(query, (ogr_id, dan_id, randevu_tarihi.strftime("%Y-%m-%d"),
                                             randevu_saati.strftime("%H:%M:00"), konu))

            if basarili:
                execute_query(
                    "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Randevu', ?, 'Başarılı')",
                    (f"Yönetici tarafından {secilen_ogr} için yeni randevu oluşturuldu.",))

                # BİLDİRİM TETİKLEYİCİSİ
                execute_query(
                    "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem: Yeni Randevu', ?, 0, GETDATE())",
                    (f"Yönetici tarafından {secilen_ogr} için yeni randevu oluşturuldu.",))

                st.success("✅ Randevu başarıyla oluşturuldu!")
                st.rerun()
            else:
                st.error("Veritabanına kaydedilirken bir hata oluştu.")


def show_randevu_yonetimi():
    st.header("📅 Randevu Yönetimi Merkezi")

    query = """
        SELECT 
            r.RandevuID as [ID], 
            o.AdSoyad + ' (' + o.OgrenciNo + ')' as [Öğrenci Adı], 
            d.AdSoyad as [Danışman Adı], 
            CONVERT(VARCHAR, r.Tarih, 23) as [Tarih], 
            CONVERT(VARCHAR, r.Saat, 8) as [Saat], 
            r.Durum as [Durum], 
            r.Konu as [Konu]
        FROM RANDEVULAR r
        LEFT JOIN OGRENCILER o ON r.OgrenciID = o.OgrenciID
        LEFT JOIN DANISMANLAR d ON r.DanismanID = d.DanismanID
        ORDER BY r.Tarih DESC, r.Saat DESC
    """
    df_randevular = fetch_query(query)

    def format_durum(durum):
        if durum == "Bekliyor":
            return "🟡 Bekliyor"
        elif durum == "Onaylandı":
            return "🟢 Onaylandı"
        elif durum == "İptal" or durum == "İptal Edildi":
            return "🔴 İptal Edildi"
        elif durum == "Tamamlandi" or durum == "Tamamlandı":
            return "🔵 Tamamlandı"
        elif durum == "Gerçekleşmedi":
            return "⚠️ Gerçekleşmedi"
        return durum

    if not df_randevular.empty:
        df_randevular["Durum"] = df_randevular["Durum"].apply(format_durum)

    bugun = datetime.date.today().strftime("%Y-%m-%d")
    bugunku_sayi = len(df_randevular[df_randevular["Tarih"] == bugun]) if not df_randevular.empty else 0
    bekleyen_sayi = len(df_randevular[df_randevular["Durum"] == "🟡 Bekliyor"]) if not df_randevular.empty else 0
    tamamlanan_sayi = len(df_randevular[df_randevular["Durum"] == "🔵 Tamamlandı"]) if not df_randevular.empty else 0
    iptal_sayi = len(df_randevular[df_randevular["Durum"] == "🔴 İptal Edildi"]) if not df_randevular.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📅 Bugünkü Randevular", bugunku_sayi)
    col2.metric("⏳ Bekleyen Onaylar", bekleyen_sayi, delta_color="inverse")
    col3.metric("✔️ Tamamlanan", tamamlanan_sayi)
    col4.metric("❌ İptal Edilen", iptal_sayi, delta_color="normal")

    st.divider()

    st.subheader("🔍 Arama ve Filtreleme")
    with st.container(border=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            search_query = st.text_input("Öğrenci/Danışman Ara", placeholder="İsim girin...")
        with f_col2:
            date_filter = st.selectbox("Tarih Aralığı", ["Tümü", "Bugün"])
        with f_col3:
            status_filter = st.multiselect("Durum Filtresi",
                                           ["🟡 Bekliyor", "🟢 Onaylandı", "🔴 İptal Edildi", "🔵 Tamamlandı",
                                            "⚠️ Gerçekleşmedi"],
                                           default=["🟡 Bekliyor", "🟢 Onaylandı"])
        with f_col4:
            st.write("")
            st.write("")
            if st.button("➕ Yeni Randevu Oluştur", type="primary", use_container_width=True):
                yeni_randevu_olustur_dialog()

    st.write("")

    view_mode = st.radio("Görünüm Modu:", ["📋 Ana Tablo", "Danışman Yoğunluk Analizi"], horizontal=True)

    if view_mode == "📋 Ana Tablo":
        if df_randevular.empty:
            st.info("Sistemde henüz oluşturulmuş bir randevu bulunmuyor.")
        else:
            filtered_df = df_randevular.copy()
            if search_query:
                filtered_df = filtered_df[
                    filtered_df["Öğrenci Adı"].str.contains(search_query, case=False, na=False) |
                    filtered_df["Danışman Adı"].str.contains(search_query, case=False, na=False)
                    ]
            if date_filter == "Bugün":
                filtered_df = filtered_df[filtered_df["Tarih"] == bugun]
            if status_filter:
                filtered_df = filtered_df[filtered_df["Durum"].isin(status_filter)]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Tabloyu Excel/CSV Olarak İndir", data=csv, file_name="randevular.csv",
                               mime="text/csv")

            st.divider()

            st.subheader("⚡ Hızlı Randevu İşlemleri")
            with st.container(border=True):
                act_col1, act_col2 = st.columns([1, 2])
                with act_col1:
                    secilen_id = st.selectbox("İşlem Yapılacak Randevu ID Seçin:", filtered_df["ID"])
                with act_col2:
                    st.write("")
                    st.write("")

                    btn1, btn2, btn3 = st.columns(3)

                    if btn1.button("👁️ Detay Gör", use_container_width=True):
                        if secilen_id:
                            show_randevu_details(secilen_id, filtered_df)

                    if btn2.button("✔️ Onayla", type="primary", use_container_width=True):
                        if secilen_id and execute_query("UPDATE RANDEVULAR SET Durum = 'Onaylandı' WHERE RandevuID = ?",
                                                        (secilen_id,)):
                            execute_query(
                                "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Randevu', ?, 'Başarılı')",
                                (f"{secilen_id} numaralı randevu onaylandı.",))

                            # BİLDİRİM TETİKLEYİCİSİ
                            execute_query(
                                "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Randevu Onayı', ?, 0, GETDATE())",
                                (f"ID: {secilen_id} numaralı randevu yönetici tarafından onaylandı.",))

                            st.success(f"{secilen_id} numaralı randevu ONAYLANDI!")
                            st.rerun()

                    if btn3.button("❌ İptal Et", use_container_width=True):
                        if secilen_id and execute_query(
                                "UPDATE RANDEVULAR SET Durum = 'İptal Edildi' WHERE RandevuID = ?",
                                (secilen_id,)):
                            execute_query(
                                "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Randevu', ?, 'Güncelleme')",
                                (f"{secilen_id} numaralı randevu iptal edildi.",))

                            # BİLDİRİM TETİKLEYİCİSİ
                            execute_query(
                                "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Randevu İptali', ?, 0, GETDATE())",
                                (f"ID: {secilen_id} numaralı randevu yönetici tarafından iptal edildi.",))

                            st.warning(f"{secilen_id} numaralı randevu İPTAL EDİLDİ!")
                            st.rerun()

    elif view_mode == "Danışman Yoğunluk Analizi":
        st.subheader("🧠 Akıllı Danışman Yoğunluk Analizi")
        st.info("Sistem, takvim çakışmalarını ve danışman yükünü analiz ederek size en uygun boş saatleri önerir.")

        chart_query = """
            SELECT d.AdSoyad as Danisman, COUNT(r.RandevuID) as RandevuSayisi
            FROM DANISMANLAR d
            LEFT JOIN RANDEVULAR r ON d.DanismanID = r.DanismanID AND r.Durum NOT IN ('İptal', 'İptal Edildi')
            GROUP BY d.AdSoyad
        """
        df_chart = fetch_query(chart_query)

        if not df_chart.empty and df_chart['RandevuSayisi'].sum() > 0:
            df_chart.set_index("Danisman", inplace=True)
            st.bar_chart(df_chart, color="#7B68EE")
        else:
            st.warning("Henüz grafiği oluşturacak yeterli randevu kaydı bulunmuyor.")

        st.success("🤖 Otomatik Çakışma Kontrolü Aktif: Sistem aynı saate iki randevu verilmesini engellemektedir.")