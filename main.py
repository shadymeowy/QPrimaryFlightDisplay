# Gerekli standart kütüphaneleri dahil et.
import sys
from math import cos, tan, pi, sin

# İlk önce PySide2 sarmalını daha sonra PyQt5 sarmalını dahil etmeyi dene.
try:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except:
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *

    # PyQt5'in QPainter.drawPolygon metodunu liste alabilmesi için düzelt.
    _old = QPainter.drawPolygon  # Eski metodu sakla.

    # Düzeltme de kullanılacak yeni metodu tanımla.
    def _new(s, p):
        # Verilen obje liste mi diye kontrol et.
        if isinstance(p, list):
            # Liste yerine metoda verilecek QPolygon objesini oluştur.
            poly = QPolygonF()  # Metoda geçecek QPolygon objesi
            # Listedeki tüm noktalar için dön.
            for ps in p:
                # Verilen noktayı QPolygon objesine ekle
                poly.append(ps)
            # Oluşturulan QPolygon objesiyle metodun kaydedilen halini çağır.
            return _old(s, poly)
        else:
            # Verilen obje liste olmadığı için modifikasyon yapmadan metodun kaydedilen halini çağır.
            return _old(s, p)
    QPainter.drawPolygon = _new

# İHA ile MAVLink bağlantısını sağlayan dronekit kütüphanesini dahil et.
from dronekit import connect


# Arayüzün gösterileceği pencere sınıfını tanımla.
class Form(QDialog):

    # Pencere oluşturulduğunda çağırılan metod
    # Bu metod parametre olarak sadece Form objesinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def __init__(self):
        # Sınıfın miras alındığı sınıfın metodunu çağır.
        super(Form, self).__init__()
        # Pencerenin başlığını değiştir.
        self.setWindowTitle("Göksat Uçuş Arayüzü")
        # Çizim komponentinin konulacağı layoutu oluştur.
        layout = QGridLayout()  # Pencerinin komponentlerini düzene koyan layout
        # Tüm çizimi yapacak olan komponenti oluştur.
        self.gcsgraphics = GCSGraphics()  # Çizimleri yapan komponent
        # Çizim komponentini layouta ekle.
        layout.addWidget(self.gcsgraphics, 0, 0, 1, 1)
        # Pencerinin layoutunu ayarla.
        self.setLayout(layout)
        # Pencerenin başlangıç posizyonunu bozmadan başlangıç boyutunu değiştir.
        self.setGeometry(self.geometry().x(), self.geometry().y(), 1000, 800)
        # Telemetri verilerini periyodik olarak kontrol edecek zamanlayıcıyı oluştur.
        self.timer = QTimer()  # Zamanlayıcı objesi
        # Zamanlayıcının çağırması gereken metodu bağla.
        self.timer.timeout.connect(self.update_widget)
        # Zamanlayıcının saniyede 60 kez çalışmasını sağla.
        self.timer.start(1000/60)
        # MAVLink bağlantısını kur.
        # Bağlantıyı saklayan Vehicle sınıfından obje.
        self.vehicle = connect("udp:127.0.0.1:14552", wait_ready=True)

    # Telemetri verilerini güncelleyecek olan metod.
    # Bu metod parametre olarak sadece Form objesinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def update_widget(self):
        # Telemetri verilerini kurulan bağlantıdan çizim komponentini güncelle.
        # Burada bazı birim ve yön düzeltmeleri de yapılmaktadır.
        # Çizim objesindeki yatış açısını güncelle.
        self.gcsgraphics.bank = -self.vehicle.attitude.roll
        # Çizim objesindeki pitch açısını güncelle.
        self.gcsgraphics.pitch = self.vehicle.attitude.pitch
        # Çizim objesindeki istikameti güncelle.
        self.gcsgraphics.heading = -self.vehicle.heading*pi/180
        # Çizim objesindeki hava süratini güncelle.
        self.gcsgraphics.airspeed = self.vehicle.airspeed
        # Çizim objesindeki irtifayı güncelle.
        self.gcsgraphics.alt = self.vehicle.location.global_relative_frame.alt
        # Çizim objesindeki düşey sürati güncelle.
        self.gcsgraphics.vspeed = -self.vehicle.velocity[-1]
        # Çizim objesindeki dönüş kayış değerini güncelle.
        self.gcsgraphics.skipskid = 0
        # Çizim objesindeki arm durumunu güncelle.
        self.gcsgraphics.arm = self.vehicle.armed
        # İHA'dan batarya bilgisi geliyor mu diye kontrol et.
        if self.gcsgraphics.battery != None:
            # Çizim objesindeki pil seviyesini güncelle.
            self.gcsgraphics.battery = self.vehicle.battery.level
        else:
            # Eğer pil seviyesi telemetri bilgilerinde yoksa çizim objesindeki pil seviyesi bilgisini 0 olarak ata.
            self.gcsgraphics.battery = 0
        # Pencere ve içerisindeki tüm komponentlerin tekrardan çizdirilmesini sağla.
        self.update()

    # Pencere kapatıldığında çağırılan metod.
    # Bu metod parametre olarak Form objesinin kendisini ve bir olay objesi alır.
    # Herhangi bir şey döndürmez.
    def closeEvent(self, event):
        # Pencerinin kapanmasıyla bağlantıyı da kapat.
        self.vehicle.close()
        # Pencerinin kapatılması olayını kabul et.
        event.accept()


# Göstergelerin tamamını çizdiren çizim komponentini tanımla.
class GCSGraphics(QWidget):

    # Çizim komponenti oluşturulduğunda çağırılan metod.
    # Bu metod parametre olarak çizim komponentinin kendisini ve
    # komponentin ebeveyn komponentini alır.
    # Herhangi bir şey döndürmez.
    def __init__(self, parent=None):
        # Sınıfın miras alındığı sınıfın metodunu çağır.
        super(GCSGraphics, self).__init__(parent)
        # Çizim alanının boyutlarını sorgula.
        # Çizim alanın boyutunun obje üzerinde saklandığı eni
        self.width = self.geometry().width()
        # Çizim alanın boyutunun obje üzerinde saklandığı boyu
        self.height = self.geometry().height()
        self.pitch = 0  # Pitch açısı
        self.bank = 0  # Yatış açısı
        self.skipskid = 0  # Dönüş kayış değeri
        self.heading = 0  # İstikamet
        self.airspeed = 0  # Hava süratı
        self.alt = 0  # İrtifa
        self.vspeed = 0  # Düşey hız
        self.arm = False  # Arm durumu
        self.battery = 0  # Pil seviyesi
        self.zoom = 1  # Arayüzün büyütme katsayısı
        # İşletim sisteminin temasının değişikliğine göre arayüzün temasını da değiştir.
        QApplication.instance().paletteChanged.connect(self.update_style)
        # Arayüzün başlangıcında ilk tema güncellemesini yap.
        self.update_style()

    # Bu metod arayüzün temasının güncellenmesini sağlar.
    # Bu metod parametre olarak çizim komponentinin kendisini
    # ve opsiyonel bir renk paleti alır.
    # Herhangi bir şey döndürmez.
    def update_style(self, palette=None):
        # Eğer bir renk paleti verilmişse onu, verilmemişse işletim sisteminin temasını kullan.
        palette = palette or self.palette()
        # Ekranın DPI bilgisini sorgula.
        self.dpi = min(self.logicalDpiX(), self.logicalDpiY())  # DPI bilgisi
        # Arayüzün büyütme katsayısı ve DPI bilgisiyle çizim kat sayısını hesapla.
        self.scale = (self.dpi/96) * self.zoom  # Çizim boyutu kat sayısı
        z = self.zoom  # Hızlı erişim için yeni bir değişken oluştur.
        s = self.scale  # Hızlı erişim için yeni bir değişken oluştur.
        # Renk paletinden önplan rengini al.
        # Yazı ve bazı çizgilerde kullanılır.
        self.fg = palette.color(QPalette.WindowText)  # Önplan rengi
        # Önplan renginde 2 birim boyutta bir font objesi
        self.fg2 = QPen(self.fg, 2*s)
        # Önplan renginde 3 birim boyutta bir font objesi
        self.fg3 = QPen(self.fg, 3*s)
        # Kalemin bitiş noktalarını yuvarlatılmış olarak ayarla.
        self.fg3.setCapStyle(Qt.RoundCap)
        # Renk paletinin işaretleme rengini al.
        # Bazı işaretlemelerde kullanılır.
        self.hg = palette.color(
            QPalette.Active, QPalette.Highlight)  # İşaretleme rengi
        # İşaretleme renginde 2 birim boyutta bir font objesi
        self.hg2 = QPen(self.hg, 2*s)
        # Kalemin bitiş ve bağlantı noktalarını yuvarlatılmış olarak ayarla.
        self.hg2.setJoinStyle(Qt.RoundJoin)
        self.hg2.setCapStyle(Qt.RoundCap)
        # İşaretleme renginde 4 birim boyutta bir font objesi
        self.hg4 = QPen(self.hg, 4*s)
        # Kalemin bitiş ve bağlantı noktalarını yuvarlatılmış olarak ayarla.
        self.hg4.setJoinStyle(Qt.RoundJoin)
        self.hg4.setCapStyle(Qt.RoundCap)
        # İşaretleme renginde 8 birim boyutta bir font objesi
        self.hg8 = QPen(self.hg, 8*s)
        # Kalemin bitiş ve bağlantı noktalarını yuvarlatılmış olarak ayarla.
        self.hg8.setJoinStyle(Qt.RoundJoin)
        self.hg8.setCapStyle(Qt.RoundCap)
        # Renk paletinden "temel" rengi al.
        # Aydınlık boyamalar da ve gösterge arkaplanlarında kullanılır.
        self.bsbr = palette.color(QPalette.Base)  # Temel renk
        # Sarı ve uyarıcı bir renk tanımla.
        # Yatış açısı büyük olduğunda durum cayrosunun çizdirilmesinde ve arm göstergesinde kullanılır.
        self.wrn = QColor(0xf6, 0x74, 0x00, 0xff)  # Uyarıcı renk
        # Uyarıcı renkte 3 birim boyutta bir font objesi
        self.wrn3 = QPen(self.wrn, 3*s)
        # Kalemin bitiş ve bağlantı noktalarını yuvarlatılmış olarak ayarla.
        self.wrn3.setJoinStyle(Qt.RoundJoin)
        self.wrn3.setCapStyle(Qt.RoundCap)
        # Kırmızı ve uyarıcı bir renk tanımla.
        # Yatış açısı çok büyük olduğunda durum cayrosunun çizdirilmesinde kullanılır.
        self.err = QColor(0xda, 0x44, 0x53, 0xff)  # Uyarıcı renk
        # Uyarıcı renkte 3 birim boyutta bir font objesi
        self.err3 = QPen(self.err, 3*s)
        # Kalemin bitiş ve bağlantı noktalarını yuvarlatılmış olarak ayarla.
        self.err3.setJoinStyle(Qt.RoundJoin)
        self.err3.setCapStyle(Qt.RoundCap)
        # Yeşil ve pozitif bir renk tanımla.
        # İHA armlı olduğunda arm göstergesinde kullanılır.
        self.pst = QColor(0x27, 0xae, 0x60)
        # Gökyüzünün çizdirilmesi için "temel" rengi kullan.
        self.sky = palette.color(QPalette.Base)  # Gökyüzü rengi
        # Yeryüzünün çizdirilmesi için pencere arkaplan rengini kullan.
        self.ground = palette.color(QPalette.Window)  # Yeryüzü rengi
        # Yazıların çizdirildiği 3 adet farklı boyutta font tanımla.
        # 12 birimlik Arial ailesinden bir font
        self.font12 = QFont("Arial", 12*z)
        # 16 birimlik Arial ailesinden bir font
        self.font16 = QFont("Arial", 16*z)
        # 20 birimlik Arial ailesinden bir font
        self.font20 = QFont('Arial', 20*z)

    # Çizim komponentinin tekrardan çizdirilmesi gerektiğinde çağırılan metod.
    # Bu metod parametre olarak çizim komponentinin kendisini ve bir olay
    # objesi alır.
    # Herhangi bir şey döndürmez.
    def paintEvent(self, e):
        # Şuanki DPI değerini al.
        dpi = min(self.logicalDpiX(), self.logicalDpiY())  # Mevcut DPI değeri
        # Mevcut DPI değeri bir öncekinden farklımı diye kontrol et.
        if dpi != self.dpi:
            # DPI değişmiş ise kalem ve fontları güncelle.
            self.update_style()
        # Çizim fonksiyonlarına erişim sunan QPainter objesini oluştur.
        self.painter = QPainter()  # Çizim objesi
        # Çizim komponenti üzerinde çizime başla.
        self.painter.begin(self)
        # Çizim objesinin yumuşatma ayarlarını değiştir.
        self.painter.setRenderHints(QPainter.Antialiasing)
        self.painter.setRenderHints(QPainter.TextAntialiasing)
        # Başlangıçta varsayılan bir kalem ve font ayarla.
        self.painter.setPen(self.fg2)
        self.painter.setFont(self.font16)
        # Yeryüzünü çizdiren metodu çağır.
        self.draw_region()
        # Gökyüzünü çizdiren metodu çağır.
        self.draw_region(sky=True)
        # Durum cayrosunda pitch değerlerini gösteren işaretlemeleri çizdir.
        self.draw_markers()
        # Durum cayrosunda mevcut yönelimi gösteren merkezi işaretçiyi çizdir.
        self.draw_cursor()
        # Durum cayrosunun yatış açısını gösteren kısmını ve dönüş kayış göstergesini çizdir
        self.draw_skipskid()
        # İstikamet göstergesini çizdir.
        self.draw_heading()
        # Hava sürat göstergesini çizdir.
        self.draw_airspeed()
        # Varyometreyi çizdir.
        self.draw_vspeed()
        # Altimetreyi çizdir.
        self.draw_altimeter()
        # Pil göstergesi ve arm durumu göstergesini çizdir.
        self.draw_status()
        # Çizimi bitir.
        self.painter.end()

    # Pil göstergesi ve arm durumu göstergesini çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_status(self):
        # Hızlı erişim için 4 adet yeni değişken oluştur.
        w = self.width
        h = self.height
        s = self.scale
        painter = self.painter
        # Çizim fırçasını "temel" renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Çizim kalemini 2 birimlik ön plan kalemi olarak değiştir.
        painter.setPen(self.fg2)
        # Pil göstergesinin boyutu ve pozisyonunu belirle.
        rect = QRectF(w-100*s, h-50*s, 100*s, 50*s)  # Pil göstergesinin alanı
        # Pil göstergesinin arkaplanını çizdir.
        painter.drawRect(rect)
        # Çizim fırçasını ve kalemini işaretleme rengi olarak değiştir.
        painter.setBrush(self.hg)
        painter.setPen(self.hg)
        # Pil seviyesini belirten dikdörgen işaretlemeyi yap.
        painter.drawRect(w-98*s, h-48*s, (96*s)*(self.battery/100), 46*s)
        # Çizim fontunu 16 birimlik font olarak değiştir.
        painter.setFont(self.font16)
        # Çizim kalemini önplan rengi olarak değiştir
        painter.setPen(self.fg)
        # Pil seviyesini yazı olarak göstergenin üstüne yazdır.
        painter.drawText(rect, Qt.AlignCenter, f"{round(self.battery)}%")
        # Çizim fırçasını "temel" renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Çizim kalemini 2 birimlik ön plan kalemi olarak değiştir.
        painter.setPen(self.fg2)
        # Arm durum göstergesinin boyutu ve pozisyonunu belirle.
        rect = QRectF(0, h-50*s, 100*s, 50*s)  # Arm durumu göstergesinin alanı
        # Arm durum göstergesinin arkaplanını çizdir.
        painter.drawRect(rect)
        # Çizim fırçası ve kalemini arm durumuna göre yeşil ve kırmızı olarak değiştir.
        painter.setBrush(self.pst if self.arm else self.err)
        painter.setPen(self.pst if self.arm else self.err)
        # Arm durumunu gösteren renkli işaretlemeyi çizdir.
        painter.drawRect(2*s, h-48*s, 96*s, 46*s)
        # Çizim fontunu 16 birimlik font olarak değiştir.
        painter.setFont(self.font16)
        # Çizim kalemini önplan rengi olarak değiştir.
        painter.setPen(self.fg)
        # Arm durumunu yazı olarak göstergenin üzerine çizdir.
        painter.drawText(
            rect,
            Qt.AlignCenter,
            "Armed" if self.arm else "Disarmed"
        )

    # Varyometreyi çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_vspeed(self):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        s = self.scale
        v = self.vspeed
        per = 30*s  # İşaretlemelerin arasındaki uzaklık.
        inc = 0.5  # İşaretlemelerin arasındaki değer farkı.
        r = per/inc  # Uzaklık başına değer farkı
        x2 = 15*w/16  # Göstergenin bittiği x koordinatı
        x1 = 15*w/16 - 40*s - 10*s  # Göstergenin başladığı x koordinatı
        y1 = 4*h/16  # Göstergenin başladığı y koordinatı
        y2 = h-y1  # Göstergenin bittiği y koordinatı
        # Çizim fontunu 12 birimlik font olarak değiştir.
        painter.setFont(self.font12)
        # "Temel" rengin opaklığını yarıya düşür.
        self.bsbr.setAlpha(128)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        self.bsbr.setAlpha(255)
        # Çizim kalemini önplan rengi olarak değiştir.
        painter.setPen(self.fg)
        # Varyometrenin arkaplanını çizdir.
        painter.drawRect(x1, y1, x2-x1 - 10*s, y2-y1)
        # Çizim kalemini önplan renginde 3 birimlik kalem olarak değiştir.
        painter.setPen(self.fg3)
        # Varyometrenin sol tarafındaki çizgiyi yeni bir çizgiyle kalınlaştır.
        painter.drawLine(QLineF(x1, y1, x1, y2))
        # Çizim objesinin mevcut ayarlarını sakla.
        painter.save()
        # Çizim objesinin çizim alanını varyometrenin alanı olarak kısıtla.
        painter.setClipRect(QRectF(x1, y1, x2-x1, y2-y1))
        # Göstergenin işaretleme sınırlarını belirle.
        l1 = int(((y1+y2)/2+v*r-y2)/per)-1  # İll işaretlemenin sırası
        l2 = int(((y1+y2)/2+v*r-y1)/per)+1  # Son işaretlemenin sırası
        # Her bir işaretlemeye karşılık gelen sıra sayısı için dön.
        for i in range(l1, l2+1):
            # İşaretlemenin düşey pozisyonunu hesapla
            pos = -i*per+v*r
            # İşaretleme çift sıralı mı diye kontrol et.
            if (i % 2) == 0:
                # İşaretlemeyi uzun bir işaretleme olarak çizdir.
                painter.drawLine(
                    QLineF(x1, (y1+y2)/2+pos,  x1+15*s, (y1+y2)/2+pos))
                # İşaretlemeye karşılık gelen değeri yazı olarak ortalayarak çizdir.
                painter.drawText(
                    QRectF(
                        x1+18*s,
                        (y1+y2)/2 + pos - 20*s,
                        x2-18*s-x1,
                        40*s
                    ),
                    Qt.AlignVCenter | Qt.AlignLeft,
                    str(int(round(abs(i*inc))))
                )
            else:
                # İşaretlemeyi kısa bir işaretleme olarak çizdir.
                painter.drawLine(
                    QLineF(x1, (y1+y2)/2+pos,  x1+8*s, (y1+y2)/2+pos))
        # Çizim objesinin ayarlarını kaydedilen ayarlardan yükle.
        # Bu çizim alanının kısıtlamasını kaldırmak için yapılır.
        painter.restore()
        # Çizim fırçasını temel renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Varyometrede hızın tam olarak yazdırıldığı yerin arkaplanını ve şeklini oluştur.
        painter.drawPolygon([
            QPointF(x2, (y1+y2)/2 - 15*s),
            QPointF(x2, (y1+y2)/2 + 15*s),
            QPointF(x1-33*s, (y1+y2)/2 + 15*s),
            QPointF(x1-33*s, (y1+y2)/2 - 15*s),
        ])
        # Çizim fontunu 16 birimlik font olarak değiştir.
        painter.setFont(self.font16)
        # Düşey hızı virgulden sonra bir basamak görünecek şekilde çizdir.
        painter.drawText(
            QRectF(
                x1,
                (y1+y2)/2 - 25*s,
                x2-x1-8*s,
                50*s
            ),
            Qt.AlignVCenter | Qt.AlignRight,
            str(float(round(abs(v), 1)))
        )

    # Altimetreyi çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_altimeter(self):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        s = self.scale
        v = self.alt
        per = 70*s  # İşaretlemelerin arasındaki uzaklık.
        inc = 5  # İşaretlemelerin arasındaki değer farkı.
        r = per/inc  # Uzaklık başına değer farkı
        x2 = 15*w/16 - 40*s  # Göstergenin bittiği x koordinatı
        x1 = 15*w/16 - 90*s - 40*s  # Göstergenin başladığı x koordinatı
        y1 = h/15 + 20*s  # Göstergenin başladığı y koordinatı
        y2 = h-y1  # Göstergenin bittiği y koordinatı
        # Çizim fontunu 16 birimlik font olarak değiştir.
        painter.setFont(self.font16)
        # "Temel" rengin opaklığını yarıya düşür.
        self.bsbr.setAlpha(128)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # "Temel" rengin opaklığını düzelt.
        self.bsbr.setAlpha(255)
        # Çizim kalemini önplan rengi olarak değiştir.
        painter.setPen(self.fg)
        # Altimetrenin arkaplanını çizdir.
        painter.drawRect(x1, y1, x2-x1 - 10*s, y2-y1)
        # Çizim kalemini önplan renginde 3 birimlik kalem olarak değiştir.
        painter.setPen(self.fg3)
        # Varyometrenin sol tarafındaki çizgiyi yeni bir çizgiyle kalınlaştır.
        painter.drawLine(QLineF(x1, y1, x1, y2))
        # Çizim objesinin mevcut ayarlarını sakla.
        painter.save()
        # Çizim objesinin çizim alanını varyometrenin alanı olarak kısıtla.
        painter.setClipRect(QRectF(x1, y1, x2-x1, y2-y1))
        # Göstergenin işaretleme sınırlarını belirle.
        l1 = int(((y1+y2)/2+v*r-y2)/per)-1  # İlk işaretlemenin sırası
        l2 = int(((y1+y2)/2+v*r-y1)/per)+1  # Son işaretlemenin sırası
        # Her bir işaretlemeye karşılık gelen sıra sayısı için dön.
        for i in range(l1, l2+1):
            # İşaretlemenin düşey pozisyonunu hesapla
            pos = -i*per+v*r
            # İşaretleme çift sıralı mı diye kontrol et.
            if (i % 2) == 0:
                # İşaretlemeyi uzun bir işaretleme olarak çizdir.
                painter.drawLine(
                    QLineF(x1, (y1+y2)/2+pos,  x1+25*s, (y1+y2)/2+pos))
                # İşaretlemeye karşılık gelen değeri yazı olarak ortalayarak çizdir.
                painter.drawText(
                    QRectF(
                        x1+33*s,
                        (y1+y2)/2 + pos - 20*s,
                        x2-33*s-x1,
                        40*s
                    ),
                    Qt.AlignVCenter | Qt.AlignLeft,
                    str(i*inc)
                )
            else:
                # İşaretlemeyi kısa bir işaretleme olarak çizdir.
                painter.drawLine(
                    QLineF(x1, (y1+y2)/2+pos,  x1+15*s, (y1+y2)/2+pos))
            # İşaretlemelerin aralarındaki değerler için küçük işaretlemeler ekle.
            for j in range(-5, 6):
                painter.drawLine(QLineF(x1, (y1+y2)/2+pos+j/5*per,
                                 x1+8*s, (y1+y2)/2+pos+j/5*per))
        # Çizim objesinin ayarlarını kaydedilen ayarlardan yükle.
        # Bu çizim alanının kısıtlamasını kaldırmak için yapılır.
        painter.restore()
        # Çizim fırçasını temel renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Altimetrede irtifanın tam olarak yazdırıldığı yerin arkaplanını ve şeklini oluştur.
        painter.drawPolygon([
            QPointF(x2, (y1+y2)/2 - 25*s),
            QPointF(x2, (y1+y2)/2 + 25*s),
            QPointF(x1+33*s, (y1+y2)/2 + 25*s),
            QPointF(x1, (y1+y2)/2),
            QPointF(x1+33*s, (y1+y2)/2 - 25*s),
        ])
        # Çizim fontunu 20 birimlik font olarak değiştir.
        painter.setFont(self.font20)
        # İrtifayı virgulden sonra bir basamak görünecek şekilde çizdir.
        painter.drawText(
            QRectF(
                x1,
                (y1+y2)/2 - 25*s,
                x2-33*s-x1,
                50*s
            ),
            Qt.AlignVCenter | Qt.AlignRight,
            str(round(v))
        )

    # Sürat göstergesini çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_airspeed(self):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        s = self.scale
        v = self.airspeed
        per = 40*s  # İşaretlemelerin arasındaki uzaklık.
        inc = 4  # İşaretlemelerin arasındaki değer farkı.
        r = per/inc  # Uzaklık başına değer farkı
        x1 = w/16  # Göstergenin başladığı x koordinatı
        x2 = x1 + 90*s  # Göstergenin bittiği x koordinatı
        y1 = h/15 + 20*s  # Göstergenin başladığı y koordinatı
        y2 = h-y1-7*s  # Göstergenin bittiği y koordinatı
        # "Temel" rengin opaklığını yarıya düşür.
        self.bsbr.setAlpha(128)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        self.bsbr.setAlpha(255)
        # Çizim kalemini önplan rengi olarak değiştir.
        painter.setPen(self.fg)
        # Sürat göstergesinin arkaplanını çizdir.
        painter.drawRect(x1 + 10*s, y1, x2-x1 - 10*s, y2-y1)
        # Çizim kalemini önplan renginde 3 birimlik kalem olarak değiştir.
        painter.setPen(self.fg3)
        # Sürat göstergesinin sağ tarafındaki çizgiyi yeni bir çizgiyle kalınlaştır.
        painter.drawLine(QLineF(x2, y1, x2, y2))
        # Çizim objesinin mevcut ayarlarını sakla.
        painter.save()
        # Çizim objesinin çizim alanını varyometrenin alanı olarak kısıtla.
        painter.setClipRect(QRectF(x1, y1, x2-x1, y2-y1))
        # Göstergenin işaretleme sınırlarını belirle.
        l1 = int(((y1+y2)/2+v*r-y2)/per)-1  # İlk işaretlemenin sırası
        l2 = int(((y1+y2)/2+v*r-y1)/per)+1  # Son işaretlemenin sırası
        # Her bir işaretlemeye karşılık gelen sıra sayısı için dön.
        for i in range(l1, l2+1):
            # İşaretlemenin düşey pozisyonunu hesapla
            pos = -i*per+v*r
            # İşaretleme çift sıralı mı diye kontrol et.
            if (i % 2) == 0:
                # İşaretlemeyi uzun bir işaretleme olarak çizdir.
                painter.drawLine(
                    QLineF(x2, (y1+y2)/2+pos,  x2-25*s, (y1+y2)/2+pos))
                # İşaretlemeye karşılık gelen değeri yazı olarak ortalayarak çizdir.
                painter.drawText(
                    QRectF(
                        x1,
                        (y1+y2)/2 + pos - 20*s,
                        x2-33*s-x1,
                        40*s
                    ),
                    Qt.AlignVCenter | Qt.AlignRight,
                    str(i*inc)
                )
            else:
                # İşaretlemeyi kısa bir işaretleme olarak çizdir.
                painter.drawLine(
                    QLineF(x2, (y1+y2)/2+pos,  x2-15*s, (y1+y2)/2+pos))
        # Çizim objesinin ayarlarını kaydedilen ayarlardan yükle.
        # Bu çizim alanının kısıtlamasını kaldırmak için yapılır.
        painter.restore()
        painter.setBrush(self.bsbr)
        # Sürat göstergesinde hızın tam olarak yazdırıldığı yerin arkaplanını ve şeklini oluştur.
        painter.drawPolygon([
            QPointF(x1, (y1+y2)/2 - 25*s),
            QPointF(x1, (y1+y2)/2 + 25*s),
            QPointF(x2-33*s, (y1+y2)/2 + 25*s),
            QPointF(x2, (y1+y2)/2),
            QPointF(x2-33*s, (y1+y2)/2 - 25*s),
        ])
        # Çizim fontunu 20 birimlik font olarak değiştir.
        painter.setFont(self.font20)
        # Süratı virgulden sonra bir basamak görünecek şekilde çizdir.
        painter.drawText(
            QRectF(
                x1,
                (y1+y2)/2 - 25*s,
                x2-33*s-x1,
                50*s
            ),
            Qt.AlignVCenter | Qt.AlignRight,
            str(round(v))
        )

    # İstikamet göstergesini çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_heading(self):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        s = self.scale
        hd = self.heading
        # İstikamet göstergesinin yarıçapını hesapla.
        x = min(4*w/16, 4*h/16)
        # Çizim kalemini 3 birimlik önplan rengi olarak değiştir.
        painter.setPen(self.fg3)
        # "Temel" rengin opaklığını yarıya düşür.
        self.bsbr.setAlpha(128)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        painter.setBrush(self.bsbr)
        # Çizim fırçasını bu yarı geçirgen renk olarak değiştir.
        self.bsbr.setAlpha(255)
        # İstikamet göstergesinin arkaplanını çizdir.
        painter.drawEllipse(w/2 - x, 17*h/16 - x, 2*x, 2*x)
        # Her 5 derecelik açı için bir işaretleme çizdir.
        for i in range(72):
            # Bir koordinat dönüşüm objesi oluştur.
            trans = QTransform()  # Koordinat dönüşüm objesi
            # Dönüşüm objesine göstergenin merkezini orijin
            # yapacak şekilde bir öteleme yaptır.
            trans.translate(w/2, 17*h/16)
            # Dönüşüm objesini istikamet açısı ve işaretlemenin açısının
            # toplamı kadar döndür
            trans.rotateRadians((i/72)*2*pi + hd)
            # Çizim objesinin koordinat dönüşümünü ayarla.
            painter.setTransform(trans)
            # Çift sıralı gösterge mi diye kontrol et.
            if (i % 2) == 0:
                # İşaretleme 4 yönden birine mi denk geliyor diye
                # kontrol et.
                if ((i//2) % 3) == 0:
                    t = str(i//2)  # İşaretlemeye karşılık gelen değer.
                    # İstikamete göre 4 yönden birine karşılık gelen
                    # bir işaretlemedeysek yazıyı değiştir.
                    if i == 0:
                        t = "N"
                    elif i == 18:
                        t = "E"
                    elif i == 36:
                        t = "S"
                    elif i == 54:
                        t = "W"
                    # İşaretlemenin değerini ortalayarak çizdir.
                    painter.drawText(
                        QRectF(
                            -20*s, - x + 15*s, 40*s, 40*s
                        ),
                        Qt.AlignCenter | Qt.AlignTop, t
                    )
                # İşaretlemeyi uzun bir işaretleme olarak çizdir.
                painter.drawLine(QLineF(0, - x, 0, - x + 15*s))
            elif i == 9 or i == 27 or i == 45 or i == 63:
                # Açı 45, 135, 275 ya da 315 dereceyse
                # farklı bir renkle işaretle.
                # Çizim kalemini uyarı rengi olarak değiştir.
                painter.setPen(self.wrn3)
                # İşaretlemeyi çizdir.
                painter.drawLine(QLineF(0, - x, 0, - x + 30*s))
                # Çizim kalemini 3 birimlik önplan rengi olarak değiştir.
                painter.setPen(self.fg3)
            else:
                # Hiçbiri değilse işaretlemeyi kısa bir işaretleme
                # olarak çizdir.
                painter.drawLine(QLineF(0, - x, 0, - x + 7*s))
            # Çizim objesinin koordinat dönüşümünü sıfırla.
            painter.resetTransform()
        # Çizim fırçasını işaretleme rengi olarak değiştir.
        painter.setBrush(self.hg)
        # Çizim kalemini 2 birimlik işaretleme rengi olarak değiştir.
        painter.setPen(self.hg2)
        # İstikamet yönünde göstergenin üzerine baştan sona
        # işaretleme rengiyle bir çizgi çizdir.
        painter.drawLine(QLineF(w/2, 17*h/16 - x, w/2, 17*h/16 + x))
        # Çizim kalemini 4 birimlik işaretleme rengi olarak değiştir.
        painter.setPen(self.hg4)
        # İstikameti gösteren işaretçiyi çizdir.
        painter.drawPolygon([
            QPointF(w/2 - 7*s, 17*h/16 - x + 17*s),
            QPointF(w/2, 17*h/16 - x + 2*s),
            QPointF(w/2 + 7*s, 17*h/16 - x + 17*s)
        ])
        # Çizim kalemini 3 birimlik işaretleme rengi olarak değiştir.
        painter.setPen(self.fg3)
        # Çizim fırçasını boş fırçayla değiştir.
        painter.setBrush(Qt.NoBrush)
        # İstikamet göstergesinin dış çizgilerini bozulmuş olma
        # ihtimaline karşı tekrardan çizdir.
        painter.drawEllipse(w/2 - x, 17*h/16 - x, 2*x, 2*x)

    # Pitch açısını gösteren işaretlemeleri çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_markers(self):
        # Hızlı erişim için 3 adet yeni değişken oluştur.
        p = self.pitch
        s = self.scale
        r = 50
        # Pitch açısını ekran üzerindeki uzaklığa çevir.
        p *= ((50/5)*s)*180/pi
        # Her çift işaretleme için dön.
        for i in range(1, 20):
            # İşaretlemerin boyutunu hesapla.
            size = 80*s*((1/4)*i+1/2)*10/(5+i)  # İşaretleme boyutu
            # İşaretleme görünür olmalı mı diye kontrol et.
            if -(4*r*1.1*s) < p+i*r*s < 4*r*1.1*s:
                # İşaretlemeyi çizdir.
                self.draw_marker(p+i*r*s,
                                 size if (i % 2) == 0 else 40*s, f"  {i*r//10}", 255-255*abs(p+i*r*s)/(4*r*1.1*s))
            # İşaretleme görünür olmalı mı diye kontrol et.
            if -(4*r*1.1*s) < p-i*50*s < 4*r*1.1*s:
                # İşaretlemeyi çizdir.
                self.draw_marker(p-i*r*s,
                                 size if (i % 2) == 0 else 40*s, f"  {i*r//10}", 255-255*abs(p-i*r*s)/(4*r*1.1*s))

    # Pitch açısını gösteren işaretlemelerden her birini çizdiren metod.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_marker(self, p, r, t="", alpha=128):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        b = self.bank
        s = self.scale
        # Önplan rengi kaleminin opaklığını değiştir.
        self.fg.setAlpha(alpha)
        # 3 birimlik önplan rengindeki kalemi de bu renk ile
        # değiştir.
        self.fg3.setColor(self.fg)
        # Çizim kalemini bu kalemle değiştir.
        painter.setPen(self.fg3)
        # Gerekli öteleme ve döndürme formullerini uygulayarak
        # işaretlemenin başladığı ve bittiği noktaları
        # hesaplayarak işaretlemeyi çizdir.
        painter.drawLine(QLineF(
            w/2 - p*sin(b) - r*cos(b),
            h/2 + p*cos(b) - r*sin(b),
            w/2 - p*sin(b) + r*cos(b),
            h/2 + p*cos(b) + r*sin(b)))
        # İşaretlemenin değer yazılarını çizdirmek
        # Bir koordinat dönüşüm objesi oluştur.
        trans = QTransform()
        # Dönüşüm objesine arayüzün merkezini orijin
        # yapacak şekilde bir öteleme yaptır.
        trans.translate(w/2, h/2)
        # Yatış açısı kadar bir döndürme uygula.
        trans.rotateRadians(b)
        # Çizim objesinin koordinat dönüşümünü değiştir.
        painter.setTransform(trans)
        # Çizim kalemini önplan rengi olarak değiştir.
        painter.setPen(self.fg)
        # Çizim fontunu 16 birimlik fontla olarak değiştir.
        painter.setFont(self.font16)
        # İşaretlemenin değerini çizdir.
        painter.drawText(r, p+8*s, t)
        # Çizim objesinin koordinat dönüşümünü sıfırla.
        painter.resetTransform()
        # Önplan renginin opaklığı düzelt.
        self.fg.setAlpha(255)
        # 3 birimlik önplan rengindeki kalemin
        # rengini düzelt.
        self.fg3.setColor(self.fg)

    # Bu metod dönüş kayış göstergesini ve durum cayrosunun yatış
    # açısını gösteren kısmını çizdirir.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_skipskid(self):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        b = self.bank
        s = self.scale
        # Çizim kalemini önplan rengi olarak değiştir.
        painter.setPen(self.fg)
        # Durum cayrosunun bu kısmını oluşturan yayın yarıçapını
        # hesapla.
        x = min(w/2-50*s, h/2-50*s)
        # Çizim kalemini 3 birimlik önplan rengi olarak değiştir.
        painter.setPen(self.fg3)
        # Çizim fırçasını önplan rengi olarak değiştir.
        painter.setBrush(self.fg)
        # Göstergenin ana hattını oluşturan yayı çizdir.
        painter.drawArc(w/2-x, h/2-x, x*2, x*2, 45*16, 90*16)
        # Eğer yatış açısı belli bir değerden küçük/büyük mü
        # diye kontrol et.
        if b < -7*pi/32 or b > 7*pi/32:
            # Yatış açısı -45 ve 45 derece arasında mı
            # diye kontrol et.
            if -pi/4 < b < pi/4:
                # Çizim fırçası ve kalemini önplan rengiyle değiştir.
                painter.setPen(self.fg3)
                painter.setBrush(self.fg)
            # Yatış açısı -60 ve 60 derece arasında mı
            # diye kontrol et.
            elif -pi/3 < b < pi/3:
                # Çizim fırçası ve kalemini uyarı rengiyle değiştir.
                painter.setPen(self.wrn3)
                painter.setBrush(self.wrn)
            # Yatış açısı bu aralıklar da değil ise
            else:
                # Çizim fırçası ve kalemini kırmızı renkle değiştir.
                painter.setPen(self.err3)
                painter.setBrush(self.err)
                # Yatış açı 60 dereceden büyük ya da 60 dereceden
                # küçük olduğundan sırasıyla 60 ya da -60 derece olarak
                # çizdir.
                b = pi/3 if b > 0 else -pi/3
            # Bu yatış açısı aralığında yayı uzun bir şekilde çizdir.
            painter.drawArc(w/2-x, h/2-x, x*2, x*2, 30*16, 120*16)
        # Yatış açısı bu aralıklar da değilse
        else:
            # Çizim fırçası ve kalemini önplan rengiyle değiştir.
            painter.setPen(self.fg3)
            painter.setBrush(self.fg)

        # Sıfır yatış açısını gösteren işaretlemeyi yap.
        painter.drawEllipse(w/2-2*s, h/2-x-2*s, 4*s, 4*s)
        # İşaretlenip değeri yazı olarak çizdirilmesi gereken
        # "özel" açıların listesini tanımla.
        ps = [-pi/6, pi/6, pi/3, -pi/3, pi /
              4, -pi/4, pi/18, -pi/18, pi/9, -pi/9]  # Özel açılar listesi
        # Her özel açı için döndür.
        for a in ps:
            # Açı (-45,45) aralığında değil ve yatış açısı bu işaretlemeler için
            # küçük bir değerse bu işaretlemeyi atla.
            if (a < -pi/4 or a > pi/4) and not (b < -7*pi/32 or b > 7*pi/32):
                continue
            # Bir koordinat dönüşüm objesi oluştur.
            trans = QTransform()
            # Dönüşüm objesine arayüzün merkezini orijin
            # yapacak şekilde bir öteleme yaptır.
            trans.translate(w/2, h/2)
            # Özel açı kadar bir döndürme uygula.
            trans.rotateRadians(a)
            # Çizim objesinin koordinat dönüşümünü ayarla.
            painter.setTransform(trans)
            # Özel açının değerini çizdir.
            painter.drawText(-10*s, -x-10*s, str(abs(round(a/pi*180))))
            # Özel açıyı yay üzerinde dolu bir daire çizdirerek işaretle.
            painter.drawEllipse(0-2*s, -x-2*s, 4*s, 4*s)
            # Çizim objesinin koordinat dönüşümünü sıfırla.
            painter.resetTransform()

        # Bir koordinat dönüşüm objesi oluştur.
        trans = QTransform()
        # Dönüşüm objesine arayüzün merkezini orijin
        # yapacak şekilde bir öteleme yaptır.
        trans.translate(w/2, h/2)
        # Dönüşüm objesine yatış açısı kadar bir döndürme uygula.
        trans.rotateRadians(b)
        # Çizim objesinin koordinat dönüşümünü ayarla.
        painter.setTransform(trans)
        # Yatış açısını göstergedeki yay üzerinde işaretle.
        painter.drawEllipse(-5*s, -x-5*s, 10*s, 10*s)
        # Dönüş kayış değeriyle arayüzdeki dönüş kayış göstergesinin
        # kayma değeri hesaplanır.
        px = -20*s-self.skipskid*20*s  # Kayma miktarı
        # Bu kayma miktarıyla bir dikdörtgen çizdir.
        painter.drawRect(px, -x+15*s, 40*s, 10*s)
        # Çizim objesinin koordinat dönüşümünü sıfırla.
        painter.resetTransform()

    # Durum cayrosundaki merkezi işaretçiyi bu metod çizdirir.
    # Bu metod parametre olarak çizim komponentinin kendisini alır.
    # Herhangi bir şey döndürmez.
    def draw_cursor(self):
        # Hızlı erişim için 4 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        s = self.scale
        # İşaretçinin dış hatlarını tutan yol objesi çizdirilir.
        path = QPainterPath()  # Noktalardan oluşan çizim yolu
        # İşaretçinin şeklini oluşturan noktalar ile
        # çizim yolu objesinin gerekli metodlarını çağır.
        path.moveTo(w/2-70*s, h/2)
        path.lineTo(w/2-40*s, h/2)
        path.lineTo(w/2, h/2+30*s)
        path.lineTo(w/2+40*s, h/2)
        path.lineTo(w/2+70*s, h/2)
        # Çizim kalemini 8 birimlik işaretleme rengi olarak değiştir.
        painter.setPen(self.hg8)
        # Çizim fırçasını boş fırça olarak değiştir.
        painter.setBrush(Qt.NoBrush)
        # İşaretçinin anahatlarını tutan çizim yolunu çizdir.
        painter.drawPath(path)
        # Çizim fırçasını ve kalemini işaretleme rengi olarak değiştir.
        painter.setPen(self.hg)
        painter.setBrush(self.hg)
        # Merkez işaretçinin merkezinde bulunan daire çizdirilir.
        painter.drawEllipse(w/2-4, h/2-4, 8*s, 8*s)

    def draw_inf_marker(self, p, b):
        painter = self.painter
        w = self.width
        h = self.height
        s = self.scale
        x1, y1, x2, y2 = self.compute_horizon(p, b)
        painter.drawLine(QLineF(x1, y1, x2, y2))

    # Bu metod durum cayrosundaki ufuk çizgisinin başlangıç ve bitiş
    # noktalarını hesaplar.
    # Bu metod parametre olarak çizim komponentinin kendisini, 
    # pitch açısı (p) ve yatış açısı (b)  alır.
    # Ufuk çizgisinin başlangıç ve bitiş noktalarının koordinlarını
    # 4 elementli bir tuple olarak döndürür.
    def compute_horizon(self, p, b):
        # Hızlı erişim için 5 adet yeni değişken oluştur.
        w = self.width
        h = self.height
        # Yatış açısı 90 ve -90 derece değilse
        if b != pi/2 and b != -pi/2:
            # Başlangıç noktası arayüzün sol kenarı üstünde olarak değiştir.
            x1 = 0
            # Başlangıç noktasının düşey konumunu ufuk çizgisi ve
            # arayüzün sol kenarının kesişimi olarak ayarla.
            y1 = h/2-w/2*tan(b)+p/cos(b)
            # Bitiş noktası arayüzün sol kenarı üstünde olarak değiştir.
            x2 = w
            # Bitiş noktasının düşey konumunu ufuk çizgisi ve
            # arayüzün sağ kenarının kesişimi olarak ayarla.
            y2 = h/2+w/2*tan(b)+p/cos(b)
        # Yatış açısı 90 derece ise
        elif b == pi/2:
            # Kodda bir sonraki koşul bloğundaki koşullardan
            # doğru olanın çalışması için başlangıç ve bitiş
            # noktasını ayarla.
            x1 = 0
            y1 = -1
            x2 = w
            y2 = h+1
        # Yatış açısı -90 derece ise
        elif b == -pi/2:
            # Kodda bir sonraki koşul bloğundaki koşullardan
            # doğru olanın çalışması için başlangıç ve bitiş
            # noktasını ayarla.
            x1 = w
            y1 = h+1
            x2 = 0
            y2 = -1
        # Eğer başlangıç noktasının düşey konumu arayüzün görünen kısmından
        # daha aşağıda kalıyorsa.
        if y1 > h:
            # Başlangıç noktasını ekranın alt kenarı ve ufuk çizgisinin
            # keşisimi olarak değiştir.
            x1 = (h/2-p/cos(b))/tan(b) + w/2
            y1 = h
        # Eğer başlangıç noktasının düşey konumu arayüzün görünen kısmından
        # daha yukarıda kalıyorsa.
        elif y1 < 0:
            # Başlangıç noktasını ekranın üst kenarı ve ufuk çizgisinin
            # keşisimi olarak değiştir.
            x1 = (-h/2-p/cos(b))/tan(b) + w/2
            y1 = 0
        # Eğer bitiş noktasının düşey konumu arayüzün görünen kısmından
        # daha aşağıda kalıyorsa.
        if y2 > h:
            # bitiş noktasını ekranın alt kenarı ve ufuk çizgisinin
            # keşisimi olarak değiştir.
            x2 = (h/2-p/cos(b))/tan(b) + w/2
            y2 = h
        # Eğer bitiş noktasının düşey konumu arayüzün görünen kısmından
        # daha yukarıda kalıyorsa.
        elif y2 < 0:
            # bitiş noktasını ekranın üst kenarı ve ufuk çizgisinin
            # keşisimi olarak değiştir.
            x2 = (-h/2-p/cos(b))/tan(b) + w/2
            y2 = 0
        # Başlangıç ve bitiş noktasının koordinatlarını döndür.
        return x1, y1, x2, y2

    # Durum cayrosundaki gökyüzü/yeryüzü bu metod tarafından çizdirilir.
    # Bu metod parametre olarak çizim komponentinin kendisini ve çizilmesi
    # gereken bölgenin gökyüzü olup olmadığını alır.
    # Herhangi bir şey döndürmez.
    def draw_region(self, sky=False):
        # Hızlı erişim için 6 adet yeni değişken oluştur.
        painter = self.painter
        w = self.width
        h = self.height
        p = self.pitch
        b = self.bank
        s = self.scale
        # Eğer yeryüzü çizdirilmek isteniyorsa çizdirilen
        # bölgeyi değil ters bölgeyi çizdir.
        inv = not sky
        # Pitch açısını ekran üzerindeki uzaklığa çevir.
        p *= ((50/5)*s)*180/pi
        # Eğer gökyüzü çizdiriliyorsa pitch "açı"sının tersi alınır.
        if sky:
            p = -p
        # Eğer yatış açısı pozitifse
        if b >= 0:
            # Kaç "tur" dönüldüğüne göre çizilen bölgeyi değiştir.
            inv ^= ((b//(pi)) % 2) == 0
            # Açının "turlar" çıkartıldıktan sonraki değeri alınır.
            b %= pi
        # Eğer yatış açısı negatifse
        else:
            # Kaç "tur" dönüldüğüne göre çizilen bölgeyi değiştir.
            inv ^= ((b//(-pi)) % 2) == 0
            # Açının "turlar" çıkartıldıktan sonraki değeri alınır.
            b %= -pi
        # Yatış açısı 90dan büyükse
        if pi/2 < b:
            # Yatış açısından 90 derece çıkar.
            b -= pi
            # Çizdirilen bölgeyi ters çevir.
            inv = not inv
        elif b < -pi/2:
            # Yatış açısına 90 derece ekle.
            b += pi
            # Çizdirilen bölgeyi ters çevir.
            inv = not inv
        # Çizdirilen bölgenin ters çevrilmesi gerekiyorsa
        # pitch "açı"sını da ters çevir.
        if inv:
            p = -p
        # Ufuk çizgisisin başlangıç ve bitiş noktaları hesaplanır.
        x1, y1, x2, y2 = self.compute_horizon(p, b)
        # Çizdirilecek bölgeyi bir çokgen olarak belirten çokgenin
        # köşeleri burada hesaplanır.
        points = []  # Çizdirilecek olan bölgenin köşe noktaları listesi
        # Başlangıç noktasını listeye ekle.
        points.append(QPointF(x1, y1))
        # Eğer bölge ters çevrilmeliyse
        if inv:
            # Eğer arayüzün sol alt köşesi çokgenin bir köşesiyse
            if 0 > -p-sin(b)*(-w/2+(0))-cos(b)*(h/2-(h)):
                # Sol alt köşeyi listeye ekle.
                points.append(QPointF(0, h))
            # Eğer arayüzün sol üst köşesi çokgenin bir köşesiyse
            if 0 > -p-sin(b)*(-w/2+(0))-cos(b)*(h/2-(0)):
                # Sol üst köşeyi listeye ekle.
                points.append(QPointF(0, 0))
            # Eğer arayüzün sağ üst köşesi çokgenin bir köşesiyse
            if 0 > -p-sin(b)*(-w/2+(w))-cos(b)*(h/2-(0)):
                # Sağ üst köşeyi listeye ekle.
                points.append(QPointF(w, 0))
            if 0 > -p-sin(b)*(-w/2+(w))-cos(b)*(h/2-(h)):
                # Sağ üst köşeyi listeye ekle.
                points.append(QPointF(w, h))
        # Eğer bölge ters çevrilmemeliyse
        else:
            # Eğer arayüzün sol üst köşesi çokgenin bir köşesiyse
            if 0 < -p-sin(b)*(-w/2+(0))-cos(b)*(h/2-(0)):
                # Sol üst köşeyi listeye ekle.
                points.append(QPointF(0, 0))
            # Eğer arayüzün sol alt köşesi çokgenin bir köşesiyse
            if 0 < -p-sin(b)*(-w/2+(0))-cos(b)*(h/2-(h)):
                # Sol alt köşeyi listeye ekle.
                points.append(QPointF(0, h))
            # Eğer arayüzün sağ alt köşesi çokgenin bir köşesiyse
            if 0 < -p-sin(b)*(-w/2+(w))-cos(b)*(h/2-(h)):
                # Sağ alt köşeyi listeye ekle.
                points.append(QPointF(w, h))
            # Eğer arayüzün sağ üst köşesi çokgenin bir köşesiyse
            if 0 < -p-sin(b)*(-w/2+(w))-cos(b)*(h/2-(0)):
                # Sağ üst köşeyi listeye ekle.
                points.append(QPointF(w, 0))
        # Başlangıç noktasını listeye ekle.
        points.append(QPointF(x2, y2))
        # Çizim kalemini 2 birimlik önplan rengi olarak değiştir.
        painter.setPen(self.fg2)
        # Çizim fırçasını gökyüzü ya da yeryüzü rengi olarak değiştir.
        painter.setBrush(self.sky if sky else self.ground)
        # Bölgeyi hesaplanan çokgen ile çizdir.
        painter.drawPolygon(points)

    # Bu metod çizim komponenti/arayüz boyutu değiştiği zaman çağılır.
    # Bu metod parametre olarak çizim komponentinin kendisini ve
    # bir olay objesi alır.
    # Herhangi bir şey döndürmez.
    def resizeEvent(self, e):
        # Sınıfın miras alındığı sınıfın metodunu çağır.
        super().resizeEvent(e)
        # Çizim komponentinin (alanının) boyutları alınarak
        # çizim kompenentinde saklanır.
        self.width = self.geometry().width()
        self.height = self.geometry().height()


# Çalıştırılan python modulü ana modül mü diye kontrol et.
if __name__ == '__main__':
    # Programa verilen komut satırı argümanlarından yeni bir uygulama
    # objesi oluştur.
    app = QApplication(sys.argv) # Uygulama objesi
    # En başta tanımlanan Form sınıfından arayüz penceresi oluşturulur.
    form = Form() # Arayüz penceresi
    # Arayüzü görünür hale getir.
    form.show()
    # Uygulamayı başlat ve döndürülen çıkış koduyla programı da sonlandır.
    sys.exit(app.exec_())
