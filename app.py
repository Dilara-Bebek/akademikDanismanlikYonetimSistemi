import streamlit as st
import time
import pandas as pd
import re
from auth import login_user, register_user, check_user_exists, verify_user_email, reset_password
from mail_service import generate_verification_code, send_verification_email
from database import fetch_query

# SİSTEM BAŞLIĞI
sistem_basligi = "Akademik Danışmanlık Yönetim Sistemi"
st.set_page_config(page_title=sistem_basligi, page_icon="🎓", layout="wide")

# Tüm formlarda kullanılacak ortak bölüm listesi
BOLUM_LISTESI = [
    "Bilgisayar Mühendisliği",
    "Elektrik-Elektronik Mühendisliği",
    "Makine Mühendisliği",
    "Mekatronik Mühendisliği",
    "Endüstri Mühendisliği",
    "İnşaat Mühendisliği",
    "Yazılım Mühendisliği"
]

# CSS , MODERN BUTON VE SEKME TASARIMI
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4) !important;
    }
    button[kind="secondary"], button[kind="tertiary"] {
        background-color: transparent !important;
        color: #64748b !important;
        border: 1px solid #e2e8f0 !important;
    }
    button[kind="secondary"]:hover, button[kind="tertiary"]:hover {
        color: #0f172a !important;
        background-color: #f1f5f9 !important;
    }
</style>
""", unsafe_allow_html=True)

# OTURUM VE GÜVENLİK DURUMLARI

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'giris_yapildi' not in st.session_state:
    st.session_state['giris_yapildi'] = False
if 'login_attempts' not in st.session_state:
    st.session_state['login_attempts'] = 0
if 'menu_selection' not in st.session_state:
    st.session_state['menu_selection'] = "📊 Anasayfa"

# E-Posta Kayıt Doğrulama State'leri
if 'verification_mode' not in st.session_state:
    st.session_state['verification_mode'] = False
if 'pending_user' not in st.session_state:
    st.session_state['pending_user'] = None
if 'verification_code' not in st.session_state:
    st.session_state['verification_code'] = None
if 'code_timestamp' not in st.session_state:
    st.session_state['code_timestamp'] = 0
if 'last_sent_timestamp' not in st.session_state:
    st.session_state['last_sent_timestamp'] = 0
if 'verification_attempts' not in st.session_state:
    st.session_state['verification_attempts'] = 0

# Şifremi Unuttum State'leri
if 'fp_mode' not in st.session_state:
    st.session_state['fp_mode'] = False
if 'fp_step' not in st.session_state:
    st.session_state['fp_step'] = 1
if 'fp_username' not in st.session_state:
    st.session_state['fp_username'] = ""
if 'fp_email' not in st.session_state:
    st.session_state['fp_email'] = ""
if 'fp_code' not in st.session_state:
    st.session_state['fp_code'] = ""


# GÜVENLİK FONKSİYONLARI
def sifre_guc_kontrol(sifre):
    if len(sifre) < 8:
        return False, "Şifreniz en az 8 karakter olmalıdır."
    if not re.search(r"[A-Z]", sifre):
        return False, "Şifre en az bir büyük harf içermelidir."
    if not re.search(r"[a-z]", sifre):
        return False, "Şifre en az bir küçük harf içermelidir."
    if not re.search(r"[0-9]", sifre):
        return False, "Şifre en az bir rakam (0-9) içermelidir."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", sifre):
        return False, "Şifre en az bir özel karakter (örn: !@#$) içermelidir."
    return True, ""


def tc_kimlik_dogrula(tc):
    if not tc.isdigit() or len(tc) != 11:
        return False
    if tc[0] == '0':
        return False

    digits = [int(d) for d in tc]

    sum_odd = sum(digits[0:9:2])
    sum_even = sum(digits[1:8:2])

    digit10 = ((sum_odd * 7) - sum_even) % 10
    if digits[9] != digit10:
        return False

    sum_all = sum(digits[0:10])
    digit11 = sum_all % 10
    if digits[10] != digit11:
        return False

    return True


def reset_verification_state():
    st.session_state['verification_mode'] = False
    st.session_state['pending_user'] = None
    st.session_state['verification_code'] = None
    st.session_state['verification_attempts'] = 0


is_admin_page = st.query_params.get("admin") == "true"

if not st.session_state['logged_in']:

    # GİZLİ ADMİN GİRİŞİ
    if is_admin_page:
        col_space1, col_admin, col_space2 = st.columns([1, 2, 1])
        with col_admin:
            st.title("⚙️ Sistem Yöneticisi Girişi")
            st.warning("Bu alan sadece yetkili sistem yöneticileri içindir. IP adresiniz loglanmaktadır.")
            with st.container(border=True):
                admin_user = st.text_input("Yönetici Kullanıcı Adı")
                admin_pass = st.text_input("Yönetici Şifresi", type="password")

                if st.button("Yönetici Olarak Giriş Yap", type="primary", use_container_width=True):
                    if st.session_state['login_attempts'] >= 3:
                        st.error("🚨 Çok fazla hatalı deneme nedeniyle işleminiz engellendi.")
                    elif not admin_user or not admin_pass:
                        st.warning("⚠️ Lütfen tüm alanları doldurun.")
                    else:
                        user = login_user(admin_user, admin_pass, expected_role="YONETİCİ")
                        if user:
                            st.session_state['logged_in'] = True
                            st.session_state['user_role'] = user.Rol
                            st.session_state['username'] = admin_user
                            st.session_state['kullanici'] = admin_user
                            st.session_state['menu_selection'] = "📊 Anasayfa"
                            st.session_state['login_attempts'] = 0
                            st.rerun()
                        else:
                            st.session_state['login_attempts'] += 1
                            st.error("❌ Hatalı yönetici bilgisi!")


    else:
        st.write("")

        col_hero, col_form, col_duyuru = st.columns([1.4, 1.5, 0.9])

        with col_hero:
            hero_html = (
                "<div style='padding-top: 10px; padding-right: 20px;'>"
                "<span style='background-color: #eff6ff; color: #2563eb; padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; border: 1px solid #bfdbfe; display: inline-flex; align-items: center; gap: 8px;'>"
                "🛡️ Güvenli Akademik Portal"
                "</span>"
                "<h1 style='font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin-top: 25px; margin-bottom: 20px; color: #0f172a; letter-spacing: -1px;'>"
                "Akademik<br>"
                "<span style='color: #2563eb;'>Başarınızı</span><br>"
                "Yönetin"
                "</h1>"
                "<p style='color: #475569; font-size: 1.1rem; line-height: 1.6; margin-bottom: 30px; max-width: 90%;'>"
                "Danışmanlarınızla iletişim kurun, ders planlamanızı yapın ve akademik süreçlerinizi yapay zeka destekli altyapımızla kolayca takip edin."
                "</p>"
                "<div style='display: flex; gap: 15px;'>"
                "<div style='background-color: white; padding: 20px; border-radius: 16px; border: 1px solid #e2e8f0; flex: 1; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>"
                "<div style='font-size: 1.8rem;'>👥</div>"
                "<div style='font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-top: 8px;'>4.800+</div>"
                "<div style='font-size: 0.85rem; color: #64748b; font-weight: 600; margin-top: 4px;'>Aktif Öğrenci</div>"
                "</div>"
                "<div style='background-color: white; padding: 20px; border-radius: 16px; border: 1px solid #e2e8f0; flex: 1; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>"
                "<div style='font-size: 1.8rem;'>👨‍🏫</div>"
                "<div style='font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-top: 8px;'>120+</div>"
                "<div style='font-size: 0.85rem; color: #64748b; font-weight: 600; margin-top: 4px;'>Danışman</div>"
                "</div>"
                "<div style='background-color: white; padding: 20px; border-radius: 16px; border: 1px solid #e2e8f0; flex: 1; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>"
                "<div style='font-size: 1.8rem;'>✨</div>"
                "<div style='font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-top: 8px;'>%94</div>"
                "<div style='font-size: 0.85rem; color: #64748b; font-weight: 600; margin-top: 4px;'>Memnuniyet Oranı</div>"
                "</div>"
                "</div>"
                "</div>"
            )
            st.markdown(hero_html, unsafe_allow_html=True)

        #ORTA TARAF: MERKEZİ GİRİŞ FORMU
        with col_form:
            st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("<div style='padding: 5px;'></div>", unsafe_allow_html=True)

                # ŞİFRE SIFIRLAMA AKIŞI
                if st.session_state['fp_mode']:
                    st.markdown("### 🔐 Şifre Sıfırlama")

                    if st.session_state['fp_step'] == 1:
                        st.caption("Sisteme kayıtlı kullanıcı bilginizi ve e-posta adresinizi girin.")
                        st.write("")
                        fp_user_input = st.text_input("OKUL NUMARASI VEYA TC KİMLİK NO", key="fp_user")
                        fp_email_input = st.text_input("KAYITLI E-POSTA ADRESİ", key="fp_mail")

                        st.write("")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Kod Gönder", type="primary", use_container_width=True):
                                if not fp_user_input or not fp_email_input:
                                    st.warning("Lütfen tüm alanları doldurun.")
                                else:
                                    # 1. SQL'den doğrulama yap
                                    is_valid, msg = verify_user_email(fp_user_input, fp_email_input)
                                    if is_valid:
                                        # 2. OTP kodu üret ve mail at
                                        kod = generate_verification_code()
                                        is_sent, mail_msg = send_verification_email(fp_email_input, kod)
                                        if is_sent:
                                            st.session_state['fp_username'] = fp_user_input
                                            st.session_state['fp_email'] = fp_email_input
                                            st.session_state['fp_code'] = kod
                                            st.session_state['fp_step'] = 2
                                            st.rerun()
                                        else:
                                            st.error(f"E-Posta gönderilemedi: {mail_msg}")
                                    else:
                                        st.error(msg)
                        with c2:
                            if st.button("İptal Et", type="secondary", use_container_width=True):
                                st.session_state['fp_mode'] = False
                                st.session_state['fp_step'] = 1
                                st.rerun()

                    elif st.session_state['fp_step'] == 2:
                        st.caption(f"**{st.session_state['fp_email']}** adresine gönderilen 6 haneli kodu giriniz.")
                        st.write("")
                        girilen_kod = st.text_input("Doğrulama Kodu", max_chars=6)

                        st.write("")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Kodu Doğrula", type="primary", use_container_width=True):
                                if girilen_kod == st.session_state['fp_code']:
                                    st.session_state['fp_step'] = 3
                                    st.rerun()
                                else:
                                    st.error("Hatalı doğrulama kodu. Lütfen e-postanızı kontrol edin.")
                        with c2:
                            if st.button("İptal Et", type="secondary", use_container_width=True):
                                st.session_state['fp_mode'] = False
                                st.session_state['fp_step'] = 1
                                st.rerun()

                    elif st.session_state['fp_step'] == 3:
                        st.caption("Doğrulama başarılı! Lütfen güvenli yeni şifrenizi belirleyin.")
                        st.write("")
                        yeni_sifre = st.text_input("YENİ ŞİFRE", type="password")
                        yeni_sifre_tekrar = st.text_input("YENİ ŞİFRE (TEKRAR)", type="password")

                        st.write("")
                        if st.button("Şifreyi Güncelle", type="primary", use_container_width=True):
                            if not yeni_sifre or not yeni_sifre_tekrar:
                                st.warning("Lütfen şifre alanlarını doldurun.")
                            elif yeni_sifre != yeni_sifre_tekrar:
                                st.error("Şifreler eşleşmiyor.")
                            else:
                                # 3. SQL'de şifreyi güncelle ,auth.py reset_password fonksiyonu
                                success, msg = reset_password(st.session_state['fp_username'], yeni_sifre)
                                if success:
                                    st.success(
                                        "✅ Şifreniz başarıyla güncellendi! Giriş ekranına yönlendiriliyorsunuz...")
                                    time.sleep(2.5)
                                    st.session_state['fp_mode'] = False
                                    st.session_state['fp_step'] = 1
                                    st.rerun()
                                else:
                                    st.error(msg)

                #  NORMAL GİRİŞ VE KAYIT SEKMELERİ

                else:
                    tab_ogr, tab_dan, tab_kayit = st.tabs(["🎓 Öğrenci Girişi", "👨‍🏫 Danışman Girişi", "📝 Kayıt Ol"])

                    # ÖĞRENCİ GİRİŞİ SEKMESİ
                    with tab_ogr:
                        st.markdown("### Öğrenci Bilgi Sistemi")
                        st.caption("Okul numaranız ve şifrenizle giriş yapın.")
                        st.write("")

                        ogr_no = st.text_input("OKUL NUMARASI", placeholder="Örn: 1111111111", max_chars=10,
                                               key="ogr_no")
                        ogr_pass = st.text_input("ÖĞRENCİ ŞİFRESİ", type="password", placeholder="••••••••",
                                                 key="ogr_pass")

                        st.write("")
                        ogr_btn = st.button("Giriş Yap ➔", type="primary", use_container_width=True,
                                            key="btn_ogr_login")

                        st.write("")
                        col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                        with col_b2:
                            # Şifremi Unuttum butonu Şifre Sıfırlama akışını tetikliyor
                            if st.button("Şifremi Unuttum", type="tertiary", use_container_width=True,
                                         key="btn_ogr_forgot"):
                                st.session_state['fp_mode'] = True
                                st.session_state['fp_step'] = 1
                                st.rerun()

                        if ogr_btn:
                            if st.session_state['login_attempts'] >= 3:
                                st.error("🚨 Çok fazla hatalı giriş yaptınız.")
                            elif len(ogr_no) != 10 or not ogr_no.isdigit():
                                st.error("❌ Okul numarası tam 10 haneli rakamlardan oluşmalıdır.")
                            elif not ogr_pass:
                                st.warning("⚠️ Şifre alanı boş bırakılamaz.")
                            else:
                                user = login_user(ogr_no, ogr_pass, expected_role="OGRENCİ")
                                if user:
                                    st.session_state['logged_in'] = True
                                    st.session_state['giris_yapildi'] = True
                                    st.session_state['user_role'] = user.Rol
                                    st.session_state['username'] = ogr_no
                                    st.session_state['kullanici'] = ogr_no
                                    st.session_state['menu_selection'] = "📊 Anasayfa"
                                    st.session_state['login_attempts'] = 0
                                    st.rerun()
                                else:
                                    st.session_state['login_attempts'] += 1
                                    st.error("❌ Hatalı okul numarası veya şifre!")

                    # DANIŞMAN GİRİŞİ SEKMESİ
                    with tab_dan:
                        st.markdown("### Danışman Girişi")
                        st.caption("Danışman yetkilerinizle sisteme erişin.")
                        st.write("")

                        dan_tc = st.text_input("TC KİMLİK NUMARASI", placeholder="Örn: 11111111111", max_chars=11,
                                               key="dan_tc")
                        dan_pass = st.text_input("DANIŞMAN ŞİFRESİ", type="password", placeholder="••••••••",
                                                 key="dan_pass")

                        st.write("")
                        dan_btn = st.button("Giriş Yap ➔", type="primary", use_container_width=True,
                                            key="btn_dan_login")

                        st.write("")
                        col_d1, col_d2, col_d3 = st.columns([1, 2, 1])
                        with col_d2:
                            # Şifremi Unuttum butonu Şifre Sıfırlama akışını tetikliyor
                            if st.button("Şifremi Unuttum", type="tertiary", use_container_width=True,
                                         key="btn_dan_forgot"):
                                st.session_state['fp_mode'] = True
                                st.session_state['fp_step'] = 1
                                st.rerun()

                        if dan_btn:
                            if st.session_state['login_attempts'] >= 3:
                                st.error("🚨 İşleminiz engellendi.")
                            elif not tc_kimlik_dogrula(dan_tc):
                                st.error("❌ Geçersiz TC Kimlik Numarası!")
                            elif not dan_pass:
                                st.warning("⚠️ Şifre alanı boş bırakılamaz.")
                            else:
                                user = login_user(dan_tc, dan_pass, expected_role="DANISMAN")
                                if user:
                                    st.session_state['logged_in'] = True
                                    st.session_state['giris_yapildi'] = True
                                    st.session_state['user_role'] = user.Rol
                                    st.session_state['username'] = dan_tc
                                    st.session_state['kullanici'] = dan_tc
                                    st.session_state['menu_selection'] = "📊 Anasayfa"
                                    st.session_state['login_attempts'] = 0
                                    st.rerun()
                                else:
                                    st.session_state['login_attempts'] += 1
                                    st.error("❌ Hatalı TC Kimlik Numarası veya şifre!")

                    #KAYIT OL SEKMESİ
                    with tab_kayit:
                        if st.session_state['verification_mode']:
                            st.markdown("### 🔐 E-Posta Doğrulama")
                            hedef_mail = st.session_state['pending_user']['email']
                            st.info(f"**{hedef_mail}** adresine gönderilen 6 haneli kodu giriniz.")
                            girilen_kod = st.text_input("Doğrulama Kodu", max_chars=6)

                            v_col1, v_col2 = st.columns(2)
                            with v_col1:
                                dogrula_btn = st.button("Doğrula", type="primary", use_container_width=True)
                            with v_col2:
                                iptal_btn = st.button("İptal Et", type="secondary", use_container_width=True)

                            if dogrula_btn:
                                if girilen_kod == st.session_state['verification_code']:
                                    p_user = st.session_state['pending_user']
                                    result = register_user(p_user['username'], p_user['password'], p_user['role'],
                                                           extra_data=p_user)
                                    is_success, msg = result if isinstance(result, tuple) else (result, "Belirsiz")
                                    if is_success:
                                        st.success("✅ Kayıt Başarılı!")
                                        reset_verification_state()
                                    else:
                                        st.error(f"❌ Hata: {msg}")
                                        reset_verification_state()
                                else:
                                    st.error("❌ Hatalı kod.")

                            if iptal_btn:
                                reset_verification_state()
                                st.rerun()
                        else:
                            st.markdown("### Yeni Hesap Oluştur")
                            kayit_turu = st.radio("Hesap Türü:", ["👨‍🎓 Öğrenci", "👨‍🏫 Danışman"], horizontal=True)

                            if kayit_turu == "👨‍🎓 Öğrenci":
                                with st.form("ogrenci_kayit_form"):
                                    reg_ogr_no = st.text_input("Okul Numarası (10 Hane)", max_chars=10)
                                    reg_ad = st.text_input("Ad Soyad")
                                    reg_tc = st.text_input("TC Kimlik No", max_chars=11)

                                    reg_bolum = st.selectbox("Bölüm", BOLUM_LISTESI)
                                    reg_sinif = st.selectbox("Sınıf", ["1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
                                    reg_mail = st.text_input("E-Posta Adresi")
                                    reg_pass = st.text_input("Şifre Belirleyin", type="password")
                                    reg_pass_confirm = st.text_input("Şifre Tekrar", type="password")
                                    captcha = st.checkbox("🤖 Robot değilim")
                                    reg_submit = st.form_submit_button("Kayıt Ol", type="primary",
                                                                       use_container_width=True)

                                    if reg_submit:
                                        is_pass_valid, pass_msg = sifre_guc_kontrol(reg_pass)

                                        if not captcha:
                                            st.error("Doğrulama gerekli.")
                                        elif not tc_kimlik_dogrula(reg_tc):
                                            st.error("❌ Hata: Geçersiz TC Kimlik Numarası girdiniz!")
                                        elif not is_pass_valid:
                                            st.error(f"Güvenlik Uyarısı: {pass_msg}")
                                        elif reg_pass != reg_pass_confirm:
                                            st.error("Şifreler uyuşmuyor.")
                                        elif check_user_exists(reg_ogr_no):
                                            st.error("Kayıtlı numara.")
                                        else:
                                            kod = generate_verification_code()
                                            is_sent, mail_msg = send_verification_email(reg_mail, kod)
                                            if is_sent:
                                                st.session_state['pending_user'] = {
                                                    'username': reg_ogr_no, 'password': reg_pass, 'role': 'OGRENCİ',
                                                    'email': reg_mail, 'ad_soyad': reg_ad, 'tc': reg_tc,
                                                    'bolum': reg_bolum,
                                                    'sinif': reg_sinif
                                                }
                                                st.session_state['verification_code'] = kod
                                                st.session_state['verification_mode'] = True
                                                st.rerun()
                                            else:
                                                st.error(mail_msg)

                            elif kayit_turu == "👨‍🏫 Danışman":
                                with st.form("dan_kayit_form"):
                                    basvuru_tc = st.text_input("TC Kimlik", max_chars=11)
                                    basvuru_ad = st.text_input("Ad Soyad")
                                    basvuru_per_no = st.text_input("Personel No")
                                    basvuru_unvan = st.selectbox("Ünvan",
                                                                 ["Prof. Dr.", "Doç. Dr.", "Dr. Öğr. Üyesi",
                                                                  "Arş. Gör."])

                                    basvuru_bolum = st.selectbox("Bölüm", BOLUM_LISTESI)
                                    basvuru_mail = st.text_input("E-Posta")
                                    basvuru_pass = st.text_input("Şifre", type="password")
                                    basvuru_pass_confirm = st.text_input("Şifre Tekrar", type="password")
                                    captcha_dan = st.checkbox("🤖 Robot değilim")
                                    dan_submit = st.form_submit_button("Başvur", type="primary",
                                                                       use_container_width=True)

                                    if dan_submit:
                                        is_pass_valid, pass_msg = sifre_guc_kontrol(basvuru_pass)

                                        if not captcha_dan:
                                            st.error("Doğrulama gerekli.")
                                        elif not tc_kimlik_dogrula(basvuru_tc):
                                            st.error("❌ Hata: Geçersiz TC Kimlik Numarası girdiniz!")
                                        elif not is_pass_valid:
                                            st.error(f"Güvenlik Uyarısı: {pass_msg}")
                                        elif basvuru_pass != basvuru_pass_confirm:
                                            st.error("Şifreler uyuşmuyor.")
                                        elif check_user_exists(basvuru_tc):
                                            st.error("Kayıtlı TC.")
                                        else:
                                            kod = generate_verification_code()
                                            is_sent, mail_msg = send_verification_email(basvuru_mail, kod)
                                            if is_sent:
                                                st.session_state['pending_user'] = {
                                                    'username': basvuru_tc, 'password': basvuru_pass,
                                                    'role': 'DANISMAN',
                                                    'email': basvuru_mail, 'ad_soyad': basvuru_ad,
                                                    'personel_no': basvuru_per_no,
                                                    'unvan': basvuru_unvan, 'bolum': basvuru_bolum
                                                }
                                                st.session_state['verification_code'] = kod
                                                st.session_state['verification_mode'] = True
                                                st.rerun()
                                            else:
                                                st.error(mail_msg)

        # DUYURULAR
        with col_duyuru:
            st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<h3 style='margin-top: 0px; margin-bottom: 20px; color: #0f172a; font-weight: 600; display: flex; align-items: center; gap: 10px;'>🔔 Akademik Duyurular</h3>",
                unsafe_allow_html=True)

            try:
                query_duyuru = "SELECT Baslik, Metin, Tur, FORMAT(Tarih, 'dd.MM.yyyy') as Tarih FROM GENEL_DUYURULAR ORDER BY DuyuruID DESC"
                df_duyurular = fetch_query(query_duyuru)

                if not df_duyurular.empty:
                    for index, row in df_duyurular.iterrows():
                        tur = row['Tur']
                        baslik = row['Baslik']
                        metin = row['Metin'].replace('\n', '<br>')
                        tarih = row['Tarih']

                        border_color = "#3b82f6"  # Varsayılan Mavi çizgi
                        if "Sarı" in tur:
                            border_color = "#f59e0b"
                        elif "Yeşil" in tur:
                            border_color = "#10b981"
                        elif "Kırmızı" in tur:
                            border_color = "#ef4444"

                        card_html = (
                            f"<div style='background-color: white; padding: 18px; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid {border_color}; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);'>"
                            f"<div style='font-size: 0.8rem; color: #64748b; margin-bottom: 6px; font-weight: 500;'>📅 {tarih}</div>"
                            f"<div style='font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 8px;'>{baslik}</div>"
                            f"<div style='font-size: 0.9rem; color: #475569; line-height: 1.5;'>{metin}</div>"
                            f"</div>"
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                else:
                    st.info("📌 Şu an için aktif bir sistem duyurusu bulunmamaktadır.")
            except Exception:
                ornek_html = (
                    "<div style='background-color: white; padding: 18px; margin-bottom: 16px; border-radius: 8px; border-left: 6px solid #3b82f6; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);'>"
                    "<div style='font-size: 0.8rem; color: #64748b; margin-bottom: 6px; font-weight: 500;'>📅 04.06.2026</div>"
                    "<div style='font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 8px;'>2026 Final Sınavları Takvimi</div>"
                    "<div style='font-size: 0.9rem; color: #475569; line-height: 1.5;'>Final sınavları 10-24 Haziran tarihleri arasında gerçekleşecektir. Başarılar dileriz.</div>"
                    "</div>"
                )
                st.markdown(ornek_html, unsafe_allow_html=True)

        # 3.ALT BİLGİ YERLEŞİMİ
        st.write("")
        st.write("")
        st.divider()
        st.markdown(
            """
            <div style="text-align: center; color: gray; font-size: 0.85em; padding-bottom: 20px;">
                © 2026 Akademik Danışmanlık Yönetim Sistemi. Tüm hakları saklıdır.<br>
                ISUBÜ Bilgisayar Mühendisliği - (v1.0.0)
            </div>
            """, unsafe_allow_html=True
        )

else:
    # ROL BAZLI YÖNLENDİRME

    # 1. YÖNETİCİ PANELİ
    if st.session_state['user_role'] == 'YONETİCİ':
        st.sidebar.title("⚙️ Yönetici Paneli")
        st.sidebar.write(f"Hoş geldiniz, **{st.session_state['kullanici']}**")
        admin_menu_options = ["📊 Anasayfa", "👥 Kullanıcı Yönetimi", "🔗 Danışman Atama", "📅 Randevu Yönetimi",
                              "📊 Raporlar", "🔔 Bildirimler", "📝 Log / Geçmiş"]
        current_index = admin_menu_options.index(st.session_state['menu_selection']) if st.session_state[
                                                                                            'menu_selection'] in admin_menu_options else 0
        menu = st.sidebar.radio("İşlemler Menüsü", admin_menu_options, index=current_index)
        st.session_state['menu_selection'] = menu

        if menu == "📊 Anasayfa":
            from admin_views.dashboard import show_dashboard

            show_dashboard()
        elif menu == "👥 Kullanıcı Yönetimi":
            from admin_views.kullaniciYonetimi import show_kullanici_yonetimi

            show_kullanici_yonetimi()
        elif menu == "🔗 Danışman Atama":
            from admin_views.danismanAtama import show_danisman_atama

            show_danisman_atama()
        elif menu == "📅 Randevu Yönetimi":
            from admin_views.randevuYonetimi import show_randevu_yonetimi

            show_randevu_yonetimi()
        elif menu == "📊 Raporlar":
            from admin_views.raporlar import show_raporlar

            show_raporlar()
        elif menu == "🔔 Bildirimler":
            from admin_views.bildirimler import show_bildirimler

            show_bildirimler()
        elif menu == "📝 Log / Geçmiş":
            from admin_views.logGecmis import show_log_gecmis

            show_log_gecmis()

    # 2. DANIŞMAN PANELİ
    elif st.session_state['user_role'] == 'DANISMAN':
        st.sidebar.title("🎓 Danışman Paneli")

        kullanici_adi = st.session_state.get('username', '')
        gosterilecek_isim = "Sayın Hocam"
        try:
            query_danisman = """
                SELECT D.Unvan, D.AdSoyad 
                FROM DANISMANLAR D
                INNER JOIN KULLANICILAR K ON D.KullaniciID = K.KullaniciID
                WHERE K.KullaniciAdi = ?
            """
            df_dan = fetch_query(query_danisman, (kullanici_adi,))
            if not df_dan.empty and pd.notna(df_dan.iloc[0]['AdSoyad']):
                unvan = df_dan.iloc[0]['Unvan'] if pd.notna(df_dan.iloc[0]['Unvan']) else ""
                ad_soyad = df_dan.iloc[0]['AdSoyad']
                gosterilecek_isim = f"{unvan} {ad_soyad}".strip()
        except Exception:
            pass

        st.sidebar.write(f"Hoş geldiniz, **{gosterilecek_isim}**")

        advisor_options = ["📊 Anasayfa", "📅 Randevularım", "👨‍🎓 Öğrencilerim", "📝 Görüşme Notları",
                           "⏰ Müsaitlik Ayarları", "🔔 Bildirimler", "⚙️ Profil & Ayarlar", "📈 Raporlar", "💬 Mesajlaşma"]
        current_index = advisor_options.index(st.session_state['menu_selection']) if st.session_state[
                                                                                         'menu_selection'] in advisor_options else 0
        menu = st.sidebar.radio("İşlemler Menüsü", advisor_options, index=current_index)
        st.session_state['menu_selection'] = menu

        if menu == "📊 Anasayfa":
            from advisor_views.dashboard import show_advisor_dashboard

            show_advisor_dashboard()
        elif menu == "📅 Randevularım":
            from advisor_views.randevularim import show_randevularim

            show_randevularim()
        elif menu == "👨‍🎓 Öğrencilerim":
            from advisor_views.ogrencilerim import show_ogrencilerim

            show_ogrencilerim()
        elif menu == "📝 Görüşme Notları":
            from advisor_views.gorusmeNotlari import show_gorusme_notlari

            show_gorusme_notlari()
        elif menu == "⏰ Müsaitlik Ayarları":
            from advisor_views.musaitlikAyarlari import show_musaitlik_ayarlari

            show_musaitlik_ayarlari()
        elif menu == "🔔 Bildirimler":
            from advisor_views.bildirimler import show_advisor_bildirimler

            show_advisor_bildirimler()
        elif menu == "⚙️ Profil & Ayarlar":
            from advisor_views.profilAyarlar import show_profil_ayarlar

            show_profil_ayarlar()
        elif menu == "📈 Raporlar":
            from advisor_views.raporlar import show_advisor_raporlar

            show_advisor_raporlar()
        elif menu == "💬 Mesajlaşma":
            from advisor_views.mesajlasma import show_advisor_mesajlasma

            show_advisor_mesajlasma()

    # 3. ÖĞRENCİ PANELİ
    elif st.session_state['user_role'] in ['OGRENCİ', 'ÖĞRENCİ']:
        st.sidebar.title("🎓 Öğrenci Paneli")

        ogrenci_no = st.session_state.get('username', '')
        gosterilecek_isim = ogrenci_no
        try:
            df_isim = fetch_query("SELECT AdSoyad FROM OGRENCILER WHERE OgrenciNo = ?", (ogrenci_no,))
            if not df_isim.empty and pd.notna(df_isim.iloc[0]['AdSoyad']):
                ad_soyad = str(df_isim.iloc[0]['AdSoyad']).strip()
                if ad_soyad != "":
                    gosterilecek_isim = ad_soyad
        except Exception:
            pass

        st.sidebar.write(f"Hoş geldin, **{gosterilecek_isim}**")

        student_options = ["📊 Anasayfa", "➕ Randevu Oluştur", "📅 Randevularım", "⏳ Geçmiş Görüşmeler",
                           "👩‍🏫 Danışmanım", "🔔 Bildirimler", "⚙️ Profil & Ayarlar", "💬 Mesajlaşma", "📈 Akademik Takip"]
        current_index = student_options.index(st.session_state['menu_selection']) if st.session_state[
                                                                                         'menu_selection'] in student_options else 0
        menu = st.sidebar.radio("İşlemler Menüsü", student_options, index=current_index)
        st.session_state['menu_selection'] = menu

        if menu == "📊 Anasayfa":
            from student_views.dashboard import show_student_dashboard

            show_student_dashboard()
        elif menu == "➕ Randevu Oluştur":
            from student_views.randevu_olustur import show_randevu_olustur

            show_randevu_olustur()
        elif menu == "📅 Randevularım":
            from student_views.randevularim import show_randevularim

            show_randevularim()
        elif menu == "⏳ Geçmiş Görüşmeler":
            from student_views.gorusme_gecmisi import show_gorusme_gecmisi

            show_gorusme_gecmisi()
        elif menu == "👩‍🏫 Danışmanım":
            from student_views.danismanim import show_danismanim

            show_danismanim()
        elif menu == "🔔 Bildirimler":
            from student_views.bildirimler import show_bildirimler

            show_bildirimler()
        elif menu == "⚙️ Profil & Ayarlar":
            from student_views.profil_ayarlar import show_profil_ayarlar

            show_profil_ayarlar()
        elif menu == "💬 Mesajlaşma":
            from student_views.mesajlasma import show_student_mesajlasma

            show_student_mesajlasma()
        elif menu == "📈 Akademik Takip":
            from student_views.akademik_takip import show_akademik_takip

            show_akademik_takip()

    st.sidebar.divider()
    if st.sidebar.button("🚪 Güvenli Çıkış Yap", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['giris_yapildi'] = False
        st.session_state['login_attempts'] = 0
        st.session_state['menu_selection'] = "📊 Anasayfa"
        st.query_params.clear()
        st.rerun()