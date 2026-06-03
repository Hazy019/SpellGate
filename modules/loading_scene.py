import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QVariantAnimation, QAbstractAnimation
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QPainter, QPen, QPixmap


# ─────────────────────────────────────────────────────────
#  LOADING BAR  — custom painted, full-width, slim 28px
# ─────────────────────────────────────────────────────────
class LoadingBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0
        self.blink    = True
        self.setFixedHeight(28)          # slim — not dominating the screen
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(18)
        glow.setColor(QColor("#22d3ee"))
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

        self._bt = QTimer(self)
        self._bt.timeout.connect(self._toggle)
        self._bt.start(420)

    def _toggle(self):
        self.blink = not self.blink
        self.update()

    def set_progress(self, val: int):
        self.progress = max(0, min(100, val))
        self.update()

    def paintEvent(self, event):
        p     = QPainter(self)
        SEG   = 30
        GAP   = 4
        seg_w = (self.width() - GAP * (SEG - 1)) / SEG
        h     = self.height()
        filled = int(self.progress / 100 * SEG)

        for i in range(SEG):
            x = int(round(i * (seg_w + GAP)))
            w = max(1, int(round(seg_w)))
            if i < filled:
                p.fillRect(x, 0, w, h, QColor("#22d3ee"))
                p.fillRect(x, 0, w, max(1, h // 5), QColor("#80eeff"))   # highlight
            elif i == filled and self.blink:
                p.fillRect(x, 0, w, h, QColor("#22d3ee55"))
            else:
                p.fillRect(x, 0, w, h, QColor("#0c2228"))
        p.end()


# ─────────────────────────────────────────────────────────
#  LOADING SCENE
# ─────────────────────────────────────────────────────────
class LoadingScene(QWidget):
    """
    Full-screen kiosk splash/loading screen.
    Layout is fixed-spacing so nothing gets cut off.

    PADDING CONSTANTS — adjust here without touching any other logic:
    """
    H_PAD   = 120   # px  left+right margin for bar / log section
    LOGO_MT = 36    # px  top margin above icon
    GAP_IB  = 18    # px  icon → SPELL gap
    GAP_SS  = 14    # px  GATE → slogan gap
    GAP_SL  = 32    # px  slogan → loading section gap
    BAR_SP  = 14    # px  spacing inside bar wrapper
    LOG_H   = 155   # px  boot-log box height
    BOT_PAD = 28    # px  bottom breathing room

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self._deco_tick    = 0

        font_id = QFontDatabase.addApplicationFont("assets/PressStart2P-Regular.ttf")
        self.arcade = (QFontDatabase.applicationFontFamilies(font_id)[0]
                       if font_id != -1 else "Courier New")

        self._build_ui()
        self._setup_scanline()
        self._start_timers()
        QTimer.singleShot(200, self._start_sequence)

    # ──────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────
    def _build_ui(self):
        self.setStyleSheet("background-color: #0a0a0a;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── TOP MARGIN ───────────────────────────────
        root.addSpacing(self.LOGO_MT)

        # ── GATE ICON ────────────────────────────────
        self._icon_lbl = QLabel(self)
        self._icon_pix = QPixmap(120, 102)
        self._draw_gate()
        self._icon_lbl.setPixmap(self._icon_pix)
        root.addWidget(self._icon_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addSpacing(self.GAP_IB)

        # ── SPELL ────────────────────────────────────
        self._spell_lbl = QLabel("SPELL", self)
        self._spell_lbl.setFont(QFont(self.arcade, 52))
        self._spell_lbl.setStyleSheet("color: #ff00ff; background: transparent;")
        self._spell_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sg = QGraphicsDropShadowEffect(self._spell_lbl)
        sg.setBlurRadius(20); sg.setColor(QColor("#ff00ff")); sg.setOffset(0, 0)
        self._spell_lbl.setGraphicsEffect(sg)
        self._spell_glow = sg
        root.addWidget(self._spell_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addSpacing(4)

        # ── GATE ─────────────────────────────────────
        self._gate_lbl = QLabel("GATE", self)
        self._gate_lbl.setFont(QFont(self.arcade, 52))
        self._gate_lbl.setStyleSheet("color: #22d3ee; background: transparent;")
        self._gate_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gg = QGraphicsDropShadowEffect(self._gate_lbl)
        gg.setBlurRadius(20); gg.setColor(QColor("#22d3ee")); gg.setOffset(0, 0)
        self._gate_lbl.setGraphicsEffect(gg)
        self._gate_glow = gg
        root.addWidget(self._gate_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addSpacing(self.GAP_SS)

        # ── SLOGAN ───────────────────────────────────
        slogan = QLabel("· UNLOCK YOUR MIND ·", self)
        slogan.setFont(QFont(self.arcade, 9))
        slogan.setStyleSheet("color: #facc15; background: transparent; letter-spacing: 5px;")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(slogan, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── ELASTIC SPACER ───────────────────────────
        # Absorbs leftover vertical space so content below is anchored.
        root.addStretch(1)
        root.addSpacing(self.GAP_SL)

        # ── LOADING SECTION ───────────────────────────
        wrap = QWidget(self)
        wrap.setStyleSheet("background: transparent;")
        wl   = QVBoxLayout(wrap)
        wl.setContentsMargins(self.H_PAD, 0, self.H_PAD, 0)
        wl.setSpacing(self.BAR_SP)

        # Stage label (above bar)
        self._stage_lbl = QLabel("SYSTEM INITIALIZING...", wrap)
        self._stage_lbl.setFont(QFont(self.arcade, 9))
        self._stage_lbl.setStyleSheet(
            "color: #22d3ee; background: transparent; letter-spacing: 2px;")
        self._stage_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(self._stage_lbl)

        # Thin rule above bar
        tl = QWidget(wrap); tl.setFixedHeight(2)
        tl.setStyleSheet("background: rgba(34,211,238,0.40); border:none;")
        wl.addWidget(tl)

        # THE BAR
        self._bar = LoadingBar(wrap)
        wl.addWidget(self._bar)

        # Thin rule below bar
        bl = QWidget(wrap); bl.setFixedHeight(2)
        bl.setStyleSheet("background: rgba(34,211,238,0.20); border:none;")
        wl.addWidget(bl)

        # Boot log terminal
        self._log = QTextEdit(wrap)
        self._log.setReadOnly(True)
        self._log.setFixedHeight(self.LOG_H)
        self._log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._log.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                border: 2px solid rgba(34,211,238,0.20);
                border-radius: 0px;
                color: #22d3ee;
                padding: 12px 16px;
            }
        """)
        self._log.setFont(QFont(self.arcade, 9))
        wl.addWidget(self._log)

        root.addWidget(wrap)

        # ── BOTTOM PADDING ────────────────────────────
        root.addSpacing(self.BOT_PAD)

        # ── VERSION STAMP (absolute bottom-right) ─────
        self._ver = QLabel("v4.0.1 · BUILD 2026", self)
        self._ver.setFont(QFont(self.arcade, 7))
        self._ver.setStyleSheet("color: #1a1a1a; background: transparent;")

    # ──────────────────────────────────────────
    #  GATE ICON PAINTER
    # ──────────────────────────────────────────
    def _draw_gate(self):
        self._icon_pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(self._icon_pix)
        S = 1.5     # scale vs 80×68 base grid

        CYAN = QColor("#22d3ee")
        MAG  = QColor("#ff00ff")
        BLK  = QColor("#0a0a0a")
        YEL  = QColor("#facc15")
        GRN  = QColor("#4ade80")

        def r(x, y, w, h, col):
            p.fillRect(int(x*S), int(y*S), int(w*S), int(h*S), col)

        r(2,  20, 12, 46, CYAN)                        # left post
        r(66, 20, 12, 46, CYAN)                        # right post
        r(2,  12, 76, 12, CYAN)                        # lintel
        r(2,  12, 76,  3, QColor(255, 255, 255, 35))   # shine strip
        r(14, 20, 52, 10, BLK)                         # arch gap

        p.setBrush(MAG); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(int(30*S), int(26*S), int(20*S), int(13*S), 8, 8)
        r(35, 37, 10, 8, MAG)                          # keyhole stem

        tick = self._deco_tick
        for i, (dx, dy, col) in enumerate([(16,5,YEL),(38,2,GRN),(60,5,MAG)]):
            lit = (tick // 4) % 3 == i
            if lit:
                r(dx, dy, 6, 6, col)
            else:
                faded = QColor(col)
                faded.setAlpha(45)
                r(dx, dy, 6, 6, faded)
        p.end()

    # ──────────────────────────────────────────
    #  SCANLINE
    # ──────────────────────────────────────────
    def _setup_scanline(self):
        self._sl = QLabel(self)
        self._sl.setStyleSheet(
            "background-color: rgba(34,211,238,15);"
            "border-bottom: 2px solid rgba(34,211,238,60);")
        self._sl.setFixedHeight(14)
        self._sl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._sl.raise_()

        self._sl_anim = QPropertyAnimation(self._sl, b"pos", self)
        self._sl_anim.setDuration(4000)
        self._sl_anim.setStartValue(QPoint(0, -20))
        self._sl_anim.setEndValue(QPoint(0, 1200))
        self._sl_anim.setLoopCount(-1)
        self._sl_anim.start()

        # Adding a subtle full-screen flicker
        self.flicker_overlay = QWidget(self)
        self.flicker_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.flicker_overlay.setStyleSheet("background-color: rgba(255, 255, 255, 5);")
        self.flicker_overlay.hide()
        
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self._do_flicker)
        self.flicker_timer.start(50)

    def _do_flicker(self):
        import random
        if random.random() > 0.98:
            self.flicker_overlay.show()
            QTimer.singleShot(30, self.flicker_overlay.hide)

    # ──────────────────────────────────────────
    #  TIMERS
    # ──────────────────────────────────────────
    def _start_timers(self):
        self._dt = QTimer(self)
        self._dt.timeout.connect(self._blink_deco)
        self._dt.start(140)

        self._sa = self._pulse(self._spell_glow, 8, 28, 1400, True)
        self._ga = self._pulse(self._gate_glow,  8, 28, 1400, False)

        self._gt = QTimer(self)
        self._gt.timeout.connect(self._glitch)
        self._gt.start(800)

    def _pulse(self, glow, lo, hi, dur, forward):
        a = QVariantAnimation(self)
        a.setDuration(dur)
        a.setStartValue(float(lo)); a.setEndValue(float(hi))
        if not forward:
            a.setDirection(QAbstractAnimation.Direction.Backward)
        a.valueChanged.connect(lambda v: glow.setBlurRadius(v))
        def _pp():
            a.setDirection(
                QAbstractAnimation.Direction.Backward
                if a.direction() == QAbstractAnimation.Direction.Forward
                else QAbstractAnimation.Direction.Forward)
            a.start()
        a.finished.connect(_pp)
        a.start()
        return a

    def _blink_deco(self):
        self._deco_tick += 1
        self._draw_gate()
        self._icon_lbl.setPixmap(self._icon_pix)

    def _glitch(self):
        if random.random() < 0.13:
            orig = self.pos()
            self.move(orig.x() + random.choice([-3, 3]), orig.y())
            QTimer.singleShot(85, lambda: self._reset(orig))

    def _reset(self, pos):
        try:
            if self.isVisible(): self.move(pos)
        except RuntimeError:
            pass

    # ──────────────────────────────────────────
    #  BOOT SEQUENCE
    # ──────────────────────────────────────────
    def _start_sequence(self):
        steps = [
            (0,    0,  "BOOTING SYSTEM",
             "<span style='color:#22d3ee'>&gt; INITIALIZING SPELLGATE SYSTEM v4.0...</span>"),
            (650,  18, "LOADING ASSETS",
             "<span style='color:#4ade80'>&gt; LOADING WORD DATABASE............. OK</span>"),
            (1200, 42, "LOADING ASSETS",
             "<span style='color:#4ade80'>&gt; MOUNTING AUDIO ENGINE............. OK</span>"),
            (1750, 60, "READING PROGRESS",
             "<span style='color:#4ade80'>&gt; READING USER PROGRESS............. OK</span>"),
            (2300, 78, "STARTING ENGINE",
             "<span style='color:#facc15'>&gt; CALIBRATING ARCADE INTERFACE...... OK</span>"),
            (2850, 92, "BUILDING SCENES",
             "<span style='color:#4ade80'>&gt; SPAWNING CRT EFFECTS.............. OK</span>"),
            (3350, 100,"LAUNCHING!",
             "<span style='color:#ff00ff'>&gt; ALL SYSTEMS ONLINE — READY! 🎮</span>"),
        ]
        for delay, pct, stage, html in steps:
            QTimer.singleShot(delay, lambda p=pct, s=stage, h=html: self._step(p, s, h))

        QTimer.singleShot(3400, self._finalize)
        QTimer.singleShot(4000, lambda: self.parent_window.start_game())

    def _step(self, pct, stage, html):
        self._bar.set_progress(pct)
        self._stage_lbl.setText(stage)
        self._log.append(html)
        self._log.verticalScrollBar().setValue(
            self._log.verticalScrollBar().maximum())

    def _finalize(self):
        for x in (self._dt, self._gt, self._sl_anim, self._sa, self._ga):
            try: x.stop()
            except: pass

        self._cv = True
        def _blink():
            try:
                txt = self._log.toPlainText()
                if self._cv:
                    if not txt.endswith("█"):
                        self._log.append("<span style='color:#22d3ee'>█</span>")
                else:
                    if txt.endswith("█"):
                        c = self._log.textCursor()
                        c.movePosition(c.MoveOperation.End)
                        c.deletePreviousChar()
                self._cv = not self._cv
            except RuntimeError:
                pass
        self._cur_t = QTimer(self)
        self._cur_t.timeout.connect(_blink)
        self._cur_t.start(500)

    # ──────────────────────────────────────────
    #  Qt OVERRIDES
    # ──────────────────────────────────────────
    def paintEvent(self, event):
        super().paintEvent(event)
        p   = QPainter(self)
        pen = QPen(QColor(255, 255, 255, 12))
        pen.setWidth(1); p.setPen(pen)
        for x in range(0, self.width(), 32):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 32):
            p.drawLine(0, y, self.width(), y)
        # Subtle darkened overlay
        p.fillRect(self.rect(), QColor(0, 0, 0, 40))
        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_sl'):
            self._sl.setFixedWidth(self.width())
            self._sl_anim.setEndValue(QPoint(0, self.height() + 20))
        if hasattr(self, 'flicker_overlay'):
            self.flicker_overlay.setGeometry(self.rect())
        if hasattr(self, '_ver'):
            self._ver.adjustSize()
            self._ver.move(
                self.width()  - self._ver.width()  - 20,
                self.height() - self._ver.height() - 14)