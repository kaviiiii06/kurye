from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar-buraya'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kurye.db'
db = SQLAlchemy(app)

class Kurye(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    kayit_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    aktif = db.Column(db.Boolean, default=True)

class Teslimat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kurye_id = db.Column(db.Integer, db.ForeignKey('kurye.id'), nullable=False)
    adres = db.Column(db.String(200), nullable=False)
    musteri_adi = db.Column(db.String(100), nullable=False)
    musteri_telefon = db.Column(db.String(20), nullable=False)
    baslangic_zamani = db.Column(db.DateTime, nullable=False)
    bitis_zamani = db.Column(db.DateTime)
    durum = db.Column(db.String(20), default='Devam Ediyor')
    ucret = db.Column(db.Float)
    kurye = db.relationship('Kurye', backref=db.backref('teslimatlar', lazy=True))

with app.app_context():
    db.create_all()

@app.route('/')
def ana_sayfa():
    kuryeler = Kurye.query.filter_by(aktif=True).all()
    teslimatlar = Teslimat.query.all()
    return render_template('index.html', kuryeler=kuryeler, teslimatlar=teslimatlar)

@app.route('/kurye/ekle', methods=['POST'])
def kurye_ekle():
    ad = request.form['ad']
    telefon = request.form['telefon']
    yeni_kurye = Kurye(ad=ad, telefon=telefon)
    db.session.add(yeni_kurye)
    db.session.commit()
    flash('Kurye başarıyla eklendi!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/kurye/sil/<int:id>', methods=['POST'])
def kurye_sil(id):
    kurye = Kurye.query.get_or_404(id)
    kurye.aktif = False
    db.session.commit()
    flash('Kurye başarıyla silindi!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/kurye/duzenle/<int:id>', methods=['POST'])
def kurye_duzenle(id):
    kurye = Kurye.query.get_or_404(id)
    kurye.ad = request.form['ad']
    kurye.telefon = request.form['telefon']
    db.session.commit()
    flash('Kurye başarıyla güncellendi!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/teslimat/ekle', methods=['POST'])
def teslimat_ekle():
    kurye_id = request.form['kurye_id']
    adres = request.form['adres']
    musteri_adi = request.form['musteri_adi']
    musteri_telefon = request.form['musteri_telefon']
    baslangic_zamani = datetime.strptime(request.form['baslangic_zamani'], '%Y-%m-%dT%H:%M')
    
    yeni_teslimat = Teslimat(
        kurye_id=kurye_id,
        adres=adres,
        musteri_adi=musteri_adi,
        musteri_telefon=musteri_telefon,
        baslangic_zamani=baslangic_zamani
    )
    db.session.add(yeni_teslimat)
    db.session.commit()
    flash('Teslimat başarıyla eklendi!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/teslimat/sil/<int:id>', methods=['POST'])
def teslimat_sil(id):
    teslimat = Teslimat.query.get_or_404(id)
    db.session.delete(teslimat)
    db.session.commit()
    flash('Teslimat başarıyla silindi!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/teslimat/duzenle/<int:id>', methods=['POST'])
def teslimat_duzenle(id):
    teslimat = Teslimat.query.get_or_404(id)
    teslimat.adres = request.form['adres']
    teslimat.musteri_adi = request.form['musteri_adi']
    teslimat.musteri_telefon = request.form['musteri_telefon']
    teslimat.baslangic_zamani = datetime.strptime(request.form['baslangic_zamani'], '%Y-%m-%dT%H:%M')
    db.session.commit()
    flash('Teslimat başarıyla güncellendi!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/teslimat/tamamla/<int:id>', methods=['POST'])
def teslimat_tamamla(id):
    teslimat = Teslimat.query.get_or_404(id)
    teslimat.bitis_zamani = datetime.utcnow()
    teslimat.durum = 'Tamamlandı'
    teslimat.ucret = float(request.form['ucret'])
    db.session.commit()
    flash('Teslimat başarıyla tamamlandı!', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/rapor/kurye-performans')
def kurye_performans():
    kuryeler = Kurye.query.filter_by(aktif=True).all()
    performans = []
    
    for kurye in kuryeler:
        tamamlanan_teslimatlar = Teslimat.query.filter_by(
            kurye_id=kurye.id,
            durum='Tamamlandı'
        ).all()
        
        toplam_teslimat = len(tamamlanan_teslimatlar)
        toplam_ucret = sum(t.ucret for t in tamamlanan_teslimatlar if t.ucret)
        ortalama_sure = 0
        
        if tamamlanan_teslimatlar:
            toplam_sure = sum(
                (t.bitis_zamani - t.baslangic_zamani).total_seconds() / 3600
                for t in tamamlanan_teslimatlar
                if t.bitis_zamani
            )
            ortalama_sure = toplam_sure / toplam_teslimat
        
        performans.append({
            'kurye': kurye,
            'toplam_teslimat': toplam_teslimat,
            'toplam_ucret': toplam_ucret,
            'ortalama_sure': round(ortalama_sure, 2)
        })
    
    return render_template('kurye_performans.html', performans=performans)

@app.route('/rapor/teslimat-istatistikleri')
def teslimat_istatistikleri():
    bugun = datetime.now().date()
    hafta_basi = bugun - timedelta(days=bugun.weekday())
    ay_basi = bugun.replace(day=1)
    
    # Günlük istatistikler
    gunluk_teslimatlar = Teslimat.query.filter(
        func.date(Teslimat.baslangic_zamani) == bugun
    ).all()
    
    # Haftalık istatistikler
    haftalik_teslimatlar = Teslimat.query.filter(
        func.date(Teslimat.baslangic_zamani) >= hafta_basi
    ).all()
    
    # Aylık istatistikler
    aylik_teslimatlar = Teslimat.query.filter(
        func.date(Teslimat.baslangic_zamani) >= ay_basi
    ).all()
    
    istatistikler = {
        'gunluk': {
            'toplam': len(gunluk_teslimatlar),
            'tamamlanan': len([t for t in gunluk_teslimatlar if t.durum == 'Tamamlandı']),
            'toplam_ucret': sum(t.ucret for t in gunluk_teslimatlar if t.ucret)
        },
        'haftalik': {
            'toplam': len(haftalik_teslimatlar),
            'tamamlanan': len([t for t in haftalik_teslimatlar if t.durum == 'Tamamlandı']),
            'toplam_ucret': sum(t.ucret for t in haftalik_teslimatlar if t.ucret)
        },
        'aylik': {
            'toplam': len(aylik_teslimatlar),
            'tamamlanan': len([t for t in aylik_teslimatlar if t.durum == 'Tamamlandı']),
            'toplam_ucret': sum(t.ucret for t in aylik_teslimatlar if t.ucret)
        }
    }
    
    return render_template('teslimat_istatistikleri.html', istatistikler=istatistikler)

@app.route('/musteri/gecmis/<telefon>')
def musteri_gecmis(telefon):
    teslimatlar = Teslimat.query.filter_by(musteri_telefon=telefon).all()
    return render_template('musteri_gecmis.html', teslimatlar=teslimatlar)

if __name__ == '__main__':
    app.run(debug=True) 