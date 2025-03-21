import sys
import hashlib
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTableWidget, QTableWidgetItem, QComboBox, 
                           QMessageBox, QTabWidget, QDateTimeEdit, QSpinBox,
                           QDoubleSpinBox, QDialog, QStackedWidget, QHeaderView,
                           QFormLayout)
from PyQt5.QtCore import Qt, QDateTime, QSizeF
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument, QPageSize
from PyQt5.QtWebEngineWidgets import QWebEngineView
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
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

class Musteri(Base):
    __tablename__ = 'musteri'
    id = Column(Integer, primary_key=True)
    ad_soyad = Column(String(100), nullable=False)
    telefon = Column(String(20), nullable=False)
    adres = Column(String(200), nullable=False)
    kayit_tarihi = Column(DateTime, default=datetime.utcnow)
    aktif = Column(Boolean, default=True)
    urun_adi = Column(String(100), nullable=True)
    ucret = Column(Float, default=0.0)

class Teslimat(Base):
    __tablename__ = 'teslimat'
    id = Column(Integer, primary_key=True)
    kurye_id = Column(Integer, ForeignKey('kurye.id'), nullable=False)
    musteri_id = Column(Integer, ForeignKey('musteri.id'), nullable=True)
    adres = Column(String(200), nullable=False)
    telefon = Column(String(20), nullable=False)  # Müşteri telefonu
    urun_adi = Column(String(100), nullable=False)  # Ürün adı
    tarih = Column(DateTime, default=datetime.utcnow)
    durum = Column(String(20), default='Devam Ediyor')
    ucret = Column(Float, default=0.0)
    kurye = relationship('Kurye', backref='teslimatlar')
    musteri = relationship('Musteri', backref='teslimatlar')

class KuryeGider(Base):
    __tablename__ = 'kurye_gider'
    id = Column(Integer, primary_key=True)
    kurye_id = Column(Integer, ForeignKey('kurye.id'), nullable=False)
    tarih = Column(DateTime, default=datetime.utcnow)
    aciklama = Column(String(200), nullable=False)
    miktar = Column(Float, nullable=False)
    kurye = relationship('Kurye', backref='giderler')

class GirisEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        # Ana layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Başlık ve logo alanı
        baslik_container = QWidget()
        baslik_layout = QVBoxLayout()
        baslik_container.setLayout(baslik_layout)
        
        # Logo (metin olarak)
        logo = QLabel('🏠')
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet('''
            font-size: 48px;
            margin-bottom: 10px;
            color: #e74c3c;
        ''')
        
        # Başlık
        baslik = QLabel('EVİM DÖNER\nKurye Takip Sistemi')
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet('''
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px 0;
        ''')
        
        baslik_layout.addWidget(logo)
        baslik_layout.addWidget(baslik)
        layout.addWidget(baslik_container)
        
        # Form container
        form_container = QWidget()
        form_container.setStyleSheet('''
            QWidget {
                background: white;
                border-radius: 10px;
                padding: 20px;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                font-size: 14px;
                margin-top: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                font-weight: bold;
            }
        ''')
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Kullanıcı adı
        self.kullanici_adi = QLineEdit()
        self.kullanici_adi.setPlaceholderText('Kullanıcı adınızı girin')
        self.kullanici_adi.setMinimumHeight(45)
        form_layout.addRow('Kullanıcı Adı:', self.kullanici_adi)
        
        # Şifre
        self.sifre = QLineEdit()
        self.sifre.setPlaceholderText('Şifrenizi girin')
        self.sifre.setEchoMode(QLineEdit.Password)
        self.sifre.setMinimumHeight(45)
        form_layout.addRow('Şifre:', self.sifre)
        
        form_container.setLayout(form_layout)
        layout.addWidget(form_container)
        
        # Giriş butonu
        self.giris_btn = QPushButton('Giriş Yap')
        self.giris_btn.setCursor(Qt.PointingHandCursor)
        self.giris_btn.clicked.connect(self.giris_yap)
        self.giris_btn.setMinimumHeight(50)
        self.giris_btn.setStyleSheet('''
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        ''')
        layout.addWidget(self.giris_btn)
        
        # Telif hakkı yazısı
        telif = QLabel('© 2024 EVİM DÖNER. Tüm hakları saklıdır.')
        telif.setAlignment(Qt.AlignCenter)
        telif.setStyleSheet('''
            color: #95a5a6;
            font-size: 12px;
            margin-top: 20px;
        ''')
        layout.addWidget(telif)
        
        # Ana widget'ın arka plan rengini ve stilini ayarla
        self.setStyleSheet('''
            QWidget {
                background-color: #f5f6fa;
            }
        ''')
        
        # Layout'u ayarla
        self.setLayout(layout)

    def giris_yap(self):
        try:
            kullanici_adi = self.kullanici_adi.text().strip()
            sifre = self.sifre.text().strip()
            
            if not kullanici_adi or not sifre:
                QMessageBox.warning(self, 'Uyarı', 'Kullanıcı adı ve şifre boş bırakılamaz!')
                return
            
            yonetici = self.parent.session.query(Yonetici).filter_by(kullanici_adi=kullanici_adi).first()
            
            if yonetici and yonetici.sifre_kontrol(sifre):
                self.parent.giris_yapildi()
            else:
                QMessageBox.warning(self, 'Hata', 'Kullanıcı adı veya şifre hatalı!')
                self.sifre.clear()
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Giriş yapılırken bir hata oluştu: {str(e)}')

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
            yonetici = self.parent.session.get(Yonetici, yonetici_id)
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
        
        try:
            # Veritabanı bağlantısı
            self.engine = create_engine('sqlite:///kurye.db', echo=True)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            
            # İlk yöneticiyi oluştur
            self.ilk_yonetici_olustur()
            
            # Ana widget ve layout
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.main_layout = QVBoxLayout()
            self.central_widget.setLayout(self.main_layout)
            
            # Stacked widget
            self.stacked_widget = QStackedWidget()
            self.main_layout.addWidget(self.stacked_widget)
            
            # Giriş ekranı
            self.giris_ekrani = GirisEkrani(self)
            self.stacked_widget.addWidget(self.giris_ekrani)
            
            # Ana ekran
            self.ana_ekran = QWidget()
            self.ana_ekran_layout = QVBoxLayout()
            self.ana_ekran.setLayout(self.ana_ekran_layout)
            
            # Tab widget
            self.tab_widget = QTabWidget()
            self.kurye_tab = QWidget()
            self.teslimat_tab = QWidget()
            self.rapor_tab = QWidget()
            self.gider_tab = QWidget()
            self.musteri_tab = QWidget()
            
            self.tab_widget.addTab(self.kurye_tab, "Kuryeler")
            self.tab_widget.addTab(self.teslimat_tab, "Teslimatlar")
            self.tab_widget.addTab(self.rapor_tab, "Raporlar")
            self.tab_widget.addTab(self.gider_tab, "Giderler")
            self.tab_widget.addTab(self.musteri_tab, "Müşteriler")
            
            self.ana_ekran_layout.addWidget(self.tab_widget)
            
            # İmza
            imza = QLabel('Uygulamayı geliştiren Baran Akbulut iyi günler dilerim')
            imza.setStyleSheet('color: #666; font-style: italic; margin: 10px; text-align: center;')
            self.ana_ekran_layout.addWidget(imza)
            
            self.stacked_widget.addWidget(self.ana_ekran)
            
            # Tab içeriklerini oluştur
            self.kurye_tab_olustur()
            self.teslimat_tab_olustur()
            self.rapor_tab_olustur()
            self.gider_tab_olustur()
            self.musteri_tab_olustur()
            
            # Tabloları güncelle
            self.kurye_tablo_guncelle()
            self.teslimat_tablo_guncelle()
            
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Uygulama başlatılırken hata oluştu: {str(e)}')
            sys.exit(1)

    def ilk_yonetici_olustur(self):
        try:
            yonetici = self.session.query(Yonetici).first()
            if not yonetici:
                ilk_yonetici = Yonetici(
                    kullanici_adi='admin',
                    ad_soyad='Sistem Yöneticisi'
                )
                ilk_yonetici.sifre_belirle('admin123')
                self.session.add(ilk_yonetici)
                self.session.commit()
        except Exception as e:
            print(f"İlk yönetici oluşturma hatası: {str(e)}")

    def giris_yapildi(self):
        try:
            self.stacked_widget.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Giriş yapılırken hata oluştu: {str(e)}')
            self.stacked_widget.setCurrentIndex(0)

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
            kurye = self.session.get(Kurye, kurye_id)
            kurye.aktif = False
            self.session.commit()
            self.kurye_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Kurye başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye silinirken hata oluştu: {str(e)}')

    def kurye_duzenle(self, kurye_id):
        try:
            kurye = self.session.get(Kurye, kurye_id)
            if not kurye:
                QMessageBox.warning(self, 'Uyarı', 'Kurye bulunamadı!')
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle('Kurye Düzenle')
            layout = QVBoxLayout(dialog)
            
            # Adı girişi
            ad_edit = QLineEdit()
            ad_edit.setText(kurye.ad)
            layout.addWidget(QLabel('Adı:'))
            layout.addWidget(ad_edit)
            
            # Telefon girişi
            telefon_edit = QLineEdit()
            telefon_edit.setText(kurye.telefon)
            layout.addWidget(QLabel('Telefon:'))
            layout.addWidget(telefon_edit)
            
            # Kaydet butonu
            kaydet_btn = QPushButton('Kaydet')
            kaydet_btn.clicked.connect(lambda: self.kurye_guncelle(
                kurye_id,
                ad_edit.text(),
                telefon_edit.text(),
                dialog
            ))
            layout.addWidget(kaydet_btn)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye düzenlenirken hata oluştu: {str(e)}')

    def kurye_guncelle(self, kurye_id, ad, telefon, dialog):
        try:
            kurye = self.session.get(Kurye, kurye_id)
            if not kurye:
                QMessageBox.warning(self, 'Uyarı', 'Kurye bulunamadı!')
                return
            
            kurye.ad = ad
            kurye.telefon = telefon
            self.session.commit()
            self.kurye_tablo_guncelle()
            dialog.accept()
            QMessageBox.information(self, 'Başarılı', 'Kurye başarıyla güncellendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Kurye güncellenirken hata oluştu: {str(e)}')

    def teslimat_tab_olustur(self):
        layout = QVBoxLayout()
        
        # Teslimat ekleme formu
        form_layout = QHBoxLayout()
        
        # Kurye seçimi
        self.teslimat_kurye = QComboBox()
        self.teslimat_kurye.setMinimumWidth(200)
        self.kurye_listesi_guncelle()
        form_layout.addWidget(QLabel('Kurye:'))
        form_layout.addWidget(self.teslimat_kurye)
        
        # Ürün adı girişi
        self.teslimat_urun = QLineEdit()
        self.teslimat_urun.setPlaceholderText('Ürün Adı')
        self.teslimat_urun.setMinimumWidth(150)
        form_layout.addWidget(QLabel('Ürün:'))
        form_layout.addWidget(self.teslimat_urun)
        
        # Adres girişi
        self.teslimat_adres = QLineEdit()
        self.teslimat_adres.setPlaceholderText('Teslimat Adresi')
        self.teslimat_adres.setMinimumWidth(300)
        form_layout.addWidget(QLabel('Adres:'))
        form_layout.addWidget(self.teslimat_adres)
        
        # Telefon girişi
        self.teslimat_telefon = QLineEdit()
        self.teslimat_telefon.setPlaceholderText('Müşteri Telefonu')
        self.teslimat_telefon.setMinimumWidth(150)
        form_layout.addWidget(QLabel('Telefon:'))
        form_layout.addWidget(self.teslimat_telefon)
        
        # Teslimat ekle butonu
        teslimat_ekle_btn = QPushButton('Teslimat Ekle')
        teslimat_ekle_btn.clicked.connect(self.teslimat_ekle)
        form_layout.addWidget(teslimat_ekle_btn)
        
        # Yazdır butonu
        yazdir_btn = QPushButton('Teslimatı Yazdır')
        yazdir_btn.clicked.connect(self.teslimat_yazdir)
        yazdir_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        form_layout.addWidget(yazdir_btn)
        
        layout.addLayout(form_layout)
        
        # Teslimat listesi
        self.teslimat_tablo = QTableWidget()
        self.teslimat_tablo.setColumnCount(9)
        self.teslimat_tablo.setHorizontalHeaderLabels(['ID', 'Kurye', 'Ürün', 'Adres', 'Telefon', 'Tarih', 'Durum', 'Ücret', 'İşlemler'])
        self.teslimat_tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.teslimat_tablo.setSelectionBehavior(QTableWidget.SelectRows)
        self.teslimat_tablo.setSelectionMode(QTableWidget.SingleSelection)
        
        layout.addWidget(self.teslimat_tablo)
        
        # Sayfalama
        sayfalama_layout = QHBoxLayout()
        self.teslimat_sayfa = QSpinBox()
        self.teslimat_sayfa.setRange(1, 1)
        self.teslimat_sayfa.valueChanged.connect(self.teslimat_tablo_guncelle)
        sayfalama_layout.addWidget(QLabel('Sayfa:'))
        sayfalama_layout.addWidget(self.teslimat_sayfa)
        
        self.teslimat_sayfa_boyut = QComboBox()
        self.teslimat_sayfa_boyut.addItems(['10', '25', '50', '100'])
        self.teslimat_sayfa_boyut.currentTextChanged.connect(self.teslimat_tablo_guncelle)
        sayfalama_layout.addWidget(QLabel('Sayfa Boyutu:'))
        sayfalama_layout.addWidget(self.teslimat_sayfa_boyut)
        
        layout.addLayout(sayfalama_layout)
        
        # Layout'u teslimat tab'ına uygula
        self.teslimat_tab.setLayout(layout)
        
        # İlk güncellemeyi yap
        self.teslimat_tablo_guncelle()

    def teslimat_ekle(self):
        try:
            if self.teslimat_kurye.count() == 0:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen önce bir kurye ekleyin!')
                return
                
            kurye_id = self.teslimat_kurye.itemData(self.teslimat_kurye.currentIndex())
            if not kurye_id:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen bir kurye seçin!')
                return
                
            if not self.teslimat_urun.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen ürün adını girin!')
                return
                
            if not self.teslimat_adres.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen teslimat adresini girin!')
                return
                
            if not self.teslimat_telefon.text():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen müşteri telefonunu girin!')
                return
            
            # Ücret girişi dialogu
            dialog = QDialog(self)
            dialog.setWindowTitle('Teslimat Ücreti')
            layout = QVBoxLayout(dialog)
            
            ucret_spin = QDoubleSpinBox()
            ucret_spin.setRange(0, 10000)
            ucret_spin.setPrefix('₺')
            ucret_spin.setSpecialValueText('₺')
            layout.addWidget(QLabel('Ücret:'))
            layout.addWidget(ucret_spin)
            
            kaydet_btn = QPushButton('Kaydet')
            kaydet_btn.clicked.connect(lambda: self.teslimat_kaydet(
                kurye_id,
                self.teslimat_adres.text(),
                self.teslimat_telefon.text(),
                self.teslimat_urun.text(),
                ucret_spin.value(),
                dialog
            ))
            layout.addWidget(kaydet_btn)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat eklenirken hata oluştu: {str(e)}')

    def teslimat_kaydet(self, kurye_id, adres, telefon, urun_adi, ucret, dialog):
        try:
            yeni_teslimat = Teslimat(
                kurye_id=kurye_id,
                musteri_id=None,  # Müşteri ID'si opsiyonel
                adres=adres,
                telefon=telefon,
                urun_adi=urun_adi,
                durum='Tamamlandı',
                ucret=ucret
            )
            self.session.add(yeni_teslimat)
            self.session.flush()  # Değişiklikleri veritabanına yansıt
            self.session.commit()  # Değişiklikleri kaydet
            
            self.teslimat_adres.clear()
            self.teslimat_telefon.clear()
            self.teslimat_urun.clear()
            self.teslimat_tablo_guncelle()
            dialog.accept()
            
            QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla eklendi!')
        except Exception as e:
            self.session.rollback()  # Hata durumunda değişiklikleri geri al
            QMessageBox.critical(self, 'Hata', f'Teslimat eklenirken hata oluştu: {str(e)}')

    def teslimat_tablo_guncelle(self):
        try:
            sayfa = self.teslimat_sayfa.value()
            sayfa_boyutu = int(self.teslimat_sayfa_boyut.currentText())
            offset = (sayfa - 1) * sayfa_boyutu
            
            # Toplam kayıt sayısını al
            toplam_kayit = self.session.query(Teslimat).count()
            max_sayfa = (toplam_kayit + sayfa_boyutu - 1) // sayfa_boyutu
            self.teslimat_sayfa.setMaximum(max(1, max_sayfa))
            
            # Sayfalı veri çek
            teslimatlar = self.session.query(Teslimat)\
                .join(Kurye)\
                .order_by(Teslimat.id.desc())\
                .offset(offset)\
                .limit(sayfa_boyutu)\
                .all()
            
            self.teslimat_tablo.setRowCount(len(teslimatlar))
            
            for i, teslimat in enumerate(teslimatlar):
                self.teslimat_tablo.setItem(i, 0, QTableWidgetItem(str(teslimat.id)))
                self.teslimat_tablo.setItem(i, 1, QTableWidgetItem(teslimat.kurye.ad))
                self.teslimat_tablo.setItem(i, 2, QTableWidgetItem(teslimat.urun_adi))
                self.teslimat_tablo.setItem(i, 3, QTableWidgetItem(teslimat.adres))
                self.teslimat_tablo.setItem(i, 4, QTableWidgetItem(teslimat.telefon))
                self.teslimat_tablo.setItem(i, 5, QTableWidgetItem(teslimat.tarih.strftime('%d.%m.%Y %H:%M')))
                self.teslimat_tablo.setItem(i, 6, QTableWidgetItem(teslimat.durum))
                self.teslimat_tablo.setItem(i, 7, QTableWidgetItem(f'₺{teslimat.ucret:.2f}'))
                
                islemler_widget = QWidget()
                islemler_layout = QHBoxLayout(islemler_widget)
                islemler_layout.setContentsMargins(5, 2, 5, 2)
                
                duzenle_btn = QPushButton('Düzenle')
                duzenle_btn.setMinimumWidth(100)
                duzenle_btn.clicked.connect(lambda checked, t=teslimat: self.teslimat_duzenle(t.id))
                
                islemler_layout.addWidget(duzenle_btn)
                
                sil_btn = QPushButton('Sil')
                sil_btn.setMinimumWidth(100)
                sil_btn.clicked.connect(lambda checked, t=teslimat: self.teslimat_sil(t.id))
                
                islemler_layout.addWidget(sil_btn)
                islemler_layout.addStretch()
                
                self.teslimat_tablo.setCellWidget(i, 8, islemler_widget)
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat tablosu güncellenirken hata oluştu: {str(e)}')
            self.teslimat_tablo.setRowCount(0)

    def teslimat_sil(self, teslimat_id):
        try:
            teslimat = self.session.get(Teslimat, teslimat_id)
            self.session.delete(teslimat)
            self.session.commit()
            self.teslimat_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat silinirken hata oluştu: {str(e)}')

    def teslimat_duzenle(self, teslimat_id):
        try:
            teslimat = self.session.get(Teslimat, teslimat_id)
            if not teslimat:
                QMessageBox.warning(self, 'Uyarı', 'Teslimat bulunamadı!')
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle('Teslimat Düzenle')
            layout = QVBoxLayout(dialog)
            
            # Kurye seçimi
            kurye_combo = QComboBox()
            kurye_combo.setMinimumWidth(200)
            kuryeler = self.session.query(Kurye).filter_by(aktif=True).all()
            for kurye in kuryeler:
                kurye_combo.addItem(kurye.ad, kurye.id)
            kurye_combo.setCurrentText(teslimat.kurye.ad)
            layout.addWidget(QLabel('Kurye:'))
            layout.addWidget(kurye_combo)
            
            # Ürün adı girişi
            urun_edit = QLineEdit()
            urun_edit.setText(teslimat.urun_adi)
            layout.addWidget(QLabel('Ürün:'))
            layout.addWidget(urun_edit)
            
            # Adres girişi
            adres_edit = QLineEdit()
            adres_edit.setText(teslimat.adres)
            layout.addWidget(QLabel('Adres:'))
            layout.addWidget(adres_edit)
            
            # Telefon girişi
            telefon_edit = QLineEdit()
            telefon_edit.setText(teslimat.telefon)
            layout.addWidget(QLabel('Telefon:'))
            layout.addWidget(telefon_edit)
            
            # Ücret girişi
            ucret_spin = QDoubleSpinBox()
            ucret_spin.setRange(0, 10000)
            ucret_spin.setPrefix('₺')
            ucret_spin.setValue(teslimat.ucret)
            layout.addWidget(QLabel('Ücret:'))
            layout.addWidget(ucret_spin)
            
            # Kaydet butonu
            kaydet_btn = QPushButton('Kaydet')
            kaydet_btn.clicked.connect(lambda: self.teslimat_guncelle(
                teslimat_id,
                kurye_combo.itemData(kurye_combo.currentIndex()),
                adres_edit.text(),
                telefon_edit.text(),
                urun_edit.text(),
                ucret_spin.value(),
                dialog
            ))
            layout.addWidget(kaydet_btn)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat düzenlenirken hata oluştu: {str(e)}')

    def teslimat_guncelle(self, teslimat_id, kurye_id, adres, telefon, urun_adi, ucret, dialog):
        try:
            teslimat = self.session.get(Teslimat, teslimat_id)
            if not teslimat:
                QMessageBox.warning(self, 'Uyarı', 'Teslimat bulunamadı!')
                return
            
            teslimat.kurye_id = kurye_id
            teslimat.adres = adres
            teslimat.telefon = telefon
            teslimat.urun_adi = urun_adi
            teslimat.ucret = ucret
            self.session.commit()
            self.teslimat_tablo_guncelle()
            dialog.accept()
            QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla güncellendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat güncellenirken hata oluştu: {str(e)}')

    def kurye_performans_goster(self):
        try:
            kuryeler = self.session.query(Kurye).filter_by(aktif=True).all()
            self.rapor_tablo.setRowCount(len(kuryeler))
            self.rapor_tablo.setColumnCount(4)
            self.rapor_tablo.setHorizontalHeaderLabels(['Kurye', 'Toplam Teslimat', 'Toplam Ücret', 'Ortalama Süre'])
            
            for i, kurye in enumerate(kuryeler):
                try:
                    tamamlanan_teslimatlar = [t for t in kurye.teslimatlar if t.durum == 'Tamamlandı']
                    
                    toplam_teslimat = len(tamamlanan_teslimatlar)
                    toplam_ucret = sum(t.ucret for t in tamamlanan_teslimatlar if t.ucret is not None)
                    
                    self.rapor_tablo.setItem(i, 0, QTableWidgetItem(kurye.ad))
                    self.rapor_tablo.setItem(i, 1, QTableWidgetItem(str(toplam_teslimat)))
                    self.rapor_tablo.setItem(i, 2, QTableWidgetItem(f'{toplam_ucret:.2f} TL'))
                    self.rapor_tablo.setItem(i, 3, QTableWidgetItem('--'))
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
            func.date(Teslimat.tarih) == bugun
        ).all()
        
        haftalik_teslimatlar = self.session.query(Teslimat).filter(
            func.date(Teslimat.tarih) >= hafta_basi
        ).all()
        
        aylik_teslimatlar = self.session.query(Teslimat).filter(
            func.date(Teslimat.tarih) >= ay_basi
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
        self.gider_kurye.setMinimumWidth(200)
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
            gider = self.session.get(KuryeGider, gider_id)
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

    def musteri_tab_olustur(self):
        layout = QVBoxLayout(self.musteri_tab)
        
        # Müşteri ekleme formu
        form_layout = QHBoxLayout()
        
        self.musteri_ad = QLineEdit()
        self.musteri_ad.setPlaceholderText('Ad Soyad')
        self.musteri_telefon = QLineEdit()
        self.musteri_telefon.setPlaceholderText('Telefon')
        self.musteri_adres = QLineEdit()
        self.musteri_adres.setPlaceholderText('Adres')
        
        musteri_ekle_btn = QPushButton('Müşteri Ekle')
        musteri_ekle_btn.clicked.connect(self.musteri_ekle)
        
        form_layout.addWidget(self.musteri_ad)
        form_layout.addWidget(self.musteri_telefon)
        form_layout.addWidget(self.musteri_adres)
        form_layout.addWidget(musteri_ekle_btn)
        
        layout.addLayout(form_layout)
        
        # Müşteri tablosu
        self.musteri_tablo = QTableWidget()
        self.musteri_tablo.setColumnCount(8)
        self.musteri_tablo.setHorizontalHeaderLabels(['ID', 'Ad Soyad', 'Telefon', 'Adres', 'Kayıt Tarihi', 'Ürün', 'Ücret', 'İşlemler'])
        
        # Dinamik sütun genişlikleri
        header = self.musteri_tablo.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ad Soyad
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Telefon
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Adres
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Kayıt Tarihi
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Ürün
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Ücret
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # İşlemler
        self.musteri_tablo.setColumnWidth(7, 300)
        
        layout.addWidget(self.musteri_tablo)
        
        # Sayfalama kontrolleri
        sayfalama_layout = QHBoxLayout()
        self.musteri_sayfa_spin = QSpinBox()
        self.musteri_sayfa_spin.setMinimum(1)
        self.musteri_sayfa_spin.valueChanged.connect(self.musteri_tablo_guncelle)
        self.musteri_sayfa_boyut_combo = QComboBox()
        self.musteri_sayfa_boyut_combo.addItems(['10', '25', '50', '100'])
        self.musteri_sayfa_boyut_combo.currentTextChanged.connect(self.musteri_tablo_guncelle)
        
        sayfalama_layout.addWidget(QLabel('Sayfa:'))
        sayfalama_layout.addWidget(self.musteri_sayfa_spin)
        sayfalama_layout.addWidget(QLabel('Sayfa Boyutu:'))
        sayfalama_layout.addWidget(self.musteri_sayfa_boyut_combo)
        sayfalama_layout.addStretch()
        
        layout.addLayout(sayfalama_layout)
        
        # İlk güncellemeyi yap
        self.musteri_tablo_guncelle()

    def musteri_ekle(self):
        try:
            if not self.musteri_ad.text().strip():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen müşteri adını girin!')
                return
                
            if not self.musteri_telefon.text().strip():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen müşteri telefonunu girin!')
                return
                
            if not self.musteri_adres.text().strip():
                QMessageBox.warning(self, 'Uyarı', 'Lütfen müşteri adresini girin!')
                return
            
            yeni_musteri = Musteri(
                ad_soyad=self.musteri_ad.text().strip(),
                telefon=self.musteri_telefon.text().strip(),
                adres=self.musteri_adres.text().strip()
            )
            self.session.add(yeni_musteri)
            self.session.commit()
            
            self.musteri_ad.clear()
            self.musteri_telefon.clear()
            self.musteri_adres.clear()
            self.musteri_tablo_guncelle()
            
            QMessageBox.information(self, 'Başarılı', 'Müşteri başarıyla eklendi!')
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Hata', f'Müşteri eklenirken hata oluştu: {str(e)}')

    def musteri_sil(self, musteri_id):
        try:
            musteri = self.session.get(Musteri, musteri_id)
            musteri.aktif = False
            self.session.commit()
            self.musteri_tablo_guncelle()
            QMessageBox.information(self, 'Başarılı', 'Müşteri başarıyla silindi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Müşteri silinirken hata oluştu: {str(e)}')

    def musteri_duzenle(self, musteri_id):
        try:
            musteri = self.session.get(Musteri, musteri_id)
            if not musteri:
                QMessageBox.warning(self, 'Uyarı', 'Müşteri bulunamadı!')
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle('Müşteri Düzenle')
            layout = QVBoxLayout(dialog)
            
            # Ad Soyad girişi
            ad_edit = QLineEdit()
            ad_edit.setText(musteri.ad_soyad)
            layout.addWidget(QLabel('Ad Soyad:'))
            layout.addWidget(ad_edit)
            
            # Telefon girişi
            telefon_edit = QLineEdit()
            telefon_edit.setText(musteri.telefon)
            layout.addWidget(QLabel('Telefon:'))
            layout.addWidget(telefon_edit)
            
            # Adres girişi
            adres_edit = QLineEdit()
            adres_edit.setText(musteri.adres)
            layout.addWidget(QLabel('Adres:'))
            layout.addWidget(adres_edit)
            
            # Kaydet butonu
            kaydet_btn = QPushButton('Kaydet')
            kaydet_btn.clicked.connect(lambda: self.musteri_guncelle(
                musteri_id,
                ad_edit.text(),
                telefon_edit.text(),
                adres_edit.text(),
                dialog
            ))
            layout.addWidget(kaydet_btn)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Müşteri düzenlenirken hata oluştu: {str(e)}')

    def musteri_guncelle(self, musteri_id, ad_soyad, telefon, adres, dialog):
        try:
            musteri = self.session.get(Musteri, musteri_id)
            if not musteri:
                QMessageBox.warning(self, 'Uyarı', 'Müşteri bulunamadı!')
                return
            
            musteri.ad_soyad = ad_soyad
            musteri.telefon = telefon
            musteri.adres = adres
            self.session.commit()
            self.musteri_tablo_guncelle()
            dialog.accept()
            QMessageBox.information(self, 'Başarılı', 'Müşteri başarıyla güncellendi!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Müşteri güncellenirken hata oluştu: {str(e)}')

    def musteri_tablo_guncelle(self):
        try:
            sayfa = self.musteri_sayfa_spin.value()
            sayfa_boyutu = int(self.musteri_sayfa_boyut_combo.currentText())
            offset = (sayfa - 1) * sayfa_boyutu
            
            # Toplam kayıt sayısını al
            toplam_kayit = self.session.query(Musteri).filter_by(aktif=True).count()
            max_sayfa = (toplam_kayit + sayfa_boyutu - 1) // sayfa_boyutu
            self.musteri_sayfa_spin.setMaximum(max(1, max_sayfa))
            
            # Sayfalı veri çek
            musteriler = self.session.query(Musteri).filter_by(aktif=True)\
                .order_by(Musteri.id.desc())\
                .offset(offset)\
                .limit(sayfa_boyutu)\
                .all()
            
            self.musteri_tablo.setRowCount(len(musteriler))
            
            for i, musteri in enumerate(musteriler):
                self.musteri_tablo.setItem(i, 0, QTableWidgetItem(str(musteri.id)))
                self.musteri_tablo.setItem(i, 1, QTableWidgetItem(musteri.ad_soyad))
                self.musteri_tablo.setItem(i, 2, QTableWidgetItem(musteri.telefon))
                self.musteri_tablo.setItem(i, 3, QTableWidgetItem(musteri.adres))
                self.musteri_tablo.setItem(i, 4, QTableWidgetItem(musteri.kayit_tarihi.strftime('%d.%m.%Y %H:%M')))
                self.musteri_tablo.setItem(i, 5, QTableWidgetItem(getattr(musteri, 'urun_adi', '')))
                self.musteri_tablo.setItem(i, 6, QTableWidgetItem(f'₺{getattr(musteri, "ucret", 0):.2f}'))
                
                islemler_widget = QWidget()
                islemler_layout = QHBoxLayout(islemler_widget)
                islemler_layout.setContentsMargins(5, 2, 5, 2)
                
                urun_duzenle_btn = QPushButton('Ürün Düzenle')
                urun_duzenle_btn.setMinimumWidth(100)
                urun_duzenle_btn.clicked.connect(lambda checked, m=musteri: self.musteri_urun_duzenle(m.id))
                
                duzenle_btn = QPushButton('Düzenle')
                duzenle_btn.setMinimumWidth(100)
                duzenle_btn.clicked.connect(lambda checked, m=musteri: self.musteri_duzenle(m.id))
                
                yazdir_btn = QPushButton('Yazdır')
                yazdir_btn.setMinimumWidth(100)
                yazdir_btn.clicked.connect(lambda checked, m=musteri: self.musteri_yazdir(m.id))
                
                sil_btn = QPushButton('Sil')
                sil_btn.setMinimumWidth(100)
                sil_btn.clicked.connect(lambda checked, m=musteri: self.musteri_sil(m.id))
                
                islemler_layout.addWidget(urun_duzenle_btn)
                islemler_layout.addWidget(duzenle_btn)
                islemler_layout.addWidget(yazdir_btn)
                islemler_layout.addWidget(sil_btn)
                islemler_layout.addStretch()
                
                self.musteri_tablo.setCellWidget(i, 7, islemler_widget)
                
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Müşteri tablosu güncellenirken hata oluştu: {str(e)}')

    def musteri_urun_duzenle(self, musteri_id):
        try:
            musteri = self.session.get(Musteri, musteri_id)
            if not musteri:
                QMessageBox.warning(self, 'Uyarı', 'Müşteri bulunamadı!')
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle('Ürün ve Ücret Düzenle')
            layout = QVBoxLayout(dialog)
            
            # Ürün adı girişi
            urun_edit = QLineEdit()
            urun_edit.setText(musteri.urun_adi or '')
            urun_edit.setPlaceholderText('Ürün Adı')
            layout.addWidget(QLabel('Ürün:'))
            layout.addWidget(urun_edit)
            
            # Ücret girişi
            ucret_spin = QDoubleSpinBox()
            ucret_spin.setRange(0, 10000)
            ucret_spin.setPrefix('₺')
            ucret_spin.setValue(musteri.ucret or 0)
            layout.addWidget(QLabel('Ücret:'))
            layout.addWidget(ucret_spin)
            
            # Kaydet butonu
            kaydet_btn = QPushButton('Kaydet')
            kaydet_btn.clicked.connect(lambda: self.musteri_urun_kaydet(
                musteri_id,
                urun_edit.text(),
                ucret_spin.value(),
                dialog
            ))
            layout.addWidget(kaydet_btn)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Ürün düzenlenirken hata oluştu: {str(e)}')

    def musteri_urun_kaydet(self, musteri_id, urun_adi, ucret, dialog):
        try:
            musteri = self.session.get(Musteri, musteri_id)
            if not musteri:
                QMessageBox.warning(self, 'Uyarı', 'Müşteri bulunamadı!')
                return
            
            musteri.urun_adi = urun_adi.strip()
            musteri.ucret = ucret
            self.session.commit()
            self.musteri_tablo_guncelle()
            dialog.accept()
            QMessageBox.information(self, 'Başarılı', 'Ürün ve ücret başarıyla güncellendi!')
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, 'Hata', f'Ürün güncellenirken hata oluştu: {str(e)}')

    def musteri_yazdir(self, musteri_id):
        try:
            musteri = self.session.get(Musteri, musteri_id)
            if not musteri:
                QMessageBox.warning(self, 'Uyarı', 'Müşteri bulunamadı!')
                return
            
            # HTML içeriği
            html = f"""
            <html>
            <head>
                <style>
                    @page {
                        size: 80mm 297mm;
                        margin: 0;
                    }
                    body { 
                        font-family: 'Arial', sans-serif;
                        margin: 0;
                        padding: 2mm;
                        font-size: 14pt;
                        line-height: 1.3;
                        width: 76mm;
                    }
                    .header { 
                        text-align: left;
                        margin-bottom: 3mm;
                        border-bottom: 1px dashed #000;
                        padding-bottom: 3mm;
                    }
                    .company-name { 
                        font-size: 20pt;
                        font-weight: bold;
                        margin-bottom: 2mm;
                    }
                    .customer-info { 
                        margin: 3mm 0;
                    }
                    .info-row { 
                        margin: 2mm 0;
                        white-space: nowrap;
                        font-size: 16pt;
                    }
                    .label { 
                        font-weight: bold;
                    }
                    .footer { 
                        margin-top: 3mm;
                        text-align: left;
                        font-size: 12pt;
                        border-top: 1px dashed #000;
                        padding-top: 3mm;
                    }
                    .divider {
                        border-top: 1px dashed #000;
                        margin: 3mm 0;
                    }
                    .product-info {
                        background-color: #f8f8f8;
                        padding: 3mm;
                        margin: 3mm 0;
                        border: 1px dashed #000;
                    }
                    .price {
                        text-align: right;
                        font-size: 18pt;
                        font-weight: bold;
                        margin: 3mm 0;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="company-name">EVİM DÖNER</div>
                    <div style="font-size: 16pt;">MÜŞTERİ FİŞİ</div>
                </div>
                
                <div class="customer-info">
                    <div class="info-row">
                        <span class="label">Fiş No:</span> {musteri.id}
                    </div>
                    <div class="info-row">
                        <span class="label">Tarih:</span> {musteri.kayit_tarihi.strftime('%d.%m.%Y %H:%M')}
                    </div>
                    <div class="divider"></div>
                    
                    <div class="product-info">
                        <div class="info-row" style="font-weight: bold; text-align: center; margin-bottom: 3mm;">
                            MÜŞTERİ BİLGİLERİ
                        </div>
                        <div class="info-row">
                            <span class="label">Ad Soyad:</span> {musteri.ad_soyad}
                        </div>
                        <div class="info-row">
                            <span class="label">Telefon:</span> {musteri.telefon}
                        </div>
                        <div class="info-row">
                            <span class="label">Adres:</span> {musteri.adres}
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    <div class="price">
                        ÜCRET: ₺{musteri.ucret:.2f}
                    </div>
                </div>
                
                <div class="footer">
                    <div>Fiş No: {musteri.id}</div>
                    <div>{datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
                </div>
            </body>
            </html>
            """
            
            # HTML görüntüleyici
            document = QTextDocument()
            document.setHtml(html)
            
            # Yazdırma önizleme
            printer = QPrinter(QPrinter.HighResolution)
            
            # Özel kağıt boyutu ayarla (80x297mm)
            printer.setPageSize(QPrinter.Custom)
            printer.setPaperSize(QSizeF(80, 297), QPrinter.Millimeter)
            
            # Kenar boşluklarını sıfırla
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
            
            # Yazdırma dialogu
            print_dialog = QPrintDialog(printer, self)
            print_dialog.setWindowTitle('Müşteri Fişi Yazdır')
            
            if print_dialog.exec_() == QPrintDialog.Accepted:
                document.print_(printer)
                QMessageBox.information(self, 'Başarılı', 'Müşteri fişi başarıyla yazdırıldı!')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Yazdırma sırasında hata oluştu: {str(e)}')

    def teslimat_yazdir(self):
        try:
            secili_satir = self.teslimat_tablo.currentRow()
            if secili_satir < 0:
                QMessageBox.warning(self, 'Uyarı', 'Lütfen yazdırılacak teslimatı seçin.')
                return
                
            teslimat_id = int(self.teslimat_tablo.item(secili_satir, 0).text())
            teslimat = self.session.get(Teslimat, teslimat_id)
            
            if not teslimat:
                QMessageBox.warning(self, 'Hata', 'Teslimat bulunamadı.')
                return
                
            # HTML içeriği
            html = f"""
            <html>
            <head>
                <style>
                    @page {{
                        size: 80mm 297mm;
                        margin: 0;
                    }}
                    body {{ 
                        font-family: 'Arial', sans-serif;
                        margin: 0;
                        padding: 2mm;
                        font-size: 12pt;
                        line-height: 1.3;
                        width: 76mm;
                    }}
                    .header {{ 
                        text-align: left;
                        margin-bottom: 3mm;
                        border-bottom: 1px dashed #000;
                        padding-bottom: 3mm;
                    }}
                    .company-name {{ 
                        font-size: 18pt;
                        font-weight: bold;
                        margin-bottom: 2mm;
                    }}
                    .delivery-info {{ 
                        margin: 3mm 0;
                    }}
                    .info-row {{ 
                        margin: 2mm 0;
                        white-space: nowrap;
                        font-size: 14pt;
                    }}
                    .label {{ 
                        font-weight: bold;
                    }}
                    .footer {{ 
                        margin-top: 3mm;
                        text-align: left;
                        font-size: 10pt;
                        border-top: 1px dashed #000;
                        padding-top: 3mm;
                    }}
                    .divider {{
                        border-top: 1px dashed #000;
                        margin: 3mm 0;
                    }}
                    .customer-info {{
                        background-color: #f8f8f8;
                        padding: 3mm;
                        margin: 3mm 0;
                        border: 1px dashed #000;
                    }}
                    .price {{
                        text-align: right;
                        font-size: 16pt;
                        font-weight: bold;
                        margin: 3mm 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="company-name">EVİM DÖNER</div>
                    <div>TESLİMAT FİŞİ</div>
                </div>
                
                <div class="delivery-info">
                    <div class="info-row">
                        <span class="label">Fiş No:</span> {teslimat.id}
                    </div>
                    <div class="info-row">
                        <span class="label">Kurye:</span> {teslimat.kurye.ad}
                    </div>
                    <div class="info-row">
                        <span class="label">Tarih:</span> {teslimat.tarih.strftime('%d.%m.%Y %H:%M')}
                    </div>
                    <div class="divider"></div>
                    
                    <div class="customer-info">
                        <div class="info-row" style="font-weight: bold; text-align: center; margin-bottom: 3mm;">
                            MÜŞTERİ BİLGİLERİ
                        </div>
                        <div class="info-row">
                            <span class="label">Telefon:</span> {teslimat.telefon}
                        </div>
                        <div class="info-row">
                            <span class="label">Adres:</span> {teslimat.adres}
                        </div>
                        <div class="info-row">
                            <span class="label">Ürün:</span> {teslimat.urun_adi}
                        </div>
                    </div>
                    
                    <div class="divider"></div>
                    <div class="price">
                        ÜCRET: ₺{teslimat.ucret:.2f}
                    </div>
                </div>
                
                <div class="footer">
                    <div>Fiş No: {teslimat.id}</div>
                    <div>{datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
                </div>
            </body>
            </html>
            """
            
            # HTML görüntüleyici
            document = QTextDocument()
            document.setHtml(html)
            
            # Yazdırma önizleme
            printer = QPrinter(QPrinter.HighResolution)
            
            # Özel kağıt boyutu ayarla (80x297mm)
            printer.setPageSize(QPrinter.Custom)
            printer.setPaperSize(QSizeF(80, 297), QPrinter.Millimeter)
            
            # Kenar boşluklarını sıfırla
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
            
            # Önizleme penceresi oluştur
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle('Teslimat Fişi Önizleme')
            preview_dialog.setMinimumSize(400, 600)
            
            preview_layout = QVBoxLayout(preview_dialog)
            
            # Önizleme görüntüleyici
            preview_view = QWebEngineView()
            preview_view.setHtml(html)
            preview_layout.addWidget(preview_view)
            
            # Ayarlar bölümü
            ayarlar_layout = QHBoxLayout()
            
            # Yazı hizalama seçenekleri
            hizalama_label = QLabel('Yazı Hizalama:')
            hizalama_combo = QComboBox()
            hizalama_combo.addItems(['Sola', 'Ortaya', 'Sağa'])
            hizalama_combo.setCurrentText('Sola')
            
            # Yazı boyutu seçenekleri
            boyut_label = QLabel('Yazı Boyutu:')
            boyut_spin = QSpinBox()
            boyut_spin.setRange(8, 16)
            boyut_spin.setValue(12)
            
            ayarlar_layout.addWidget(hizalama_label)
            ayarlar_layout.addWidget(hizalama_combo)
            ayarlar_layout.addWidget(boyut_label)
            ayarlar_layout.addWidget(boyut_spin)
            ayarlar_layout.addStretch()
            
            preview_layout.addLayout(ayarlar_layout)
            
            # Butonlar
            button_layout = QHBoxLayout()
            
            yazdir_btn = QPushButton('Yazdır')
            yazdir_btn.clicked.connect(lambda: self.teslimat_yazdir_onayla(
                document, printer, preview_dialog, hizalama_combo.currentText(), boyut_spin.value()
            ))
            
            iptal_btn = QPushButton('İptal')
            iptal_btn.clicked.connect(preview_dialog.reject)
            
            button_layout.addWidget(yazdir_btn)
            button_layout.addWidget(iptal_btn)
            preview_layout.addLayout(button_layout)
            
            preview_dialog.exec_()
                    
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Teslimat yazdırma işlemi sırasında hata oluştu: {str(e)}')

    def teslimat_yazdir_onayla(self, document, printer, preview_dialog, hizalama, boyut):
        try:
            # Yazdırma dialogu
            print_dialog = QPrintDialog(printer, self)
            print_dialog.setWindowTitle('Teslimat Fişi Yazdır')
            
            if print_dialog.exec_() == QPrintDialog.Accepted:
                try:
                    # HTML içeriğini güncelle
                    html = document.toHtml()
                    
                    # Yazı hizalama ayarını uygula
                    if hizalama == 'Sola':
                        html = html.replace('text-align: center', 'text-align: left')
                    elif hizalama == 'Ortaya':
                        html = html.replace('text-align: left', 'text-align: center')
                    elif hizalama == 'Sağa':
                        html = html.replace('text-align: center', 'text-align: right')
                    
                    # Yazı boyutunu güncelle
                    html = html.replace('font-size: 12pt', f'font-size: {boyut}pt')
                    html = html.replace('font-size: 18pt', f'font-size: {boyut+6}pt')
                    html = html.replace('font-size: 14pt', f'font-size: {boyut+2}pt')
                    html = html.replace('font-size: 16pt', f'font-size: {boyut+4}pt')
                    html = html.replace('font-size: 10pt', f'font-size: {boyut-2}pt')
                    
                    # Güncellenmiş HTML'i belgeye uygula
                    document.setHtml(html)
                    
                    # Yazdırma işlemini başlat
                    document.print_(printer)
                    QMessageBox.information(self, 'Başarılı', 'Teslimat başarıyla yazdırıldı!')
                    preview_dialog.accept()
                except Exception as e:
                    QMessageBox.critical(self, 'Yazdırma Hatası', f'Yazdırma sırasında hata oluştu: {str(e)}')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Yazdırma işlemi sırasında hata oluştu: {str(e)}')

    def closeEvent(self, event):
        try:
            if hasattr(self, 'session'):
                try:
                    self.session.flush()
                    self.session.commit()
                except Exception as e:
                    print(f"Veritabanı kaydetme hatası: {str(e)}")
                finally:
                    try:
                        self.session.close()
                    except Exception as e:
                        print(f"Oturum kapatma hatası: {str(e)}")
        except Exception as e:
            print(f"Kapatma hatası: {str(e)}")
        finally:
            event.accept()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        
        # Veritabanı bağlantısı
        engine = create_engine('sqlite:///kurye.db', echo=True)
        
        # Veritabanı tablolarını oluştur
        Base.metadata.create_all(engine)
        
        # Uygulama penceresini oluştur
        window = KuryeTakipUygulamasi()
        window.show()
        
        # Uygulama döngüsünü başlat
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Uygulama başlatma hatası: {str(e)}")
        sys.exit(1) 