"""The BİL4011 presentation, backed by the project's evaluation reports."""

import csv
import json
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import (
    QColor, QKeySequence, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient, QShortcut,
)
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from homtech.settings import ALIGNED_MODEL_DIR, ARTIFACTS_DIR, CAPTURE_MODEL_DIR


TOPICS = (
    "Problem ve veri seti", "Analiz ve ön işleme", "Model seçimi ve eğitim",
    "Model değerlendirmesi", "Modelin dağıtımı", "Arayüz tasarımı", "Canlı demo",
)

EXPRESSIONS = {
    "angry": "Kızgınlık", "disgust": "İğrenme", "fear": "Korku", "happy": "Mutluluk",
    "sad": "Üzüntü", "surprise": "Şaşkınlık", "neutral": "Nötr",
}
SHORT_EXPRESSIONS = {
    "angry": "Kızgın.", "disgust": "İğren.", "fear": "Korku", "happy": "Mutlu.",
    "sad": "Üzüntü", "surprise": "Şaşkın.", "neutral": "Nötr",
}
METHOD_STEPS = (
    ("Yüzü hazırla", "OpenCV tek yüzü arar. Gözler bulunursa yüz hizalanır. "
     "Kırpım gri tona ve 96 × 96 piksele dönüştürülür, ardından histogram eşitlenir."),
    ("HOG çıkar", "8 × 8 piksellik hücrelerde kenar yönleri 12 kutuda sayılır. "
     "Örtüşen 16 × 16 bloklar yerel kontrasta göre normalleştirilir ve görüntü 5.808 özelliğe dönüşür."),
    ("Ölçekle ve indirge", "StandardScaler öğrenilen eğitim ortalaması ve standart sapmasıyla özellikleri ölçekler. "
     "PCA, en çok değişkenlik taşıyan 128 doğrusal bileşene indirger. İki adım da yalnızca eğitim verisine uydurulur."),
    ("RBF SVM ile sınıflandır", "RBF çekirdeği, özellik uzayında doğrusal olmayan karar sınırları öğrenir. "
     "Yedi sınıf için 21 ikili karşılaştırma yapılır. Dengeli sınıf ağırlıkları, seyrek sınıfların eğitimdeki etkisini artırır."),
)

STYLE = """
QWidget#coursePanel, QWidget#courseCanvas, QScrollArea { background: #17181B; }
QFrame#courseRail { background: #1E1F23; border: 1px solid #36373D; border-radius: 15px; }
QFrame#courseCard { background: #222328; border: 1px solid #3A3B41; border-radius: 13px; }
QFrame#courseMetric {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #31302E,stop:0.42 #27272B,stop:1 #202126);
    border: 1px solid #50483E; border-top: 2px solid #997C55; border-radius: 12px;
}
QFrame#courseCover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2D2722,stop:0.48 #211F22,stop:1 #18191D);
    border: 1px solid #776145; border-radius: 19px;
}
QFrame#courseSection { border: none; border-left: 2px solid #B79561; }
QFrame#courseFooter { background: #1E1F23; border: 1px solid #36373D; border-radius: 11px; }
QLabel#coverTitle { color: #FFF4E4; font-size: 46px; font-weight: 750; }
QLabel#coverTitle[compact="true"] { font-size: 38px; }
QLabel#coverMethod { color: #EDCA90; font-size: 14px; font-weight: 650; }
QLabel#courseKicker { color: #E4BF7D; font-size: 13px; font-weight: 700; }
QLabel#courseTitle { color: #F4F2EE; font-size: 36px; font-weight: 700; }
QLabel#courseLead { color: #CAC9CE; font-size: 16px; }
QLabel#courseValue { color: #F3D094; font-size: 31px; font-weight: 700; }
QLabel#courseMetricName { color: #D4D0C9; font-size: 13px; }
QLabel#courseBody { color: #D3D2D7; font-size: 14px; }
QLabel#matrixAxis { color: #E5C389; font-size: 12px; font-weight: 650; }
QLabel#matrixHead { color: #C4C1CB; font-size: 12px; }
QLabel#matrixDetail { color: #F3DCB3; background: #312920; border-radius: 6px;
                      padding: 7px 9px; font-size: 13px; }
QComboBox#courseSelect { background: #303138; border: 1px solid #5B5760; border-radius: 7px; padding: 5px 10px; }
QComboBox#courseSelect:focus { border-color: #DDB478; }
QComboBox#courseSelect QAbstractItemView { background: #292A30; selection-background-color: #59462D; }
QPushButton#courseNav { background: transparent; border-color: transparent; text-align: left;
                       padding: 9px; font-size: 13px; color: #D3D2D7; }
QPushButton#courseNav:hover, QPushButton#courseNav:focus { border-color: #B99966; }
QPushButton#courseNav:checked { background: #3A3022; border-color: #80633A; color: #F7D9A2; }
QPushButton#courseTopic { background: transparent; border: 1px solid transparent; text-align: left;
                         padding: 10px 9px; font-size: 13px; color: #D3D2D7; }
QPushButton#courseTopic:hover, QPushButton#courseTopic:focus { border-color: #937747; }
QPushButton#courseTopic:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #493824,stop:1 #2A2728);
    border: 1px solid #765D38; border-left: 3px solid #E7C07D; color: #FFE1A9;
}
QProgressBar#courseBar { background: #35363E; border: none; border-radius: 4px; }
QProgressBar#courseBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #917047,stop:1 #EDCA8E); border-radius: 4px;
}
QProgressBar#courseProgress { background: #37353B; border: none; border-radius: 3px; }
QProgressBar#courseProgress::chunk { background: #DFB978; border-radius: 3px; }
"""


def number(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def percent(value: float) -> str:
    return f"%{100 * value:.2f}".replace(".", ",")


def read_report(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def trial_rows(run: str):
    try:
        with (ARTIFACTS_DIR / "runs" / run / "validation_results.csv").open(encoding="utf-8") as stream:
            return list(csv.DictReader(stream))
    except (OSError, csv.Error):
        return []


def caption(text, style="courseBody"):
    widget = QLabel(text)
    widget.setObjectName(style)
    widget.setWordWrap(True)
    return widget


def card():
    frame = QFrame()
    frame.setObjectName("courseCard")
    content = QVBoxLayout(frame)
    content.setContentsMargins(16, 12, 16, 12)
    content.setSpacing(5)
    return frame, content


def stats(*items):
    row = QHBoxLayout()
    row.setSpacing(9)
    for value, name in items:
        frame, content = card()
        frame.setObjectName("courseMetric")
        content.addWidget(caption(value, "courseValue"))
        content.addWidget(caption(name, "courseMetricName"))
        row.addWidget(frame, 1)
    return row


def note(title, text):
    frame, content = card()
    content.addWidget(caption(title, "heading"))
    content.addWidget(caption(text))
    return frame


def bars(title, entries, maximum):
    frame, content = card()
    content.addWidget(caption(title, "heading"))
    grid = QGridLayout()
    grid.setColumnStretch(1, 1)
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(5)
    for i, (name, value, display) in enumerate(entries):
        grid.addWidget(caption(name), i, 0)
        bar = QProgressBar()
        bar.setObjectName("courseBar")
        bar.setRange(0, maximum)
        bar.setValue(value)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setAccessibleName(f"{name} · {display}")
        grid.addWidget(bar, i, 1)
        marker = QLabel(display, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(marker, i, 2)
    content.addLayout(grid)
    return frame


def method_flow():
    frame, content = card()
    content.addWidget(caption("Görüntüden sınıf skoruna", "heading"))
    stages = QHBoxLayout()
    stages.setSpacing(7)
    detail = caption("")
    for i, (title, explanation) in enumerate(METHOD_STEPS):
        button = QPushButton(title)
        button.setCheckable(True)
        button.setObjectName("courseNav")
        button.setAccessibleDescription(explanation)
        stages.addWidget(button, 1)
        button.clicked.connect(lambda checked=False, index=i: select(index))

    def select(index):
        for i in range(stages.count()):
            stages.itemAt(i).widget().setChecked(i == index)
        detail.setText(METHOD_STEPS[index][1])

    select(0)
    content.addLayout(stages)
    content.addWidget(detail)
    return frame


class CoverArtwork(QWidget):
    """Illustrate the transition from a detected face to a lighting scene."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 168)
        self.setAccessibleName("Yüz algılamadan ışık sahnesine uzanan şematik çizim")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale = min(self.width() / 310, self.height() / 224)
        painter.translate((self.width() - 310 * scale) / 2, (self.height() - 224 * scale) / 2)
        painter.scale(scale, scale)
        field = QRectF(6, 8, 298, 208)
        frame = QPainterPath()
        frame.addRoundedRect(field, 17, 17)
        painter.setClipPath(frame)
        painter.fillRect(field, QColor("#1C1D22"))
        glow = QRadialGradient(QPointF(115, 95), 148)
        glow.setColorAt(0, QColor("#493A2B"))
        glow.setColorAt(1, QColor("#1B1C21"))
        painter.fillRect(field, glow)

        painter.setPen(QPen(QColor(111, 90, 67, 71), 1))
        for x in range(24, 300, 17):
            painter.drawLine(QPointF(x, 12), QPointF(x, 210))
        for y in range(25, 215, 17):
            painter.drawLine(QPointF(6, y), QPointF(304, y))
        painter.setPen(QPen(QColor(93, 80, 68, 144), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(38, 41, 140, 140))
        painter.drawEllipse(QRectF(53, 56, 110, 110))

        portrait = QPainterPath(QPointF(67, 99))
        portrait.cubicTo(65, 73, 80, 56, 107, 56)
        portrait.cubicTo(134, 56, 151, 73, 149, 100)
        portrait.cubicTo(147, 131, 132, 157, 108, 161)
        portrait.cubicTo(84, 157, 70, 131, 67, 99)
        painter.setPen(QPen(QColor("#DFC196"), 1.7))
        painter.drawPath(portrait)

        landmarks = QPainterPath(QPointF(79, 96))
        landmarks.quadTo(88, 89, 98, 96)
        landmarks.moveTo(118, 96)
        landmarks.quadTo(128, 89, 137, 96)
        landmarks.moveTo(108, 101)
        landmarks.quadTo(101, 117, 112, 119)
        landmarks.moveTo(90, 132)
        landmarks.quadTo(108, 143, 126, 132)
        painter.drawPath(landmarks)
        painter.setPen(QPen(QColor("#F1CD8A"), 2.1))
        for x, y, dx, dy in ((54, 48, 1, 1), (162, 48, -1, 1), (54, 173, 1, -1), (162, 173, -1, -1)):
            corner = QPointF(x, y)
            painter.drawLine(corner, QPointF(x + 15 * dx, y))
            painter.drawLine(corner, QPointF(x, y + 15 * dy))
        painter.setPen(QPen(QColor("#AB8859"), 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(164, 111), QPointF(215, 111))

        lamp_glow = QRadialGradient(QPointF(249, 128), 61)
        lamp_glow.setColorAt(0, QColor(231, 177, 100, 95))
        lamp_glow.setColorAt(1, QColor(231, 177, 100, 0))
        painter.fillRect(QRectF(186, 72, 118, 126), lamp_glow)
        painter.setPen(QPen(QColor("#6F5D49"), 1))
        painter.drawRoundedRect(QRectF(207, 64, 81, 103), 13, 13)
        painter.setPen(QPen(QColor("#EAC385"), 1.7))
        painter.drawLine(QPointF(248, 75), QPointF(248, 98))
        shade = QPainterPath(QPointF(229, 115))
        shade.quadTo(234, 97, 248, 97)
        shade.quadTo(262, 97, 267, 115)
        shade.closeSubpath()
        painter.fillPath(shade, QColor("#A78552"))
        painter.drawPath(shade)
        for start, end in (((238, 123), (233, 134)), ((248, 125), (248, 138)), ((258, 123), (263, 134))):
            painter.drawLine(QPointF(*start), QPointF(*end))
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#665440"), 1))
        painter.drawPath(frame)


class EvaluationPanel(QFrame):
    def __init__(self, camera, aligned):
        super().__init__()
        self.setObjectName("courseCard")
        self.reports = (camera, aligned)
        self._selected_cell = None
        self.cell_buttons = QButtonGroup(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)
        controls = QHBoxLayout()
        self.title = caption("Karışıklık matrisi", "heading")
        controls.addWidget(self.title, 1)
        self.profile = self._selector("Test profili", ("Kamera hattı", "Hizalı fotoğraf"))
        self.display = self._selector("Gösterim", ("Satır yüzdesi", "Örnek sayısı", "Sınıf metrikleri"))
        controls.addWidget(self.profile)
        controls.addWidget(self.display)
        layout.addLayout(controls)
        self.grid = QGridLayout()
        self.grid.setSpacing(4)
        layout.addLayout(self.grid)
        self.summary = caption("", "caption")
        layout.addWidget(self.summary)
        self.cell_detail = caption("", "matrixDetail")
        layout.addWidget(self.cell_detail)
        self.profile.currentIndexChanged.connect(self._render)
        self.display.currentIndexChanged.connect(self._render)
        self._render()

    @staticmethod
    def _selector(name, choices):
        selector = QComboBox()
        selector.setObjectName("courseSelect")
        selector.setAccessibleName(name)
        selector.addItems(choices)
        return selector

    def _render(self):
        for button in self.cell_buttons.buttons():
            self.cell_buttons.removeButton(button)
        while self.grid.count():
            widget = self.grid.takeAt(0).widget()
            widget.hide()
            widget.deleteLater()
        report = self.reports[self.profile.currentIndex()]
        classes = report["classes"]
        metrics_view = self.display.currentIndex() == 2
        self.cell_detail.setVisible(not metrics_view)
        self.title.setText("Sınıf metrikleri" if metrics_view else "Karışıklık matrisi")
        for i in range(1, len(classes) + 1):
            self.grid.setColumnStretch(i, int(not metrics_view or i <= 4))
        if metrics_view:
            self._render_metrics(report, classes)
        else:
            self._render_matrix(report, classes, as_percent=self.display.currentIndex() == 0)

    def _render_metrics(self, report, classes):
        headings = ("Gerçek ifade", "Precision", "Recall", "F1", "Örnek")
        for column, heading in enumerate(headings):
            self.grid.addWidget(caption(heading, "matrixAxis"), 0, column)
        for row, key in enumerate(classes, 1):
            values = report["classification_report"][key]
            self.grid.addWidget(caption(EXPRESSIONS[key]), row, 0)
            for col, metric in enumerate(("precision", "recall", "f1-score"), 1):
                self.grid.addWidget(caption(percent(values[metric])), row, col)
            self.grid.addWidget(caption(number(int(values["support"]))), row, 4)
        self.summary.setText("Precision · Bu etiketi alan tahminlerin ne kadarı doğru?   "
                             "Recall · Gerçek örneklerin ne kadarı yakalandı?")

    def _render_matrix(self, report, classes, *, as_percent):
        self.cell_detail.setText("Ayrıntıları alt panelde görmek için bir hücre seçin.")
        self.grid.addWidget(caption("Tahmin edilen ifade →", "matrixAxis"), 0, 1, 1, len(classes))
        self.grid.addWidget(caption("Gerçek ifade ↓", "matrixAxis"), 1, 0)
        for col, key in enumerate(classes, 1):
            heading = caption(SHORT_EXPRESSIONS[key], "matrixHead")
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            heading.setToolTip(EXPRESSIONS[key])
            self.grid.addWidget(heading, 1, col)
        for row, (actual, counts) in enumerate(zip(classes, report["confusion_matrix"]), 2):
            self.grid.addWidget(caption(EXPRESSIONS[actual], "matrixHead"), row, 0)
            total = sum(counts)
            for col, (prediction, value) in enumerate(zip(classes, counts), 1):
                rate = value / total if total else 0
                cell = QPushButton(f"%{rate * 100:.0f}" if as_percent else number(value))
                cell.setObjectName("matrixCell")
                cell.setCheckable(True)
                self.cell_buttons.addButton(cell)
                text = f"{EXPRESSIONS[actual]} → {EXPRESSIONS[prediction]} · {value}/{total} ({percent(rate)})"
                cell.setToolTip(text)
                cell.setAccessibleName(text)
                cell.setFixedHeight(24)
                diagonal = actual == prediction
                base, peak = ((54, 44, 34), (224, 181, 112)) if diagonal else ((43, 44, 52), (128, 138, 161))
                rgb = tuple(round(low + (high - low) * rate) for low, high in zip(base, peak))
                text_color = "#211A12" if diagonal and rate >= 0.48 else "#F3F0ED"
                cell.setStyleSheet(
                    f"QPushButton#matrixCell {{ background: rgb{rgb}; color: {text_color}; "
                    "border: 1px solid transparent; border-radius: 4px; padding: 0 3px; min-height: 0; }"
                    "QPushButton#matrixCell:hover, QPushButton#matrixCell:focus { border-color: #C8A873; }"
                    "QPushButton#matrixCell:checked { border-color: #F6D495; font-weight: 800; }"
                )
                detail = (f"{number(total)} {EXPRESSIONS[actual].lower()} örneğinin "
                          f"{number(value)} tanesi {EXPRESSIONS[prediction].lower()} olarak tahmin edildi "
                          f"({percent(rate)}).")
                coordinate = (actual, prediction)
                cell.clicked.connect(lambda checked=False, xy=coordinate, message=detail: self._select_cell(xy, message))
                if coordinate == self._selected_cell:
                    cell.setChecked(True)
                    self.cell_detail.setText(detail)
                self.grid.addWidget(cell, row, col)
        self.summary.setText("Altın köşegen doğru tahminleri gösterir. Satır yüzdesi, hücreyi o gerçek sınıfın toplamına böler."
                             if as_percent else
                             "Altın köşegen doğru tahminleri gösterir. Hücreler testteki örnek sayılarını gösterir.")

    def _select_cell(self, coordinate, message):
        self._selected_cell = coordinate
        self.cell_detail.setText(message)


class CoursePanel(QWidget):
    demo_requested = Signal()
    fullscreen_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("coursePanel")
        self.setStyleSheet(STYLE)
        self.pages = QStackedWidget()
        self._animated_canvas = None
        self._transition = QVariantAnimation(self)
        self._transition.setStartValue(0.75)
        self._transition.setEndValue(1.0)
        self._transition.setDuration(170)
        self._transition.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._transition.valueChanged.connect(self._update_opacity)
        self._transition.finished.connect(self._clear_transition)
        self.fullscreen = QPushButton("Tam ekran")
        self.fullscreen.clicked.connect(self.fullscreen_requested.emit)
        self.back = QPushButton("Geri")
        self.next = QPushButton("İleri")
        self.next.setObjectName("primary")
        self.back.clicked.connect(lambda: self.step(-1))
        self.next.clicked.connect(lambda: self.step(1))
        self.position = QLabel()
        self.progress = QProgressBar()
        self.progress.setObjectName("courseProgress")
        self.progress.setRange(0, len(TOPICS))
        self.progress.setTextVisible(False)
        self.progress.setFixedSize(94, 6)
        self.progress.setAccessibleName("Sunum ilerlemesi")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(16)
        layout.addWidget(self._rail())
        body = QVBoxLayout()
        body.setSpacing(9)
        body.addWidget(self.pages, 1)
        controls = QFrame()
        controls.setObjectName("courseFooter")
        footer = QHBoxLayout(controls)
        footer.setContentsMargins(10, 5, 6, 5)
        footer.addWidget(self.position)
        footer.addWidget(self.progress)
        footer.addStretch()
        footer.addWidget(self.fullscreen)
        footer.addWidget(self.back)
        footer.addWidget(self.next)
        body.addWidget(controls)
        layout.addLayout(body, 1)

        self._build_pages()
        self.go_to(0)
        for key, action in (
            ("Left", lambda: self.step(-1)),
            ("Right", lambda: self.step(1)),
            ("PageUp", lambda: self.step(-1)),
            ("PageDown", lambda: self.step(1)),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(action)

    def _rail(self):
        rail = QFrame()
        rail.setObjectName("courseRail")
        rail.setFixedWidth(194)
        body = QVBoxLayout(rail)
        body.setContentsMargins(11, 15, 11, 12)
        body.setSpacing(5)
        body.addWidget(caption("BİL4011", "courseKicker"))
        body.addWidget(caption("Final sunumu", "sceneName"))
        body.addSpacing(8)
        self.links = []
        for i, topic in enumerate(TOPICS):
            button = QPushButton(topic)
            button.setObjectName("courseTopic")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, index=i: self.go_to(index))
            self.links.append(button)
            body.addWidget(button)
        body.addStretch()
        demo = QPushButton("Uygulamaya geç")
        demo.clicked.connect(self.demo_requested.emit)
        body.addWidget(demo)
        return rail

    def go_to(self, index):
        changed = self.pages.currentIndex() != index
        self._transition.stop()
        self._clear_transition()
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.links):
            button.setChecked(i == index)
        self.position.setText(f"Bölüm {index + 1} / {len(TOPICS)}")
        self.progress.setValue(index + 1)
        self.back.setEnabled(index > 0)
        self.next.setText("Demoya geç" if index == len(TOPICS) - 1 else "İleri")
        if changed and self.isVisible():
            self._animated_canvas = self.pages.currentWidget().widget()
            effect = QGraphicsOpacityEffect(self._animated_canvas)
            effect.setOpacity(0.75)
            self._animated_canvas.setGraphicsEffect(effect)
            self._transition.start()

    def _update_opacity(self, opacity):
        if self._animated_canvas is not None:
            self._animated_canvas.graphicsEffect().setOpacity(opacity)

    def _clear_transition(self):
        if self._animated_canvas is not None:
            self._animated_canvas.setGraphicsEffect(None)
            self._animated_canvas = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = event.size().width() < 980
        if self.cover_title.property("compact") != compact:
            self.cover_title.setProperty("compact", compact)
            style = self.cover_title.style()
            style.unpolish(self.cover_title)
            style.polish(self.cover_title)

    def step(self, direction):
        index = self.pages.currentIndex() + direction
        if index == len(TOPICS):
            self.demo_requested.emit()
        elif index >= 0:
            self.go_to(index)

    def _page(self, index, title, lead, *, cover=False):
        viewport = QScrollArea()
        viewport.setFrameShape(QFrame.Shape.NoFrame)
        viewport.setWidgetResizable(True)
        canvas = QWidget()
        canvas.setObjectName("courseCanvas")
        layout = QVBoxLayout(canvas)
        layout.setContentsMargins(8, 5, 12, 8)
        layout.setSpacing(12)
        if cover:
            layout.addWidget(self._cover(title, lead))
        else:
            heading = QFrame()
            heading.setObjectName("courseSection")
            header = QVBoxLayout(heading)
            header.setContentsMargins(13, 3, 2, 3)
            header.setSpacing(7)
            header.addWidget(caption(TOPICS[index], "courseKicker"))
            header.addWidget(caption(title, "courseTitle"))
            header.addWidget(caption(lead, "courseLead"))
            layout.addWidget(heading)
        viewport.setWidget(canvas)
        self.pages.addWidget(viewport)
        return layout

    def _cover(self, title, lead):
        cover = QFrame()
        cover.setObjectName("courseCover")
        cover.setMinimumHeight(256)
        row = QHBoxLayout(cover)
        row.setContentsMargins(21, 17, 16, 17)
        row.setSpacing(12)
        content = QVBoxLayout()
        content.setSpacing(8)
        content.addStretch()
        content.addWidget(caption("BİL4011 · MAKİNE ÖĞRENMESİ", "courseKicker"))
        self.cover_title = caption(title, "coverTitle")
        content.addWidget(self.cover_title)
        content.addWidget(caption(lead, "courseLead"))
        content.addWidget(caption("HOG  →  PCA  →  RBF SVM", "coverMethod"))
        start = QPushButton("Yöntemi incele")
        start.setObjectName("primary")
        start.clicked.connect(lambda: self.go_to(1))
        content.addWidget(start, 0, Qt.AlignmentFlag.AlignLeft)
        content.addStretch()
        row.addLayout(content, 3)
        row.addWidget(CoverArtwork(), 2)
        return cover

    def _build_pages(self):
        audit = read_report(ARTIFACTS_DIR / "datasets" / "rafdb-audit.json")
        aligned = read_report(ALIGNED_MODEL_DIR / "evaluation" / "metrics.json")
        camera = read_report(CAPTURE_MODEL_DIR / "evaluation" / "metrics.json")

        page = self._page(0, "Yüz ifadesinden\nev moduna",
                          "HOMTECH, yüz ifadesini analiz eder ve kullanıcının onayına bir aydınlatma modu sunar.",
                          cover=True)
        if audit:
            splits = audit["splits"]
            sizes = [splits[name]["total"] for name in ("train", "validation", "test")]
            page.addLayout(stats((number(sum(sizes)), "RAF-DB BasicEmo görseli"),
                                 (str(len(audit["classes"])), "ifade sınıfı"),
                                 (number(sizes[-1]), "resmî test görseli")))
            page.addWidget(note("Eğitim ve test ayrımı",
                                f"Eğitim {number(sizes[0])} · Doğrulama {number(sizes[1])} · Test {number(sizes[2])}. "
                                "Doğrulama, resmî eğitim kümesinden sınıf oranları korunarak ayrıldı."))
        else:
            page.addWidget(note("RAF-DB BasicEmo", "Yerel veri denetimi raporu bulunamadı."))
        page.addWidget(note("Problem türü", "Tek görüntüden görünür yüz ifadesi tahmini, çok sınıflı bir sınıflandırma problemidir."))
        page.addStretch()

        page = self._page(1, "Piksellerden özelliklere",
                          "Görüntüler ve etiketler denetlendi. Sınıf dağılımı, mutluluk ve korku arasındaki büyük örnek farkını gösteriyor.")
        page.addWidget(method_flow())
        if audit:
            counts = audit["splits"]["train"]["counts"]
            page.addWidget(bars("Eğitim kümesindeki sınıf dağılımı",
                                [(EXPRESSIONS[key], value, number(value)) for key, value in counts.items()],
                                max(counts.values())))
        page.addWidget(caption("Özellik hattı · 96 × 96 piksel → 5.808 HOG özelliği → 128 PCA bileşeni → 7 ifade",
                               "courseKicker"))
        page.addStretch()

        page = self._page(2, "Doğrusal SVM’den RBF SVM’e",
                          "Hizalı yedi sınıflı deneylerde aynı doğrulama ayrımı kullanıldı. Seçim ölçütü sınıflara eşit ağırlık veren macro F1 oldu.")
        runs = (("hog-svm-001", "Doğrusal SVM"), ("classical-search-001", "Doğrusal SVM · HOG taraması"),
                ("flip-search-001", "Doğrusal SVM · yatay çevirme"), ("rbf-search-001", "PCA + RBF SVM"))
        entries = []
        for directory, title in runs:
            trials = trial_rows(directory)
            if trials:
                trial = max(trials, key=lambda row: float(row["validation_macro_f1"]))
                score = float(trial["validation_macro_f1"])
                entries.append((title, round(score * 10000), percent(score)))
        if entries:
            page.addWidget(bars("En iyi doğrulama macro F1 değerleri", entries, 10000))
        else:
            page.addWidget(note("Deney sonuçları", "Yerel doğrulama raporları bulunamadı."))
        rbf_trials = trial_rows("rbf-search-001")
        if rbf_trials:
            tuning, content = card()
            content.addWidget(caption("RBF modelinde C seçimi", "heading"))
            table = QGridLayout()
            for col, value in enumerate(("C", "Doğrulama doğruluğu", "Doğrulama macro F1")):
                table.addWidget(caption(value, "matrixAxis"), 0, col)
            for row, trial in enumerate(rbf_trials, 1):
                values = (trial["c"].replace(".", ","), percent(float(trial["validation_accuracy"])),
                          percent(float(trial["validation_macro_f1"])))
                for col, value in enumerate(values):
                    table.addWidget(caption(value), row, col)
            content.addLayout(table)
            content.addWidget(caption("C büyüdükçe model eğitim hatalarını daha fazla cezalandırır. "
                                      "C=1, doğrulamada daha yüksek macro F1 ürettiği için seçildi.", "caption"))
            page.addWidget(tuning)
        page.addWidget(caption("Arama · HOG yönü ve hücre boyutu, yatay çevirme ve C. Resmî test model seçiminde kullanılmadı.",
                               "caption"))
        page.addWidget(note("Model tahmini nasıl seçiyor?",
                            "SVM, yüzü yedi ifade sınıfına göre puanlar. En yüksek karar skorunu alan sınıf ana tahmin, "
                            "bir sonraki sınıf ikinci tahmin olur. İki skor arasındaki fark ışık önerisinin karar "
                            "eşiğinde kullanılır. Olasılık yüzdesi göstermek için ayrıca kalibrasyon gerekir."))
        page.addStretch()

        page = self._page(3, "Testte model ne kadar iyi?",
                          "Doğruluk, modelin birinci sıraya koyduğu ifadenin test etiketiyle eşleşme oranıdır. "
                          "Resmî test, model seçimi tamamlandıktan sonra çalıştırıldı.")
        if aligned and camera:
            page.addLayout(stats((percent(aligned["accuracy"]), "Hizalı fotoğraf · doğruluk"),
                                 (percent(camera["accuracy"]), "Kamera hattı · doğruluk"),
                                 (percent(camera["macro_f1"]), "Kamera hattı · macro F1")))
            page.addWidget(EvaluationPanel(camera, aligned))
            page.addWidget(caption(
                f"Kamera hattında {number(camera['official_test_samples'])} test fotoğrafının "
                f"{number(camera['samples'])} tanesi yüz algılamadan geçti. Karar eşiğini geçen "
                f"{number(camera['accepted_predictions'])} tahminin {number(camera['correct_accepted_predictions'])} tanesi doğruydu.",
                "caption"))
            sadness = camera["classes"].index("sad")
            neutral = camera["classes"].index("neutral")
            sad_row = camera["confusion_matrix"][sadness]
            page.addWidget(note("Benzer ifadeler neden karışıyor?",
                                "Hafif üzüntü ile nötr ifade tek karede benzer görünebilir. Işık, yüz açısı ve "
                                "sınıfların örnek sayısı da sınıflandırmayı etkileyebilir. Kamera hattında "
                                f"{number(sum(sad_row))} üzüntü örneğinin {number(sad_row[neutral])} tanesi "
                                "nötr olarak tahmin edildi. Gerçek etiket ikinci sıradaysa doğruluk hesabında bu örnek hata sayılır."))
        else:
            page.addWidget(note("Test raporu", "Kamera hattı veya hizalı fotoğraf test raporu bulunamadı."))
        page.addStretch()

        page = self._page(4, "Model masaüstünde çalışıyor",
                          "Eğitilmiş HOG + PCA + RBF SVM hattı Python ve PySide6 uygulamasına yerel model dosyası olarak entegre edildi.")
        page.addWidget(note("Kamera modeli", "Kamera kareleri ve normal fotoğraflar yüz algılama ve hizalamadan geçer. "
                            "Model, orijinal RAF-DB görüntülerinden aynı ön işleme ile hazırlanan yüzlerle eğitildi."))
        page.addWidget(note("Hizalı fotoğraf modeli", "Yakın kırpılmış yüzler için hizalı veride eğitilen model kullanılır. "
                            "Bu yoldan çıkan tahmin, ışık önerisi oluşturmadan gösterilir."))
        page.addWidget(note("Canlı karar kuralı", "Uygulama yaklaşık saniyede iki kareyi işler ve en yüksek iki SVM skoruna "
                            "karşılık gelen ifadeleri gösterir. Işık önerisi, üç güvenilir karenin en az bir saniye "
                            "boyunca aynı ifadeyi vermesiyle oluşur ve kullanıcı onayını bekler."))
        page.addWidget(note("Cihazda işleme", "Analiz ağ servisi gerektirmez. Aydınlatma bu sürümde uygulama içinde önizlenir."))
        page.addStretch()

        page = self._page(5, "Ev modları ve kullanıcı onayı",
                          "Kullanıcı fotoğraf yükleyebilir, kameradan kare çekebilir veya canlı ifadeyi izleyebilir.")
        page.addLayout(stats(("4", "Elle seçilebilir ev modu"), ("2", "Görüntü kaynağı")))
        page.addWidget(note("Günlük · Sıcak ortam · Rahatlama · Odak",
                            "Modlar kameradan bağımsız seçilebilir. Model bir mod önerdiğinde kullanıcı uygulayabilir veya reddedebilir."))
        page.addWidget(note("Tahmin ve öneri",
                            "En güçlü ifade tahmini ekranda görünür. Kararsız veya iğrenme tahminlerinde öneri çıkmaz. "
                            "Canlı öneri için birden fazla güvenilir kare gerekir."))
        page.addStretch()

        page = self._page(6, "Şimdi uygulamada deneyelim",
                          "Fotoğraf, canlı kamera ve mod onayını aynı uygulama üzerinden gösterin.")
        moments = QHBoxLayout()
        moments.setSpacing(9)
        for topic, title, description in (
            ("FOTOĞRAF", "Kızgınlık → Rahatlama", "Hazır örneği seçip ana ve ikinci tahmini, ardından önerilen modu gösterin."),
            ("MOD ONAYI", "Önizle ve uygula", "Ayarları önizleyip onaylayın. İğrenme örneğiyle öneri çıkmayan akışı da gösterin."),
            ("CANLI KAMERA", "Tahmini canlı izle", "Kamerayı açın ve kareler geldikçe ifade tahmininin nasıl güncellendiğini gösterin."),
        ):
            frame, content = card()
            frame.setObjectName("courseMetric")
            frame.setMinimumHeight(142)
            frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            content.setAlignment(Qt.AlignmentFlag.AlignTop)
            content.addWidget(caption(topic, "courseKicker"))
            content.addWidget(caption(title, "heading"))
            content.addWidget(caption(description))
            moments.addWidget(frame, 1)
        page.addLayout(moments)
        page.addWidget(caption("Ders içi sunum günleri · 15, 22 ve 29 Aralık 2026", "caption"))
        page.addStretch()
