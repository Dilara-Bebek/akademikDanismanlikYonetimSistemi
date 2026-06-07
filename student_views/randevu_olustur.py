import streamlit as st
import pandas as pd
import datetime
from database import fetch_query, execute_query
def show_randevu_olustur():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("➕ Yeni Randevu Oluştur")
    st.markdown("---")

    # 1. ÖĞRENCİ VE DANIŞMAN BİLGİLERİNİ ÇEKME
    query_info = """
        SELECT O.OgrenciID, O.DanismanID, D.AdSoyad AS DanismanAd
        FROM OGRENCILER O
        LEFT JOIN DANISMANLAR D ON O.DanismanID = D.DanismanID
        WHERE O.OgrenciNo = ?
    """
    df_info = fetch_query(query_info, (ogrenci_no,))

    if df_info.empty or pd.isna(df_info.iloc[0]['DanismanID']):
        st.warning(
            "⚠️ Sisteme kayıtlı bir danışmanınız bulunmamaktadır. Randevu alabilmek için yönetici ile iletişime geçiniz.")
        return

    ogrenci_id = int(df_info.iloc[0]['OgrenciID'])
    danisman_id = int(df_info.iloc[0]['DanismanID'])
    danisman_ad = df_info.iloc[0]['DanismanAd']

    # 2. DANIŞMAN AYARLARINI ÇEKME
    query_ayarlar = "SELECT SlotSuresi FROM DANISMAN_AYARLARI WHERE DanismanID = ?"
    df_ayarlar = fetch_query(query_ayarlar, (danisman_id,))

    # Eğer hoca ayar yapmamışsa varsayılan 30 dakika olsun
    slot_suresi = int(df_ayarlar.iloc[0]['SlotSuresi']) if not df_ayarlar.empty else 30

    # 3. RANDEVU FORMU VE AKILLI ÇAKIŞMA KONTROLÜ
    with st.container(border=True):
        st.subheader("🗓️ Randevu Detayları")
        st.info(f"👩‍🏫 **Danışmanınız:** {danisman_ad} | ⏳ **Görüşme Süresi:** {slot_suresi} Dakika")

        col1, col2 = st.columns(2)

        with col1:
            min_date = datetime.date.today() + datetime.timedelta(days=1)
            max_date = datetime.date.today() + datetime.timedelta(days=30)
            secilen_tarih = st.date_input("Randevu Tarihi Seçiniz", min_value=min_date, max_value=max_date)

        # Seçilen günün ismini Türkçeye çevirme
        gunler_tr = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
        secilen_gun_adi = gunler_tr[secilen_tarih.weekday()]
        tarih_str = secilen_tarih.strftime("%Y-%m-%d")

        # KONTROL 1: Hoca o gün kapalı mı (Tatil/İzin)?
        query_tatil = "SELECT Aciklama FROM KAPALI_GUNLER WHERE DanismanID = ? AND Tarih = ?"
        df_tatil = fetch_query(query_tatil, (danisman_id, tarih_str))

        if not df_tatil.empty:
            tatil_nedeni = df_tatil.iloc[0]['Aciklama']
            st.error(f"Danışmanınız bu tarihte kapalıdır. (Neden: {tatil_nedeni}) Lütfen başka bir tarih seçiniz.")
            return

        # KONTROL 2: Hoca haftalık planda o gün çalışıyor mu? (Saatleri kaç?)
        query_mesai = "SELECT AcikMi, Baslangic, Bitis FROM CALISMA_SAATLERI WHERE DanismanID = ? AND Gun = ?"
        df_mesai = fetch_query(query_mesai, (danisman_id, secilen_gun_adi))

        # Eğer kaydı yoksa Pazartesi-Cuma 09:00-17:00 kabul et
        if df_mesai.empty:
            acik_mi = True if secilen_tarih.weekday() < 5 else False
            baslangic_saati = datetime.time(9, 0)
            bitis_saati = datetime.time(17, 0)
        else:
            acik_mi = bool(df_mesai.iloc[0]['AcikMi'])
            baslangic_saati = pd.to_datetime(str(df_mesai.iloc[0]['Baslangic'])).time()
            bitis_saati = pd.to_datetime(str(df_mesai.iloc[0]['Bitis'])).time()

        if not acik_mi:
            st.error(
                f"Danışmanınız {secilen_gun_adi} günleri randevu kabul etmemektedir. Lütfen başka bir gün seçiniz.")
            return

        # 4.SAAT SLOTLARINI ÜRETME
        # Başlangıç ve bitiş saatlerini datetime objesine çevirip slot süresi kadar artırarak liste oluşturuyoruz
        start_dt = datetime.datetime.combine(secilen_tarih, baslangic_saati)
        end_dt = datetime.datetime.combine(secilen_tarih, bitis_saati)
        delta = datetime.timedelta(minutes=slot_suresi)

        tum_saatler = []
        current = start_dt
        while current + delta <= end_dt:
            tum_saatler.append(current.strftime("%H:%M"))
            current += delta

        # KONTROL 3: Dolu Saatleri Çek (Çakışma Önleyici)
        query_dolu_saatler = """
            SELECT Saat
            FROM RANDEVULAR
            WHERE DanismanID = ? AND Tarih = ? AND Durum IN ('Bekliyor', 'Onaylandı')
        """
        df_dolu = fetch_query(query_dolu_saatler, (danisman_id, tarih_str))

        dolu_saatler = []
        if not df_dolu.empty:
            dolu_saatler = [str(saat)[:5] for saat in df_dolu['Saat']]

        # Müsait saatleri filtrele
        musait_saatler = [saat for saat in tum_saatler if saat not in dolu_saatler]

        with col2:
            if not musait_saatler:
                st.error("Seçtiğiniz tarihte danışmanınızın tüm randevu slotları doludur.")
                secilen_saat = None
            else:
                #Sistem Önerisi
                onerilen_saat = musait_saatler[0]
                st.success(f"💡 **Sistem Önerisi:** En yakın müsait saat **{onerilen_saat}**")

                secilen_saat = st.selectbox("Müsait Saatler", musait_saatler)

        konu = st.text_area("Randevu Konusu / Açıklama (Zorunlu)",
                            placeholder="Örn: Ders seçimi hakkında görüşmek istiyorum...", max_chars=200)

        # 5. VERİTABANINA KAYDETME
        if st.button("✅ Randevu Talebini Gönder", type="primary", use_container_width=True):
            if not secilen_saat:
                st.error("Lütfen geçerli bir saat seçiniz.")
            elif not konu.strip():
                st.warning("Lütfen görüşme konusunu kısaca belirtiniz.")
            else:
                # Durumu otomatik olarak 'Bekliyor' yapıyoruz
                insert_query = """
                    INSERT INTO RANDEVULAR (OgrenciID, DanismanID, Tarih, Saat, Konu, Durum)
                    VALUES (?, ?, ?, ?, ?, 'Bekliyor')
                """
                saat_sql = f"{secilen_saat}:00"

                success = execute_query(insert_query, (ogrenci_id, danisman_id, tarih_str, saat_sql, konu))

                if success:
                    st.success(f" Randevu talebiniz başarıyla oluşturuldu! (Tarih: {tarih_str} Saat: {secilen_saat})")

                else:
                    st.error("Randevu oluşturulurken veritabanı kaynaklı bir hata oluştu.")