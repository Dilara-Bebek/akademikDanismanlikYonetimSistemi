import hashlib
import bcrypt
import re
from database import get_connection

# 1. GÜVENLİK ALGORİTMALARI
def hash_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False

    if len(str(hashed_password)) == 64:
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), str(hashed_password).encode('utf-8'))
    except Exception:
        return False

def validate_tc_algorithm(tc):
    if len(tc) != 11 or not tc.isdigit() or tc[0] == '0':
        return False

    digits = [int(d) for d in tc]

    sum_odd = sum(digits[0:9:2])
    sum_even = sum(digits[1:8:2])

    if (sum_odd * 7 - sum_even) % 10 != digits[9]:
        return False

    if sum(digits[:10]) % 10 != digits[10]:
        return False

    return True


def validate_strong_password(password):
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalıdır."
    if not re.search(r"[A-Z]", password):
        return False, "Şifre en az bir büyük harf içermelidir."
    if not re.search(r"[a-z]", password):
        return False, "Şifre en az bir küçük harf içermelidir."
    if not re.search(r"[0-9]", password):
        return False, "Şifre en az bir rakam (0-9) içermelidir."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Şifre en az bir özel karakter (örn: !@#$) içermelidir."

    return True, "Şifre güvenli."

# 2. VERİTABANI İŞLEMLERİ

def check_user_exists(username):
    conn = get_connection()
    if not conn:
        return True

    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM KULLANICILAR WHERE KullaniciAdi = ?", (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def verify_user_email(username, email):
    """
    Şifre sıfırlama talebinde girilen e-postanın, o kullanıcıya ait olup olmadığını doğrular.
    """
    conn = get_connection()
    if not conn:
        return False, "Veritabanı bağlantı hatası."

    cursor = conn.cursor()
    try:
        query = """
            SELECT K.KullaniciAdi FROM KULLANICILAR K
            LEFT JOIN OGRENCILER O ON K.KullaniciID = O.KullaniciID
            LEFT JOIN DANISMANLAR D ON K.KullaniciID = D.KullaniciID
            WHERE K.KullaniciAdi = ? AND (O.Email = ? OR D.Email = ?)
        """
        cursor.execute(query, (username, email, email))
        user = cursor.fetchone()

        if user:
            return True, "Kullanıcı doğrulandı."
        else:
            return False, "Girdiğiniz bilgilere ait bir kullanıcı kaydı bulunamadı."
    except Exception as e:
        print(f"E-Posta Doğrulama Hatası: {e}")
        return False, "Sistem hatası."
    finally:
        conn.close()


def login_user(username, password, expected_role=None):
    if not username or not password:
        return None

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    query = "SELECT * FROM KULLANICILAR WHERE KullaniciAdi = ?"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(password, getattr(user, 'SifreHash', None)):
        return None

    if expected_role and expected_role.upper() not in str(getattr(user, 'Rol', '')).upper():
        return None

    return user


def register_user(username, password, role, extra_data=None):
    if extra_data is None:
        extra_data = {}

    if not username or not password or not role:
        return False, "Eksik bilgi girdiniz."

    role_upper = role.upper()
    email = extra_data.get('email', '')

    is_strong, msg = validate_strong_password(password)
    if not is_strong:
        return False, msg

    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Lütfen geçerli bir e-posta adresi giriniz."

    if "OGRENC" in role_upper or "ÖĞRENC" in role_upper:
        if len(username) != 10 or not username.isdigit():
            return False, "Öğrenci numarası tam 10 haneli rakam olmalıdır."

    elif "DANISMAN" in role_upper or "DANIŞMAN" in role_upper:
        if not validate_tc_algorithm(username):
            return False, "Geçersiz TC Kimlik Numarası! Algoritma doğrulaması başarısız."

    conn = get_connection()
    if not conn:
        return False, "Veritabanı bağlantı hatası."

    cursor = conn.cursor()

    try:
        if check_user_exists(username):
            return False, "Bu kullanıcı sisteme zaten kayıtlı."

        hashed_pw = hash_password(password)

        query = "INSERT INTO KULLANICILAR (KullaniciAdi, SifreHash, Rol) OUTPUT INSERTED.KullaniciID VALUES (?, ?, ?)"
        cursor.execute(query, (username, hashed_pw, role))
        kullanici_id = cursor.fetchone()[0]

        if "OGRENC" in role_upper or "ÖĞRENC" in role_upper:
            tc = extra_data.get('tc', '')
            ad_soyad = extra_data.get('ad_soyad', '')
            bolum = extra_data.get('bolum', '')
            sinif = extra_data.get('sinif', '')

            insert_ogr = "INSERT INTO OGRENCILER (KullaniciID, OgrenciNo, TC, AdSoyad, Bolum, Sinif, Email) VALUES (?, ?, ?, ?, ?, ?, ?)"
            cursor.execute(insert_ogr, (kullanici_id, username, tc, ad_soyad, bolum, sinif, email))

        elif "DANISMAN" in role_upper or "DANIŞMAN" in role_upper:
            ad_soyad = extra_data.get('ad_soyad', '')
            unvan = extra_data.get('unvan', '')
            bolum = extra_data.get('bolum', '')
            personel_no = extra_data.get('personel_no', '')

            insert_dan = "INSERT INTO DANISMANLAR (KullaniciID, AdSoyad, Unvan, Bolum, Email, PersonelNo) VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(insert_dan, (kullanici_id, ad_soyad, unvan, bolum, email, personel_no))

        conn.commit()
        return True, "Kayıt Başarılı"
    except Exception as e:
        print(f"Kayıt Hatası: {e}")
        return False, "Sistem kaynaklı bir hata oluştu."
    finally:
        conn.close()


def reset_password(username, new_password):
    if not username or not new_password:
        return False, "Eksik bilgi girdiniz."

    is_strong, msg = validate_strong_password(new_password)
    if not is_strong:
        return False, msg

    conn = get_connection()
    if not conn:
        return False, "Veritabanı bağlantı hatası."

    cursor = conn.cursor()

    try:
        if not check_user_exists(username):
            return False, "Kullanıcı bulunamadı."

        hashed_pw = hash_password(new_password)
        query = "UPDATE KULLANICILAR SET SifreHash = ? WHERE KullaniciAdi = ?"
        cursor.execute(query, (hashed_pw, username))
        conn.commit()
        return True, "Şifre başarıyla güncellendi."
    except Exception as e:
        print(f"Şifre Sıfırlama Hatası: {e}")
        return False, "Veritabanı hatası."
    finally:
        conn.close()


def admin_add_user(username, password, role, extra_data=None):
    return register_user(username, password, role, extra_data=extra_data)


def get_all_users():
    """
    Yönetici panelinde göstermek üzere kullanıcıları Ad Soyad bilgileriyle beraber getirir.
    """
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    query = """
        SELECT 
            K.KullaniciAdi, 
            K.Rol,
            COALESCE(O.AdSoyad, D.AdSoyad, 'Sistem Yöneticisi') as AdSoyad
        FROM KULLANICILAR K
        LEFT JOIN OGRENCILER O ON K.KullaniciID = O.KullaniciID
        LEFT JOIN DANISMANLAR D ON K.KullaniciID = D.KullaniciID
    """
    cursor.execute(query)
    users = cursor.fetchall()
    conn.close()

    return [{"Ad Soyad": u[2], "Giriş Bilgisi": u[0], "Rol": u[1], "Durum": "Aktif"} for u in users]


def delete_user(username):
    if username.lower() == "admin":
        return False, "Sistem yöneticisi (admin) hesabı silinemez!"

    conn = get_connection()
    if not conn:
        return False, "Veritabanı bağlantı hatası."

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT KullaniciID, Rol FROM KULLANICILAR WHERE KullaniciAdi = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return False, "Kullanıcı sistemde bulunamadı."

        kullanici_id = user[0]
        rol = str(user[1]).upper()

        if "OGRENC" in rol or "ÖĞRENC" in rol:
            cursor.execute("DELETE FROM OGRENCILER WHERE KullaniciID = ?", (kullanici_id,))
        elif "DANISMAN" in rol or "DANIŞMAN" in rol:
            cursor.execute("DELETE FROM DANISMANLAR WHERE KullaniciID = ?", (kullanici_id,))

        cursor.execute("DELETE FROM KULLANICILAR WHERE KullaniciID = ?", (kullanici_id,))

        conn.commit()
        return True, "Kullanıcı başarıyla silindi."
    except Exception as e:
        print(f"Silme Hatası: {e}")
        return False, "Sistem kaynaklı bir hata oluştu."
    finally:
        conn.close()