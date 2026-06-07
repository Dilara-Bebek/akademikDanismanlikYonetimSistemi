import smtplib
from email.message import EmailMessage
import random
import streamlit as st
def generate_verification_code():
    """6 haneli rastgele doğrulama kodu üretir."""
    return str(random.randint(100000, 999999))
def send_verification_email(to_email, code):
    """st.secrets kullanarak Gmail SMTP üzerinden gerçek mail gönderir."""
    try:
        sender_email = st.secrets["smtp"]["email"]
        sender_password = st.secrets["smtp"]["password"]

        msg = EmailMessage()
        msg['Subject'] = 'Akademik Danışmanlık Sistemi - Hesap Doğrulama'
        msg['From'] = f"Akademik Danışmanlık Sistemi <{sender_email}>"
        msg['To'] = to_email

        # bir HTML içeriği
        icerik = f"""Merhaba,

Akademik Danışmanlık Sistemine kayıt başvurunuz alınmıştır. 
İşleminizi tamamlamak ve hesabınızı aktifleştirmek için doğrulama kodunuz:

GÜVENLİK KODU: {code}

* Bu kod 5 dakika boyunca geçerlidir.
* Eğer bu işlemi siz yapmadıysanız, lütfen bu e-postayı dikkate almayınız.

İyi çalışmalar dileriz,
Akademik Danışmanlık Sistemi Yönetimi
"""
        msg.set_content(icerik)

        # Gmail SMTP sunucusuna güvenli ssl bağlantı
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)

        return True, "Doğrulama kodu e-posta adresinize gönderildi."

    except Exception as e:
        print(f"SMTP Hatası: {e}")
        return False, f"E-posta gönderilemedi! Google'ın yanıtı: {str(e)}"