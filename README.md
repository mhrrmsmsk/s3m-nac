# S3M NAC (Network Access Control) Policy Engine

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com/)
[![FreeRADIUS](https://img.shields.io/badge/FreeRADIUS-3.2-darkred.svg)](https://freeradius.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

Bu proje, S3M Security staj değerlendirme süreci kapsamında tasarlanmış ve geliştirilmiş, **RADIUS protokolü tabanlı bir Network Access Control (NAC)** sistemidir. Sistem; ağa dahil olmak isteyen cihaz ve kullanıcılar için AAA (Authentication, Authorization, Accounting) süreçlerini uçtan uca yönetmektedir.

Tüm altyapı Docker Compose kullanılarak izole bir ağ ortamında konteynerize edilmiş olup, dinamik politika yönetimi FastAPI tabanlı bir RESTful API üzerinden sağlanmaktadır.

## Mimari ve Kullanılan Teknolojiler

* **RADIUS Sunucusu:** FreeRADIUS 3.2 (Yetkilendirme ve paket işleme)
* **Veritabanı:** PostgreSQL 18 (Kimlik bilgileri, ağ politikaları ve kalıcı oturum logları)
* **Önbellek & Rate Limiting:** Redis 8 (Aktif oturumların takibi ve Brute-Force koruması)
* **Policy Engine:** Python 3.13 & FastAPI (Dinamik karar mekanizması ve REST API)
* **İzleme Arayüzü:** HTML5 & Tailwind CSS (Gerçek zamanlı ağ izleme paneli)

## Temel Yetenekler (AAA)

### 1. Authentication (Kimlik Doğrulama)
* **PAP Desteği:** 802.1X mimarisine uygun, şifre tabanlı standart kullanıcı doğrulaması.
* **MAB (MAC Authentication Bypass):** IP telefon, yazıcı ve IoT gibi akılsız cihazların donanım adresleri (MAC) üzerinden ağa güvenli erişimi.
* **Proaktif Güvenlik (Rate-Limiting):** Üst üste 5 hatalı giriş denemesinde, ilgili kullanıcının/cihazın Redis tabanlı bir sayaç ile 10 dakika boyunca ağdan izole edilmesi.

### 2. Authorization (Yetkilendirme)
* **Dinamik VLAN Ataması:** Kullanıcı gruplarına (`admin`, `employee`, `guest`) özel ağ segmentasyonu (Tunnel-Type, Tunnel-Private-Group-Id atamaları).
* **Policy Engine Entegrasyonu:** FreeRADIUS'un `rlm_rest` modülü ile FastAPI üzerinden canlı politika denetimi.

### 3. Accounting (Hesaplaşma ve İzleme)
* **Kalıcı Loglama:** `Accounting-Start` ve `Accounting-Stop` paketlerinin PostgreSQL `radacct` tablosuna anlık işlenmesi.
* **Zero-Touch Dashboard:** Ağa bağlanan cihazların Redis önbelleği üzerinden web arayüzüne milisaniyeler içinde yansıtılması.

---

## Kurulum ve Çalıştırma

Sistemi lokal ortamınızda ayağa kaldırmak için **Docker** ve **Docker Compose** yüklü olmalıdır.

**1. Repoyu Klonlayın:**
```bash
git clone https://github.com/mhrrmsmsk/s3m-nac.git
cd s3m-nac