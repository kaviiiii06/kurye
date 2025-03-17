# Kurye Takip Sistemi

Bu proje, kurye firmalarının teslimatlarını ve kuryelerini takip etmek için geliştirilmiş basit bir web uygulamasıdır.

## Özellikler

- Kurye ekleme ve yönetme
- Teslimat oluşturma ve takip etme
- Teslimat durumu güncelleme
- Teslimat ücreti belirleme
- Teslimat geçmişi görüntüleme

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:
```bash
python kurye_takip.py
```

3. Tarayıcınızda `http://localhost:5000` adresine gidin.

## Kullanım

1. Önce "Yeni Kurye Ekle" formunu kullanarak kuryeleri sisteme ekleyin.
2. "Yeni Teslimat Ekle" formunu kullanarak teslimatları oluşturun.
3. Teslimat listesinden teslimatların durumunu takip edin.
4. Tamamlanan teslimatlar için ücret belirleyip "Tamamla" butonuna tıklayın.

## Veritabanı

Uygulama SQLite veritabanı kullanmaktadır. Veritabanı dosyası (`kurye.db`) otomatik olarak oluşturulacaktır. 