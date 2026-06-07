import streamlit as st
import pandas as pd
from database import fetch_query, execute_query
from auth import verify_password, hash_password  # Şifre işlemleri için ana auth dosyamızı kullanıyoruz
def show_profil_ayarlar():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    ogrenci_no = st.session_state['username']

    st.title("👤 Profil ve Ayarlar")
    st.markdown("---")

    # 1. VERİLERİ ÇEKME
    query = "SELECT * FROM OGRENCILER WHERE OgrenciNo = ?"
    df = fetch_query(query, (ogrenci_no,))

    if df.empty:
        st.error("Profil bilgileri yüklenemedi.")
        return

    user_data = df.iloc[0]

    # Veritabanından gelen telefon NULL ise boş string yapalım ki arayüz hata vermesin
    mevcut_tel = user_data.get('Telefon', '')
    if pd.isna(mevcut_tel):
        mevcut_tel = ''

    # 2. ARAYÜZ TASARIMI
    tab1, tab2, tab3 = st.tabs(["📋 Kişisel Bilgiler", "🔐 Şifre Değiştir", "⚙️ Bildirim Tercihleri"])

    with tab1:
        st.subheader("Kişisel Bilgilerinizi Güncelleyin")
        st.info(
            "💡 Güvenlik gereği **Ad Soyad** ve **TC Kimlik Numaranız** değiştirilemez. Hatalı olduğunu düşünüyorsanız sistem yöneticisiyle görüşün.")

        with st.form("profil_form"):
            col1, col2 = st.columns(2)

            with col1:
                # disabled=True eklenerek veri girişi kapatıldı
                yeni_ad = st.text_input("Ad Soyad", value=user_data.get('AdSoyad', ''), disabled=True)
                yeni_tc = st.text_input("TC Kimlik Numarası", value=user_data.get('TC', ''), disabled=True)

            with col2:
                yeni_email = st.text_input("E-posta Adresi", value=user_data.get('Email', ''))
                #TELEFON KONTROLÜ: Max 10 karakter ve placeholder eklendi
                yeni_tel = st.text_input("Telefon Numarası (Başında 0 olmadan)", value=mevcut_tel, max_chars=10,
                                         placeholder="5551234567")

            submit_profil = st.form_submit_button("Bilgileri Güncelle", type="primary")

            if submit_profil:
                # 10 haneli rakam kontrolü (boş değilse)
                if yeni_tel and (not yeni_tel.isdigit() or len(yeni_tel) != 10):
                    st.error(
                        "❌ Telefon numarası tam 10 haneli olmalı ve sadece rakamlardan oluşmalıdır! (Örn: 5551234567)")
                else:
                    # SQL Sorgusu
                    update_q = """
                        UPDATE OGRENCILER 
                        SET Email = ?, Telefon = ? 
                        WHERE OgrenciNo = ?
                    """
                    if execute_query(update_q, (yeni_email, yeni_tel, ogrenci_no)):
                        st.success("✅ Bilgileriniz başarıyla güncellendi!")
                        st.rerun()
                    else:
                        st.error("Güncelleme sırasında bir hata oluştu.")

    with tab2:
        st.subheader("Güvenlik Ayarları")
        with st.form("sifre_form"):
            current_pass = st.text_input("Mevcut Şifre", type="password")
            new_pass = st.text_input("Yeni Şifre", type="password")
            confirm_pass = st.text_input("Yeni Şifre (Tekrar)", type="password")

            submit_sifre = st.form_submit_button("Şifreyi Güncelle", type="primary")

            if submit_sifre:
                # 1. Mevcut şifre kontrolü (Sistemdeki auth.py'deki bcrypt algoritmasına bağlandı)
                check_q = "SELECT SifreHash FROM KULLANICILAR WHERE KullaniciAdi = ?"
                df_check = fetch_query(check_q, (ogrenci_no,))

                if df_check.empty or not verify_password(current_pass, df_check.iloc[0]['SifreHash']):
                    st.error("❌ Mevcut şifreniz hatalı!")
                elif new_pass != confirm_pass:
                    st.error("❌ Yeni şifreler eşleşmiyor!")
                elif len(new_pass) < 8:
                    st.error("❌ Yeni şifre güvenlik gereği en az 8 karakter olmalıdır.")
                else:
                    # 2. Şifre Güncelleme (Yeni algoritma ile SifreHash sütununa)
                    update_s_q = "UPDATE KULLANICILAR SET SifreHash = ? WHERE KullaniciAdi = ?"
                    if execute_query(update_s_q, (hash_password(new_pass), ogrenci_no)):
                        st.success("✅ Şifreniz başarıyla değiştirildi.")
                    else:
                        st.error("Şifre güncellenirken hata oluştu.")

    with tab3:
        st.subheader("Bildirim Ayarları")

        # Veritabanında BildirimTercihi varsa onu alalım, yoksa 'Hepsi' varsayılan olsun
        mevcut_tercih = user_data.get('BildirimTercihi', 'Hepsi')
        if pd.isna(mevcut_tercih) or mevcut_tercih not in ["Hepsi", "Sadece Onay/İptal", "Sadece Yaklaşan Randevular",
                                                           "Hiçbiri"]:
            mevcut_tercih = "Hepsi"

        secenekler = ["Hepsi", "Sadece Onay/İptal", "Sadece Yaklaşan Randevular", "Hiçbiri"]
        index_val = secenekler.index(mevcut_tercih)

        tercih = st.radio(
            "Hangi durumlarda bildirim almak istersiniz?",
            secenekler,
            index=index_val
        )

        if st.button("Tercihleri Kaydet", type="primary"):
            try:
                # Veritabanında BildirimTercihi sütunu varsa oraya yazar
                update_pref = "UPDATE OGRENCILER SET BildirimTercihi = ? WHERE OgrenciNo = ?"
                if execute_query(update_pref, (tercih, ogrenci_no)):
                    st.success("✅ Bildirim tercihleriniz kaydedildi.")
                    st.rerun()
                else:
                    st.error("Güncelleme başarısız. SQL tablonuzda 'BildirimTercihi' sütunu eksik olabilir.")
            except Exception as e:
                st.error(f"Hata oluştu: {e}")