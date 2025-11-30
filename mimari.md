# OUTDATED

# Sistem Tasarım Dokümanı: Yüksek Hızlı Video Akış Muxer

## 1. Yönetici Özeti

Bu sistem, video içeriklerini (YouTube gibi) doğrudan kullanıcının yerel depolamasına aktarmak için tasarlanmış yüksek performanslı bir HTTP proxy servisidir. Geleneksel indirme yöntemlerinden farklı olarak, bu mimari **sunucu diskinde dosya saklamaz**. "Pass-Through Muxing" stratejisi kullanır; veri kaynaktan alınır, RAM’de birleştirilir ve gerçek zamanlı olarak kullanıcıya aktarılır.

Sistem, eşzamanlılık yönetimi için **Python `asyncio`** kullanır ve harici mesaj aracılara (Redis/RabbitMQ) ihtiyaç duymaz.

---

## 2. Sistem Mimarisi

### 2.1 Temel Desen: Pass-Through Boru

Sunucu, şeffaf bir tünel görevi görür. İki eş zamanlı bağlantı kurar:

1. **Upstream:** YouTube CDN’e bağlanarak ham Video ve Ses akışlarını çeker.
2. **Downstream:** Kullanıcı istemcisine birleşik MP4 akışını iletir.

**Veri Akışı:**
`YouTube CDN` → `FFmpeg Alt Süreç (Sunucu RAM’i)` → `FastAPI Parça Üreteci` → `Kullanıcı Dosya Sistemi`

### 2.2 Altyapı Bileşenleri

- **Uygulama Sunucusu:** Python 3.10+ (FastAPI + Uvicorn)
- **Medya Motoru:** FFmpeg (`subprocess` üzerinden çalıştırılır)
- **Meta Veri Motoru:** `yt-dlp` (Python kütüphane sarmalayıcısı)
- **Depolama:** **Yok** (Sadece geçici RAM tamponları)

---

## 3. Eşzamanlılık Modeli: "Çift Kapı"

Kaynak tükenmesini (DoS) önlemek ve Hizmet Kalitesini (QoS) sağlamak için, sistem standart Python `asyncio` yapıları ile **İki Katmanlı Kabul Kontrolü** uygular.

### Kapı 1: Toplam Bağlantı Sınırlayıcı (Kapasite)

- **Metrik:** Açık Soket Sayısı (Aktif İndirmeler + Bekleyen Kullanıcılar)
- **Mekanizma:** `asyncio.Lock` korumalı sayaç
- **Limit:** `50` (Yapılandırılabilir)
- **Davranış:**

  - Eğer `Mevcut Bağlantılar < 50`: İstek kabul edilir.
  - Eğer `Mevcut Bağlantılar >= 50`: İstek **HTTP 503 Service Unavailable** ile reddedilir.

- **Amaç:** Sunucu RAM ve Dosya Tanımlayıcılarını korumak.

### Kapı 2: Aktif İşçi Sınırlayıcı (Bant Genişliği)

- **Metrik:** Aktif FFmpeg Süreçleri
- **Mekanizma:** `asyncio.Semaphore`
- **Limit:** `25` (Yapılandırılabilir)
- **Davranış:**

  - Eğer `Semaphore` slotları varsa: İndirme hemen başlar.
  - Eğer `Semaphore` kilitli ise: İstek **Beklemeye alınır** (RAM’de sıraya alınır) ve bir slot boşalana kadar bekler.

- **Amaç:** Ağ Bant Genişliği ve CPU’yu korumak.

---

## 4. Bileşen Tasarımı ve Python Modül Kullanımı

### 4.1 Meta Veri Kontrolü (`/info`)

Ağır işlemleri tetiklemeden hafif meta veri çıkarır.

- **Modül:** `yt_dlp.YoutubeDL`
- **Konfigürasyon:** `{'extract_flat': True, 'dump_json': True}`
- **Çıktı:** Video Başlığı, Süre, Küçük Resim URL’si ve Yükleyici bilgilerini içeren JSON döner
- **Kaynak Kullanımı:** Minimal CPU, geçici ağ çağrısı

### 4.2 Akış Kontrolü (`/download`)

Ana motor. `subprocess` ve HTTP akışının yaşam döngüsünü yönetir.

**Adım 1: Başlık ve URL Çıkarma**

- **Modül:** `yt_dlp`
- **İşlem:** `extract_info(url, download=False)` çalıştırılır
- **Önemli Çıktılar:**

  1. **Akış URL’leri:** Video ve Ses kaynak dosyalarının doğrudan linkleri
  2. **HTTP Başlıkları:** `User-Agent` ve `Cookies`. **Downstream’de HTTP 403 hatasını önlemek için yakalanmalıdır.**

**Adım 2: Muxing Motoru**

- **Modül:** `subprocess` (`asyncio.subprocess` veya `subprocess.Popen`)
- **Komut:** `ffmpeg`
- **Argümanlar:**

  - **Girdiler:** Video ve Ses URL’leri `-i` ile verilir
  - **Başlıklar:** Adım 1’de yakalanan başlıklar `-headers` ile her girişten önce eklenir
  - **Kodekler:** `-c copy` (Doğrudan Akış Kopyası, CPU dostu)
  - **Konteyner:** `-f mp4`
  - **Muxing Bayrakları:** `-movflags frag_keyframe+empty_moov`

    - _Neden:_ Standart MP4 meta verisi dosya sonunda yazılır. Akış için "fragmented MP4" gerekir; meta veriler parça parça yazılır, böylece indirme bitmeden oynatma mümkün olur.

  - **Çıktı:** `STDOUT` borusuna (`-`)

**Adım 3: Async Üreteci**

- **Modül:** `asyncio`
- **Mantık:**

  - FFmpeg `stdout` borusundan `32KB` veya `64KB` parçalar okunur
  - Bloklayıcı I/O için `await asyncio.to_thread()` veya native async okuma kullanılır
  - Parçalar yanıt olarak üretilir
  - **Yaşam Döngüsü Yönetimi:** `GeneratorExit` (Kullanıcı Bağlantısı Kesildi) dinlenir. Kullanıcı ayrılırsa, FFmpeg alt sürecine `SIGTERM/SIGKILL` gönderilmelidir; aksi halde “zombi süreç” oluşur

**Adım 4: Yanıt**

- **Modül:** `fastapi.responses.StreamingResponse`
- **Başlıklar:**

  - `Content-Disposition: attachment; filename="video.mp4"` (İndirmeyi zorlar)
  - `Content-Length`: Tahmini boyut (`yt-dlp` meta verisinden). İstemci ilerleme çubuğu için gerekli

---

## 5. İstemci Tarafı Entegrasyon Sözleşmesi

### 5.1 Dosya Sistemi API’si

Backend, depolama mantığını istemciye (Frontend) bırakır:

1. İstemci `/info` çağrısı yapar ve küçük resim/başlığı gösterir
2. İstemci `window.showSaveFilePicker()` ile kullanıcı diskine erişim açar
3. İstemci `fetch('/download')` başlatır
4. İstemci bir `WritableStream` oluşturur
5. HTTP yanıtını doğrudan Disk `WritableStream`’e yönlendirir

### 5.2 Hata Yönetimi

- **HTTP 503:** “Sunucu Meşgul, lütfen bekleyin.” mesajı göster
- **HTTP 400/404:** Geçersiz URL veya Video silinmiş
- **Akış Kesilmesi:** Ağ bağlantısı kesilirse bu sürüm “Resume” (Range Request) desteklemez. İndirme yeniden başlamalıdır

---

## 6. Ölçeklenebilirlik ve Limitler

| Parametre             | Önerilen Değer | Kısıtlama Kaynağı                                            |
| :-------------------- | :------------- | :----------------------------------------------------------- |
| **Aktif İşçiler**     | **25**         | Ağ Kartı (NIC) Doyumu, 1Gbps port ve 1080p bitrate varsayımı |
| **Maksimum Kapasite** | **50**         | Mevcut RAM, her bekleyen bağlantı ~50KB-1MB tüketir          |
| **Tampon Boyutu**     | **64 KB**      | Python üreteci verimliliği optimizasyonu                     |

## 7. Yazılım Mühendisleri İçin Uygulama Kontrol Listesi

1. **Eşzamanlılık Sınıfı:** `Semaphore` ve `Lock` tutan Singleton `ConnectionManager` sınıfı oluştur
2. **Alt Süreç Güvenliği:** Stream başarısız olursa `process.kill()` `finally` bloğunda çağrılmalı
3. **Başlık Ekleme:** `yt-dlp` `http_headers`’ın FFmpeg için `Key: Value\r\n` formatında olduğunu doğrula
4. **Tampon Ayarı:** Üreteç binary parçaları (`read(n)`), satır (`readline()`) değil, okumalı
