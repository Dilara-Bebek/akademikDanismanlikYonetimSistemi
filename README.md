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


