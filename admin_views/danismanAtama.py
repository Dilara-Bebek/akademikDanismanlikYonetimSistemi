import streamlit as st
import pandas as pd
from database import fetch_query, execute_query


def show_danisman_atama():
    st.header("🔗 Öğrenci - Danışman Eşleştirme")
    st.markdown("Sisteme kayıtlı öğrencileri, ilgili danışman hocalarla bu ekrandan eşleştirebilirsiniz.")

    #  Öğrencileri çekerken artık Bolum bilgisini vs. al
    df_ogrenciler = fetch_query("SELECT OgrenciID, OgrenciNo, AdSoyad, Bolum FROM OGRENCILER")

    # sistemde danışman var mı
    df_tum_danismanlar = fetch_query("SELECT DanismanID FROM DANISMANLAR")

    if df_ogrenciler.empty or df_tum_danismanlar.empty:
        st.warning(
            "⚠️ Eşleştirme yapabilmek için sistemde en az 1 Öğrenci ve 1 Danışman kayıtlı olmalıdır. Lütfen 'Kullanıcı Yönetimi' sayfasından kayıt ekleyin.")
        return

    # Öğrenci listesini hazırla
    df_ogrenciler["Gosterim"] = df_ogrenciler["AdSoyad"] + " (" + df_ogrenciler["OgrenciNo"].astype(str) + ")"
    ogrenci_dict = dict(zip(df_ogrenciler["Gosterim"], df_ogrenciler["OgrenciID"]))
    ogrenci_listesi = list(ogrenci_dict.keys())

    with st.container(border=True):
        st.subheader("Yeni Atama Yap / Güncelle")

        #Burada st.form kullanmıyoruz ki birinci kutuyu seçince sayfa anında yenilensin
        col_ogr, col_dan = st.columns(2)

        with col_ogr:
            secilen_ogrenci_gosterim = st.selectbox("👨‍🎓 Öğrenci Seçin", ogrenci_listesi)

        # Seçilen öğrencinin veritabanındaki bölümünü bul
        secilen_ogr_id = ogrenci_dict[secilen_ogrenci_gosterim]
        secilen_bolum = df_ogrenciler.loc[df_ogrenciler['OgrenciID'] == secilen_ogr_id, 'Bolum'].values[0]

        with col_dan:
            #Sadece öğrenciyle aynı bolumdeki hocaları SQL'den çek
            query_dan = "SELECT DanismanID, AdSoyad, Unvan FROM DANISMANLAR WHERE Bolum = ?"
            df_danismanlar = fetch_query(query_dan, (secilen_bolum,))

            if not df_danismanlar.empty:
                # Hocaların önüne ünvanlarını da ekle
                df_danismanlar["DanismanGosterim"] = df_danismanlar["Unvan"].fillna("") + " " + df_danismanlar[
                    "AdSoyad"]
                df_danismanlar["DanismanGosterim"] = df_danismanlar["DanismanGosterim"].str.strip()

                danisman_dict = dict(zip(df_danismanlar["DanismanGosterim"], df_danismanlar["DanismanID"]))
                danisman_listesi = list(danisman_dict.keys())

                # Kutucuk başlığına bölüm adını da yaz
                secilen_danisman_adi = st.selectbox(f"👨‍🏫 Danışman Seçin ({secilen_bolum})", danisman_listesi)
            else:
                # Eğer o bölümde henüz kayıtlı hoca yoksa sisteme uyarı ver
                st.selectbox("👨‍🏫 Danışman Seçin", ["Bu bölümde henüz kayıtlı hoca bulunmuyor."], disabled=True)
                secilen_danisman_adi = None

        st.write("")
        submit_btn = st.button("🔗 Danışmanı Ata", type="primary", use_container_width=True)

        if submit_btn:
            if secilen_danisman_adi is None:
                st.error(
                    "⚠️ Seçili bölüme ait danışman bulunmadığı için atama yapılamaz. Lütfen önce o bölüme bir danışman kaydedin.")
            else:
                dan_id = danisman_dict[secilen_danisman_adi]

                query = "UPDATE OGRENCILER SET DanismanID = ? WHERE OgrenciID = ?"
                basarili = execute_query(query, (dan_id, secilen_ogr_id))

                if basarili:
                    st.success(
                        f"✅ Başarılı! {secilen_ogrenci_gosterim} kullanıcısı, {secilen_danisman_adi} isimli hocaya atandı.")

                    log_aciklama = f"{secilen_ogrenci_gosterim} kullanıcısına, {secilen_danisman_adi} danışman olarak atandı."
                    execute_query(
                        "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Danışman Atama', ?, 'Başarılı')",
                        (log_aciklama,))

                    # BİLDİRİM TETİKLEYİCİSİ
                    execute_query(
                        "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem: Danışman Ataması', ?, 0, GETDATE())",
                        (f"{secilen_ogrenci_gosterim} öğrencisine, {secilen_danisman_adi} danışman olarak atandı.",))

                    # 1 saniye bekleyip sayfayı yeniliyoruz ki yeşil başarı mesajı anında kaybolmasın
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Atama sırasında veritabanı hatası oluştu.")

    st.divider()
    st.subheader("📋 Mevcut Öğrenci - Danışman Eşleşmeleri")

    liste_query = """
        SELECT 
            o.AdSoyad + ' (' + o.OgrenciNo + ')' as [Öğrenci Bilgisi], 
            ISNULL(d.AdSoyad, '⚠️ Henüz Atanmadı') as [Atanan Danışman]
        FROM OGRENCILER o
        LEFT JOIN DANISMANLAR d ON o.DanismanID = d.DanismanID
        ORDER BY o.AdSoyad
    """
    df_liste = fetch_query(liste_query)

    if not df_liste.empty:
        st.dataframe(df_liste, use_container_width=True, hide_index=True)