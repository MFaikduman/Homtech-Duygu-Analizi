"""Desktop photo and camera workflow for facial-expression analysis."""

import sys
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

import cv2
from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QImage, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRubberBand,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from homtech.capture import AnalyzeImage, CameraStream, LiveAnalysis
from homtech.course_panel import CoursePanel
from homtech.demo_examples import EXAMPLES
from homtech.ml.capture_data import DEFAULT_ORIGINAL_ARCHIVE
from homtech.ml.live import LiveConsensus
from homtech.ml.predict import DEFAULT_CAPTURE_MODEL, Expression


THEME = """
QWidget { color: #F4F2EE; font-family: "Segoe UI"; font-size: 14px; }
QMainWindow, QWidget#workspace, QScrollArea#workspaceScroll { background: #17181B; }
QScrollBar:vertical { background: #1B1C20; width: 10px; }
QScrollBar::handle:vertical { background: #55545B; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QWidget#topBar { background: #1C1D21; border-bottom: 1px solid #35363C; }
QLabel#brandMark { background: #E3BE79; color: #211A12; border-radius: 10px;
                  font-size: 21px; font-weight: 800; }
QLabel#brandName { font-size: 17px; font-weight: 700; }
QLabel#brandDetail { color: #B8BAC2; font-size: 12px; }
QLabel#pageTitle { color: #FFF3E0; font-size: 36px; font-weight: 700; }
QLabel#heroLead { color: #D2CBC2; font-size: 14px; }
QLabel#heading { font-size: 20px; font-weight: 700; }
QLabel#muted { color: #BFC0C7; }
QLabel#caption { color: #B2B4BE; font-size: 12px; }
QLabel#sceneName { font-size: 17px; font-weight: 650; }
QLabel#decisionTitle { font-size: 20px; font-weight: 700; }
QLabel#expression { color: #F5D394; font-size: 26px; font-weight: 700; }
QLabel#secondExpression { color: #C4C2C9; font-size: 14px; }
QFrame#panel { background: #202126; border: 1px solid #383941; border-radius: 16px; }
QFrame#modesPanel {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #302922,stop:0.41 #252327,stop:1 #202126);
    border: 1px solid #594B3B; border-radius: 17px;
}
QFrame#modeIndicator { background: #242325; border: 1px solid #5C4A34; border-radius: 10px; }
QFrame#analysisReadout {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #352C23,stop:1 #27272C);
    border: 1px solid #554737; border-left: 2px solid #B89161; border-radius: 10px;
}
QFrame#decisionCard { background: #26272D; border: 1px solid #41424A; border-radius: 12px; }
QFrame#decisionCard[tone="gold"] { background: #2B2724; border-color: #7A5E39; }
QFrame#decisionCard[tone="green"] { background: #252C28; border-color: #4D6653; }
QFrame#hairline { background: #383A40; }
QLabel#chip { background: #313239; border: 1px solid #4A4C55; border-radius: 12px;
             color: #D8D9E0; padding: 4px 10px; font-size: 12px; font-weight: 600; }
QLabel#chip[state="gold"] { background: #3B3021; border-color: #765A35; color: #F3D197; }
QLabel#chip[state="green"] { background: #29382F; border-color: #4F6B59; color: #C2E4CD; }
QPushButton { background: #303138; border: 1px solid #50525B; border-radius: 8px;
              padding: 10px 13px; min-height: 20px; font-weight: 650; }
QPushButton:hover { background: #3A3B44; border-color: #A5906C; }
QPushButton:pressed { background: #25262A; }
QPushButton#primary { background: #E4BF7D; border-color: #E4BF7D; color: #211A12; }
QPushButton#primary:hover { background: #F3D299; border-color: #F3D299; }
QPushButton#primary:pressed { background: #CDA767; border-color: #CDA767; }
QPushButton#approve { background: #3B3021; border-color: #987744; color: #F5D89F; }
QPushButton#approve:hover { background: #4D3D28; border-color: #C3A26C; }
QPushButton#approve:pressed { background: #302619; }
QPushButton:focus, QPushButton#primary:focus, QPushButton#approve:focus { border-color: #FFE0A3; }
QPushButton:disabled, QPushButton#primary:disabled, QPushButton#approve:disabled {
    background: #2A2B31; border-color: #3D3F46; color: #8E909A;
}
QPushButton#homeMode {
    background: #24252A; border-color: #49494F; border-radius: 11px; padding: 0; min-height: 95px;
}
QPushButton#homeMode:hover { background: #2E2D33; border-color: #A5906C; }
QPushButton#homeMode[modeState="active"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #473825,stop:1 #302921);
    border-color: #AC8857;
}
QPushButton#homeMode[modeState="selected"] { background: #34302C; border-color: #E0BA78; }
QPushButton#homeMode:focus { border-color: #FFE0A3; }
QLabel#modeCardName { font-size: 16px; font-weight: 700; color: #F5F0E9; }
QLabel#modeCardStatus { font-size: 11px; font-weight: 650; color: #E9C389; }
QLabel#modeCardValues { font-size: 12px; color: #D3C9BA; }
QProgressBar#sceneLevel { background: #464049; border: none; border-radius: 2px; }
QPushButton#viewNav { background: transparent; border-color: transparent; color: #CBC9C7; }
QPushButton#viewNav:hover, QPushButton#viewNav:focus { border-color: #80633A; }
QPushButton#viewNav:checked { background: #3A3022; border-color: #765A35; color: #F7D9A2; }
QPushButton#demoExample, QPushButton#previewSuggestion { background: #28292E; border: 1px solid #45464F;
    border-radius: 7px; font-size: 13px; padding: 4px 8px; min-height: 20px; }
QPushButton#previewSuggestion { padding: 10px 8px; }
QPushButton#demoExample:hover, QPushButton#demoExample:focus,
QPushButton#previewSuggestion:hover, QPushButton#previewSuggestion:focus { border-color: #D7B070; }
QPushButton#demoExample:checked, QPushButton#previewSuggestion:checked {
    color: #F7D9A2; background: #3B3021; border-color: #AC8956;
}
QPushButton#demoExample:disabled, QPushButton#previewSuggestion:disabled { color: #898991; }
"""


@dataclass(frozen=True)
class Scene:
    title: str
    kelvin: int
    brightness: int
    color: str
    purpose: str

    @property
    def settings(self) -> str:
        return f"{self.kelvin:,} K  ·  %{self.brightness} parlaklık".replace(",", ".")


BALANCED = Scene("Günlük", 3500, 55, "#F5D9A4", "Dengeli ışık")
WARM = Scene("Sıcak ortam", 3000, 68, "#F4BA66", "Sohbet ve dinlenme")
SOFT = Scene("Rahatlama", 2700, 33, "#F19A62", "Yumuşak, loş ışık")
BRIGHT = Scene("Odak", 4200, 78, "#F4E9D0", "Okuma ve çalışma")
HOME_MODES = (BALANCED, WARM, SOFT, BRIGHT)

EXPRESSIONS = {
    "happy": ("Mutluluk", WARM),
    "angry": ("Kızgınlık", SOFT),
    "fear": ("Korku", SOFT),
    "sad": ("Üzüntü", WARM),
    "surprise": ("Şaşkınlık", BRIGHT),
    "neutral": ("Nötr", BALANCED),
    "disgust": ("İğrenme", None),
}
PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")
WORKSPACE_WIDTH = 1440


def label(text: str, style: str, *, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(style)
    widget.setWordWrap(wrap)
    return widget


def chip(text: str) -> QLabel:
    widget = label(text, "chip")
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
    widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return widget


def rule() -> QFrame:
    line = QFrame()
    line.setObjectName("hairline")
    line.setFixedHeight(1)
    return line


class ModeCard(QPushButton):
    def __init__(self, scene: Scene):
        super().__init__()
        self.setObjectName("homeMode")
        self.setAccessibleName(scene.title)
        self.setToolTip(scene.settings)

        content = QWidget(self)
        content.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(content)

        column = QVBoxLayout(content)
        column.setContentsMargins(12, 10, 12, 9)
        column.setSpacing(4)
        headline = QHBoxLayout()
        headline.setSpacing(7)
        swatch = QLabel()
        swatch.setFixedSize(16, 16)
        swatch.setStyleSheet(f"background: {scene.color}; border-radius: 8px; border: 1px solid #F4DFC0;")
        headline.addWidget(swatch)
        headline.addWidget(label(scene.title, "modeCardName"), 1)
        self.state = label("", "modeCardStatus")
        headline.addWidget(self.state)
        column.addLayout(headline)
        column.addWidget(label(scene.purpose, "caption"))
        column.addStretch()

        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addWidget(label(scene.settings.replace(" parlaklık", ""), "modeCardValues"), 1)
        level = QProgressBar()
        level.setObjectName("sceneLevel")
        level.setTextVisible(False)
        level.setValue(scene.brightness)
        level.setFixedSize(35, 4)
        level.setStyleSheet(f"QProgressBar::chunk {{ background: {scene.color}; border-radius: 2px; }}")
        footer.addWidget(level)
        column.addLayout(footer)

    def set_mode_state(self, state: str):
        self.state.setText({"active": "Etkin", "selected": "Seçili"}.get(state, ""))
        if self.property("modeState") != state:
            self.setProperty("modeState", state)
            style = self.style()
            style.unpolish(self)
            style.polish(self)


class PhotoPreview(QWidget):
    region_selected = Signal(object)
    photo_dropped = Signal(object)

    def __init__(self):
        super().__init__()
        self.image = QImage()
        self.face = None
        self.mirrored = False
        self._selecting = False
        self._selection_start = None
        self._selection = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._drop_highlight = False
        self.status_text = ""
        self.status_tone = "neutral"
        self._image_fade = QVariantAnimation(self)
        self._image_fade.setDuration(170)
        self._image_fade.setStartValue(0.0)
        self._image_fade.setEndValue(1.0)
        self._image_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._image_fade.valueChanged.connect(self.update)
        self.setMinimumHeight(235)
        self.setAccessibleName("Fotoğraf ve kamera görüntüsü")

    def enable_photo_drop(self, enabled):
        self.setAcceptDrops(enabled)
        self._set_drop_highlight(False)

    def _set_drop_highlight(self, active):
        if active != self._drop_highlight:
            self._drop_highlight = active
            self.update()

    def _dropped_photo(self, event):
        if not self.acceptDrops() or not (event.possibleActions() & Qt.DropAction.CopyAction):
            return None
        urls = event.mimeData().urls()
        if len(urls) != 1 or not urls[0].isLocalFile():
            return None
        path = Path(urls[0].toLocalFile())
        return path if path.suffix.lower() in PHOTO_EXTENSIONS and path.is_file() else None

    def dragEnterEvent(self, event):
        if self._dropped_photo(event) is None:
            event.ignore()
            return
        self._set_drop_highlight(self._screen_rect().contains(event.position()))
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def dragMoveEvent(self, event):
        accepted = self._screen_rect().contains(event.position()) and self._dropped_photo(event) is not None
        self._set_drop_highlight(accepted)
        if accepted:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_drop_highlight(False)
        event.accept()

    def dropEvent(self, event):
        self._set_drop_highlight(False)
        path = self._dropped_photo(event)
        if path is None or not self._screen_rect().contains(event.position()):
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        self.photo_dropped.emit(path)

    def clear(self):
        self._image_fade.stop()
        self.enable_selection(False)
        self.image = QImage()
        self.face = None
        self.mirrored = False
        self.update()

    def set_mirrored(self, mirrored: bool):
        self.mirrored = mirrored
        self.update()

    def enable_selection(self, enabled):
        self._selecting = enabled
        self._selection_start = None
        self._selection.hide()
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor)

    def _tablet_rect(self):
        available = QRectF(self.rect()).adjusted(5, 5, -5, -7)
        body = QRectF(0, 0, min(available.width(), available.height() * 1.9), available.height())
        body.moveCenter(available.center())
        return body

    def _screen_rect(self):
        return self._tablet_rect().adjusted(13, 21, -13, -22)

    def _image_rect(self, bounds):
        scaled = self.image.size().scaled(bounds.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRectF(0, 0, scaled.width(), scaled.height())
        rect.moveCenter(bounds.center())
        return rect

    def _mirror_x(self, x, width):
        return max(0.0, 1.0 - (x + width)) if self.mirrored else x

    def mousePressEvent(self, event):
        if not self._selecting or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        area = self._image_rect(self._screen_rect())
        if area.contains(event.position()):
            self._selection_start = event.position()
            self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        if self._selection_start is None:
            return super().mouseMoveEvent(event)
        area = self._image_rect(self._screen_rect())
        region = QRectF(self._selection_start, event.position()).normalized().intersected(area)
        self._selection.setGeometry(region.toAlignedRect())
        self._selection.show()

    def mouseReleaseEvent(self, event):
        if self._selection_start is None or event.button() != Qt.MouseButton.LeftButton:
            return super().mouseReleaseEvent(event)
        area = self._image_rect(self._screen_rect())
        region = QRectF(self._selection_start, event.position()).normalized().intersected(area)
        self._selection_start = None
        self._selection.hide()
        if min(region.width(), region.height()) >= 12:
            width = region.width() / area.width()
            display_x = (region.x() - area.x()) / area.width()
            self.region_selected.emit((self._mirror_x(display_x, width),
                                       (region.y() - area.y()) / area.height(),
                                       width, region.height() / area.height()))

    def set_status(self, text: str, tone: str = "neutral"):
        if (text, tone) != (self.status_text, self.status_tone):
            self.status_text, self.status_tone = text, tone
            self.setAccessibleDescription(text)
            self.update()

    def set_image(self, pixels, width, height, stride, *, face=None, animate=False):
        self.image = QImage(pixels, width, height, stride, QImage.Format.Format_RGB888).copy()
        self.face = face
        self._image_fade.stop()
        if animate:
            self._image_fade.start()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tablet = self._tablet_rect()
        self._paint_tablet(painter, tablet)
        bounds = self._screen_rect()
        clip = QPainterPath()
        clip.addRoundedRect(bounds, 15, 15)
        screen_gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        screen_gradient.setColorAt(0, QColor("#33291D" if self._drop_highlight else "#21232A"))
        screen_gradient.setColorAt(1, QColor("#201A14" if self._drop_highlight else "#111216"))
        painter.fillPath(clip, screen_gradient)
        painter.setClipPath(clip)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.image.isNull():
            center = bounds.center()
            painter.setPen(QPen(QColor("#D5B17B"), 1.8))
            lens = QRectF(center.x() - 8, center.y() - 25, 16, 16)
            painter.drawRoundedRect(QRectF(center.x() - 24, center.y() - 35, 48, 36), 7, 7)
            painter.drawEllipse(lens)
            painter.setPen(QColor("#BFC0C7"))
            caption = QRectF(bounds.left() + 12, center.y() + 14, bounds.width() - 24, 36)
            painter.drawText(caption, Qt.AlignmentFlag.AlignCenter,
                             "Fotoğrafı buraya bırakın" if self._drop_highlight
                             else "Fotoğrafı buraya sürükleyip bırakın")
        else:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            target = self._image_rect(bounds)
            painter.save()
            if self._image_fade.state() == QVariantAnimation.State.Running:
                painter.setOpacity(self._image_fade.currentValue())
            if self.mirrored:
                painter.translate(2 * target.center().x(), 0)
                painter.scale(-1, 1)
            painter.drawImage(target, self.image)
            painter.restore()
            if self.face:
                x, y, w, h = self.face
                rectangle = QRectF(target.x() + self._mirror_x(x, w) * target.width(),
                                   target.y() + y * target.height(),
                                   w * target.width(), h * target.height())
                painter.setPen(QPen(QColor("#28241D"), 4))
                painter.drawRoundedRect(rectangle, 5, 5)
                painter.setPen(QPen(QColor("#F3CE8D"), 2))
                painter.drawRoundedRect(rectangle, 5, 5)
        if self.status_text and not self._drop_highlight:
            self._paint_status(painter, bounds)
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#F3CE8D"), 2) if self._drop_highlight else QPen(QColor("#3C3D45"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bounds, 15, 15)

    def _paint_status(self, painter, bounds):
        colors = {"neutral": "#D2D1D7", "gold": "#F3CE8D", "green": "#B9DEBB"}
        accent = QColor(colors[self.status_tone])
        badge = QRectF(bounds.left() + 11, bounds.top() + 10,
                       painter.fontMetrics().horizontalAdvance(self.status_text) + 31, 24)
        painter.setBrush(QColor(22, 22, 25, 232))
        outline = QColor(accent)
        outline.setAlpha(110)
        painter.setPen(QPen(outline, 1))
        painter.drawRoundedRect(badge, 8, 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawEllipse(QPointF(badge.left() + 11, badge.center().y()), 2.8, 2.8)
        painter.setPen(accent)
        painter.drawText(badge.adjusted(20, 0, -9, 0), Qt.AlignmentFlag.AlignVCenter, self.status_text)

    def _paint_tablet(self, painter, tablet):
        center = tablet.center().x()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#111216"))
        painter.drawRoundedRect(tablet.translated(0, 4), 26, 26)

        metal = QLinearGradient(tablet.topLeft(), tablet.bottomRight())
        metal.setColorAt(0, QColor("#817263"))
        metal.setColorAt(0.22, QColor("#3D4048"))
        metal.setColorAt(0.72, QColor("#282931"))
        metal.setColorAt(1, QColor("#6A5844"))
        painter.setBrush(metal)
        painter.setPen(QPen(QColor("#AC8B66"), 1))
        painter.drawRoundedRect(tablet, 26, 26)

        bezel = tablet.adjusted(3, 3, -3, -3)
        painter.setBrush(QColor("#15161A"))
        painter.setPen(QPen(QColor("#2B2D34"), 1))
        painter.drawRoundedRect(bezel, 23, 23)

        camera = QRectF(center - 14, tablet.top() + 6, 28, 10)
        painter.setPen(QPen(QColor("#35363D"), 1))
        painter.setBrush(QColor("#0E0F12"))
        painter.drawRoundedRect(camera, 5, 5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#77614A"))
        painter.drawEllipse(QPointF(center, camera.center().y()), 2.2, 2.2)
        painter.setBrush(QColor("#C9A06B"))
        painter.drawEllipse(QPointF(center - 0.6, camera.center().y() - 0.6), 0.75, 0.75)

        painter.setBrush(QColor("#56545A"))
        painter.drawRoundedRect(QRectF(center - 27, tablet.bottom() - 12, 54, 3), 1.5, 1.5)


class LightPreview(QWidget):
    """Render the applied scene's color and brightness in a lamp preview."""

    def __init__(self):
        super().__init__()
        self.scene = BALANCED
        self._tint = QColor(BALANCED.color)
        self._from_tint = QColor(self._tint)
        self._brightness = float(BALANCED.brightness)
        self._from_brightness = self._brightness
        self._transition = QVariantAnimation(self)
        self._transition.setDuration(220)
        self._transition.setStartValue(0.0)
        self._transition.setEndValue(1.0)
        self._transition.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._transition.valueChanged.connect(self._blend_scene)
        self.setMinimumHeight(100)
        self.setAccessibleName("Işık sahnesinin önizlemesi")

    def set_scene(self, scene: Scene):
        if scene == self.scene:
            return
        self._transition.stop()
        self._from_tint = QColor(self._tint)
        self._from_brightness = self._brightness
        self.scene = scene
        self._transition.start()

    def _blend_scene(self, progress):
        target = QColor(self.scene.color)
        start = self._from_tint
        self._tint = QColor.fromRgbF(
            start.redF() + (target.redF() - start.redF()) * progress,
            start.greenF() + (target.greenF() - start.greenF()) * progress,
            start.blueF() + (target.blueF() - start.blueF()) * progress,
        )
        self._brightness = self._from_brightness + (self.scene.brightness - self._from_brightness) * progress
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(bounds, 11, 11)
        painter.setClipPath(clip)
        painter.fillRect(bounds, QColor("#17181D"))

        w, h = self.width(), self.height()
        center = w * 0.51
        floor = h * 0.84
        tint = QColor(self._tint)
        power = self._brightness / 100
        transparent = QColor(tint)
        transparent.setAlpha(0)
        ambient = QRadialGradient(QPointF(center, h * 0.60), w * 0.63)
        glow = QColor(tint)
        glow.setAlphaF(0.20 * power)
        ambient.setColorAt(0, glow)
        ambient.setColorAt(1, transparent)
        painter.fillRect(bounds, ambient)

        painter.setPen(QPen(QColor("#303139"), 1))
        for fraction in (0.13, 0.37, 0.65, 0.88):
            x = w * fraction
            painter.drawLine(QPointF(x, 0), QPointF(x, floor))
        painter.drawLine(QPointF(0, floor), QPointF(w, floor))

        floor_glow = QRadialGradient(QPointF(0, 0), 1)
        glow.setAlphaF(0.44 * power)
        floor_glow.setColorAt(0, glow)
        floor_glow.setColorAt(1, transparent)
        painter.save()
        painter.translate(center, floor + h * 0.025)
        painter.scale(w * 0.53, h * 0.095)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(floor_glow)
        painter.drawEllipse(QPointF(0, 0), 1, 1)
        painter.restore()

        rim_y = h * 0.31
        shade_width = min(w * 0.22, h * 0.42)
        half = shade_width / 2
        beam = QPainterPath(QPointF(center - half * 0.94, rim_y))
        beam.lineTo(center + half * 0.94, rim_y)
        beam.lineTo(center + w * 0.29, floor)
        beam.quadTo(center, floor + h * 0.095, center - w * 0.29, floor)
        beam.closeSubpath()
        beam_gradient = QLinearGradient(0, rim_y, 0, floor + h * 0.045)
        glow.setAlphaF(0.40 * power)
        beam_gradient.setColorAt(0, glow)
        glow_mid = QColor(tint)
        glow_mid.setAlphaF(0.16 * power)
        beam_gradient.setColorAt(0.45, glow_mid)
        beam_gradient.setColorAt(1, transparent)
        painter.fillPath(beam, beam_gradient)

        painter.setPen(QPen(QColor("#8A7A62"), 1.5))
        painter.drawLine(QPointF(center, 0), QPointF(center, rim_y - h * 0.105))
        shade = QPainterPath(QPointF(center - half, rim_y))
        shade.cubicTo(center - half * 0.85, rim_y - h * 0.055,
                      center - half * 0.45, rim_y - h * 0.108, center, rim_y - h * 0.108)
        shade.cubicTo(center + half * 0.45, rim_y - h * 0.108,
                      center + half * 0.85, rim_y - h * 0.055, center + half, rim_y)
        shade.quadTo(center, rim_y + h * 0.02, center - half, rim_y)
        shade.closeSubpath()
        shade_gradient = QLinearGradient(center - half, 0, center + half, 0)
        shade_gradient.setColorAt(0, QColor("#4B4137"))
        shade_gradient.setColorAt(0.47, QColor("#8D7659"))
        shade_gradient.setColorAt(1, QColor("#443A32"))
        painter.fillPath(shade, shade_gradient)
        painter.setPen(QPen(QColor("#9C8463"), 1))
        painter.drawPath(shade)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(tint)
        painter.drawEllipse(QRectF(center - half * 0.92, rim_y - 1, half * 1.84, 4))
        painter.setClipping(False)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#3C3D45"), 1))
        painter.drawRoundedRect(bounds, 11, 11)


class MainWindow(QMainWindow):
    def __init__(self, model_path: Path = DEFAULT_CAPTURE_MODEL):
        super().__init__()
        self._model_path = model_path
        self._pending_scene: Scene | None = None
        self._selected_mode: Scene | None = None
        self._active_scene = BALANCED
        self._previewed_suggestion: Scene | None = None
        self._camera: CameraStream | None = None
        self._analysis: AnalyzeImage | None = None
        self._live_analysis: LiveAnalysis | None = None
        self._live_consensus = LiveConsensus()
        self._last_live_prediction: tuple[Expression, float] | None = None
        self._live_face = None
        self._last_sample_at: float | None = None
        self._live_timer = QTimer(self)
        self._live_timer.setInterval(200)
        self._live_timer.timeout.connect(self._expire_live_prediction)
        self._camera_live = False
        self._last_frame = None
        self._closing = False
        self.setWindowTitle("HOMTECH EmotionAI")
        self.setMinimumSize(880, 690)
        self.resize(1150, 880)

        root = QWidget()
        root.setObjectName("workspace")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._top_bar())

        scroll = QScrollArea()
        scroll.setObjectName("workspaceScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("workspace")
        body.setMinimumHeight(790)
        center = QHBoxLayout(body)
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(0)
        center.addStretch()
        dashboard = QWidget()
        dashboard.setMaximumWidth(WORKSPACE_WIDTH)
        center.addWidget(dashboard, 1)
        center.addStretch()
        workspace = QVBoxLayout(dashboard)
        workspace.setContentsMargins(24, 18, 24, 14)
        workspace.setSpacing(16)
        workspace.addWidget(self._mode_panel())
        content = QHBoxLayout()
        content.setSpacing(16)
        content.addWidget(self._photo_panel(), 3)
        content.addWidget(self._analysis_panel(), 2)
        workspace.addLayout(content, 1)
        workspace.addWidget(self._example_panel())
        workspace.addWidget(label("Görüntüler cihazda işlenir. Işık sahnesi önizlemede uygulanır.", "caption"))
        scroll.setWidget(body)
        self.views = QStackedWidget()
        self.views.addWidget(scroll)
        self.course_panel = CoursePanel()
        self.course_panel.demo_requested.connect(lambda: self._show_view(0))
        self.course_panel.fullscreen_requested.connect(self._toggle_presentation_fullscreen)
        self.views.addWidget(self.course_panel)
        layout.addWidget(self.views, 1)
        self.setCentralWidget(root)
        self.fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self.fullscreen_shortcut.activated.connect(self._toggle_presentation_fullscreen)
        self.escape_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.escape_shortcut.activated.connect(self._exit_presentation_fullscreen)
        self._show_scene(BALANCED)
        self._reset_decision()
        self._sync_input_actions()
        self.setTabOrder(self.load_button, self.camera_button)
        self.setTabOrder(self.camera_button, self.capture_button)
        self.setTabOrder(self.capture_button, self.preview_suggestion_button)
        self.setTabOrder(self.preview_suggestion_button, self.reject_button)
        self.setTabOrder(self.reject_button, self.approve_button)
        self.setTabOrder(self.approve_button, self.example_buttons[0])

    def _mode_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("modesPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 15)
        layout.setSpacing(11)

        heading = QHBoxLayout()
        heading.setSpacing(12)
        title = QVBoxLayout()
        title.setSpacing(3)
        title.addWidget(label("Ev aydınlatma modları", "pageTitle"))
        title.addWidget(label("Bir mod seçin veya yüz ifadesine göre öneri alın.", "heroLead", wrap=True))
        heading.addLayout(title, 1)

        actions = QVBoxLayout()
        actions.setSpacing(5)
        indicator = QFrame()
        indicator.setObjectName("modeIndicator")
        indicator_layout = QHBoxLayout(indicator)
        indicator_layout.setContentsMargins(9, 5, 9, 5)
        indicator_layout.setSpacing(9)
        self.mode_dot = QLabel()
        self.mode_dot.setFixedSize(13, 13)
        indicator_layout.addWidget(self.mode_dot)
        self.mode_selection = label("", "modeCardStatus")
        indicator_layout.addWidget(self.mode_selection)
        indicator_layout.addStretch()
        actions.addWidget(indicator)
        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        self.mode_cancel = QPushButton("Vazgeç")
        self.mode_cancel.clicked.connect(lambda: self._select_mode(None))
        self.mode_apply = QPushButton("Modu uygula")
        self.mode_apply.setObjectName("approve")
        self.mode_apply.clicked.connect(self._apply_selected_mode)
        buttons.addWidget(self.mode_cancel)
        buttons.addWidget(self.mode_apply)
        actions.addLayout(buttons)
        heading.addLayout(actions)
        layout.addLayout(heading)

        choices = QHBoxLayout()
        choices.setSpacing(8)
        self.mode_buttons = {}
        for mode in HOME_MODES:
            button = ModeCard(mode)
            button.clicked.connect(lambda checked=False, mode=mode: self._select_mode(mode))
            choices.addWidget(button, 1)
            self.mode_buttons[mode] = button
        layout.addLayout(choices)
        return panel

    def _select_mode(self, mode: Scene | None):
        self._previewed_suggestion = None
        self._selected_mode = None if mode == self._active_scene else mode
        self._update_mode_controls()
        self._update_scene_preview()

    def _update_mode_controls(self):
        active = self._active_scene
        selected = self._selected_mode
        for mode, button in self.mode_buttons.items():
            state = "active" if mode == active else "selected" if mode == selected else ""
            button.set_mode_state(state)
            status = {"active": " Etkin mod.", "selected": " Önizlenen mod."}.get(state, "")
            button.setAccessibleDescription(f"{mode.purpose}. {mode.settings}.{status}")
        self.mode_selection.setText(f"Etkin mod · {active.title}")
        self.mode_dot.setStyleSheet(f"background: {active.color}; border-radius: 6px;")
        self.mode_cancel.setEnabled(selected is not None)
        self.mode_apply.setEnabled(selected is not None)

    def _apply_selected_mode(self):
        selected = self._selected_mode
        if selected is None:
            return
        self._selected_mode = None
        self._show_scene(selected)
        if self._pending_scene == selected:
            self._pending_scene = None
            self._show_decision("Etkin mod", selected.title, "Bu mod önizlemede uygulanıyor.", tone="green")

    def _top_bar(self) -> QWidget:
        header = QWidget()
        header.setObjectName("topBar")
        outer = QHBoxLayout(header)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch()
        toolbar = QWidget()
        toolbar.setMaximumWidth(WORKSPACE_WIDTH)
        outer.addWidget(toolbar, 1)
        outer.addStretch()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(24, 10, 24, 10)
        layout.setSpacing(11)
        mark = label("H", "brandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(38, 38)
        layout.addWidget(mark)
        identity = QVBoxLayout()
        identity.setSpacing(0)
        identity.addWidget(label("HOMTECH", "brandName"))
        identity.addWidget(label("EmotionAI", "brandDetail"))
        layout.addLayout(identity)
        layout.addStretch()
        self.view_buttons = []
        for i, title in enumerate(("Uygulama", "BİL4011 Sunumu")):
            button = QPushButton(title)
            button.setObjectName("viewNav")
            button.setCheckable(True)
            button.setChecked(i == 0)
            button.clicked.connect(lambda checked=False, index=i: self._show_view(index))
            self.view_buttons.append(button)
            layout.addWidget(button)
        return header

    def _show_view(self, index):
        self.views.setCurrentIndex(index)
        for i, button in enumerate(self.view_buttons):
            button.setChecked(i == index)
        if index == 1:
            self.course_panel.next.setFocus()
        else:
            first_example = self.example_buttons[0]
            (first_example if first_example.isEnabled() else self.load_button).setFocus()

    def _toggle_presentation_fullscreen(self):
        if self.isFullScreen():
            self._exit_presentation_fullscreen()
        elif self.views.currentIndex() == 1:
            self.showFullScreen()
            self.course_panel.fullscreen.setText("Tam ekrandan çık")

    def _exit_presentation_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.course_panel.fullscreen.setText("Tam ekran")

    def _photo_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        title = QHBoxLayout()
        title.addWidget(label("Kamera ve fotoğraf", "heading"))
        title.addStretch()
        self.source_status = chip("Bekleniyor")
        title.addWidget(self.source_status)
        layout.addLayout(title)
        self.photo = PhotoPreview()
        self.photo.region_selected.connect(self._analyze_selected_face)
        self.photo.photo_dropped.connect(self._analyze_photo_file)
        layout.addWidget(self.photo, 1)
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.load_button = QPushButton("Fotoğraf yükle")
        self.load_button.setObjectName("primary")
        self.load_button.clicked.connect(self._choose_photo)
        self.camera_button = QPushButton("Kamerayı aç")
        self.camera_button.clicked.connect(self._toggle_camera)
        self.capture_button = QPushButton("Kareyi çek")
        self.capture_button.clicked.connect(self._capture_frame)
        for button in (self.load_button, self.camera_button, self.capture_button):
            controls.addWidget(button, 1)
        layout.addLayout(controls)
        return panel

    def _example_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(7)
        self.examples_title = label("Hazır örnekler", "sceneName")
        layout.addWidget(self.examples_title)
        examples = QHBoxLayout()
        examples.setSpacing(7)
        self.example_buttons = []
        for index, example in enumerate(EXAMPLES):
            button = QPushButton(EXPRESSIONS[example.label][0])
            button.setObjectName("demoExample")
            button.setCheckable(True)
            button.setAccessibleDescription("Hazır RAF-DB fotoğrafını analiz et")
            button.clicked.connect(lambda checked=False, i=index: self._try_example(i))
            examples.addWidget(button, 1)
            self.example_buttons.append(button)
        layout.addLayout(examples)
        return panel

    def _analysis_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(label("İfade analizi", "heading"))
        readout = QFrame()
        readout.setObjectName("analysisReadout")
        readout_layout = QVBoxLayout(readout)
        readout_layout.setContentsMargins(12, 9, 12, 9)
        readout_layout.setSpacing(3)
        self.expression_value = label("Görüntü bekleniyor", "expression", wrap=True)
        readout_layout.addWidget(self.expression_value)
        self.second_expression = label("", "secondExpression", wrap=True)
        self.second_expression.setVisible(False)
        readout_layout.addWidget(self.second_expression)
        layout.addWidget(readout)
        self.decision_panel = self._decision_card()
        layout.addWidget(self.decision_panel)
        layout.addWidget(rule())
        title = QHBoxLayout()
        self.preview_title = label("Etkin mod önizlemesi", "caption")
        title.addWidget(self.preview_title)
        title.addStretch()
        self.scene_name = label("", "sceneName")
        title.addWidget(self.scene_name)
        layout.addLayout(title)
        self.preview = LightPreview()
        layout.addWidget(self.preview, 1)
        self.scene_settings = label("", "caption")
        layout.addWidget(self.scene_settings)
        return panel

    def _decision_card(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("decisionCard")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(8)
        status_row = QHBoxLayout()
        status_row.addWidget(label("Önerilen ev modu", "caption"))
        status_row.addStretch()
        self.decision_status = chip("")
        status_row.addWidget(self.decision_status)
        layout.addLayout(status_row)

        result = QHBoxLayout()
        result.setSpacing(10)
        self.proposal_swatch = QLabel()
        self.proposal_swatch.setFixedSize(30, 30)
        result.addWidget(self.proposal_swatch)
        result_text = QVBoxLayout()
        result_text.setSpacing(3)
        self.decision_title = label("", "decisionTitle", wrap=True)
        self.decision_detail = label("", "muted", wrap=True)
        result_text.addWidget(self.decision_title)
        result_text.addWidget(self.decision_detail)
        result.addLayout(result_text, 1)
        layout.addLayout(result)

        self.suggestion_actions = QWidget()
        actions = QHBoxLayout(self.suggestion_actions)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        self.reject_button = QPushButton("Reddet")
        self.reject_button.clicked.connect(self.reject_suggestion)
        self.preview_suggestion_button = QPushButton("Önizle")
        self.preview_suggestion_button.setObjectName("previewSuggestion")
        self.preview_suggestion_button.setCheckable(True)
        self.preview_suggestion_button.clicked.connect(self._preview_suggestion)
        self.approve_button = QPushButton("Onayla ve uygula")
        self.approve_button.setObjectName("approve")
        self.approve_button.clicked.connect(self.apply_suggestion)
        actions.addWidget(self.reject_button, 2)
        actions.addWidget(self.preview_suggestion_button, 2)
        actions.addWidget(self.approve_button, 3)
        layout.addWidget(self.suggestion_actions)
        return panel

    def _show_scene(self, scene: Scene):
        self._active_scene = scene
        if self._selected_mode == scene:
            self._selected_mode = None
        self._update_mode_controls()
        self._update_scene_preview()

    def _preview_suggestion(self, checked):
        self._previewed_suggestion = self._pending_scene if checked else None
        if self._previewed_suggestion is not None:
            self._selected_mode = None
            self._update_mode_controls()
        self._update_scene_preview()

    def _update_scene_preview(self):
        staged = self._selected_mode or self._previewed_suggestion
        scene = staged or self._active_scene
        title = "Önizleme · Onay bekliyor" if staged is not None else "Etkin mod önizlemesi"
        self.preview_title.setText(title)
        self.preview.set_scene(scene)
        self.preview.setAccessibleDescription(f"{title}. {scene.title}. {scene.settings}")
        self.scene_name.setText(scene.title)
        self.scene_settings.setText(scene.settings)
        self.preview_suggestion_button.setChecked(self._previewed_suggestion is not None)

    def _show_decision(self, status: str, title: str, detail: str, *, tone: str = "neutral"):
        self.decision_status.setText(status)
        self.decision_status.setProperty("state", tone)
        style = self.decision_status.style()
        style.unpolish(self.decision_status)
        style.polish(self.decision_status)
        if self.decision_panel.property("tone") != tone:
            self.decision_panel.setProperty("tone", tone)
            panel_style = self.decision_panel.style()
            panel_style.unpolish(self.decision_panel)
            panel_style.polish(self.decision_panel)
        self.decision_title.setText(title)
        self.decision_detail.setText(detail)
        pending = self._pending_scene
        if self._previewed_suggestion is not None and self._previewed_suggestion != pending:
            self._previewed_suggestion = None
            self._update_scene_preview()
        self.proposal_swatch.setVisible(pending is not None)
        self.suggestion_actions.setVisible(pending is not None)
        if pending is not None:
            self.proposal_swatch.setStyleSheet(
                f"background: {pending.color}; border: 1px solid #F3E2C1; border-radius: 7px;"
            )
        self.reject_button.setEnabled(pending is not None)
        self.preview_suggestion_button.setEnabled(pending is not None)
        self.approve_button.setEnabled(pending is not None)

    def _reset_decision(self):
        self._pending_scene = None
        self.photo.set_status("")
        self._show_second_expression()
        self._show_decision("Bekleniyor", "Mod önerisi bekleniyor", "Tek kişinin yüzünün göründüğü bir görüntü kullanın.")

    def _sync_input_actions(self):
        idle = self._analysis is None and not self._closing
        inputs_stopped = self._camera is None and self._live_analysis is None
        self.load_button.setEnabled(idle and inputs_stopped)
        self.photo.enable_photo_drop(idle and inputs_stopped)
        archive_exists = DEFAULT_ORIGINAL_ARCHIVE.is_file()
        for button in self.example_buttons:
            button.setEnabled(idle and inputs_stopped and archive_exists)
        self.examples_title.setText("Hazır örnekler" if archive_exists else "Hazır örnek arşivi bulunamadı")
        self.camera_button.setEnabled(idle and (inputs_stopped or self._camera_live))
        self.camera_button.setText("Kamerayı kapat" if self._camera_live else "Kamerayı aç")
        self.capture_button.setEnabled(idle and self._camera_live and self._last_frame is not None)

    def _choose_photo(self):
        extensions = " ".join(f"*{suffix}" for suffix in PHOTO_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf seçin", "", f"Fotoğraflar ({extensions});;Tüm dosyalar (*)",
        )
        if path:
            self._analyze_photo_file(Path(path))

    def _analyze_photo_file(self, path: Path):
        if self.load_button.isEnabled():
            self._mark_example()
            self.photo.clear()
            self._start_analysis(path, "Fotoğraf")

    def _try_example(self, index):
        if self.example_buttons[index].isEnabled():
            self._mark_example(index)
            self.photo.clear()
            self._start_analysis(EXAMPLES[index], "RAF-DB örneği")

    def _mark_example(self, selected: int | None = None):
        for index, button in enumerate(self.example_buttons):
            button.setChecked(index == selected)

    def _toggle_camera(self):
        if self._camera is not None:
            self._stop_camera()
            self.photo.clear()
            self.source_status.setText("Kamera kapalı")
            self.expression_value.setText("Görüntü bekleniyor")
            self._reset_decision()
            return
        self._mark_example()
        self.photo.clear()
        self.photo.set_mirrored(True)
        self._reset_decision()
        self.expression_value.setText("Görüntü bekleniyor")
        self.source_status.setText("Kamera açılıyor")
        self.photo.set_status("Kamera açılıyor", "gold")
        self._camera_live = True
        self._camera = CameraStream(self)
        self._camera.frame_ready.connect(self._show_camera_frame)
        self._camera.failed.connect(self._camera_error)
        self._camera.finished.connect(self._camera_finished)
        self._live_analysis = LiveAnalysis(self._model_path, self)
        self._live_analysis.prediction_ready.connect(self._show_live_prediction)
        self._live_analysis.face_unavailable.connect(self._show_live_face_error)
        self._live_analysis.failed.connect(self._show_live_error)
        self._live_analysis.finished.connect(self._live_analysis_finished)
        self._sync_input_actions()
        self._live_analysis.start()
        self._camera.start()
        self._live_timer.start()

    def _show_camera_frame(self, frame, captured_at: float):
        if not self._camera_live:
            return
        first_frame = self._last_frame is None
        self._last_frame = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        self.photo.set_image(rgb.data, width, height, rgb.strides[0], face=self._live_face)
        if first_frame:
            self.source_status.setText("Kamera açık")
            if self._live_analysis is not None:
                self._show_live_waiting()
            self._sync_input_actions()
        if self._live_analysis is not None and (self._last_sample_at is None
                or captured_at - self._last_sample_at >= LiveConsensus.frame_interval):
            self._last_sample_at = captured_at
            self._live_analysis.submit(frame, captured_at)

    def _stop_camera(self):
        self._camera_live = False
        self._last_frame = None
        self._last_sample_at = None
        self._live_face = None
        self._live_consensus.reset()
        self._last_live_prediction = None
        self._live_timer.stop()
        if self._camera is not None:
            self._camera.requestInterruption()
        if self._live_analysis is not None:
            self._live_analysis.requestInterruption()
        self._sync_input_actions()

    def _camera_error(self, message):
        if self._camera_live:
            self._stop_camera()
            self.photo.clear()
            self.source_status.setText("Kamera kapalı")
            self._show_analysis_error(message)

    def _camera_finished(self):
        self._camera.deleteLater()
        self._camera = None
        self._stop_camera()
        self._finish_close()

    def _show_live_waiting(self):
        self._pending_scene = None
        self.photo.set_status("Yüz aranıyor", "gold")
        self._show_second_expression()
        self.expression_value.setText("Kamera görüntüsü bekleniyor")
        self._show_decision("Canlı analiz", "Öneri bekleniyor", "Bir süre kameraya önden bakın.")

    def _show_live_prediction(self, result: Expression, captured_at: float):
        if not self._camera_live or monotonic() - captured_at > LiveAnalysis.maximum_frame_age:
            return
        self._live_face = result.face
        self.photo.face = result.face
        self.photo.set_status("Tahmin hazır", "green")
        self.photo.update()
        self._show_second_expression(result.second_label)
        self._last_live_prediction = (result, captured_at)
        previous = self._live_consensus.label
        stable = self._live_consensus.observe(None if result.uncertain else result.label, captured_at)
        if stable is not None and stable != previous:
            self._show_prediction(result, live=True)
        if stable is None:
            self._show_tentative_prediction(result.label, live=True, low_score=result.uncertain)
        else:
            name, _ = EXPRESSIONS[result.label]
            self.expression_value.setText(name if stable == result.label and not result.uncertain
                                          else f"Olası ifade: {name}")

    def _show_live_face_error(self, message: str, captured_at: float):
        if not self._camera_live or monotonic() - captured_at > LiveAnalysis.maximum_frame_age:
            return
        self._live_consensus.reset()
        self._last_live_prediction = None
        self._live_face = None
        self.photo.face = None
        self.photo.update()
        self._show_analysis_error(message)
        self.photo.set_status("Yüz aranıyor", "gold")

    def _show_live_error(self, message: str):
        self._show_live_face_error(message, monotonic())
        if self._camera_live:
            self.photo.set_status("Analiz durdu")

    def _expire_live_prediction(self):
        if not self._camera_live:
            return
        now = monotonic()
        proposal_expired = self._live_consensus.expire(now)
        if self._last_live_prediction is None:
            return
        result, captured_at = self._last_live_prediction
        if now - captured_at > LiveConsensus.window:
            self._last_live_prediction = None
            self._live_face = None
            self.photo.face = None
            self.photo.update()
            self._show_live_waiting()
        elif proposal_expired:
            self._show_tentative_prediction(result.label, live=True, low_score=result.uncertain)

    def _live_analysis_finished(self):
        self._live_analysis.deleteLater()
        self._live_analysis = None
        self._sync_input_actions()
        self._finish_close()

    def _capture_frame(self):
        if self._last_frame is not None:
            frame = self._last_frame
            self._stop_camera()
            self._start_analysis(frame, "Kamera karesi")

    def _start_analysis(self, source, source_name, *, region=None):
        self.photo.enable_selection(False)
        self.photo.set_status("Görüntü hazırlanıyor", "gold")
        self.source_status.setText(source_name)
        self.expression_value.setText("Analiz ediliyor")
        self._show_second_expression()
        self._pending_scene = None
        self._show_decision("Bekleniyor", "Yüz aranıyor", "İfade tahmini hazırlanıyor.")
        self._analysis = AnalyzeImage(source, self._model_path, self, region=region)
        self._analysis.image_ready.connect(self._show_photo)
        self._analysis.face_ready.connect(self._show_detected_face)
        self._analysis.prediction_ready.connect(self._show_prediction)
        self._analysis.failed.connect(self._show_image_error)
        self._analysis.face_not_found.connect(self._offer_face_selection)
        self._analysis.finished.connect(self._analysis_finished)
        self._sync_input_actions()
        self._analysis.start()

    def _show_photo(self, image):
        self._loaded_photo = image
        self.photo.set_image(image.tobytes(), image.width, image.height, image.width * 3, animate=True)
        self.photo.set_status("Yüz aranıyor", "gold")

    def _show_detected_face(self, bounds):
        self.photo.face = bounds
        self.photo.set_status("Analiz ediliyor", "gold")
        self.photo.update()

    def _offer_face_selection(self, message):
        self._show_analysis_error(message)
        self.photo.enable_selection(True)
        self.photo.set_status("Yüzü seç")
        self.expression_value.setText("Yüzü seç")
        self._show_decision("El ile seçim", "Yüzü çerçevele",
                            "Fotoğrafta sürükleyerek alın, yanaklar ve çeneyi kapsayan bir alan çiz.")

    def _show_image_error(self, message):
        if self._analysis.region is not None:
            self._offer_face_selection(message)
            self.decision_detail.setText(message)
        else:
            self._show_analysis_error(message)

    def _analyze_selected_face(self, region):
        if self._analysis is None and not self._closing:
            self._start_analysis(self._loaded_photo, self.source_status.text(), region=region)

    def _show_prediction(self, result: Expression, *, live: bool = False):
        self.photo.face = result.face
        self.photo.set_status("Tahmin hazır", "green")
        self.photo.update()
        self._show_second_expression(result.second_label)
        if result.uncertain:
            self._show_tentative_prediction(result.label, close_portrait=result.close_portrait)
            return
        name, scene = EXPRESSIONS[result.label]
        self.expression_value.setText(name)
        self._pending_scene = scene
        if scene is None:
            self._show_decision("Öneri yok", "Mod değişikliği yok", "Bu ifade için ev modu önerilmiyor.")
            return
        detail = f"{name} tahmini  •  {scene.settings}" if live else scene.settings
        self._show_decision("Onay bekliyor", scene.title, detail, tone="gold")

    def _show_second_expression(self, key: str | None = None):
        self.second_expression.setText("" if key is None else f"İkinci tahmin · {EXPRESSIONS[key][0]}")
        self.second_expression.setVisible(key is not None)

    def _show_tentative_prediction(self, expression: str, *, close_portrait: bool = False,
                                   live: bool = False, low_score: bool = True):
        name, _ = EXPRESSIONS[expression]
        title = f"Olası ifade: {name}"
        status = "Yakın çekim" if close_portrait else "Düşük güven" if low_score else "Canlı analiz"
        if self.expression_value.text() == title and self.decision_status.text() == status:
            return
        self._pending_scene = None
        self.expression_value.setText(title)
        if close_portrait:
            detail = "Yakın kırpılmış fotoğraf yalnızca ifade tahmini için kullanıldı."
        elif live and not low_score:
            detail = "Işık önerisi için aynı ifadenin birkaç karede görülmesi gerekir."
        else:
            detail = "Tahmin skoru ışık önerisi eşiğinin altında."
        self._show_decision(status, "Öneri yok", detail)

    def _show_analysis_error(self, message):
        self.expression_value.setText("Sonuç yok")
        self.photo.set_status("Sonuç yok")
        self._show_second_expression()
        self._pending_scene = None
        self._show_decision("Öneri yok", "Analiz tamamlanamadı", message)

    def _analysis_finished(self):
        self._analysis.deleteLater()
        self._analysis = None
        self._sync_input_actions()
        self._finish_close()

    def closeEvent(self, event):
        if self._camera is None and self._analysis is None and self._live_analysis is None:
            super().closeEvent(event)
            return
        self._closing = True
        self._stop_camera()
        event.ignore()

    def _finish_close(self):
        if self._closing and self._camera is None and self._analysis is None and self._live_analysis is None:
            self.close()

    def reject_suggestion(self):
        if self._pending_scene is None:
            return
        self._pending_scene = None
        self._show_decision("Reddedildi", "Öneri reddedildi", f"Etkin mod · {self._active_scene.title}")

    def apply_suggestion(self):
        scene = self._pending_scene
        if scene is None:
            return
        self._pending_scene = None
        self._selected_mode = None
        self._previewed_suggestion = None
        self._show_scene(scene)
        self._show_decision("Onaylandı", scene.title, "Ev modu önizlemede uygulandı.", tone="green")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(THEME)
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
