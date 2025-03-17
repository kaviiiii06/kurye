import sys
import hashlib
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTableWidget, QTableWidgetItem, QComboBox, 
                           QMessageBox, QTabWidget, QDateTimeEdit, QSpinBox,
                           QDoubleSpinBox, QDialog, QStackedWidget, QHeaderView)
from PyQt5.QtCore import Qt, QDateTime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

Base = declarative_base()

class Yonetici(Base):
    __tablename__ = 'yonetici'
    id = Column(Integer, primary_key=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    sifre_hash = Column(String(128), nullable=False)
    salt = Column(String(32), nullable=False)
    ad_soyad = Column(String(100), nullable=False)

    def sifre_belirle(self, sifre):
        self.salt = os.urandom(16).hex()
        self.sifre_hash = hashlib.sha256((sifre + self.salt).encode()).hexdigest()

    def sifre_kontrol(self, sifre):
        return self.sifre_hash == hashlib.sha256((sifre + self.salt).encode()).hexdigest()

class Kurye(Base):
    __tablename__ = 'kurye'
    id = Column(Integer, primary_key=True)
    ad = Column(String(100), nullable=False)
    telefon = Column(String(20), nullable=False)
    kayit_tarihi = Column(DateTime, default=datetime.utcnow)
    aktif = Column(Boolean, default=True)

class Teslimat(Base):
    __tablename__ = 'teslimat'
    id = Column(Integer, primary_key=True)
    kurye_id = Column(Integer, ForeignKey('kurye.id'), nullable=False)
    adres = Column(String(200), nullable=False)
    musteri_adi = Column(String(100), nullable=False)
    musteri_telefon = Column(String(20), nullable=False)
    baslangic_zamani = Column(DateTime, nullable=False)
    bitis_zamani = Column(DateTime)
    durum = Column(String(20), default='Devam Ediyor')
    ucret = Column(Float)
    kurye = relationship('Kurye', backref='teslimatlar')

class KuryeGider(Base):
    __tablename__ = 'kurye_gider'
    id = Column(Integer, primary_key=True)
    kurye_id = Column(Integer, ForeignKey('kurye.id'), nullable=False)
    tarih = Column(DateTime, default=datetime.utcnow)
    aciklama = Column(String(200), nullable=False)
    miktar = Column(Float, nullable=False)
    kurye = relationship('Kurye', backref='giderler')

engine = create_engine('sqlite:///kurye.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class GirisEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        # Ana layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Logo veya başlık
        baslik = QLabel('EVİM DÖNER')
        baslik.setStyleSheet('font-size: 36px; font-weight: bold; color: #e74c3c; margin: 20px; font-family: "Segoe UI", Arial, sans-serif;')
        baslik.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(baslik)
        
        # Giriş formu
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_widget.setLayout(form_layout)
        form_layout.setSpacing(15)
        
        self.kullanici_adi = QLineEdit()
        self.kullanici_adi.setPlaceholderText('Kullanıcı Adı')
        self.kullanici_adi.setStyleSheet('padding: 10px; font-size: 14px;')
        self.sifre = QLineEdit()
        self.sifre.setPlaceholderText('Şifre')
        self.sifre.setEchoMode(QLineEdit.Password)
        self.sifre.setStyleSheet('padding: 10px; font-size: 14px;')
        
        giris_btn = QPushButton('Giriş Yap')
        giris_btn.clicked.connect(self.giris_yap)
        giris_btn.setStyleSheet('background-color: #e74c3c; color: white; padding: 12px; border-radius: 5px; font-size: 14px; font-weight: bold; min-width: 200px;')
        
        form_layout.addWidget(self.kullanici_adi)
        form_layout.addWidget(self.sifre)
        form_layout.addWidget(giris_btn)
        
        main_layout.addWidget(form_widget)

    def giris_yap(self):
        kullanici_adi = self.kullanici_adi.text()
        sifre = self.sifre.text()
        
        yonetici = self.parent.session.query(Yonetici).filter_by(
            kullanici_adi=kullanici_adi
        ).first()
        
        if yonetici and yonetici.sifre_kontrol(sifre):
            self.parent.yonetici = yonetici
            self.parent.giris_yapildi()
            self.parent.stacked_widget.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, 'Hata', 'Kullanıcı adı veya şifre hatalı!')

class YoneticiPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        # Ana layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Üst bilgi çubuğu
        ust_bilgi = QHBoxLayout()
        
        # Yönetici bilgisi varsa göster
        if hasattr(self.parent, 'yonetici') and self.parent.yonetici:
            yonetici_bilgi = QLabel(f'Hoş geldiniz, {self.parent.yonetici.ad_soyad}')
            ust_bilgi.addWidget(yonetici_bilgi)
        
        cikis_btn = QPushButton('Çıkış Yap')
        cikis_btn.clicked.connect(self.cikis_yap)
        ust_bilgi.addStretch()
        ust_bilgi.addWidget(cikis_btn)
        main_layout.addLayout(ust_bilgi)
        
        # Yönetici işlemleri
        islemler_layout = QHBoxLayout()
        
        yeni_yonetici_btn = QPushButton('Yeni Yönetici Ekle')
        yeni_yonetici_btn.clicked.connect(self.yeni_yonetici_ekle)
        
        yonetici_listesi_btn = QPushButton('Yönetici Listesi')
        yonetici_listesi_btn.clicked.connect(self.yonetici_listesi_goster)
        
        tema_btn = QPushButton('Tema Ayarları')
        tema_btn.clicked.connect(self.tema_ayarlari)
        
        islemler_layout.addWidget(yeni_yonetici_btn)
        islemler_layout.addWidget(yonetici_listesi_btn)
        islemler_layout.addWidget(tema_btn)
        
        main_layout.addLayout(islemler_layout)
        
        # Yönetici tablosu
        self.yonetici_tablo = QTableWidget()
        self.yonetici_tablo.setColumnCount(5)
        self.yonetici_tablo.setHorizontalHeaderLabels(['ID', 'Ad Soyad', 'Kullanıcı Adı', 'Şifre', 'İşlemler'])
        
        # Sütun genişliklerini ayarla
        self.yonetici_tablo.setColumnWidth(0, 50)   # ID
        self.yonetici_tablo.setColumnWidth(1, 200)  # Ad Soyad
        self.yonetici_tablo.setColumnWidth(2, 150)  # Kullanıcı Adı
        self.yonetici_tablo.setColumnWidth(3, 150)  # Şifre
        self.yonetici_tablo.setColumnWidth(4, 150)  # İşlemler
        
        main_layout.addWidget(self.yonetici_tablo)

    def cikis_yap(self):
        self.parent.yonetici = None
        self.parent.stacked_widget.setCurrentIndex(0)  # Giriş ekranına dön

    def yeni_yonetici_ekle(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Yeni Yönetici Ekle')
        layout = QVBoxLayout(dialog)
        
        ad_soyad = QLineEdit()
        ad_soyad.setPlaceholderText('Ad Soyad')
        kullanici_adi = QLineEdit()
        kullanici_adi.setPlaceholderText('Kullanıcı Adı')
        sifre = QLineEdit()
        sifre.setPlaceholderText('Şifre')
        sifre.setEchoMode(QLineEdit.Password)
        
        kaydet_btn = QPushButton('Kaydet')
        kaydet_btn.clicked.connect(lambda: self.yonetici_kaydet(
            dialog, ad_soyad.text(), kullanici_adi.text(), sifre.text()
        ))
        
        layout.addWidget(ad_soyad)
        layout.addWidget(kullanici_adi)
        layout.addWidget(sifre)
        layout.addWidget(kaydet_btn)
        
        dialog.exec_()

    def yonetici_kaydet(self, dialog, ad_soyad, kullanici_adi, sifre):
        try:
            yeni_yonetici = Yonetici(
                ad_soyad=ad_soyad,
                kullanici_adi=kullanici_adi
            )
            yeni_yonetici.sifre_belirle(sifre)
            self.parent.session.add(yeni_yonetici)
            self.parent.session.commit()
            dialog.accept()
            self.yonetici_listesi_goster()
            QMessageBox.information(self, 'Başarılı', 'Yönetici başarıyla eklendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Yönetici eklenirken hata oluştu: {str(e)}')

    def yonetici_listesi_goster(self):
        yoneticiler = self.parent.session.query(Yonetici).all()
        self.yonetici_tablo.setRowCount(len(yoneticiler))
        
        for i, yonetici in enumerate(yoneticiler):
            self.yonetici_tablo.setItem(i, 0, QTableWidgetItem(str(yonetici.id)))
            self.yonetici_tablo.setItem(i, 1, QTableWidgetItem(yonetici.ad_soyad))
            self.yonetici_tablo.setItem(i, 2, QTableWidgetItem(yonetici.kullanici_adi))
            
            islemler_widget = QWidget()
            islemler_layout = QHBoxLayout(islemler_widget)
            islemler_layout.setContentsMargins(5, 2, 5, 2)
            
            sil_btn = QPushButton('Sil')
            sil_btn.clicked.connect(lambda checked, y=yonetici: self.yonetici_sil(y.id))
            
            islemler_layout.addWidget(sil_btn)
            self.yonetici_tablo.setCellWidget(i, 4, islemler_widget)

    def yonetici_sil(self, yonetici_id):
        try:
            yonetici = self.parent.session.query(Yonetici).get(yonetici_id)
            if yonetici.id == self.parent.yonetici.id:
                QMessageBox.warning(self, 'Uyarı', 'Kendi hesabınızı silemezsiniz!')
                return
            self.parent.session.delete(yonetici)
            self.parent.session.commit()
            self.yonetici_listesi_goster()
            QMessageBox.information(self, 'Başarılı', 'Yönetici başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Yönetici silinirken hata oluştu: {str(e)}')

    def tema_ayarlari(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Tema Ayarları')
        dialog.setMinimumWidth(400)
        
        # Ana layout
        main_layout = QVBoxLayout()
        dialog.setLayout(main_layout)
        
        # Ana renk seçimi
        ana_renk_widget = QWidget()
        ana_renk_layout = QHBoxLayout()
        ana_renk_widget.setLayout(ana_renk_layout)
        
        ana_renk_label = QLabel('Ana Renk:')
        ana_renk_combo = QComboBox()
        ana_renk_combo.addItems(['Kırmızı', 'Mavi', 'Yeşil', 'Mor', 'Turuncu'])
        ana_renk_layout.addWidget(ana_renk_label)
        ana_renk_layout.addWidget(ana_renk_combo)
        main_layout.addWidget(ana_renk_widget)
        
        # Arka plan rengi seçimi
        arkaplan_widget = QWidget()
        arkaplan_layout = QHBoxLayout()
        arkaplan_widget.setLayout(arkaplan_layout)
        
        arkaplan_label = QLabel('Arka Plan:')
        arkaplan_combo = QComboBox()
        arkaplan_combo.addItems(['Açık', 'Koyu'])
        arkaplan_layout.addWidget(arkaplan_label)
        arkaplan_layout.addWidget(arkaplan_combo)
        main_layout.addWidget(arkaplan_widget)
        
        # Yazı tipi boyutu
        yazi_boyut_widget = QWidget()
        yazi_boyut_layout = QHBoxLayout()
        yazi_boyut_widget.setLayout(yazi_boyut_layout)
        
        yazi_boyut_label = QLabel('Yazı Boyutu:')
        yazi_boyut_spin = QSpinBox()
        yazi_boyut_spin.setRange(12, 20)  # Daha büyük yazı boyutu aralığı
        yazi_boyut_spin.setValue(14)  # Varsayılan yazı boyutu
        yazi_boyut_layout.addWidget(yazi_boyut_label)
        yazi_boyut_layout.addWidget(yazi_boyut_spin)
        main_layout.addWidget(yazi_boyut_widget)
        
        # Uygula butonu
        uygula_btn = QPushButton('Uygula')
        uygula_btn.clicked.connect(lambda: self.tema_uygula(
            ana_renk_combo.currentText(),
            arkaplan_combo.currentText(),
            yazi_boyut_spin.value(),
            dialog
        ))
        main_layout.addWidget(uygula_btn)
        
        dialog.exec_()

    def tema_uygula(self, ana_renk, arkaplan, yazi_boyut, dialog):
        try:
            # Ana renk kodları
            renk_kodlari = {
                'Kırmızı': '#e74c3c',
                'Mavi': '#3498db',
                'Yeşil': '#2ecc71',
                'Mor': '#9b59b6',
                'Turuncu': '#e67e22'
            }
            
            # Arka plan renkleri
            arkaplan_renkleri = {
                'Açık': '#ffffff',
                'Koyu': '#2c3e50'
            }
            
            # Yazı renkleri
            yazi_renkleri = {
                'Açık': '#000000',
                'Koyu': '#ffffff'
            }
            
            # Tema CSS'i
            tema_css = f"""
            QWidget {{
                background-color: {arkaplan_renkleri[arkaplan]};
                color: {yazi_renkleri[arkaplan]};
                font-size: {yazi_boyut}px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QMainWindow {{
                background-color: {arkaplan_renkleri[arkaplan]};
            }}
            QLabel {{
                color: {yazi_renkleri[arkaplan]};
                font-size: {yazi_boyut + 2}px;
                font-weight: normal;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {renk_kodlari[ana_renk]};
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: {yazi_boyut}px;
                font-weight: bold;
                border: none;
                min-width: 150px;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {renk_kodlari[ana_renk]}dd;
            }}
            QTableWidget {{
                background-color: {arkaplan_renkleri[arkaplan]};
                color: {yazi_renkleri[arkaplan]};
                gridline-color: {renk_kodlari[ana_renk]}44;
                border: 1px solid {renk_kodlari[ana_renk]}44;
                font-size: {yazi_boyut}px;
            }}
            QTableWidget::item {{
                padding: 12px;
                background-color: {arkaplan_renkleri[arkaplan]};
                color: {yazi_renkleri[arkaplan]};
            }}
            QTableWidget::item:selected {{
                background-color: {renk_kodlari[ana_renk]}44;
                color: {yazi_renkleri[arkaplan]};
            }}
            QHeaderView::section {{
                background-color: {renk_kodlari[ana_renk]};
                color: white;
                padding: 12px;
                border: none;
                font-size: {yazi_boyut}px;
                font-weight: bold;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {arkaplan_renkleri[arkaplan]};
                color: {yazi_renkleri[arkaplan]};
                border: 2px solid {renk_kodlari[ana_renk]}44;
                padding: 12px;
                border-radius: 6px;
                font-size: {yazi_boyut}px;
                min-height: 40px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QTabWidget::pane {{
                border: 2px solid {renk_kodlari[ana_renk]}44;
                background-color: {arkaplan_renkleri[arkaplan]};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {arkaplan_renkleri[arkaplan]};
                color: {yazi_renkleri[arkaplan]};
                padding: 12px 20px;
                border: 2px solid {renk_kodlari[ana_renk]}44;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: {yazi_boyut}px;
                font-weight: bold;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background-color: {renk_kodlari[ana_renk]};
                color: white;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {arkaplan_renkleri[arkaplan]};
                width: 16px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {renk_kodlari[ana_renk]}44;
                border-radius: 8px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {renk_kodlari[ana_renk]}66;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
            
            # Tema CSS'ini uygula
            self.parent.setStyleSheet(tema_css)
            
            # Tüm widget'ları güncelle
            for widget in self.parent.findChildren(QWidget):
                widget.setStyleSheet(tema_css)
            
            dialog.accept()
            QMessageBox.information(self, 'Başarılı', 'Tema başarıyla uygulandı!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Tema uygulanırken hata oluştu: {str(e)}')

class KuryeTakipUygulamasi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('EVİM DÖNER - Kurye Takip Sistemi')
        self.setGeometry(100, 100, 1200, 800)
        
        # Veritabanı oturumu
        self.session = Session()
        
        # Yönetici bilgisi
        self.yonetici = None
        
        # Ana widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Ana layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # Stacked widget oluştur
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Giriş ekranı
        self.giris_ekrani = GirisEkrani(self)
        self.stacked_widget.addWidget(self.giris_ekrani)
        
        # Ana ekran
        self.ana_ekran = QWidget()
        self.ana_ekran_layout = QVBoxLayout()
        self.ana_ekran.setLayout(self.ana_ekran_layout)
        
        # Başlık etiketi
        baslik = QLabel('EVİM DÖNER')
        baslik.setStyleSheet('font-size: 24px; font-weight: bold; color: #e74c3c; margin: 10px; text-align: center;')
        self.ana_ekran_layout.addWidget(baslik)
        
        # Tab widget oluştur
        self.tab_widget = QTabWidget()
        self.ana_ekran_layout.addWidget(self.tab_widget)
        
        # Tabları oluştur
        self.kurye_tab = QWidget()
        self.teslimat_tab = QWidget()
        self.rapor_tab = QWidget()
        self.gider_tab = QWidget()  # Yeni gider tab'ı
        
        self.tab_widget.addTab(self.kurye_tab, "Kuryeler")
        self.tab_widget.addTab(self.teslimat_tab, "Teslimatlar")
        self.tab_widget.addTab(self.rapor_tab, "Raporlar")
        self.tab_widget.addTab(self.gider_tab, "Giderler")  # Yeni tab'ı ekle
        
        # İmza etiketi
        imza = QLabel('Uygulamayı geliştiren Baran Akbulut iyi günler dilerim')
        imza.setStyleSheet('color: #666; font-style: italic; margin: 10px; text-align: center;')
        self.ana_ekran_layout.addWidget(imza)
        
        self.stacked_widget.addWidget(self.ana_ekran)
        
        # Tab içeriklerini oluştur
        self.kurye_tab_olustur()
        self.teslimat_tab_olustur()
        self.rapor_tab_olustur()
        self.gider_tab_olustur()  # Gider tab'ını oluştur
        
        # Tabloları güncelle
        self.kurye_tablo_guncelle()
        self.teslimat_tablo_guncelle()
        
        # İlk yöneticiyi oluştur
        self.ilk_yonetici_olustur()

    def ilk_yonetici_olustur(self):
        yonetici = self.session.query(Yonetici).first()
        if not yonetici:
            ilk_yonetici = Yonetici(
                kullanici_adi='admin',
                ad_soyad='Sistem Yöneticisi'
            )
            ilk_yonetici.sifre_belirle('admin123')
            self.session.add(ilk_yonetici)
            self.session.commit()

    def kurye_tab_olustur(self):
        layout = QVBoxLayout(self.kurye_tab)
        
        # Kurye ekleme formu
        form_layout = QHBoxLayout()
        
        self.kurye_ad = QLineEdit()
        self.kurye_ad.setPlaceholderText('Kurye Adı')
        self.kurye_telefon = QLineEdit()
        self.kurye_telefon.setPlaceholderText('Telefon')
        
        kurye_ekle_btn = QPushButton('Kurye Ekle')
        kurye_ekle_btn.clicked.connect(self.kurye_ekle)
        
        form_layout.addWidget(self.kurye_ad)
        form_layout.addWidget(self.kurye_telefon)
        form_layout.addWidget(kurye_ekle_btn)
        
        layout.addLayout(form_layout)
        
        # Kurye tablosu
        self.kurye_tablo = QTableWidget()
        self.kurye_tablo.setColumnCount(5)
        self.kurye_tablo.setHorizontalHeaderLabels(['ID', 'Ad', 'Telefon', 'Kayıt Tarihi', 'İşlemler'])
        
        # Dinamik sütun genişlikleri
        header = self.kurye_tablo.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ad
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Telefon
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Kayıt Tarihi
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # İşlemler
        self.kurye_tablo.setColumnWidth(4, 300)
        
        layout.addWidget(self.kurye_tablo)
        
        # Sayfalama kontrolleri
        sayfalama_layout = QHBoxLayout()
        self.sayfa_spin = QSpinBox()
        self.sayfa_spin.setMinimum(1)
        self.sayfa_spin.valueChanged.connect(self.kurye_tablo_guncelle)
        self.sayfa_boyut_combo = QComboBox()
        self.sayfa_boyut_combo.addItems(['10', '25', '50', '100'])
        self.sayfa_boyut_combo.currentTextChanged.connect(self.kurye_tablo_guncelle)
        
        sayfalama_layout.addWidget(QLabel('Sayfa:'))
        sayfalama_layout.addWidget(self.sayfa_spin)
        sayfalama_layout.addWidget(QLabel('Sayfa Boyutu:'))
        sayfalama_layout.addWidget(self.sayfa_boyut_combo)
        sayfalama_layout.addStretch()
        
        layout.addLayout(sayfalama_layout)

    def kurye_tablo_guncelle(self):
        try:
            sayfa = self.sayfa_spin.value()
            sayfa_boyutu = int(self.sayfa_boyut_combo.currentText())
            offset = (sayfa - 1) * sayfa_boyutu
            
            # Toplam kayıt sayısını al
            toplam_kayit = self.session.query(Kurye).filter_by(aktif=True).count()
            max_sayfa = (toplam_kayit + sayfa_boyutu - 1) // sayfa_boyutu
            self.sayfa_spin.setMaximum(max(1, max_sayfa))
            
            # Sayfalı veri çek
            kuryeler = self.session.query(Kurye).filter_by(aktif=True)\
                .order_by(Kurye.id.desc())\
                .offset(offset)\
                .limit(sayfa_boyutu)\
                .all()
            
            self.kurye_tablo.setRowCount(len(kuryeler))
            
            for i, kurye in enumerate(kuryeler):
                self.kurye_tablo.setItem(i, 0, QTableWidgetItem(str(kurye.id)))
                self.kurye_tablo.setItem(i, 1, QTableWidgetItem(kurye.ad))
                self.kurye_tablo.setItem(i, 2, QTableWidgetItem(kurye.telefon))
                self.kurye_tablo.setItem(i, 3, QTableWidgetItem(kurye.kayit_tarihi.strftime('%d.%m.%Y %H:%M')))
                
                islemler_widget = QWidget()
                islemler_layout = QHBoxLayout(islemler_widget)
                islemler_layout.setContentsMargins(5, 2, 5, 2)
                
                duzenle_btn = QPushButton('Düzenle')
                duzenle_btn.setMinimumWidth(100)
                duzenle_btn.clicked.connect(lambda checked, k=kurye: self.kurye_duzenle(k.id))
                
                sil_btn = QPushButton('Sil')
                sil_btn.setMinimumWidth(100)
                sil_btn.clicked.connect(lambda checked, k=kurye: self.kurye_sil(k.id))
                
                islemler_layout.addWidget(duzenle_btn)
                islemler_layout.addWidget(sil_btn)
                islemler_layout.addStretch()
                
                self.kurye_tablo.setCellWidget(i, 4, islemler_widget)
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye tablosu güncellenirken hata oluştu: {str(e)}')

    def kurye_ekle(self):
        try:
            yeni_kurye = Kurye(
                ad=self.kurye_ad.text(),
                telefon=self.kurye_telefon.text()
            )
            self.session.add(yeni_kurye)
            self.session.commit()
            
            self.kurye_ad.clear()
            self.kurye_telefon.clear()
            self.kurye_tablo_guncelle()
            
            QMessageBox.information(self, 'Başarılı', 'Kurye başarıyla eklendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye eklenirken hata oluştu: {str(e)}')

    def kurye_sil(self, kurye_id):
        try:
            kurye = self.session.query(Kurye).get(kurye_id)
            kurye.aktif = False
            self.session.commit()
            self.kurye_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Kurye başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye silinirken hata oluştu: {str(e)}')

    def kurye_duzenle(self, kurye_id):
        try:
            kurye = self.session.query(Kurye).get(kurye_id)
            kurye.ad = self.kurye_ad.text()
            kurye.telefon = self.kurye_telefon.text()
            self.session.commit()
            self.kurye_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Kurye başarıyla güncellendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye güncellenirken hata oluştu: {str(e)}')

    def teslimat_tab_olustur(self):
        layout = QVBoxLayout(self.teslimat_tab)
        
        # Teslimat ekleme formu
        form_layout = QHBoxLayout()
        
        self.teslimat_kurye = QComboBox()
        self.kurye_listesi_guncelle()
        self.teslimat_adres = QLineEdit()
        self.teslimat_adres.setPlaceholderText('Teslimat Adresi')
        self.teslimat_musteri_adi = QLineEdit()
        self.teslimat_musteri_adi.setPlaceholderText('Müşteri Adı')
        self.teslimat_musteri_telefon = QLineEdit()
        self.teslimat_musteri_telefon.setPlaceholderText('Müşteri Telefonu')
        self.teslimat_baslangic = QDateTimeEdit()
        self.teslimat_baslangic.setDateTime(QDateTime.currentDateTime())
        
        teslimat_ekle_btn = QPushButton('Teslimat Ekle')
        teslimat_ekle_btn.clicked.connect(self.teslimat_ekle)
        
        form_layout.addWidget(self.teslimat_kurye)
        form_layout.addWidget(self.teslimat_adres)
        form_layout.addWidget(self.teslimat_musteri_adi)
        form_layout.addWidget(self.teslimat_musteri_telefon)
        form_layout.addWidget(self.teslimat_baslangic)
        form_layout.addWidget(teslimat_ekle_btn)
        
        layout.addLayout(form_layout)
        
        # Teslimat tablosu
        self.teslimat_tablo = QTableWidget()
        self.teslimat_tablo.setColumnCount(9)
        self.teslimat_tablo.setHorizontalHeaderLabels(['ID', 'Kurye', 'Müşteri', 'Adres', 'Başlangıç', 'Bitiş', 'Durum', 'Ücret', 'İşlemler'])
        
        # Dinamik sütun genişlikleri
        header = self.teslimat_tablo.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Kurye
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Müşteri
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Adres
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Başlangıç
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Bitiş
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Durum
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Ücret
        header.setSectionResizeMode(8, QHeaderView.Fixed)  # İşlemler
        self.teslimat_tablo.setColumnWidth(8, 300)
        
        layout.addWidget(self.teslimat_tablo)
        
        # Sayfalama kontrolleri
        sayfalama_layout = QHBoxLayout()
        self.teslimat_sayfa_spin = QSpinBox()
        self.teslimat_sayfa_spin.setMinimum(1)
        self.teslimat_sayfa_spin.valueChanged.connect(self.teslimat_tablo_guncelle)
        self.teslimat_sayfa_boyut_combo = QComboBox()
        self.teslimat_sayfa_boyut_combo.addItems(['10', '25', '50', '100'])
        self.teslimat_sayfa_boyut_combo.currentTextChanged.connect(self.teslimat_tablo_guncelle)
        
        sayfalama_layout.addWidget(QLabel('Sayfa:'))
        sayfalama_layout.addWidget(self.teslimat_sayfa_spin)
        sayfalama_layout.addWidget(QLabel('Sayfa Boyutu:'))
        sayfalama_layout.addWidget(self.teslimat_sayfa_boyut_combo)
        sayfalama_layout.addStretch()
        
        layout.addLayout(sayfalama_layout)

    def teslimat_ekle(self):
        try:
            if self.teslimat_kurye.count() == 0:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen önce bir kurye ekleyin!')
                return
                
            kurye_id = self.teslimat_kurye.itemData(self.teslimat_kurye.currentIndex())
            if not kurye_id:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen bir kurye seçin!')
                return
                
            if not self.teslimat_adres.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen teslimat adresini girin!')
                return
                
            if not self.teslimat_musteri_adi.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen müşteri adını girin!')
                return
                
            if not self.teslimat_musteri_telefon.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen müşteri telefonunu girin!')
                return
            
            yeni_teslimat = Teslimat(
                kurye_id=kurye_id,
                adres=self.teslimat_adres.text(),
                musteri_adi=self.teslimat_musteri_adi.text(),
                musteri_telefon=self.teslimat_musteri_telefon.text(),
                baslangic_zamani=self.teslimat_baslangic.dateTime().toPyDateTime()
            )
            self.session.add(yeni_teslimat)
            self.session.commit()
            
            self.teslimat_adres.clear()
            self.teslimat_musteri_adi.clear()
            self.teslimat_musteri_telefon.clear()
            self.teslimat_tablo_guncelle()
            
            QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla eklendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat eklenirken hata oluştu: {str(e)}')

    def teslimat_tamamla(self, teslimat_id, ucret):
        try:
            teslimat = self.session.query(Teslimat).get(teslimat_id)
            teslimat.bitis_zamani = datetime.utcnow()
            teslimat.durum = 'Tamamlandı'
            teslimat.ucret = ucret
            self.session.commit()
            self.teslimat_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla tamamlandı!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat tamamlanırken hata oluştu: {str(e)}')

    def teslimat_sil(self, teslimat_id):
        try:
            teslimat = self.session.query(Teslimat).get(teslimat_id)
            self.session.delete(teslimat)
            self.session.commit()
            self.teslimat_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat silinirken hata oluştu: {str(e)}')

    def teslimat_tablo_guncelle(self):
        try:
            sayfa = self.teslimat_sayfa_spin.value()
            sayfa_boyutu = int(self.teslimat_sayfa_boyut_combo.currentText())
            offset = (sayfa - 1) * sayfa_boyutu
            
            # Toplam kayıt sayısını al
            toplam_kayit = self.session.query(Teslimat).count()
            max_sayfa = (toplam_kayit + sayfa_boyutu - 1) // sayfa_boyutu
            self.teslimat_sayfa_spin.setMaximum(max(1, max_sayfa))
            
            # Sayfalı veri çek
            teslimatlar = self.session.query(Teslimat)\
                .order_by(Teslimat.id.desc())\
                .offset(offset)\
                .limit(sayfa_boyutu)\
                .all()
            
            self.teslimat_tablo.setRowCount(len(teslimatlar))
            
            for i, teslimat in enumerate(teslimatlar):
                self.teslimat_tablo.setItem(i, 0, QTableWidgetItem(str(teslimat.id)))
                self.teslimat_tablo.setItem(i, 1, QTableWidgetItem(teslimat.kurye.ad))
                self.teslimat_tablo.setItem(i, 2, QTableWidgetItem(teslimat.musteri_adi))
                self.teslimat_tablo.setItem(i, 3, QTableWidgetItem(teslimat.adres))
                self.teslimat_tablo.setItem(i, 4, QTableWidgetItem(teslimat.baslangic_zamani.strftime('%d.%m.%Y %H:%M')))
                self.teslimat_tablo.setItem(i, 5, QTableWidgetItem(teslimat.bitis_zamani.strftime('%d.%m.%Y %H:%M') if teslimat.bitis_zamani else '-'))
                self.teslimat_tablo.setItem(i, 6, QTableWidgetItem(teslimat.durum))
                self.teslimat_tablo.setItem(i, 7, QTableWidgetItem(f'₺{teslimat.ucret:.2f}' if teslimat.ucret else '-'))
                
                islemler_widget = QWidget()
                islemler_layout = QHBoxLayout(islemler_widget)
                islemler_layout.setContentsMargins(5, 2, 5, 2)
                
                if teslimat.durum == 'Devam Ediyor':
                    tamamla_btn = QPushButton('Tamamla')
                    tamamla_btn.setMinimumWidth(100)
                    tamamla_btn.clicked.connect(lambda checked, t=teslimat: self.teslimat_tamamla_dialog(t.id))
                    islemler_layout.addWidget(tamamla_btn)
                
                sil_btn = QPushButton('Sil')
                sil_btn.setMinimumWidth(100)
                sil_btn.clicked.connect(lambda checked, t=teslimat: self.teslimat_sil(t.id))
                
                islemler_layout.addWidget(sil_btn)
                islemler_layout.addStretch()
                
                self.teslimat_tablo.setCellWidget(i, 8, islemler_widget)
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat tablosu güncellenirken hata oluştu: {str(e)}')

    def teslimat_tamamla_dialog(self, teslimat_id):
        dialog = QDialog(self)
        dialog.setWindowTitle('Teslimat Tamamla')
        layout = QVBoxLayout(dialog)
        
        ucret_spin = QDoubleSpinBox()
        ucret_spin.setRange(0, 10000)
        ucret_spin.setPrefix('₺')
        layout.addWidget(QLabel('Ücret:'))
        layout.addWidget(ucret_spin)
        
        tamamla_btn = QPushButton('Tamamla')
        tamamla_btn.clicked.connect(lambda: self.teslimat_tamamla(teslimat_id, ucret_spin.value()))
        layout.addWidget(tamamla_btn)
        
        dialog.exec_()

    def kurye_performans_goster(self):
        try:
            kuryeler = self.session.query(Kurye).filter_by(aktif=True).all()
            self.rapor_tablo.setRowCount(len(kuryeler))
            self.rapor_tablo.setColumnCount(4)
            self.rapor_tablo.setHorizontalHeaderLabels(['Kurye', 'Toplam Teslimat', 'Toplam Ücret', 'Ortalama Süre'])
            
            for i, kurye in enumerate(kuryeler):
                try:
                    tamamlanan_teslimatlar = [t for t in kurye.teslimatlar if t.durum == 'Tamamlandı' and t.bitis_zamani is not None]
                    
                    toplam_teslimat = len(tamamlanan_teslimatlar)
                    toplam_ucret = sum(t.ucret for t in tamamlanan_teslimatlar if t.ucret is not None)
                    ortalama_sure = 0
                    
                    if tamamlanan_teslimatlar:
                        toplam_sure = sum(
                            (t.bitis_zamani - t.baslangic_zamani).total_seconds() / 3600
                            for t in tamamlanan_teslimatlar
                            if t.bitis_zamani is not None
                        )
                        ortalama_sure = toplam_sure / toplam_teslimat
                    
                    self.rapor_tablo.setItem(i, 0, QTableWidgetItem(kurye.ad))
                    self.rapor_tablo.setItem(i, 1, QTableWidgetItem(str(toplam_teslimat)))
                    self.rapor_tablo.setItem(i, 2, QTableWidgetItem(f'{toplam_ucret:.2f} TL'))
                    self.rapor_tablo.setItem(i, 3, QTableWidgetItem(f'{ortalama_sure:.2f} saat'))
                except Exception as e:
                    QMessageBox.warning(self, 'Uyarı', f'Kurye {kurye.ad} için performans hesaplanırken hata oluştu: {str(e)}')
                    continue
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Performans raporu oluşturulurken hata oluştu: {str(e)}')
            self.rapor_tablo.setRowCount(0)
            self.rapor_tablo.setColumnCount(0)

    def teslimat_istatistikleri_goster(self):
        bugun = datetime.now().date()
        hafta_basi = bugun - timedelta(days=bugun.weekday())
        ay_basi = bugun.replace(day=1)
        
        gunluk_teslimatlar = self.session.query(Teslimat).filter(
            func.date(Teslimat.baslangic_zamani) == bugun
        ).all()
        
        haftalik_teslimatlar = self.session.query(Teslimat).filter(
            func.date(Teslimat.baslangic_zamani) >= hafta_basi
        ).all()
        
        aylik_teslimatlar = self.session.query(Teslimat).filter(
            func.date(Teslimat.baslangic_zamani) >= ay_basi
        ).all()
        
        self.rapor_tablo.setRowCount(3)
        self.rapor_tablo.setColumnCount(3)
        self.rapor_tablo.setHorizontalHeaderLabels(['Periyot', 'Toplam Teslimat', 'Toplam Ücret'])
        
        # Günlük istatistikler
        self.rapor_tablo.setItem(0, 0, QTableWidgetItem('Günlük'))
        self.rapor_tablo.setItem(0, 1, QTableWidgetItem(str(len(gunluk_teslimatlar))))
        self.rapor_tablo.setItem(0, 2, QTableWidgetItem(f"{sum(t.ucret for t in gunluk_teslimatlar if t.ucret):.2f} TL"))
        
        # Haftalık istatistikler
        self.rapor_tablo.setItem(1, 0, QTableWidgetItem('Haftalık'))
        self.rapor_tablo.setItem(1, 1, QTableWidgetItem(str(len(haftalik_teslimatlar))))
        self.rapor_tablo.setItem(1, 2, QTableWidgetItem(f"{sum(t.ucret for t in haftalik_teslimatlar if t.ucret):.2f} TL"))
        
        # Aylık istatistikler
        self.rapor_tablo.setItem(2, 0, QTableWidgetItem('Aylık'))
        self.rapor_tablo.setItem(2, 1, QTableWidgetItem(str(len(aylik_teslimatlar))))
        self.rapor_tablo.setItem(2, 2, QTableWidgetItem(f"{sum(t.ucret for t in aylik_teslimatlar if t.ucret):.2f} TL"))

    def rapor_tab_olustur(self):
        layout = QVBoxLayout(self.rapor_tab)
        
        # Rapor butonları
        btn_layout = QHBoxLayout()
        
        kurye_rapor_btn = QPushButton('Kurye Performans Raporu')
        kurye_rapor_btn.clicked.connect(self.kurye_performans_goster)
        
        teslimat_rapor_btn = QPushButton('Teslimat İstatistikleri')
        teslimat_rapor_btn.clicked.connect(self.teslimat_istatistikleri_goster)
        
        btn_layout.addWidget(kurye_rapor_btn)
        btn_layout.addWidget(teslimat_rapor_btn)
        
        layout.addLayout(btn_layout)
        
        # Rapor tablosu
        self.rapor_tablo = QTableWidget()
        layout.addWidget(self.rapor_tablo)

    def gider_tab_olustur(self):
        layout = QVBoxLayout(self.gider_tab)
        
        # Gider ekleme formu
        form_layout = QHBoxLayout()
        
        self.gider_kurye = QComboBox()
        self.kurye_listesi_guncelle()
        self.gider_aciklama = QLineEdit()
        self.gider_aciklama.setPlaceholderText('Gider Açıklaması')
        self.gider_miktar = QDoubleSpinBox()
        self.gider_miktar.setRange(0, 10000)
        self.gider_miktar.setPrefix('₺')
        
        gider_ekle_btn = QPushButton('Gider Ekle')
        gider_ekle_btn.clicked.connect(self.gider_ekle)
        
        form_layout.addWidget(self.gider_kurye)
        form_layout.addWidget(self.gider_aciklama)
        form_layout.addWidget(self.gider_miktar)
        form_layout.addWidget(gider_ekle_btn)
        
        layout.addLayout(form_layout)
        
        # Gider tablosu
        self.gider_tablo = QTableWidget()
        self.gider_tablo.setColumnCount(6)
        self.gider_tablo.setHorizontalHeaderLabels(['ID', 'Kurye', 'Tarih', 'Açıklama', 'Miktar', 'İşlemler'])
        
        # Dinamik sütun genişlikleri
        header = self.gider_tablo.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Kurye
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Tarih
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Açıklama
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Miktar
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # İşlemler
        self.gider_tablo.setColumnWidth(5, 150)
        
        layout.addWidget(self.gider_tablo)
        
        # Sayfalama kontrolleri
        sayfalama_layout = QHBoxLayout()
        self.gider_sayfa_spin = QSpinBox()
        self.gider_sayfa_spin.setMinimum(1)
        self.gider_sayfa_spin.valueChanged.connect(self.gider_tablo_guncelle)
        self.gider_sayfa_boyut_combo = QComboBox()
        self.gider_sayfa_boyut_combo.addItems(['10', '25', '50', '100'])
        self.gider_sayfa_boyut_combo.currentTextChanged.connect(self.gider_tablo_guncelle)
        
        sayfalama_layout.addWidget(QLabel('Sayfa:'))
        sayfalama_layout.addWidget(self.gider_sayfa_spin)
        sayfalama_layout.addWidget(QLabel('Sayfa Boyutu:'))
        sayfalama_layout.addWidget(self.gider_sayfa_boyut_combo)
        sayfalama_layout.addStretch()
        
        layout.addLayout(sayfalama_layout)
        
        # İlk güncellemeyi yap
        self.gider_tablo_guncelle()

    def gider_ekle(self):
        try:
            if self.gider_kurye.count() == 0:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen önce bir kurye ekleyin!')
                return
                
            kurye_id = self.gider_kurye.itemData(self.gider_kurye.currentIndex())
            if not kurye_id:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen bir kurye seçin!')
                return
                
            if not self.gider_aciklama.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen gider açıklaması girin!')
                return
            
            yeni_gider = KuryeGider(
                kurye_id=kurye_id,
                aciklama=self.gider_aciklama.text(),
                miktar=self.gider_miktar.value()
            )
            self.session.add(yeni_gider)
            self.session.commit()
            
            self.gider_aciklama.clear()
            self.gider_miktar.setValue(0)
            self.gider_tablo_guncelle()
            
            QMessageBox.information(self, 'Başarılı', 'Gider başarıyla eklendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Gider eklenirken hata oluştu: {str(e)}')

    def gider_sil(self, gider_id):
        try:
            gider = self.session.query(KuryeGider).get(gider_id)
            self.session.delete(gider)
            self.session.commit()
            self.gider_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Gider başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Gider silinirken hata oluştu: {str(e)}')

    def gider_tablo_guncelle(self):
        try:
            sayfa = self.gider_sayfa_spin.value()
            sayfa_boyutu = int(self.gider_sayfa_boyut_combo.currentText())
            offset = (sayfa - 1) * sayfa_boyutu
            
            # Toplam kayıt sayısını al
            toplam_kayit = self.session.query(KuryeGider).count()
            max_sayfa = (toplam_kayit + sayfa_boyutu - 1) // sayfa_boyutu
            self.gider_sayfa_spin.setMaximum(max(1, max_sayfa))
            
            # Sayfalı veri çek
            giderler = self.session.query(KuryeGider)\
                .order_by(KuryeGider.id.desc())\
                .offset(offset)\
                .limit(sayfa_boyutu)\
                .all()
            
            self.gider_tablo.setRowCount(len(giderler))
            
            for i, gider in enumerate(giderler):
                self.gider_tablo.setItem(i, 0, QTableWidgetItem(str(gider.id)))
                self.gider_tablo.setItem(i, 1, QTableWidgetItem(gider.kurye.ad))
                self.gider_tablo.setItem(i, 2, QTableWidgetItem(gider.tarih.strftime('%d.%m.%Y %H:%M')))
                self.gider_tablo.setItem(i, 3, QTableWidgetItem(gider.aciklama))
                self.gider_tablo.setItem(i, 4, QTableWidgetItem(f'₺{gider.miktar:.2f}'))
                
                islemler_widget = QWidget()
                islemler_layout = QHBoxLayout(islemler_widget)
                islemler_layout.setContentsMargins(5, 2, 5, 2)
                
                sil_btn = QPushButton('Sil')
                sil_btn.setMinimumWidth(100)
                sil_btn.clicked.connect(lambda checked, g=gider: self.gider_sil(g.id))
                
                islemler_layout.addWidget(sil_btn)
                islemler_layout.addStretch()
                
                self.gider_tablo.setCellWidget(i, 5, islemler_widget)
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Gider tablosu güncellenirken hata oluştu: {str(e)}')

    def kurye_listesi_guncelle(self):
        try:
            # Teslimat kurye listesini güncelle
            if hasattr(self, 'teslimat_kurye'):
                self.teslimat_kurye.clear()
                
            # Gider kurye listesini güncelle
            if hasattr(self, 'gider_kurye'):
                self.gider_kurye.clear()
            
            kuryeler = self.session.query(Kurye).filter_by(aktif=True).all()
            
            if hasattr(self, 'teslimat_kurye'):
                for kurye in kuryeler:
                    self.teslimat_kurye.addItem(kurye.ad, kurye.id)
                    
            if hasattr(self, 'gider_kurye'):
                for kurye in kuryeler:
                    self.gider_kurye.addItem(kurye.ad, kurye.id)
                    
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye listesi güncellenirken hata oluştu: {str(e)}')

    def giris_yapildi(self):
        try:
            # Ana ekrana geç
            self.stacked_widget.setCurrentIndex(1)
            
            # Eğer yönetici tab'ı zaten varsa kaldır
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Yönetici Paneli":
                    self.tab_widget.removeTab(i)
                    break
            
            # Yönetici panelini oluştur
            self.yonetici_tab = YoneticiPanel(self)
            
            # Tab widget'a yönetici panelini ekle
            self.tab_widget.addTab(self.yonetici_tab, "Yönetici Paneli")
            
            # Yönetici listesini göster
            self.yonetici_tab.yonetici_listesi_goster()
            
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Giriş yapılırken hata oluştu: {str(e)}')
            self.yonetici = None
            self.stacked_widget.setCurrentIndex(0)  # Giriş ekranına geri dön

    def closeEvent(self, event):
        self.session.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KuryeTakipUygulamasi()
    window.show()
    sys.exit(app.exec_()) 