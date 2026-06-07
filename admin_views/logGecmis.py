import streamlit as st
import pandas as pd
import plotly.express as px
import time
from database import fetch_query, execute_query


# LOG DETAYLARI
@st.dialog("🔍 Log Detay İncelemesi")
def show_log_detail(log_id, df):
    detay = df[df["Log ID"] == log_id].iloc[0]

    st.markdown(f"### İşlem Özeti: {detay['İşlem Türü']}")
    st.info(f"**Açıklama:** {detay['Açıklama']}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"👤 **Kullanıcı:** {detay['Kullanıcı']}")
        st.write(f"📌 **Durum:** {detay['Durum']}")
    with col2:
        st.write(f"🕒 **Tarih & Saat:** {detay['Tarih']}")

    st.divider()
    st.caption(
        "🔒 Bu işlem KVKK ve veri bütünlüğü gereği SQL Server üzerinde zaman damgasıyla saklanmaktadır.")


#  VERİTABANI SIFIRLAMA
@st.dialog("⚠️ Sistemi ve Logları Sıfırla")
def reset_system_dialog():
    st.warning(
        "Bu işlem veritabanındaki tüm işlem geçmişi loglarını kalıcı olarak temizleyecektir. İşlem geri alınamaz!")
    st.info("İşlemi onaylıyor musunuz?")
    col1, col2 = st.columns(2)
    if col1.button("✔️ Evet, Tüm Logları Sıfırla", type="primary", use_container_width=True):
        try:
            # SQL tablosundaki tüm logları temizleyen işlem
            execute_query("DELETE FROM SISTEM_LOGLARI")
            execute_query(
                "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Sistem Sıfırlama', 'Sistem işlem geçmişi ve logları yönetici tarafından tamamen sıfırlandı.', 'Uyarı')")
            st.toast("Veritabanı logları sıfırlandı.", icon="🔄")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
    if col2.button("❌ İptal", use_container_width=True):
        st.rerun()


def show_log_gecmis():
    st.header("📋 Sistem Kayıtları ve Veritabanı Yönetimi")
    st.caption(
        "Sistemdeki tüm hareketler KVKK ve güvenlik standartları gereği veritabanında kayıt altına alınır. Buradaki tüm veriler ve yönetim araçları doğrudan SQL Server ile entegredir.")

    #  SQL'DEN LOG VERİLERİNİ ÇEKME
    query = """
        SELECT 
            l.LogID as [Log ID],
            ISNULL(k.KullaniciAdi, 'Sistem / Anonim') as [Kullanıcı],
            l.IslemTuru as [İşlem Türü],
            l.Aciklama as [Açıklama],
            FORMAT(l.Tarih, 'yyyy-MM-dd HH:mm') as [Tarih],
            l.Durum as [Durum]
        FROM SISTEM_LOGLARI l
        LEFT JOIN KULLANICILAR k ON l.KullaniciID = k.KullaniciID
        ORDER BY l.LogID DESC
    """
    df_logs = fetch_query(query)

    def format_durum(durum):
        if durum == "Başarılı":
            return "🟢 Başarılı"
        elif durum == "Hata" or durum == "Uyarı":
            return "🔴 Hata"
        elif durum == "Güncelleme":
            return "🟡 Güncelleme"
        return f"⚪ {durum}"

    if not df_logs.empty:
        df_logs["Durum"] = df_logs["Durum"].apply(format_durum)

    # GÜVENLİK ANALİZ
    st.subheader("🧠 Akıllı Aktivite Analizi")
    if not df_logs.empty:
        hata_sayisi = len(df_logs[df_logs["Durum"] == "🔴 Hata"])
        if hata_sayisi > 0:
            st.error(
                f"**Durum Tespiti:** Sistem kayıtlarında **{hata_sayisi} adet** kritik hata veya uyarı logu tespit edildi.")
        else:
            st.success(
                "✅ Sistem Durumu: Stabil. Olağandışı bir hata veya kritik güvenlik ihlali aktivitesi tespit edilmedi.")
    else:
        st.info("Sistemde analiz edilecek log hareketi bulunmuyor.")

    st.divider()

    #GRAFİKLER
    if not df_logs.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("**📊 Sistem İşlem Türü Dağılımı**")
            fig_pie = px.pie(df_logs, names="İşlem Türü", hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.write("**📈 İşlem Durumu Analizi**")
            durum_sayilari = df_logs["Durum"].value_counts().reset_index()
            durum_sayilari.columns = ["Durum", "Sayi"]
            fig_bar = px.bar(durum_sayilari, x="Durum", y="Sayi", color="Durum",
                             color_discrete_map={"🟢 Başarılı": "#00CC96", "🔴 Hata": "#EF553B",
                                                 "🟡 Güncelleme": "#FFA15A", "⚪ None": "#CCCCCC"})
            st.plotly_chart(fig_bar, use_container_width=True)

    #FİLTRELEME ALANI
    st.subheader("🔍 Canlı Log Filtreleme ve Arama")
    with st.container(border=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_query = st.text_input("Arama (Kullanıcı veya Açıklama)") #arama yeri
        with f_col2:
            durum_filter = st.selectbox("Durum Filtresi", ["Tümü", "🟢 Başarılı", "🔴 Hata", "🟡 Güncelleme"])
        with f_col3:
            turler = ["Tümü"] + list(df_logs["İşlem Türü"].unique()) if not df_logs.empty else ["Tümü"]
            tur_filter = st.selectbox("İşlem Türü", turler)

    #LOG TABLOSU VE İŞLEMLER
    if not df_logs.empty:
        filtered_df = df_logs.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df['Kullanıcı'].str.contains(search_query, case=False, na=False) |
                filtered_df['Açıklama'].str.contains(search_query, case=False, na=False)
                ]
        if durum_filter != "Tümü":
            filtered_df = filtered_df[filtered_df['Durum'] == durum_filter]
        if tur_filter != "Tümü":
            filtered_df = filtered_df[filtered_df['İşlem Türü'] == tur_filter]

        st.subheader("📋 Sistem Kayıt Listesi (Kara Kutu)")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        with st.container(border=True):
            act_col1, act_col2, act_col3 = st.columns([2, 1, 1])
            with act_col1:
                secilen_log = st.selectbox("İncelenecek Log ID'yi Seçin:", filtered_df["Log ID"])
            with act_col2:
                st.write("")
                st.write("")
                if st.button("👁️ Log Detayını Aç", use_container_width=True):
                    if secilen_log:
                        show_log_detail(secilen_log, filtered_df)
            with act_col3:
                st.write("")
                st.write("")
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Güvenlik Loglarını İndir (CSV)", data=csv, file_name="sistem_loglari.csv",
                                   mime="text/csv", use_container_width=True)
    else:
        st.info("Sistemde gösterilecek herhangi bir log kaydı bulunmuyor.")

    #  VERİTABANI YÖNETİM PANELİ
    st.divider()
    st.subheader("⚙️ Veritabanı Bakım ve Yönetim Paneli")
    st.markdown(
        "Veritabanı optimizasyon ve temizlik işlemlerini buradan doğrudan SQL Server üzerinde yürütebilirsiniz.")

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        with st.container(border=True):
            st.markdown("#### 📂 Veritabanı Temizlik İşlemleri")
            if st.button("🗑️ Eski Logları Temizle (Son 1 Yıl)", use_container_width=True):
                try:
                    # SQL Server üzerinde 1 yıldan eski logları  temizleyen işlem
                    execute_query("DELETE FROM SISTEM_LOGLARI WHERE Tarih < DATEADD(year, -1, GETDATE())")
                    execute_query(
                        "INSERT INTO SISTEM_LOGLARI (IslemTuru, Aciklama, Durum) VALUES ('Log Temizliği', 'Yönetici tarafından 1 yıldan eski log kayıtları temizlendi.', 'Güncelleme')")
                    st.success("1 yıldan eski log kayıtları başarıyla temizlendi.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Veritabanı işlemi başarısız: {e}")

    with m_col2:
        with st.container(border=True):
            st.markdown("#### 🚨 Sıfırlama İşlemi")
            if st.button("🔄 Tüm Sistem Loglarını Sıfırla", type="primary", use_container_width=True):
                reset_system_dialog()