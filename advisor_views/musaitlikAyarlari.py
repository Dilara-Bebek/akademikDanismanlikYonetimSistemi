import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query

def show_musaitlik_ayarlari():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    danisman_kullanici_adi = st.session_state['username']

    st.header("⏰ Müsaitlik ve Takvim Ayarları")
    st.markdown(
        "Öğrencilerin sizden randevu alabileceği günleri, çalışma saatlerinizi, tatillerinizi ve randevu otomasyon kurallarınızı buradan yönetebilirsiniz.")

    # 1. DANIŞMAN ID'SİNİ ÇEKME
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

    # 2. MEVCUT AYARLARI VERİTABANINDAN ÇEKME
    query_ayarlar = "SELECT * FROM DANISMAN_AYARLARI WHERE DanismanID = ?"
    df_ayarlar = fetch_query(query_ayarlar, (danisman_id,))

    if df_ayarlar.empty:
        slot_suresi = 30
        oto_onay = False
        kendi_ogr = True
    else:
        slot_suresi = int(df_ayarlar.iloc[0]['SlotSuresi'])
        oto_onay = bool(df_ayarlar.iloc[0]['OtomatikOnay'])
        kendi_ogr = bool(df_ayarlar.iloc[0]['SadeceKendiOgr'])

    slot_str = f"{slot_suresi} Dakika" if slot_suresi < 60 else "1 Saat"

    #SEKMELER
    tab_haftalik, tab_tatil, tab_gelismis = st.tabs([
        "📅 Haftalık Çalışma Planı",
        "🏝️ İstisnalar ve Tatiller",
        "⚙️ Otomasyon ve Gelişmiş Ayarlar"
    ])

    # 1. HAFTALIK ÇALIŞMA PLANI
    with tab_haftalik:
        st.subheader("Haftalık Randevu Saatleri")
        st.info(
            "Sadece açık (yeşil) olan günlerde öğrencilere randevu takviminiz açık görünecektir. Saatleri kendi ders ve toplantı programınıza göre ayarlayabilirsiniz.")

        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        varsayilan_acik = [True, True, True, True, True, False, False]

        # Veritabanından hocanın daha önce kaydettiği saatleri çek
        query_saatler = "SELECT * FROM CALISMA_SAATLERI WHERE DanismanID = ?"
        df_saatler = fetch_query(query_saatler, (danisman_id,))

        saatler_dict = {}
        if not df_saatler.empty:
            for index, row in df_saatler.iterrows():
                # SQL'den gelen time formatını Streamlitin anlayacağı datetime.time objesine çeviriyoruz
                saatler_dict[row['Gun']] = {
                    'AcikMi': bool(row['AcikMi']),
                    'Baslangic': pd.to_datetime(str(row['Baslangic'])).time() if pd.notna(
                        row['Baslangic']) else datetime.time(9, 0),
                    'Bitis': pd.to_datetime(str(row['Bitis'])).time() if pd.notna(row['Bitis']) else datetime.time(17,
                                                                                                                   0)
                }

        yeni_saatler = {}

        with st.form("haftalik_plan_form"):
            for i, gun in enumerate(gunler):
                # Eğer SQL'de varsa onu al, yoksa varsayılanı kullan
                is_open_default = saatler_dict.get(gun, {}).get('AcikMi', varsayilan_acik[i])
                start_default = saatler_dict.get(gun, {}).get('Baslangic', datetime.time(9, 0))
                end_default = saatler_dict.get(gun, {}).get('Bitis', datetime.time(17, 0))

                with st.container(border=True):
                    col_toggle, col_start, col_end = st.columns([1, 1, 1])
                    with col_toggle:
                        is_active = st.toggle(gun, value=is_open_default, key=f"toggle_{gun}")
                    with col_start:
                        # hocalar saatlere müdahale edebilir,Gün kapalıysa saat seçimi de disable olur
                        start_time = st.time_input("Başlangıç", value=start_default, disabled=not is_active,
                                                   key=f"start_{gun}")
                    with col_end:
                        end_time = st.time_input("Bitiş", value=end_default, disabled=not is_active, key=f"end_{gun}")

                # Seçilen değerleri sözlükte tutuyoruz ki formu kaydedince SQL'e yollayalım
                yeni_saatler[gun] = {"AcikMi": is_active, "Baslangic": start_time, "Bitis": end_time}

            if st.form_submit_button("💾 Çalışma Planını Kaydet", type="primary", use_container_width=True):
                # Veritabanını güncelle
                if df_saatler.empty:
                    # İlk defa kaydediyorsa INSERT yap
                    for g, vals in yeni_saatler.items():
                        b_str = vals['Baslangic'].strftime("%H:%M:%S")
                        e_str = vals['Bitis'].strftime("%H:%M:%S")
                        execute_query(
                            "INSERT INTO CALISMA_SAATLERI (DanismanID, Gun, AcikMi, Baslangic, Bitis) VALUES (?, ?, ?, ?, ?)",
                            (danisman_id, g, vals['AcikMi'], b_str, e_str))
                else:
                    # Daha önce kaydı varsa UPDATE yap
                    for g, vals in yeni_saatler.items():
                        b_str = vals['Baslangic'].strftime("%H:%M:%S")
                        e_str = vals['Bitis'].strftime("%H:%M:%S")
                        execute_query(
                            "UPDATE CALISMA_SAATLERI SET AcikMi = ?, Baslangic = ?, Bitis = ? WHERE DanismanID = ? AND Gun = ?",
                            (vals['AcikMi'], b_str, e_str, danisman_id, g))

                st.success("Haftalık çalışma saatleriniz veritabanına başarıyla kaydedildi!")
                st.rerun()

    # TATİLLER VE İSTİSNALAR
    with tab_tatil:
        st.subheader("Özel Günler ve İzinler")
        st.markdown("Bu tarihlerde takviminiz **otomatik olarak randevulara kapatılacaktır.**")

        with st.container(border=True):
            t_col1, t_col2 = st.columns([2, 1])
            with t_col1:
                tatil_tarihi = st.date_input("Tatil veya İzin Günü Seçin", min_value=datetime.date.today())
                tatil_nedeni = st.text_input("Açıklama (Örn: Yıllık İzin, Konferans)", placeholder="İsteğe bağlı...")
            with t_col2:
                st.write("")
                st.write("")
                if st.button("➕ Kapalı Gün Ekle", use_container_width=True, type="primary"):
                    tarih_str = tatil_tarihi.strftime("%Y-%m-%d")
                    insert_tatil = "INSERT INTO KAPALI_GUNLER (DanismanID, Tarih, Aciklama) VALUES (?, ?, ?)"
                    if execute_query(insert_tatil, (danisman_id, tarih_str, tatil_nedeni)):
                        st.success(f"{tarih_str} takvime başarıyla eklendi.")
                        st.rerun()
                    else:
                        st.error("Eklenirken bir hata oluştu.")

        st.write("📌 **Eklenmiş Tatiller / Kapalı Günler**")

        query_tatiller = "SELECT KapaliID, Tarih, Aciklama FROM KAPALI_GUNLER WHERE DanismanID = ? ORDER BY Tarih ASC"
        df_tatiller = fetch_query(query_tatiller, (danisman_id,))

        if df_tatiller.empty:
            st.info("Sisteme eklenmiş herhangi bir kapalı gününüz bulunmamaktadır.")
        else:
            gosterim_df = df_tatiller.copy()
            gosterim_df['Durum'] = "🔴 Kapalı"
            st.dataframe(gosterim_df[['Tarih', 'Aciklama', 'Durum']], use_container_width=True, hide_index=True)

            with st.expander("🗑️ Yanlış Eklenen Günü Sil"):
                silinecek_id = st.selectbox("Silmek istediğiniz tarihi seçin:", df_tatiller['KapaliID'].tolist(),
                                            format_func=lambda
                                                x: f"{df_tatiller[df_tatiller['KapaliID'] == x].iloc[0]['Tarih']} - {df_tatiller[df_tatiller['KapaliID'] == x].iloc[0]['Aciklama']}")

                if st.button("Seçili Günü Sil", type="secondary"):
                    if execute_query("DELETE FROM KAPALI_GUNLER WHERE KapaliID = ?", (int(silinecek_id),)):
                        st.success("Kapalı gün başarıyla silindi.")
                        st.rerun()

    # 3. GELİŞMİŞ AYARLAR
    with tab_gelismis:
        st.subheader("Randevu Otomasyonu ve Slot Ayarları")

        with st.container(border=True):
            st.markdown("#### ⏳ Slot (Görüşme) Süreleri")
            yeni_slot_str = st.select_slider(
                "Bir randevunun standart süresi ne kadar olsun?",
                options=["15 Dakika", "20 Dakika", "30 Dakika", "45 Dakika", "1 Saat"],
                value=slot_str
            )
            st.caption(
                "Sistem, çalışma saatlerinizi yukarıdaki süre dilimlerine bölerek öğrencilere randevu seçenekleri sunar.")

        with st.container(border=True):
            st.markdown("#### 🤖 Akıllı Planlama & Çakışma Engelleyici")
            yeni_oto = st.toggle("✅ Otomatik Onay Sistemi", value=oto_onay,
                                 help="Müsait olduğunuz slotlara gelen randevu talepleri sistem tarafından otomatik onaylanır.")

            st.toggle("🚫 Çakışma Önleyici Algoritma", value=True, disabled=True,
                      help="Aynı saate iki randevu alınmasını engeller. Sistem güvenliği için zorunlu olarak aktiftir.")
            yeni_kendi = st.toggle("🎓 Sadece Kendi Öğrencilerime Aç", value=kendi_ogr,
                                   help="Kapatırsanız, bölümdeki diğer öğrenciler de boş vakitlerinizde sizden randevu talep edebilir.")

        if st.button("⚙️ Otomasyon Ayarlarını Kaydet", type="primary", use_container_width=True):
            yeni_slot_int = int(yeni_slot_str.split(" ")[0]) if "Dakika" in yeni_slot_str else 60

            if df_ayarlar.empty:
                insert_ayar = """
                    INSERT INTO DANISMAN_AYARLARI (DanismanID, SlotSuresi, OtomatikOnay, SadeceKendiOgr) 
                    VALUES (?, ?, ?, ?)
                """
                success = execute_query(insert_ayar, (danisman_id, yeni_slot_int, yeni_oto, yeni_kendi))
            else:
                update_ayar = """
                    UPDATE DANISMAN_AYARLARI 
                    SET SlotSuresi = ?, OtomatikOnay = ?, SadeceKendiOgr = ? 
                    WHERE DanismanID = ?
                """
                success = execute_query(update_ayar, (yeni_slot_int, yeni_oto, yeni_kendi, danisman_id))

            if success:
                st.success(
                    "Randevu otomasyonu ve slot tercihleri başarıyla kaydedildi! Yeni kurallar hemen geçerli olacaktır.")

            else:
                st.error("Ayarlar kaydedilirken bir hata oluştu.")