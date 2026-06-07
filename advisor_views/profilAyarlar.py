import streamlit as st
import pandas as pd
import os  # Dosya (Fotoğraf) işlemleri için eklendi
from database import fetch_query, execute_query
from auth import verify_password, hash_password

# FOTOĞRAF KAYIT KLASÖRÜNÜ HAZIRLAMA
# Eğer proje klasöründe 'profil_fotograflari' adında bir klasör yoksa otomatik oluşturur
PROFILE_DIR = "profil_fotograflari"
if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)


def show_profil_ayarlar():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı.")
        return

    kullanici_adi = st.session_state['username']  # Danışmanlar için bu TC Kimlik Numarasıdır

    st.header("⚙️ Profil ve Ayarlar")
    st.markdown("Kişisel bilgilerinizi, profil fotoğrafınızı ve hesap güvenliğinizi buradan yönetebilirsiniz.")

    #1. VERİTABANINDAN VERİ ÇEKME
    query = """
        SELECT D.DanismanID, D.AdSoyad, D.Unvan, D.Bolum, D.Email, D.Telefon, D.Ofis, D.PersonelNo, K.SifreHash
        FROM DANISMANLAR D
        INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
        WHERE K.KullaniciAdi = ?
    """
    df = fetch_query(query, (kullanici_adi,))

    if df.empty:
        st.error("Profil bilgileri yüklenemedi. Veritabanı kaydınız eksik olabilir.")
        return

    user_data = df.iloc[0]
    danisman_id = int(user_data['DanismanID'])

    # Fotoğrafın kaydedileceği ,okunacağı dosya yolu
    foto_path = os.path.join(PROFILE_DIR, f"danisman_{danisman_id}.png")

    # NULL gelebilecek alanları kontrol altına alıyoruz
    mevcut_tel = user_data.get('Telefon', '') if pd.notna(user_data.get('Telefon')) else ''
    mevcut_ofis = user_data.get('Ofis', '') if pd.notna(user_data.get('Ofis')) else ''
    mevcut_email = user_data.get('Email', '') if pd.notna(user_data.get('Email')) else ''

    # Arayüz sekmeleri
    tab_profil, tab_ayarlar = st.tabs(["👤 Profil Bilgileri", "🔐 Hesap Güvenliği"])

    # 2. PROFİL BİLGİLERİ SEKMESİ
    with tab_profil:
        st.subheader("Kişisel Bilgiler")
        st.info(
            "💡 Güvenlik gereği **Ünvan, Ad Soyad, Bölüm** ve **Personel No** değiştirilemez. Hatalı olduğunu düşünüyorsanız sistem yöneticisine başvurun.")

        with st.container(border=True):
            col_img, col_info = st.columns([1, 3])

            with col_img:
                # FOTOĞRAF GÖSTERİMİ VE KALDIRMA
                if os.path.exists(foto_path):
                    st.image(foto_path, width=150)

                    # Fotoğraf Kaldırma Butonu
                    if st.button("🗑️ Fotoğrafı Kaldır", key="remove_photo", use_container_width=True):
                        try:
                            os.remove(foto_path)
                            st.rerun()  # Sayfayı yenile ki varsayılan avatar gelsin
                        except Exception as e:
                            st.error(f"Dosya silinirken hata oluştu: {e}")
                else:
                    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)

                # Fotoğraf Yükleme Aracı
                uploaded_file = st.file_uploader("Yeni Fotoğraf Seç", type=["png", "jpg", "jpeg"],
                                                 label_visibility="collapsed")
                st.caption("Max 2MB (PNG/JPG)")

            with col_info:
                with st.form("danisman_profil_form"):
                    c1, c2 = st.columns(2)

                    with c1:
                        # DEĞİŞTİRİLEMEZ ALANLAR
                        tam_isim = f"{user_data.get('Unvan', '')} {user_data.get('AdSoyad', '')}".strip()
                        st.text_input("Ünvan ve Ad Soyad", value=tam_isim, disabled=True)
                        st.text_input("Bölüm", value=user_data.get('Bolum', ''), disabled=True)
                        st.text_input("Personel Numarası", value=str(user_data.get('PersonelNo', '')), disabled=True)

                    with c2:
                        # GÜNCELLENEBİLİR ALANLAR
                        yeni_email = st.text_input("E-Posta Adresi", value=mevcut_email)
                        yeni_tel = st.text_input("Telefon Numarası (Başında 0 olmadan)", value=mevcut_tel, max_chars=10,
                                                 placeholder="5551234567")
                        yeni_ofis = st.text_input("Ofis Bilgisi", value=mevcut_ofis,
                                                  placeholder="Örn: E-Blok 2. Kat No: 205")

                    submit_profil = st.form_submit_button("💾 Profil Bilgilerini Kaydet", type="primary",
                                                          use_container_width=True)

                    if submit_profil:
                        # 1. Eğer yeni fotoğraf seçildiyse onu klasöre kaydet
                        if uploaded_file is not None:
                            with open(foto_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                        # 2. Telefon numarası kuralını kontrol et
                        if yeni_tel and (not yeni_tel.isdigit() or len(yeni_tel) != 10):
                            st.error(
                                "❌ Telefon numarası tam 10 haneli olmalı ve sadece rakamlardan oluşmalıdır! (Örn: 5551234567)")
                        else:
                            # 3. SQL Güncellemesi
                            update_q = """
                                UPDATE DANISMANLAR 
                                SET Email = ?, Telefon = ?, Ofis = ? 
                                WHERE DanismanID = ?
                            """
                            if execute_query(update_q, (yeni_email, yeni_tel, yeni_ofis, danisman_id)):
                                st.success("✅ Profil bilgileriniz başarıyla güncellendi!")
                                st.rerun()
                            else:
                                st.error("Güncelleme sırasında bir hata oluştu.")

    #3. HESAP GÜVENLİĞİ SEKMESİ
    with tab_ayarlar:
        with st.container(border=True):
            st.markdown("#### 🔑 Şifre Değiştirme")
            st.caption("Güvenliğiniz için şifrenizi belirli aralıklarla değiştirmenizi öneririz.")

            with st.form("danisman_sifre_form"):
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    eski_sifre = st.text_input("Mevcut Şifre", type="password")
                with p_col2:
                    yeni_sifre = st.text_input("Yeni Şifre", type="password")
                    yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar)", type="password")

                submit_sifre = st.form_submit_button("Şifreyi Güncelle", type="primary")

                if submit_sifre:
                    mevcut_hash = user_data.get('SifreHash', '')

                    if not verify_password(eski_sifre, mevcut_hash):
                        st.error("❌ Mevcut şifreniz hatalı!")
                    elif yeni_sifre != yeni_sifre_tekrar:
                        st.error("❌ Yeni şifreler eşleşmiyor!")
                    elif len(yeni_sifre) < 8:
                        st.error("❌ Yeni şifre güvenlik gereği en az 8 karakter olmalıdır.")
                    else:
                        update_s_q = "UPDATE KULLANICILAR SET SifreHash = ? WHERE KullaniciAdi = ?"
                        if execute_query(update_s_q, (hash_password(yeni_sifre), kullanici_adi)):
                            st.success("✅ Şifreniz başarıyla değiştirildi.")
                        else:
                            st.error("Şifre güncellenirken hata oluştu.")