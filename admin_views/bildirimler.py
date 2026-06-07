import streamlit as st
import pandas as pd
from database import fetch_query, execute_query


def show_bildirimler():
    st.header("🔔 Bildirim Merkezi ve Onaylar")

    #sqlden bildirim çekme
    query = """
        SELECT 
            BildirimID,
            ISNULL(Baslik, 'Sistem') as Baslik,
            Mesaj,
            OkunduMu,
            FORMAT(Tarih, 'yyyy-MM-dd HH:mm') as Tarih
        FROM BILDIRIMLER
        ORDER BY BildirimID DESC
    """
    df_bildirimler = fetch_query(query)

    # Okunmamış bildirim sayısını hesapla
    unread_count = len(df_bildirimler[df_bildirimler['OkunduMu'] == False]) if not df_bildirimler.empty else 0

    # Görselleştirme için yardımcı fonksiyon
    def get_notif_style(baslik):
        if "Randevu" in baslik:
            return "🔴 Kritik", "📅"
        elif "Kullanıcı" in baslik:
            return "🟢 Normal", "👤"
        elif "Uyarı" in baslik or "Hata" in baslik:
            return "🟡 Orta", "⚠️"
        else:
            return "🔵 Bilgi", "🔔"

    # ÜST BİLGİ ALANI
    if unread_count > 0:
        st.error(f"🚨 **{unread_count} Yeni Okunmamış Bildiriminiz Var!**")
    else:
        st.success("✅ Tüm bildirimleri okudunuz. Yakalanacak yeni bir şey yok.")

    st.divider()

    # ANA SEKMELER: GELEN KUTUSU, AYARLAR VE YENİ DUYURU YÖNETİMİ
    tab_inbox, tab_settings, tab_duyuru = st.tabs(["📥 Gelen Kutusu", "⚙️ Bildirim Ayarları", "📢 Genel Duyuru Yönetimi"])

    with tab_inbox:
        # FİLTRELEME VE TOPLU İŞLEMLER
        with st.container(border=True):
            f_col1, f_col2, f_col3 = st.columns([2, 1, 2])
            with f_col1:
                filter_type = st.selectbox("📌 Bildirim Türü", ["Tümü", "Randevu", "Kullanıcı", "Sistem", "Uyarı"])
            with f_col2:
                st.write("")
                filter_unread = st.checkbox("❗ Sadece Okunmayanlar")
            with f_col3:
                st.write("")
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button("✔️ Tümünü Okundu Yap", use_container_width=True):
                        execute_query("UPDATE BILDIRIMLER SET OkunduMu = 1")
                        st.toast("Tüm bildirimler SQL'de okundu olarak işaretlendi.", icon="✅")
                        st.rerun()
                with b_col2:
                    if st.button("🗑️ Tümünü Sil", use_container_width=True):
                        execute_query("DELETE FROM BILDIRIMLER")
                        st.toast("Veritabanındaki tüm bildirimler silindi.", icon="🗑️")
                        st.rerun()

        # BİLDİRİM LİSTESİ
        st.write("")

        if df_bildirimler.empty:
            st.info("📭 Sistemde henüz hiç bildirim kaydı bulunmuyor.")
        else:
            filtered_df = df_bildirimler.copy()

            if filter_type != "Tümü":
                filtered_df = filtered_df[filtered_df['Baslik'].str.contains(filter_type, case=False, na=False)]
            if filter_unread:
                filtered_df = filtered_df[filtered_df['OkunduMu'] == False]

            if filtered_df.empty:
                st.info("📭 Bu filtrelere uygun bildirim bulunmuyor.")
            else:
                for index, notif in filtered_df.iterrows():
                    n_id = notif['BildirimID']
                    n_read = notif['OkunduMu']
                    n_msg = notif['Mesaj']
                    n_time = notif['Tarih']
                    n_priority, n_icon = get_notif_style(notif['Baslik'])

                    with st.container(border=True):
                        col_icon, col_msg, col_time, col_act = st.columns([1, 6, 2, 2])

                        with col_icon:
                            st.subheader(n_icon)

                        with col_msg:
                            if not n_read:
                                st.markdown(f"**{n_msg}**")
                            else:
                                st.markdown(f"<span style='color:gray'>{n_msg}</span>", unsafe_allow_html=True)

                        with col_time:
                            st.caption(f"{n_priority} | {n_time}")
                            if not n_read:
                                st.markdown("🆕 *Yeni*")

                        with col_act:
                            a_col1, a_col2 = st.columns(2)
                            with a_col1:
                                st.button("Detay", key=f"detay_{n_id}", use_container_width=True)
                            with a_col2:
                                if not n_read:
                                    if st.button("✔️", key=f"read_{n_id}", help="Okundu İşaretle"):
                                        execute_query("UPDATE BILDIRIMLER SET OkunduMu = 1 WHERE BildirimID = ?",
                                                      (n_id,))
                                        st.rerun()
                                else:
                                    if st.button("🗑️", key=f"del_{n_id}", help="Sil"):
                                        execute_query("DELETE FROM BILDIRIMLER WHERE BildirimID = ?", (n_id,))
                                        st.rerun()

    # BİLDİRİM AYARLARI
    with tab_settings:
        st.subheader("⚙️ Sistem Bildirim Tercihleri")
        st.info("Hangi durumlarda ve hangi kanallardan bildirim almak istediğinizi yönetin.")

        with st.container(border=True):
            st.markdown("#### 📅 Randevu Bildirimleri")
            st.checkbox("Yeni Randevu Oluşturulduğunda", value=True)
            st.checkbox("Randevu İptal Edildiğinde", value=True)
            st.checkbox("Randevu Saatine 1 Saat Kala (Hatırlatıcı)", value=True)

        with st.container(border=True):
            st.markdown("#### ⚠️ Sistem ve Kullanıcı Bildirimleri")
            st.checkbox("Yeni Kullanıcı Kaydolduğunda", value=False)
            st.checkbox("Sistem Yoğunluğu Kritik Seviyeye Ulaştığında", value=True)
            st.checkbox("Haftalık Akıllı Sistem Özetleri", value=True)

        with st.container(border=True):
            st.markdown("#### 📧 Bildirim Kanalları")
            st.toggle("Sistem İçi Bildirimler", value=True)
            st.toggle("E-Posta Bildirimleri Gönder", value=False)
            st.toggle("SMS Bildirimleri Gönder", value=False)

        if st.button("💾 Ayarları Kaydet", type="primary"):
            st.toast("Ayarlarınız sisteme kaydedildi!", icon="✅")

    #  GENEL DUYURU YÖNETİMİ
    with tab_duyuru:
        st.subheader("📢 Ana Sayfa Duyuru Panosu Yönetimi")
        st.markdown(
            "Buradan yayınlayacağınız duyurular, sisteme giriş ekranındaki sağ panoda tüm öğrencilere ve danışmanlara anında gösterilecektir.")

        with st.form("yeni_duyuru_ekle"):
            d_baslik = st.text_input("📌 Duyuru Başlığı", placeholder="Örn: 2026 Bahar Dönemi Kayıtları")
            d_metin = st.text_area("📝 Duyuru Metni", placeholder="Duyurunun detaylarını buraya yazın...")
            d_tur = st.selectbox("🎨 Duyuru Teması (Rengi)",
                                 ["Bilgi (Mavi)", "Uyarı (Sarı)", "Başarı/Yeni Özellik (Yeşil)",
                                  "Hata/Kritik (Kırmızı)"])

            ekle_btn = st.form_submit_button("Anasayfada Yayınla", type="primary", use_container_width=True)

            if ekle_btn:
                if len(d_baslik) > 3 and len(d_metin) > 5:
                    try:
                        execute_query("INSERT INTO GENEL_DUYURULAR (Baslik, Metin, Tur) VALUES (?, ?, ?)",
                                      (d_baslik, d_metin, d_tur))
                        st.toast("Duyuru ana sayfada başarıyla yayınlandı!", icon="📢")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Veritabanına yazılırken hata oluştu: {e}")
                else:
                    st.warning("Lütfen geçerli bir başlık ve detaylı bir metin giriniz.")

        st.divider()
        st.markdown("#### 🗑️ Yayındaki Duyuruları Kaldır")
        try:
            df_aktif_duyurular = fetch_query(
                "SELECT DuyuruID, Baslik, Tur, FORMAT(Tarih, 'yyyy-MM-dd HH:mm') as Tarih FROM GENEL_DUYURULAR ORDER BY DuyuruID DESC")
            if not df_aktif_duyurular.empty:
                for index, row in df_aktif_duyurular.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([4, 2, 1])
                        c1.markdown(f"**{row['Baslik']}**")
                        c2.caption(f"{row['Tur']} | {row['Tarih']}")
                        if c3.button("Kaldır", key=f"del_dy_{row['DuyuruID']}", type="secondary",
                                     use_container_width=True):
                            execute_query("DELETE FROM GENEL_DUYURULAR WHERE DuyuruID = ?", (row['DuyuruID'],))
                            st.rerun()
            else:
                st.info("Şu anda ana sayfada yayında olan bir duyuru bulunmuyor.")
        except Exception:
            st.warning("Henüz duyuru veritabanı kurulmamış olabilir.")