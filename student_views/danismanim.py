import streamlit as st
import pandas as pd
import os  # Dosya kontrolü için eklendi
from database import fetch_query, execute_query
import datetime

# Fotoğrafların bulunduğu klasör yolu
PROFILE_DIR = "profil_fotograflari"


def show_danismanim():
    if 'username' not in st.session_state:
        st.error("Oturum bilgisi bulunamadı. Lütfen tekrar giriş yapın.")
        return

    ogrenci_no = st.session_state['username']

    st.title("👩‍🏫 Danışman Profil ve İletişim")
    st.markdown("---")

    # 1. ÖĞRENCİNİN DANIŞMAN ID'SİNİ ÇEKME
    query_student = "SELECT DanismanID FROM OGRENCILER WHERE OgrenciNo = ?"
    df_student = fetch_query(query_student, (ogrenci_no,))

    if df_student.empty or pd.isna(df_student.iloc[0]['DanismanID']):
        st.warning(
            "⚠️ Sisteme kayıtlı bir danışmanınız bulunmamaktadır. Lütfen bölüm sekreterliği ile iletişime geçin.")
        return

    danisman_id = int(df_student.iloc[0]['DanismanID'])

    # 2. DANIŞMAN BİLGİLERİNİ ÇEKME
    # * kullanarak tablodaki tüm sütunları çekiyoruz
    query_advisor = "SELECT * FROM DANISMANLAR WHERE DanismanID = ?"
    df_advisor = fetch_query(query_advisor, (danisman_id,))

    if df_advisor.empty:
        st.error("Danışman detaylarına ulaşılamıyor.")
        return

    # Veriyi bir sözlüğe çeviriyoruz ki olmayan sütunları .get() ile yakalayabilelim
    advisor_data = df_advisor.iloc[0].to_dict()

    unvan = advisor_data.get('Unvan', '')
    ad_soyad = advisor_data.get('AdSoyad', 'İsim Bilgisi Yok')
    tam_isim = f"{unvan} {ad_soyad}".strip()

    bolum = advisor_data.get('Bolum', 'Bilgisayar Mühendisliği')  # Varsayılan bölüm
    email = advisor_data.get('Email', 'E-posta bilgisi sisteme girilmemiş.')
    telefon = advisor_data.get('Telefon', 'Telefon numarası sisteme girilmemiş.')
    ofis = advisor_data.get('Ofis', 'Ofis bilgisi bulunmuyor.')


    # 3.PROFİL GÖRÜNÜMÜ
    with st.container(border=True):
        col_img, col_info = st.columns([1, 4])

        with col_img:
            #FOTOĞRAF KONTROLÜ
            foto_path = os.path.join(PROFILE_DIR, f"danisman_{danisman_id}.png")
            danisman_isim_seed = str(ad_soyad).replace(" ", "")

            if os.path.exists(foto_path):
                # Danışman kendi fotoğrafını yüklemişse onu göster
                st.image(foto_path, use_container_width=True)
            else:
                # Yüklememişse ismine özel avatar oluştur
                st.image(f"https://api.dicebear.com/7.x/avataaars/svg?seed={danisman_isim_seed}&backgroundColor=e2e8f0",
                         use_container_width=True)

        with col_info:
            st.subheader(f" {tam_isim}")
            st.write(f"🏢 **Bağlı Olduğu Bölüm:** {bolum}")
            st.write(f"✉️ **Kurumsal E-posta:** {email}")
            st.write(f"📞 **Dahili Telefon:** {telefon}")
            st.write(f"🚪 **Ofis / Oda No:** {ofis}")

    st.markdown("<br>", unsafe_allow_html=True)  # Araya biraz boşluk

    # 4. HIZLI MESAJ GÖNDERME MODÜLÜ
    st.subheader("💬 Hızlı Mesaj Gönder")
    st.write("Danışmanınıza sistem üzerinden doğrudan bir not veya soru iletebilirsiniz.")

    with st.form("hizli_mesaj_form", clear_on_submit=True):
        mesaj_konusu = st.text_input("Mesaj Konusu (Örn: Staj Onayı Hakkında)")
        mesaj_metni = st.text_area("Mesajınız", placeholder="Sayın hocam, iyi çalışmalar. Ekteki evraklarım için...",
                                   height=150)

        submit_btn = st.form_submit_button("📤 Mesajı İlet", type="primary")

        if submit_btn:
            if not mesaj_konusu.strip() or not mesaj_metni.strip():
                st.warning("Lütfen mesaj konusunu ve içeriğini boş bırakmayınız.")
            else:

                st.success(f"✅ Mesajınız **{tam_isim}** adlı danışmanınıza başarıyla iletildi!")
                st.info("💡 İpucu: Tüm mesaj geçmişinizi sol menüdeki 'Mesajlaşma' sekmesinden takip edebilirsiniz.")