import os
import sys

from math import cos, radians, tan, pi, sin

try:
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtOpenGL import *
    from PySide6.QtOpenGLWidgets import *
except ImportError:
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtOpenGL import *


if "NO_GL" in os.environ and os.environ["NO_GL"] == "1":
    print("NO_GL is set, using QWidget instead of QOpenGLWidget", file=sys.stderr)
    WidgetClass = QWidget
else:
    WidgetClass = QOpenGLWidget


class QPrimaryFlightDisplay(WidgetClass):
    def __init__(self, parent=None):
        super(QPrimaryFlightDisplay, self).__init__(parent)
        self.pitch = 0
        self.roll = 0
        self.skipskid = 0
        self.heading = 0
        self.airspeed = 0
        self.alt = 0
        self.vspeed = 0
        self.battery = 0
        self.arm = False
        self.zoom = 1
        if WidgetClass == QOpenGLWidget:
            self.setAutoFillBackground(False)
            fmt = QSurfaceFormat()
            fmt.setSamples(8)
            self.setFormat(fmt)
        QApplication.instance().paletteChanged.connect(self.update_style)
        self.update_style()

    def update_style(self, palette=None):
        palette = palette or self.palette()
        self.dpi = min(self.logicalDpiX(), self.logicalDpiY())
        self.scale = (self.dpi / 96) * self.zoom
        z = self.zoom
        s = self.scale
        self.fg = palette.color(QPalette.WindowText)
        self.fg2 = QPen(self.fg, 2 * s)
        self.fg3 = QPen(self.fg, 3 * s)
        self.fg3.setCapStyle(Qt.RoundCap)
        self.hg = palette.color(
            QPalette.Active, QPalette.Highlight)
        self.hg2 = QPen(self.hg, 2 * s)
        self.hg2.setJoinStyle(Qt.RoundJoin)
        self.hg2.setCapStyle(Qt.RoundCap)
        self.hg4 = QPen(self.hg, 4 * s)
        self.hg4.setJoinStyle(Qt.RoundJoin)
        self.hg4.setCapStyle(Qt.RoundCap)
        self.hg8 = QPen(self.hg, 8 * s)
        self.hg8.setJoinStyle(Qt.RoundJoin)
        self.hg8.setCapStyle(Qt.RoundCap)
        self.bsbr = palette.color(QPalette.Base)
        self.wrn = QColor(0xf6, 0x74, 0x00, 0xff)
        self.wrn3 = QPen(self.wrn, 3 * s)
        self.wrn3.setJoinStyle(Qt.RoundJoin)
        self.wrn3.setCapStyle(Qt.RoundCap)
        self.err = QColor(0xda, 0x44, 0x53, 0xff)
        self.err3 = QPen(self.err, 3 * s)
        self.err3.setJoinStyle(Qt.RoundJoin)
        self.err3.setCapStyle(Qt.RoundCap)
        self.pst = QColor(0x27, 0xae, 0x60)
        self.sky = palette.color(QPalette.Base)
        self.ground = palette.color(QPalette.Window)
        self.font12 = QFont("Arial", 12 * z)
        self.font16 = QFont("Arial", 16 * z)
        self.font20 = QFont('Arial', 20 * z)

    def paintEvent(self, e):
        dpi = min(self.logicalDpiX(), self.logicalDpiY())
        if dpi != self.dpi:
            self.update_style()
        self.painter = QPainter()
        self.painter.begin(self)
        self.painter.setRenderHints(QPainter.Antialiasing)
        self.painter.setRenderHints(QPainter.TextAntialiasing)
        self.painter.setPen(self.fg2)
        self.painter.setFont(self.font16)
        self.draw_region()
        self.draw_region(sky=True)
        self.draw_markers()
        self.draw_cursor()
        self.draw_skipskid()
        self.draw_heading()
        self.draw_airspeed()
        self.draw_vspeed()
        self.draw_altimeter()
        self.draw_status()
        self.painter.end()

    def draw_status(self):
        w = self.geometry().width()
        h = self.geometry().height()
        s = self.scale
        painter = self.painter
        if self.battery is not None:
            painter.setBrush(self.bsbr)
            painter.setPen(self.fg2)
            rect = QRectF(w - 100 * s, h - 50 * s, 100 * s, 50 * s)
            painter.drawRect(rect)
            painter.setBrush(self.hg)
            painter.setPen(self.hg)
            painter.drawRect(w - 98 * s, h - 48 * s, (96 * s) * (self.battery / 100), 46 * s)
            painter.setFont(self.font16)
            painter.setPen(self.fg)
            painter.drawText(rect, Qt.AlignCenter, f"{round(self.battery)}%")

        if self.arm is not None:
            painter.setBrush(self.bsbr)
            painter.setPen(self.fg2)
            rect = QRectF(0, h - 50 * s, 100 * s, 50 * s)
            painter.drawRect(rect)
            painter.setBrush(self.pst if self.arm else self.err)
            painter.setPen(self.pst if self.arm else self.err)
            painter.drawRect(2 * s, h - 48 * s, 96 * s, 46 * s)
            painter.setFont(self.font16)
            painter.setPen(self.fg)
            painter.drawText(
                rect,
                Qt.AlignCenter,
                "Armed" if self.arm else "Disarmed"
            )

    def draw_vspeed(self):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        s = self.scale
        v = self.vspeed
        per = 30 * s
        inc = 0.5
        r = per / inc
        x2 = 15 * w / 16
        x1 = 15 * w / 16 - 40 * s - 10 * s
        y1 = 4 * h / 16
        y2 = h - y1
        painter.setFont(self.font12)
        self.bsbr.setAlpha(128)
        painter.setBrush(self.bsbr)
        self.bsbr.setAlpha(255)
        painter.setPen(self.fg)
        painter.drawRect(x1, y1, x2 - x1 - 10 * s, y2 - y1)
        painter.setPen(self.fg3)
        painter.drawLine(QLineF(x1, y1, x1, y2))
        painter.save()
        painter.setClipRect(QRectF(x1, y1, x2 - x1, y2 - y1))
        l1 = int(((y1 + y2) / 2 + v * r - y2) / per) - 1
        l2 = int(((y1 + y2) / 2 + v * r - y1) / per) + 1
        for i in range(l1, l2 + 1):
            pos = -i * per + v * r
            if (i % 2) == 0:
                painter.drawLine(
                    QLineF(x1, (y1 + y2) / 2 + pos, x1 + 15 * s, (y1 + y2) / 2 + pos))
                painter.drawText(
                    QRectF(
                        x1 + 18 * s,
                        (y1 + y2) / 2 + pos - 20 * s,
                        x2 - 18 * s - x1,
                        40 * s
                    ),
                    Qt.AlignVCenter | Qt.AlignLeft,
                    str(int(round(abs(i * inc))))
                )
            else:
                painter.drawLine(
                    QLineF(x1, (y1 + y2) / 2 + pos, x1 + 8 * s, (y1 + y2) / 2 + pos))
        painter.restore()
        painter.setBrush(self.bsbr)
        painter.drawPolygon([
            QPointF(x2, (y1 + y2) / 2 - 15 * s),
            QPointF(x2, (y1 + y2) / 2 + 15 * s),
            QPointF(x1 - 33 * s, (y1 + y2) / 2 + 15 * s),
            QPointF(x1 - 33 * s, (y1 + y2) / 2 - 15 * s),
        ])
        painter.setFont(self.font16)
        painter.drawText(
            QRectF(
                x1,
                (y1 + y2) / 2 - 25 * s,
                x2 - x1 - 8 * s,
                50 * s
            ),
            Qt.AlignVCenter | Qt.AlignRight,
            str(float(round(abs(v), 1)))
        )

    def draw_altimeter(self):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        s = self.scale
        v = self.alt
        per = 70 * s
        inc = 5
        r = per / inc
        x2 = 15 * w / 16 - 40 * s
        x1 = 15 * w / 16 - 90 * s - 40 * s
        y1 = h / 15 + 20 * s
        y2 = h - y1
        painter.setFont(self.font16)
        self.bsbr.setAlpha(128)
        painter.setBrush(self.bsbr)
        self.bsbr.setAlpha(255)
        painter.setPen(self.fg)
        painter.drawRect(x1, y1, x2 - x1 - 10 * s, y2 - y1)
        painter.setPen(self.fg3)
        painter.drawLine(QLineF(x1, y1, x1, y2))
        painter.save()
        painter.setClipRect(QRectF(x1, y1, x2 - x1, y2 - y1))
        l1 = int(((y1 + y2) / 2 + v * r - y2) / per) - 1
        l2 = int(((y1 + y2) / 2 + v * r - y1) / per) + 1
        for i in range(l1, l2 + 1):
            pos = -i * per + v * r
            if (i % 2) == 0:
                painter.drawLine(
                    QLineF(x1, (y1 + y2) / 2 + pos, x1 + 25 * s, (y1 + y2) / 2 + pos))
                painter.drawText(
                    QRectF(
                        x1 + 33 * s,
                        (y1 + y2) / 2 + pos - 20 * s,
                        x2 - 33 * s - x1,
                        40 * s
                    ),
                    Qt.AlignVCenter | Qt.AlignLeft,
                    str(i * inc)
                )
            else:
                painter.drawLine(
                    QLineF(x1, (y1 + y2) / 2 + pos, x1 + 15 * s, (y1 + y2) / 2 + pos))
            for j in range(-5, 6):
                painter.drawLine(QLineF(x1, (y1 + y2) / 2 + pos + j / 5 * per,
                                 x1 + 8 * s, (y1 + y2) / 2 + pos + j / 5 * per))
        painter.restore()
        painter.setBrush(self.bsbr)
        painter.drawPolygon([
            QPointF(x2, (y1 + y2) / 2 - 25 * s),
            QPointF(x2, (y1 + y2) / 2 + 25 * s),
            QPointF(x1 + 33 * s, (y1 + y2) / 2 + 25 * s),
            QPointF(x1, (y1 + y2) / 2),
            QPointF(x1 + 33 * s, (y1 + y2) / 2 - 25 * s),
        ])
        painter.setFont(self.font20)
        painter.drawText(
            QRectF(
                x1,
                (y1 + y2) / 2 - 25 * s,
                x2 - 33 * s - x1,
                50 * s
            ),
            Qt.AlignVCenter | Qt.AlignRight,
            str(round(v))
        )

    def draw_airspeed(self):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        s = self.scale
        v = self.airspeed
        per = 40 * s
        inc = 4
        r = per / inc
        x1 = w / 16
        x2 = x1 + 90 * s
        y1 = h / 15 + 20 * s
        y2 = h - y1 - 7 * s
        self.bsbr.setAlpha(128)
        painter.setBrush(self.bsbr)
        self.bsbr.setAlpha(255)
        painter.setPen(self.fg)
        painter.drawRect(x1 + 10 * s, y1, x2 - x1 - 10 * s, y2 - y1)
        painter.setPen(self.fg3)
        painter.drawLine(QLineF(x2, y1, x2, y2))
        painter.save()
        painter.setClipRect(QRectF(x1, y1, x2 - x1, y2 - y1))
        l1 = int(((y1 + y2) / 2 + v * r - y2) / per) - 1
        l2 = int(((y1 + y2) / 2 + v * r - y1) / per) + 1
        for i in range(l1, l2 + 1):
            pos = -i * per + v * r
            if (i % 2) == 0:
                painter.drawLine(
                    QLineF(x2, (y1 + y2) / 2 + pos, x2 - 25 * s, (y1 + y2) / 2 + pos))
                painter.drawText(
                    QRectF(
                        x1,
                        (y1 + y2) / 2 + pos - 20 * s,
                        x2 - 33 * s - x1,
                        40 * s
                    ),
                    Qt.AlignVCenter | Qt.AlignRight,
                    str(i * inc)
                )
            else:
                painter.drawLine(
                    QLineF(x2, (y1 + y2) / 2 + pos, x2 - 15 * s, (y1 + y2) / 2 + pos))
        painter.restore()
        painter.setBrush(self.bsbr)
        painter.drawPolygon([
            QPointF(x1, (y1 + y2) / 2 - 25 * s),
            QPointF(x1, (y1 + y2) / 2 + 25 * s),
            QPointF(x2 - 33 * s, (y1 + y2) / 2 + 25 * s),
            QPointF(x2, (y1 + y2) / 2),
            QPointF(x2 - 33 * s, (y1 + y2) / 2 - 25 * s),
        ])
        painter.setFont(self.font20)
        painter.drawText(
            QRectF(
                x1,
                (y1 + y2) / 2 - 25 * s,
                x2 - 33 * s - x1,
                50 * s
            ),
            Qt.AlignVCenter | Qt.AlignRight,
            str(round(v))
        )

    def draw_heading(self):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        s = self.scale
        if self.heading is None:
            return
        hd = -radians(self.heading)
        x = min(4 * w / 16, 4 * h / 16)
        painter.setPen(self.fg3)
        self.bsbr.setAlpha(128)
        painter.setBrush(self.bsbr)
        self.bsbr.setAlpha(255)
        painter.drawEllipse(w / 2 - x, 17 * h / 16 - x, 2 * x, 2 * x)
        for i in range(72):
            trans = QTransform()
            trans.translate(w / 2, 17 * h / 16)
            trans.rotateRadians((i / 72) * 2 * pi + hd)
            painter.setTransform(trans)
            if (i % 2) == 0:
                if ((i // 2) % 3) == 0:
                    t = str(i // 2)
                    if i == 0:
                        t = "N"
                    elif i == 18:
                        t = "E"
                    elif i == 36:
                        t = "S"
                    elif i == 54:
                        t = "W"
                    painter.drawText(
                        QRectF(
                            -20 * s, - x + 15 * s, 40 * s, 40 * s
                        ),
                        Qt.AlignCenter | Qt.AlignTop, t
                    )
                painter.drawLine(QLineF(0, - x, 0, - x + 15 * s))
            elif i == 9 or i == 27 or i == 45 or i == 63:
                painter.setPen(self.wrn3)
                painter.drawLine(QLineF(0, - x, 0, - x + 30 * s))
                painter.setPen(self.fg3)
            else:
                painter.drawLine(QLineF(0, - x, 0, - x + 7 * s))
            painter.resetTransform()
        painter.setBrush(self.hg)
        painter.setPen(self.hg2)
        painter.drawLine(QLineF(w / 2, 17 * h / 16 - x, w / 2, 17 * h / 16 + x))
        painter.setPen(self.hg4)
        painter.drawPolygon([
            QPointF(w / 2 - 7 * s, 17 * h / 16 - x + 17 * s),
            QPointF(w / 2, 17 * h / 16 - x + 2 * s),
            QPointF(w / 2 + 7 * s, 17 * h / 16 - x + 17 * s)
        ])
        painter.setPen(self.fg3)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(w / 2 - x, 17 * h / 16 - x, 2 * x, 2 * x)

    def draw_markers(self):
        p = self.pitch
        s = self.scale
        r = 50
        p *= ((50 / 5) * s) * 180 / pi
        for i in range(1, 20):
            size = 80 * s * ((1 / 4) * i + 1 / 2) * 10 / (5 + i)
            if -(4 * r * 1.1 * s) < p + i * r * s < 4 * r * 1.1 * s:
                self.draw_marker(p + i * r * s,
                                 size if (i % 2) == 0 else 40 * s, f"  {i*r//10}", 255 - 255 * abs(p + i * r * s) / (4 * r * 1.1 * s))
            if -(4 * r * 1.1 * s) < p - i * 50 * s < 4 * r * 1.1 * s:
                self.draw_marker(p - i * r * s,
                                 size if (i % 2) == 0 else 40 * s, f"  {i*r//10}", 255 - 255 * abs(p - i * r * s) / (4 * r * 1.1 * s))

    def draw_marker(self, p, r, t="", alpha=128):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        b = -self.roll
        s = self.scale
        self.fg.setAlpha(alpha)
        self.fg3.setColor(self.fg)
        painter.setPen(self.fg3)
        painter.drawLine(QLineF(
            w / 2 - p * sin(b) - r * cos(b),
            h / 2 + p * cos(b) - r * sin(b),
            w / 2 - p * sin(b) + r * cos(b),
            h / 2 + p * cos(b) + r * sin(b)))
        trans = QTransform()
        trans.translate(w / 2, h / 2)
        trans.rotateRadians(b)
        painter.setTransform(trans)
        painter.setPen(self.fg)
        painter.setFont(self.font16)
        painter.drawText(r, p + 8 * s, t)
        painter.resetTransform()
        self.fg.setAlpha(255)
        self.fg3.setColor(self.fg)

    def draw_skipskid(self):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        b = -self.roll
        s = self.scale
        painter.setPen(self.fg)
        x = min(w / 2 - 50 * s, h / 2 - 50 * s)
        painter.setPen(self.fg3)
        painter.setBrush(self.fg)
        painter.drawArc(w / 2 - x, h / 2 - x, x * 2, x * 2, 45 * 16, 90 * 16)
        if b < -7 * pi / 32 or b > 7 * pi / 32:
            if -pi / 4 < b < pi / 4:
                painter.setPen(self.fg3)
                painter.setBrush(self.fg)
            elif -pi / 3 < b < pi / 3:
                painter.setPen(self.wrn3)
                painter.setBrush(self.wrn)
            else:
                painter.setPen(self.err3)
                painter.setBrush(self.err)
                b = pi / 3 if b > 0 else -pi / 3
            painter.drawArc(w / 2 - x, h / 2 - x, x * 2, x * 2, 30 * 16, 120 * 16)
        else:
            painter.setPen(self.fg3)
            painter.setBrush(self.fg)
        painter.drawEllipse(w / 2 - 2 * s, h / 2 - x - 2 * s, 4 * s, 4 * s)
        ps = [-pi / 6, pi / 6, pi / 3, -pi / 3, pi /
              4, -pi / 4, pi / 18, -pi / 18, pi / 9, -pi / 9]
        for a in ps:
            if (a < -pi / 4 or a > pi / 4) and not (b < -7 * pi / 32 or b > 7 * pi / 32):
                continue
            trans = QTransform()
            trans.translate(w / 2, h / 2)
            trans.rotateRadians(a)
            painter.setTransform(trans)
            painter.drawText(-10 * s, -x - 10 * s, str(abs(round(a / pi * 180))))
            painter.drawEllipse(0 - 2 * s, -x - 2 * s, 4 * s, 4 * s)
            painter.resetTransform()
        trans = QTransform()
        trans.translate(w / 2, h / 2)
        trans.rotateRadians(b)
        painter.setTransform(trans)
        painter.drawEllipse(-5 * s, -x - 5 * s, 10 * s, 10 * s)
        px = -20 * s - self.skipskid * 20 * s
        painter.drawRect(px, -x + 15 * s, 40 * s, 10 * s)
        painter.resetTransform()

    def draw_cursor(self):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        s = self.scale
        path = QPainterPath()
        path.moveTo(w / 2 - 70 * s, h / 2)
        path.lineTo(w / 2 - 40 * s, h / 2)
        path.lineTo(w / 2, h / 2 + 30 * s)
        path.lineTo(w / 2 + 40 * s, h / 2)
        path.lineTo(w / 2 + 70 * s, h / 2)
        painter.setPen(self.hg8)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        painter.setPen(self.hg)
        painter.setBrush(self.hg)
        painter.drawEllipse(w / 2 - 4, h / 2 - 4, 8 * s, 8 * s)

    def compute_horizon(self, p, b):
        w = self.geometry().width()
        h = self.geometry().height()
        if b != pi / 2 and b != -pi / 2:
            x1 = 0
            y1 = h / 2 - w / 2 * tan(b) + p / cos(b)
            x2 = w
            y2 = h / 2 + w / 2 * tan(b) + p / cos(b)
        elif b == pi / 2:
            x1 = 0
            y1 = -1
            x2 = w
            y2 = h + 1
        elif b == -pi / 2:
            x1 = w
            y1 = h + 1
            x2 = 0
            y2 = -1
        try:
            if y1 > h:
                x1 = (h / 2 - p / cos(b)) / tan(b) + w / 2
                y1 = h
            elif y1 < 0:
                x1 = (-h / 2 - p / cos(b)) / tan(b) + w / 2
                y1 = 0
            if y2 > h:
                x2 = (h / 2 - p / cos(b)) / tan(b) + w / 2
                y2 = h
            elif y2 < 0:
                x2 = (-h / 2 - p / cos(b)) / tan(b) + w / 2
                y2 = 0
        except ZeroDivisionError:
            pass
        return x1, y1, x2, y2

    def draw_region(self, sky=False):
        painter = self.painter
        w = self.geometry().width()
        h = self.geometry().height()
        p = self.pitch
        b = -self.roll
        s = self.scale
        inv = not sky
        p *= ((50 / 5) * s) * 180 / pi
        if sky:
            p = -p
        if b >= 0:
            inv ^= ((b // (pi)) % 2) == 0
            b %= pi
        else:
            inv ^= ((b // (-pi)) % 2) == 0
            b %= -pi
        if pi / 2 < b:
            b -= pi
            inv = not inv
        elif b < -pi / 2:
            b += pi
            inv = not inv
        if inv:
            p = -p
        x1, y1, x2, y2 = self.compute_horizon(p, b)
        points = []
        points.append(QPointF(x1, y1))
        if inv:
            if 0 > -p - sin(b) * (-w / 2 + (0)) - cos(b) * (h / 2 - (h)):
                points.append(QPointF(0, h))
            if 0 > -p - sin(b) * (-w / 2 + (0)) - cos(b) * (h / 2 - (0)):
                points.append(QPointF(0, 0))
            if 0 > -p - sin(b) * (-w / 2 + (w)) - cos(b) * (h / 2 - (0)):
                points.append(QPointF(w, 0))
            if 0 > -p - sin(b) * (-w / 2 + (w)) - cos(b) * (h / 2 - (h)):
                points.append(QPointF(w, h))
        else:
            if 0 < -p - sin(b) * (-w / 2 + (0)) - cos(b) * (h / 2 - (0)):
                points.append(QPointF(0, 0))
            if 0 < -p - sin(b) * (-w / 2 + (0)) - cos(b) * (h / 2 - (h)):
                points.append(QPointF(0, h))
            if 0 < -p - sin(b) * (-w / 2 + (w)) - cos(b) * (h / 2 - (h)):
                points.append(QPointF(w, h))
            if 0 < -p - sin(b) * (-w / 2 + (w)) - cos(b) * (h / 2 - (0)):
                points.append(QPointF(w, 0))
        points.append(QPointF(x2, y2))
        painter.setPen(self.fg2)
        painter.setBrush(self.sky if sky else self.ground)
        painter.drawPolygon(points)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    pfd = QPrimaryFlightDisplay()
    pfd.show()
    try:
        sys.exit(app.exec())
    except AttributeError:
        sys.exit(app.exec_())
