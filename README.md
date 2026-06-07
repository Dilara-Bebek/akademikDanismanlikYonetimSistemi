# 🎓 Akademik Danışmanlık Yönetim Sistemi

Bu proje, üniversitelerdeki akademik danışmanlık süreçlerini dijitalleştirmek, öğrenci-danışman iletişimini güçlendirmek ve yapay zeka destekli analizlerle akademik başarıyı artırmak amacıyla geliştirilmiş kapsamlı bir web uygulamasıdır.

## 🌟 Öne Çıkan Özellikler

* **Üç Katmanlı Rol Mimarisi:** Sistem Yöneticisi (Admin), Danışman ve Öğrenci olmak üzere üç farklı yetki seviyesi ve bunlara özel kontrol panelleri.
* **🤖 Yapay Zeka Destekli Transkript Analizi:** Öğrencilerin yüklediği PDF formatındaki E-Devlet transkriptleri Google Gemini 2.5 Flash modeli ile taranır; alınan dersler, harf notları ve GNO otomatik olarak sisteme işlenerek performans grafikleri oluşturulur.
* **Akıllı Randevu Sistemi:** Çakışma önleyici algoritma ile danışmanların mesai saatleri, tatil günleri ve dolu seansları hesaplanarak öğrencilere en uygun boş zaman dilimleri önerilir.
* **Güvenli Kimlik Doğrulama:** Bcrypt ile şifreleme, TC Kimlik No algoritma kontrolü ve Gmail SMTP üzerinden gönderilen 6 haneli OTP kodu ile çok faktörlü e-posta doğrulaması.
* **Entegre İletişim:** Danışman ve öğrenciler arasında dosya (PDF, resim vb.) gönderimine imkan tanıyan uçtan uca mesajlaşma modülü.
* **Akademik Hedef ve Risk Takibi:** Danışmanların öğrencilere görev (örn: literatür taraması) atayabildiği ve GNO/Devamsızlık oranlarına göre sistemin otomatik risk uyarısı verdiği erken uyarı mekanizması.

## 🛠️ Kullanılan Teknolojiler

* **Frontend & Backend:** Python, Streamlit
* **Veritabanı:** Microsoft SQL Server (T-SQL), `pyodbc`
* **Yapay Zeka:** Google Gemini API (`google-generativeai`), `pypdf`
* **Veri Görselleştirme:** Pandas, Plotly Express
* **Güvenlik & İletişim:** `bcrypt`, `smtplib` (E-posta servisleri)

## ⚙️ Kurulum ve Çalıştırma Talimatları

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

**1. Depoyu Klonlayın**
```bash
git clone [https://github.com/Dilara-Bebek/akademikDanismanlikYonetimSistemi.git](https://github.com/Dilara-Bebek/akademikDanismanlikYonetimSistemi.git)
cd akademikDanismanlikYonetimSistemi
```

**2. Gerekli Kütüphaneleri Yükleyin**
```bash
pip install -r requirements.txt
```

**3. Veritabanı Bağlantısını Ayarlayın**
* Bilgisayarınızda SQL Server kurulu olmalıdır.
* Proje içerisindeki veritabanı scriptlerini çalıştırarak `AkademikDanismanlikDB` tablosunu ve ilişkili şemaları oluşturun.
* `database.py` dosyası içerisindeki `SERVER=.\SQLEXPRESS;` kısmını kendi SQL Server adınıza göre güncelleyin.

**4. Çevre Değişkenlerini (Secrets) Yapılandırın**
Proje ana dizininde `.streamlit` adında bir klasör oluşturun ve içine `secrets.toml` adında bir dosya açarak API/Mail bilgilerinizi girin:

```toml
[smtp]
email = "sistem_mailiniz@gmail.com"
password = "gmail_uygulama_sifreniz"

[gemini]
api_key = "google_gemini_api_anahtariniz"
```

**5. İlk Yöneticinin Oluşturulması**
Sisteme giriş yapabilmek için ilk admin hesabını oluşturun:

```bash
python create_admin.py
```

**6. Uygulamayı Başlatın**
```bash
streamlit run app.py
```

## 📖 Kullanım Rehberi

* **Yönetici Girişi:** Tarayıcıda açılan adresin sonuna `?admin=true` ekleyerek (örn: `localhost:8501/?admin=true`) gizli yönetici paneline erişebilir; bölüm, danışman ve sistem tanımlamalarını yapabilirsiniz.
* **Danışmanlar:** Kendilerine atanan öğrencilerin transkript analizlerini görüntüleyebilir, haftalık müsaitlik takvimlerini oluşturabilir ve randevuları onaylayıp sistem üzerinden not düşebilirler.
* **Öğrenciler:** Kayıt sonrası e-posta doğrulamalarını tamamlayarak panele erişir; PDF transkriptlerini AI sistemine okutabilir, danışmanlarından randevu alabilir ve hedeflerini takip edebilirler.

---
*Geliştirici: Dilara Bebek - ISUBÜ Bilgisayar Mühendisliği*
