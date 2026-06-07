import bcrypt
from database import get_connection
def setup_first_admin():
    # Admin bilgileri
    admin_user = "admin"
    admin_pass = "Admin123!" # Güçlü şifre politikasına uygun
    admin_role = "YONETİCİ"

    conn = get_connection()
    if not conn:
        print("❌ Veritabanına bağlanılamadı!")
        return

    cursor = conn.cursor()

    try:
        # Önce bu kullanıcı zaten var mı diye kontrol edelim
        cursor.execute("SELECT * FROM KULLANICILAR WHERE KullaniciAdi = ?", (admin_user,))
        if cursor.fetchone():
            print("⚠️ 'admin' kullanıcısı zaten veritabanında mevcut.")
            return

        # Şifreyi BCrypt ile güvenli hale getir
        print("⏳ Şifre hashleniyor...")
        hashed_pw = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Veritabanına kaydet
        query = "INSERT INTO KULLANICILAR (KullaniciAdi, SifreHash, Rol) VALUES (?, ?, ?)"
        cursor.execute(query, (admin_user, hashed_pw, admin_role))
        conn.commit()

        print("✅ Sistem Yöneticisi (Admin) başarıyla oluşturuldu!")
        print("-" * 30)
        print(f"Kullanıcı Adı : {admin_user}")
        print(f"Şifre         : {admin_pass}")
        print("-" * 30)

    except Exception as e:
        print(f"❌ Kayıt sırasında hata oluştu: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_first_admin()