import streamlit as st

def show_advisor_bildirimler():
    st.header("🔔 Bildirim Merkezi")
    st.markdown(
        "Öğrencilerinizden gelen randevu taleplerini, iptalleri ve yaklaşan görüşme hatırlatmalarını buradan takip edebilirsiniz.")

    if 'advisor_notifications' not in st.session_state:
        st.session_state.advisor_notifications = [
            {"id": 1, "type": "Yeni Talep", "icon": "📅",
             "message": "Dilara Bebek sizden yeni bir randevu talep etti. (28 Mart, 13:30)", "time": "10 dk önce",
             "read": False, "action": "Randevulara Git"},
            {"id": 2, "type": "İptal", "icon": "❌", "message": "Ahmet Yılmaz bugünkü 15:00 randevusunu iptal etti.",
             "time": "2 saat önce", "read": False, "action": "Detay Gör"},
            {"id": 3, "type": "Hatırlatma", "icon": "⏰",
             "message": "Yaklaşan Görüşme: Zeynep Can ile randevunuz 30 dakika sonra başlayacak.", "time": "30 dk önce",
             "read": True, "action": "Görüşme Notu Hazırla"},
            {"id": 4, "type": "Yeni Talep", "icon": "📅",
             "message": "Mehmet Demir sizden yeni bir randevu talep etti. (29 Mart, 10:00)", "time": "1 gün önce",
             "read": True, "action": "Randevulara Git"},
        ]

    notifs = st.session_state.advisor_notifications
    unread_count = sum(1 for n in notifs if not n['read'])

    col1, col2 = st.columns([3, 1])
    with col1:
        if unread_count > 0:
            st.warning(f"🔔 **{unread_count} adet okunmamış bildiriminiz var.**")
        else:
            st.success("✅ Tüm bildirimleri okudunuz. Yakalanacak yeni bir gelişme yok.")
    with col2:
        if st.button("✔️ Tümünü Okundu Yap", use_container_width=True):
            for n in notifs:
                n['read'] = True
            st.rerun()

    st.divider()

    #  FİLTRELEME
    with st.container(border=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            filter_type = st.selectbox("📌 Bildirim Türü", ["Tümü", "Yeni Talep", "İptal", "Hatırlatma"])
        with f_col2:
            st.write("")  # Hizalama
            filter_unread = st.checkbox("❗ Sadece Okunmayanları Göster")

    # Filtreleri Uygulama
    filtered_notifs = notifs
    if filter_type != "Tümü":
        filtered_notifs = [n for n in filtered_notifs if n['type'] == filter_type]
    if filter_unread:
        filtered_notifs = [n for n in filtered_notifs if not n['read']]

    #  BİLDİRİM LİSTESİ
    st.write("")
    if not filtered_notifs:
        st.info("📭 Bu filtrelere uygun bildirim bulunmuyor.")
    else:
        for notif in filtered_notifs:
            with st.container(border=True):
                c_icon, c_msg, c_time, c_act = st.columns([1, 6, 2, 3])

                with c_icon:
                    st.subheader(notif['icon'])

                with c_msg:
                    if not notif['read']:
                        st.markdown(f"**{notif['message']}**")  # Okunmamışsa kalın (bold)
                    else:
                        st.markdown(f"<span style='color:gray'>{notif['message']}</span>",
                                    unsafe_allow_html=True)  # Okunmuşsa gri

                with c_time:
                    st.caption(f"{notif['time']}")
                    if not notif['read']:
                        st.markdown("🆕 *Yeni*")

                with c_act:
                    act1, act2 = st.columns([2, 1])
                    with act1:
                        # İlgili sayfaya yönlendirme butonu
                        if st.button(notif['action'], key=f"btn_{notif['id']}", use_container_width=True):
                            st.toast(f"'{notif['action']}' sayfasına yönlendiriliyorsunuz...", icon="🚀")
                    with act2:
                        # Okundu İşaretleme veya Silme
                        if not notif['read']:
                            if st.button("✔️", key=f"read_{notif['id']}", help="Okundu İşaretle"):
                                notif['read'] = True
                                st.rerun()
                        else:
                            if st.button("🗑️", key=f"del_{notif['id']}", help="Sil"):
                                st.session_state.advisor_notifications.remove(notif)
                                st.rerun()