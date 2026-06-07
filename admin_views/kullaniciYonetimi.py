import streamlit as st
import pandas as pd
import time
import re
from auth import admin_add_user, get_all_users, delete_user
from database import execute_query

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


def show_kullanici_yonetimi():
    st.header("👥 Kullanıcı Yönetimi")
    st.markdown(
        "Sisteme yeni öğrenciler ve danışmanlar ekleyebilir, mevcut kullanıcıların listesini görüntüleyebilirsiniz.")

    tab_ekle, tab_liste = st.tabs(["➕ Yeni Kullanıcı Ekle", "📋 Kullanıcı Listesi"])

    # YENİ KULLANICI EKLEME
    with tab_ekle:
        with st.container(border=True):
            st.subheader("Sisteme Kullanıcı Tanımla")
            st.caption(
                "Eklenen kullanıcılar otomatik olarak ilgili alt tablolara (Öğrenci/Danışman) tüm detaylarıyla kaydedilir.")

            secilen_rol = st.radio("Eklenecek Kullanıcı Türü Seçiniz", ["👨‍🎓 Öğrenci", "👨‍🏫 Danışman"], horizontal=True)
            st.write("")

            if secilen_rol == "👨‍🎓 Öğrenci":
                with st.form("admin_ogr_ekle_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        yeni_ogr_no = st.text_input("Okul Numarası (10 Hane Rakam)", max_chars=10)
                        yeni_ad = st.text_input("Ad Soyad")
                        yeni_tc = st.text_input("TC Kimlik Numarası (11 Hane Rakam)", max_chars=11)
                    with col2:
                        # BÖLÜM LİSTESİ
                        yeni_bolum = st.selectbox("Bölüm", BOLUM_LISTESI)
                        yeni_sinif = st.selectbox("Sınıf", ["1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"])
                        yeni_mail = st.text_input("E-Posta Adresi", placeholder="ornek@mail.com")

                    yeni_sifre = st.text_input("Şifre Belirleyin", type="password")
                    submit_btn = st.form_submit_button("💾 Öğrenciyi Sisteme Ekle", type="primary",
                                                       use_container_width=True)

                    if submit_btn:
                        if not yeni_ogr_no or not yeni_ad or not yeni_tc or not yeni_mail or not yeni_sifre:
                            st.warning("⚠️ Lütfen tüm alanları doldurun.")
                        elif not yeni_ogr_no.isdigit() or len(yeni_ogr_no) != 10:
                            st.error("🚨 KURAL İHLALİ: Okul Numarası tam 10 haneli rakam olmalıdır!")
                        elif not yeni_tc.isdigit() or len(yeni_tc) != 11:
                            st.error("🚨 KURAL İHLALİ: TC Kimlik Numarası tam 11 haneli rakam olmalıdır!")
                        else:
                            extra_data = {
                                'tc': yeni_tc,
                                'ad_soyad': yeni_ad,
                                'bolum': yeni_bolum,
                                'sinif': yeni_sinif,
                                'email': yeni_mail
                            }
                            result = admin_add_user(yeni_ogr_no, yeni_sifre, "OGRENCİ", extra_data=extra_data)
                            is_success, msg = result if isinstance(result, tuple) else (result,
                                                                                        "İşlem sonucu belirsiz.")

                            if is_success:
                                st.success(f"✅ {yeni_ad} başarıyla öğrenci olarak sisteme eklendi!")
                                try:
                                    log_aciklama = f"Yeni öğrenci eklendi: {yeni_ogr_no} - {yeni_ad}"
                                    execute_query(
                                        "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Kullanıcı Ekleme', ?, 'Başarılı')",
                                        (log_aciklama,))

                                    #  BİLDİRİM TETİKLEYİCİSİ
                                    execute_query(
                                        "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem: Kullanıcı Eklendi', ?, 0, GETDATE())",
                                        (f"Yeni öğrenci sisteme kaydedildi: {yeni_ad} ({yeni_ogr_no})",))
                                except:
                                    pass
                            else:
                                st.error(f"❌ {msg}")

            elif secilen_rol == "👨‍🏫 Danışman":
                with st.form("admin_danisman_ekle_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        yeni_tc = st.text_input("TC Kimlik Numarası (11 Hane Rakam)", max_chars=11)
                        yeni_ad = st.text_input("Ad Soyad")
                        yeni_per_no = st.text_input("Akademik Personel Numarası")
                    with col2:
                        yeni_unvan = st.selectbox("Ünvan",
                                                  ["Prof. Dr.", "Doç. Dr.", "Dr. Öğr. Üyesi", "Arş. Gör.", "Öğr. Gör."])
                        #BÖLÜM LİSTESİ
                        yeni_bolum = st.selectbox("Bölüm", BOLUM_LISTESI)
                        yeni_mail = st.text_input("E-Posta Adresi", placeholder="ornek@mail.com")

                    yeni_sifre = st.text_input("Şifre Belirleyin", type="password")
                    submit_btn = st.form_submit_button("💾 Danışmanı Sisteme Ekle", type="primary",
                                                       use_container_width=True)

                    if submit_btn:
                        if not yeni_tc or not yeni_ad or not yeni_per_no or not yeni_mail or not yeni_sifre:
                            st.warning("⚠️ Lütfen tüm alanları doldurun.")
                        elif not yeni_tc.isdigit() or len(yeni_tc) != 11:
                            st.error("🚨 KURAL İHLALİ: TC Kimlik Numarası tam 11 haneli rakam olmalıdır!")
                        else:
                            extra_data = {
                                'ad_soyad': yeni_ad,
                                'personel_no': yeni_per_no,
                                'unvan': yeni_unvan,
                                'bolum': yeni_bolum,
                                'email': yeni_mail
                            }
                            result = admin_add_user(yeni_tc, yeni_sifre, "DANISMAN", extra_data=extra_data)
                            is_success, msg = result if isinstance(result, tuple) else (result,
                                                                                        "İşlem sonucu belirsiz.")

                            if is_success:
                                st.success(f"✅ {yeni_unvan} {yeni_ad} başarıyla danışman olarak sisteme eklendi!")
                                try:
                                    log_aciklama = f"Yeni danışman eklendi: {yeni_tc} - {yeni_ad}"
                                    execute_query(
                                        "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Kullanıcı Ekleme', ?, 'Başarılı')",
                                        (log_aciklama,))

                                    #  BİLDİRİM TETİKLEYİCİSİ
                                    execute_query(
                                        "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem: Kullanıcı Eklendi', ?, 0, GETDATE())",
                                        (f"Yeni danışman sisteme kaydedildi: {yeni_unvan} {yeni_ad}",))
                                except:
                                    pass
                            else:
                                st.error(f"❌ {msg}")

    #  KULLANICI LİSTESİ VE SİLME
    with tab_liste:
        st.subheader("Sistemdeki Tüm Kullanıcılar")

        user_list = get_all_users()

        if user_list:
            df_users = pd.DataFrame(user_list)

            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Kayıtlı Kullanıcı", len(df_users))
            c2.metric("Öğrenci Sayısı", len(df_users[df_users["Rol"] == "OGRENCİ"]))
            c3.metric("Danışman Sayısı", len(df_users[df_users["Rol"] == "DANISMAN"]))

            st.write("")

            with st.container(border=True):
                arama = st.text_input("🔍 Listede Kullanıcı Ara", placeholder="Ad Soyad veya rol yazın...")

            if arama:
                df_users = df_users[
                    df_users.apply(lambda row: row.astype(str).str.contains(arama, case=False).any(), axis=1)]

            st.dataframe(df_users[["Ad Soyad", "Rol", "Durum"]], use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🗑️ Kullanıcı Silme İşlemi")
            st.warning("⚠️ DİKKAT: Bir kullanıcıyı sildiğinizde, ona ait tüm veriler sistemden kalıcı olarak silinir.")

            silinebilir_kullanicilar = df_users[df_users["Giriş Bilgisi"] != "admin"].apply(
                lambda x: f"{x['Ad Soyad']} ({x['Giriş Bilgisi']})", axis=1
            ).tolist()

            silinecek_kisi = st.selectbox("Silinecek Kullanıcıyı Seçiniz:",
                                          ["Lütfen bir kullanıcı seçin..."] + silinebilir_kullanicilar)

            if st.button("🚨 Seçili Kullanıcıyı Kalıcı Olarak Sil", type="primary"):
                if silinecek_kisi != "Lütfen bir kullanıcı seçin...":
                    username_to_delete = re.search(r'\((.*?)\)$', silinecek_kisi).group(1)

                    is_deleted, del_msg = delete_user(username_to_delete)

                    if is_deleted:
                        st.success(f"✅ Kullanıcı sistemden tamamen silindi!")
                        try:
                            log_aciklama = f"Kullanıcı silindi: {silinecek_kisi}"
                            execute_query(
                                "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Kullanıcı Silme', ?, 'Başarılı')",
                                (log_aciklama,))

                            #  BİLDİRİM TETİKLEYİCİSİ
                            execute_query(
                                "INSERT INTO BILDIRIMLER (Baslik, Mesaj, OkunduMu, Tarih) VALUES ('Sistem Uyarısı', ?, 0, GETDATE())",
                                (f"Kullanıcı sistemden tamamen silindi: {silinecek_kisi}",))
                        except:
                            pass

                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Silme işlemi başarısız: {del_msg}")
                else:
                    st.error("⚠️ Lütfen silmek için tablodan bir kullanıcı seçiniz.")

        else:
            st.info("Sistemde henüz kayıtlı kullanıcı bulunmuyor.")