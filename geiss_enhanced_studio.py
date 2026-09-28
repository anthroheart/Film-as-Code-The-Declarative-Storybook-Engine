#!/usr/bin/env python3
"""
===============================================================================
       GEISS ENHANCED STUDIO & HD MUSIC VIDEO SYNTHESIZER
       Tribute to Ryan Geiss (1998) - Modernized for Film & AI Cinema
       Features: Live Viewport up to Native 1080p, Morphing Plasma, 20+ Controls
       License: Creative Commons BY 4.0
       Created by: Thomas B. Sweet (Anthro Entertainment LLC) using Gemini 3.8 Flash
===============================================================================
"""

import os
import sys
import math
import time
import subprocess
import numpy as np
import cv2

# Auto-detect PyQt6 or fallback to PyQt5
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QSlider, QLabel, QComboBox, QFileDialog, QProgressBar,
        QFrame, QTabWidget, QScrollArea, QGroupBox
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
except ImportError:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QSlider, QLabel, QComboBox, QFileDialog, QProgressBar,
        QFrame, QTabWidget, QScrollArea, QGroupBox
    )
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor

import pygame

# Initialize sound mixer
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

# =============================================================================
# COLOR PALETTES
# =============================================================================

PALETTES = {
    "Violet Starlight (Flicker)": [
        (0.00, (20, 10, 45)),
        (0.25, (180, 50, 220)),
        (0.50, (255, 120, 200)),
        (0.75, (100, 220, 255)),
        (1.00, (255, 255, 255))
    ],
    "Solar Flare (Classic Fire)": [
        (0.00, (15, 0, 0)),
        (0.25, (200, 30, 0)),
        (0.50, (255, 140, 0)),
        (0.80, (255, 235, 90)),
        (1.00, (255, 255, 255))
    ],
    "Electric Cyberpunk": [
        (0.00, (5, 5, 30)),
        (0.30, (0, 230, 255)),
        (0.60, (255, 0, 180)),
        (0.85, (120, 255, 110)),
        (1.00, (255, 255, 255))
    ],
    "Liquid Emerald": [
        (0.00, (0, 20, 15)),
        (0.30, (0, 190, 95)),
        (0.60, (40, 255, 200)),
        (0.85, (210, 255, 110)),
        (1.00, (255, 255, 255))
    ],
    "Deep Cosmos (Psychedelic)": [
        (0.00, (30, 5, 40)),
        (0.25, (0, 120, 255)),
        (0.55, (255, 40, 130)),
        (0.80, (255, 210, 40)),
        (1.00, (255, 255, 255))
    ]
}


# =============================================================================
# GEISS ENHANCED WARP & PLASMA ENGINE
# =============================================================================

class GeissEnhancedEngine:
    def __init__(self, width=640, height=360):
        self.w = width
        self.h = height
        self.buffer = np.zeros((self.h, self.w, 3), dtype=np.float32)

        # 1. Warp & Flow
        self.zoom = 1.018
        self.rot = 0.012
        self.swirl = 0.45
        self.swirl_falloff = 0.05
        self.turb_x = 0.00
        self.turb_y = 0.00
        self.turb_freq = 3.0
        self.symmetry = 0

        # 2. Morphing Plasma
        self.plasma_opacity = 0.35
        self.plasma_speed = 1.0
        self.plasma_scale = 3.5
        self.plasma_audio_drive = 0.6

        # 3. Optics & Color
        self.decay = 0.955
        self.blur_k = 3
        self.chroma = 0.007
        self.vignette = 0.25
        self.palette_speed = 0.2
        self.contrast = 1.05
        self.palette_name = "Violet Starlight (Flicker)"

        # 4. Audio Lasers
        self.polar_radius = 0.38
        self.polar_amp = 0.25
        self.ribbon_y = 0.82
        self.ribbon_amp = 0.12
        self.bass_shock = 0.04

        self.time_counter = 0.0
        self._init_mesh()

    def resize(self, width, height):
        self.w = max(64, width)
        self.h = max(64, height)
        self.buffer = np.zeros((self.h, self.w, 3), dtype=np.float32)
        self._init_mesh()

    def _init_mesh(self):
        xs = np.linspace(-1.0, 1.0, self.w, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, self.h, dtype=np.float32)
        self.grid_x, self.grid_y = np.meshgrid(xs, ys)

        self.grid_r = np.sqrt(self.grid_x**2 + self.grid_y**2) + 1e-6
        self.grid_theta = np.arctan2(self.grid_y, self.grid_x)
        self.vignette_map = np.clip(1.0 - (self.grid_r * 0.7), 0.0, 1.0)[:, :, np.newaxis]

        # Fast downscaled grid for real-time plasma
        self.pw = max(32, self.w // 4)
        self.ph = max(32, self.h // 4)
        pxs = np.linspace(-1.0, 1.0, self.pw, dtype=np.float32)
        pys = np.linspace(-1.0, 1.0, self.ph, dtype=np.float32)
        self.p_gx, self.p_gy = np.meshgrid(pxs, pys)

    def step(self, waveform, bass_energy=0.0):
        self.time_counter += 0.03 * self.plasma_speed

        eff_zoom = self.zoom + (bass_energy * self.bass_shock)
        eff_rot = self.rot + (math.sin(self.time_counter * 0.7) * 0.005)
        eff_swirl = self.swirl * (1.0 + bass_energy * 0.7)

        r_warped = self.grid_r / eff_zoom
        theta_warped = self.grid_theta + eff_rot + (self.grid_r * eff_swirl * self.swirl_falloff)

        gx = r_warped * np.cos(theta_warped)
        gy = r_warped * np.sin(theta_warped)

        if self.turb_x > 0.0 or self.turb_y > 0.0:
            gx += np.sin(self.grid_y * self.turb_freq + self.time_counter) * (self.turb_x * 0.05)
            gy += np.cos(self.grid_x * self.turb_freq + self.time_counter) * (self.turb_y * 0.05)

        if self.symmetry == 1:
            gx = np.abs(gx) * np.sign(self.grid_x)
        elif self.symmetry == 2:
            gx = np.abs(gx) * np.sign(self.grid_x)
            gy = np.abs(gy) * np.sign(self.grid_y)

        base_x = (gx + 1.0) * 0.5 * (self.w - 1)
        base_y = (gy + 1.0) * 0.5 * (self.h - 1)

        warped = np.empty_like(self.buffer)
        for c, offset in enumerate([-self.chroma, 0.0, self.chroma]):
            map_x = (base_x * (1.0 + offset)).astype(np.float32)
            map_y = (base_y * (1.0 + offset)).astype(np.float32)
            warped[:, :, c] = cv2.remap(
                self.buffer[:, :, c], map_x, map_y,
                cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT
            )

        # SAFE DECAY & CONTRAST (Prevents Overflow & NaNs)
        clamped_warp = np.clip(warped * self.decay, 0.0, 1.0)
        if abs(self.contrast - 1.0) > 0.001:
            decayed = np.power(clamped_warp, self.contrast)
        else:
            decayed = clamped_warp

        k = self.blur_k if self.blur_k % 2 != 0 else self.blur_k + 1
        self.buffer = cv2.GaussianBlur(decayed, (k, k), 0.4)

        if self.plasma_opacity > 0.01:
            self._inject_morphing_plasma(bass_energy)

        self._inject_audio(waveform, bass_energy)

        if self.vignette > 0.0:
            eff_vig = 1.0 - (1.0 - self.vignette_map) * self.vignette
            self.buffer *= eff_vig

        # Sanitize buffer
        self.buffer = np.nan_to_num(self.buffer, nan=0.0, posinf=1.0, neginf=0.0)
        return np.clip(self.buffer, 0.0, 1.0)

    def _inject_morphing_plasma(self, bass_energy):
        t = self.time_counter
        s = self.plasma_scale
        audio_boost = 1.0 + (bass_energy * self.plasma_audio_drive)

        p1 = np.sin(self.p_gx * s + t)
        p2 = np.cos(self.p_gy * s - t * 0.8)
        p3 = np.sin((self.p_gx + self.p_gy) * (s * 0.7) + t * 1.3)
        p4 = np.sin(np.sqrt(self.p_gx**2 + self.p_gy**2) * (s * 1.2) - t * 1.5)

        plasma = ((p1 + p2 + p3 + p4 + 4.0) / 8.0) * audio_boost
        plasma_up = cv2.resize(plasma, (self.w, self.h), interpolation=cv2.INTER_LINEAR)

        pal_color = self._get_palette_color((self.time_counter * self.palette_speed) % 1.0)
        c_bgr = np.array([pal_color[2], pal_color[1], pal_color[0]], dtype=np.float32) / 255.0

        for c in range(3):
            self.buffer[:, :, c] += plasma_up * c_bgr[c] * (self.plasma_opacity * 0.4)

    def _inject_audio(self, waveform, bass_energy):
        if waveform is None or len(waveform) < 64:
            return

        cx, cy = self.w // 2, self.h // 2
        pts_count = min(len(waveform), 256)

        # 1. Circular Polar Oscilloscope
        angles = np.linspace(0, 2 * math.pi, pts_count, endpoint=False)
        base_r = min(cx, cy) * self.polar_radius * (1.0 + bass_energy * 0.35)
        radii = base_r + waveform[:pts_count] * (min(cx, cy) * self.polar_amp)

        px = (cx + radii * np.cos(angles)).astype(np.int32)
        py = (cy + radii * np.sin(angles)).astype(np.int32)
        poly_pts = np.column_stack([px, py])

        pal_rgb = self._get_palette_color((self.time_counter * self.palette_speed) % 1.0)
        c_bgr = (pal_rgb[2] / 255.0, pal_rgb[1] / 255.0, pal_rgb[0] / 255.0)

        cv2.polylines(self.buffer, [poly_pts], isClosed=True, color=c_bgr, thickness=2, lineType=cv2.LINE_AA)

        # 2. Horizontal Ribbon Waveform
        xs = np.linspace(20, self.w - 20, pts_count, dtype=np.int32)
        ys = (self.h * self.ribbon_y + waveform[:pts_count] * (self.h * self.ribbon_amp)).astype(np.int32)
        ribbon_pts = np.column_stack([xs, ys])

        glow = tuple(min(1.0, val * 1.6) for val in c_bgr)
        cv2.polylines(self.buffer, [ribbon_pts], isClosed=False, color=glow, thickness=2, lineType=cv2.LINE_AA)

    def _get_palette_color(self, val):
        palette = PALETTES.get(self.palette_name, PALETTES["Violet Starlight (Flicker)"])
        val = np.clip(val, 0.0, 1.0)
        for i in range(len(palette) - 1):
            p0, c0 = palette[i]
            p1, c1 = palette[i + 1]
            if p0 <= val <= p1:
                t = (val - p0) / (p1 - p0)
                return (
                    int(c0[0] + t * (c1[0] - c0[0])),
                    int(c0[1] + t * (c1[1] - c0[1])),
                    int(c0[2] + t * (c1[2] - c0[2]))
                )
        return palette[-1][1]


# =============================================================================
# EXPORT THREAD (720p & 1080p PIPELINE)
# =============================================================================

class EnhancedVideoExportThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_path, output_path, resolution_tuple, engine_params):
        super().__init__()
        self.audio_path = audio_path
        self.output_path = output_path
        self.res_w, self.res_h = resolution_tuple
        self.params = engine_params
        self.is_running = True

    def run(self):
        temp_raw_video = "temp_enhanced_geiss.mp4"
        try:
            cmd_audio = ["ffmpeg", "-y", "-i", self.audio_path, "-f", "f32le", "-ac", "1", "-ar", "44100", "-"]
            pipe_audio = subprocess.Popen(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            raw_audio, _ = pipe_audio.communicate()
            samples = np.frombuffer(raw_audio, dtype=np.float32)

            if len(samples) == 0:
                self.error.emit("Could not decode audio stream.")
                return

            sample_rate = 44100
            fps = 30
            total_duration = len(samples) / float(sample_rate)
            total_frames = int(total_duration * fps)

            engine = GeissEnhancedEngine(self.res_w, self.res_h)
            for k, v in self.params.items():
                setattr(engine, k, v)

            cmd_video = [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{self.res_w}x{self.res_h}", "-pix_fmt", "bgr24", "-r", str(fps),
                "-i", "-",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                temp_raw_video
            ]
            proc_video = subprocess.Popen(cmd_video, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

            chunk_size = int(sample_rate / fps)
            for f in range(total_frames):
                if not self.is_running:
                    proc_video.stdin.close()
                    proc_video.kill()
                    return

                idx_start = f * chunk_size
                idx_end = idx_start + 1024
                chunk = samples[idx_start:idx_end] if idx_end <= len(samples) else np.zeros(1024, dtype=np.float32)

                bass_energy = min(1.0, float(np.sqrt(np.mean(chunk[:128]**2))) * 4.0)
                frame_float = engine.step(chunk, bass_energy)
                frame_bgr = (frame_float * 255.0).astype(np.uint8)
                proc_video.stdin.write(frame_bgr.tobytes())

                if f % 15 == 0:
                    self.progress.emit(f, total_frames)

            proc_video.stdin.close()
            proc_video.wait()

            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_raw_video,
                "-i", self.audio_path,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "256k",
                "-shortest",
                self.output_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(temp_raw_video):
                os.remove(temp_raw_video)

            self.finished.emit(self.output_path)

        except Exception as e:
            if os.path.exists(temp_raw_video):
                os.remove(temp_raw_video)
            self.error.emit(str(e))


# =============================================================================
# GUI VIEWPORT & MAIN STUDIO WINDOW
# =============================================================================

class ViewportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(480, 270)
        self.current_pixmap = None

    def update_frame(self, bgr_array):
        h, w, _ = bgr_array.shape
        rgb = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2RGB)
        fmt = QImage.Format.Format_RGB888 if hasattr(QImage, 'Format') else QImage.Format_RGB888
        qimg = QImage(rgb.data, w, h, 3 * w, fmt)
        self.current_pixmap = QPixmap.fromImage(qimg)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.current_pixmap:
            painter.drawPixmap(self.rect(), self.current_pixmap)
        else:
            painter.fillRect(self.rect(), QColor(14, 12, 20))


class GeissEnhancedStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geiss Enhanced Studio - Synthesizer & Video Master by Anthro Entertainment LLC")
        self.resize(1340, 840)
        self.setMinimumSize(1024, 680)

        self.audio_path = None
        self.samples = None
        self.sample_rate = 44100
        self.is_playing = False

        # Default live resolution: 540p balanced
        self.engine = GeissEnhancedEngine(960, 540)

        self._build_style()
        self._build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    def _build_style(self):
        self.setStyleSheet("""
        QMainWindow { background-color: #121018; }
        QWidget { color: #E2E2EC; font-family: 'Segoe UI', 'Ubuntu', sans-serif; font-size: 13px; }
        QTabWidget::pane { border: 1px solid #2C263D; background: #181522; border-radius: 6px; }
        QTabBar::tab { background: #221D30; color: #A9A2C2; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
        QTabBar::tab:selected { background: #682CC4; color: #FFFFFF; }
        QPushButton { background-color: #352B4D; color: #FFFFFF; border-radius: 5px; padding: 7px 14px; font-weight: bold; border: none; }
        QPushButton:hover { background-color: #4C3C6F; }
        QPushButton#accentBtn { background-color: #682CC4; }
        QPushButton#accentBtn:hover { background-color: #7E3AF2; }
        QSlider::groove:horizontal { height: 6px; background: #2A243A; border-radius: 3px; }
        QSlider::sub-page:horizontal { background: #682CC4; border-radius: 3px; }
        QSlider::handle:horizontal { background: #EAE6F8; width: 14px; margin: -4px 0; border-radius: 7px; }
        QComboBox { background-color: #231E31; border: 1px solid #3B3352; border-radius: 4px; padding: 5px; color: #FFFFFF; }
        QProgressBar { background-color: #181522; border: 1px solid #3B3352; border-radius: 5px; text-align: center; color: white; }
        QProgressBar::chunk { background-color: #682CC4; border-radius: 4px; }
        """)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Left Column: Viewport & Transport
        left_box = QVBoxLayout()
        main_layout.addLayout(left_box, stretch=3)

        self.viewport = ViewportWidget()
        left_box.addWidget(self.viewport, stretch=1)

        # Transport & Quality Bar
        bar = QHBoxLayout()
        self.btn_load = QPushButton("📂 Open Audio...")
        self.btn_load.clicked.connect(self.load_audio)
        bar.addWidget(self.btn_load)

        self.btn_play = QPushButton("▶ Play / Pause")
        self.btn_play.clicked.connect(self.toggle_play)
        bar.addWidget(self.btn_play)

        self.lbl_track = QLabel("No audio loaded")
        bar.addWidget(self.lbl_track, stretch=1)

        # LIVE VIEWPORT QUALITY SELECTOR
        bar.addWidget(QLabel("Live View:"))
        self.combo_live_res = QComboBox()
        self.combo_live_res.addItem("Live: 540p (960x540)", (960, 540))
        self.combo_live_res.addItem("Live: 1080p (1920x1080) [Native]", (1920, 1080))
        self.combo_live_res.addItem("Live: 720p (1280x720)", (1280, 720))
        self.combo_live_res.addItem("Live: 360p (640x360) [Fast]", (640, 360))
        self.combo_live_res.currentIndexChanged.connect(self._on_live_res_changed)
        bar.addWidget(self.combo_live_res)

        # Export Format Dropdown
        self.combo_res = QComboBox()
        self.combo_res.addItem("Export: 1080p Full HD", (1920, 1080))
        self.combo_res.addItem("Export: 720p HD", (1280, 720))
        bar.addWidget(self.combo_res)

        self.btn_export = QPushButton("✨ Synthesize Video")
        self.btn_export.setObjectName("accentBtn")
        self.btn_export.clicked.connect(self.export_video)
        bar.addWidget(self.btn_export)
        left_box.addLayout(bar)

        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        left_box.addWidget(self.pbar)

        # Right Column: 20+ Parameter Tabs
        tab_widget = QTabWidget()
        tab_widget.setFixedWidth(380)
        main_layout.addWidget(tab_widget)

        # TAB 1: WARP & FLOW
        tab_warp = QWidget()
        t1 = QVBoxLayout(tab_warp)
        t1.addWidget(self._make_slider("1. Inward Zoom", "zoom", 0.98, 1.06, self.engine.zoom))
        t1.addWidget(self._make_slider("2. Rotation Velocity", "rot", -0.05, 0.05, self.engine.rot))
        t1.addWidget(self._make_slider("3. Swirl Vortex", "swirl", 0.0, 1.5, self.engine.swirl))
        t1.addWidget(self._make_slider("4. Swirl Falloff", "swirl_falloff", 0.01, 0.2, self.engine.swirl_falloff))
        t1.addWidget(self._make_slider("5. Wave Turbulence X", "turb_x", 0.0, 1.0, self.engine.turb_x))
        t1.addWidget(self._make_slider("6. Wave Turbulence Y", "turb_y", 0.0, 1.0, self.engine.turb_y))
        t1.addWidget(self._make_slider("7. Turbulence Frequency", "turb_freq", 1.0, 10.0, self.engine.turb_freq))

        lbl_sym = QLabel("8. Kaleidoscope Symmetry:")
        self.combo_sym = QComboBox()
        self.combo_sym.addItems(["Off (Standard Flow)", "Mirror Horizontal", "Mandala 4-Fold"])
        self.combo_sym.currentIndexChanged.connect(lambda i: setattr(self.engine, 'symmetry', i))
        t1.addWidget(lbl_sym)
        t1.addWidget(self.combo_sym)
        t1.addStretch(1)
        tab_widget.addTab(tab_warp, "🌀 Warp & Flow")

        # TAB 2: MORPHING PLASMA
        tab_plasma = QWidget()
        t2 = QVBoxLayout(tab_plasma)
        t2.addWidget(self._make_slider("9. Plasma Opacity", "plasma_opacity", 0.0, 1.0, self.engine.plasma_opacity))
        t2.addWidget(self._make_slider("10. Morphing Speed", "plasma_speed", 0.1, 3.0, self.engine.plasma_speed))
        t2.addWidget(self._make_slider("11. Spatial Scale", "plasma_scale", 1.0, 8.0, self.engine.plasma_scale))
        t2.addWidget(self._make_slider("12. Audio Bass Drive", "plasma_audio_drive", 0.0, 2.0, self.engine.plasma_audio_drive))
        t2.addStretch(1)
        tab_widget.addTab(tab_plasma, "✨ Plasma")

        # TAB 3: OPTICS & COLOR
        tab_optics = QWidget()
        t3 = QVBoxLayout(tab_optics)
        t3.addWidget(QLabel("Color Palette:"))
        self.combo_pal = QComboBox()
        self.combo_pal.addItems(list(PALETTES.keys()))
        self.combo_pal.currentTextChanged.connect(lambda t: setattr(self.engine, 'palette_name', t))
        t3.addWidget(self.combo_pal)

        t3.addWidget(self._make_slider("13. Trail Persistence", "decay", 0.88, 0.99, self.engine.decay))
        t3.addWidget(self._make_slider("14. Chromatic Lens Dispersion", "chroma", 0.0, 0.02, self.engine.chroma))
        t3.addWidget(self._make_slider("15. Lens Vignette", "vignette", 0.0, 0.8, self.engine.vignette))
        t3.addWidget(self._make_slider("16. Palette Cycling Speed", "palette_speed", 0.0, 1.0, self.engine.palette_speed))
        t3.addWidget(self._make_slider("17. Dynamic Contrast", "contrast", 0.9, 1.3, self.engine.contrast))
        t3.addStretch(1)
        tab_widget.addTab(tab_optics, "🌈 Optics & Color")

        # TAB 4: AUDIO LASERS
        tab_lasers = QWidget()
        t4 = QVBoxLayout(tab_lasers)
        t4.addWidget(self._make_slider("18. Polar Ring Radius", "polar_radius", 0.1, 0.8, self.engine.polar_radius))
        t4.addWidget(self._make_slider("19. Polar Wave Height", "polar_amp", 0.05, 0.6, self.engine.polar_amp))
        t4.addWidget(self._make_slider("20. Ribbon Vertical Y", "ribbon_y", 0.5, 0.95, self.engine.ribbon_y))
        t4.addWidget(self._make_slider("21. Ribbon Amplitude", "ribbon_amp", 0.02, 0.35, self.engine.ribbon_amp))
        t4.addWidget(self._make_slider("22. Bass Beat Shockwave", "bass_shock", 0.0, 0.12, self.engine.bass_shock))
        t4.addStretch(1)
        tab_widget.addTab(tab_lasers, "⚡ Audio Lasers")

    def _make_slider(self, label_text, attr_name, min_v, max_v, default_v):
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 2, 0, 2)
        l.addWidget(QLabel(label_text))
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(0, 1000)
        norm = int(((default_v - min_v) / (max_v - min_v)) * 1000)
        s.setValue(norm)
        s.valueChanged.connect(
            lambda v, a=attr_name, mi=min_v, ma=max_v: setattr(self.engine, a, mi + (v / 1000.0) * (ma - mi))
        )
        l.addWidget(s)
        return box

    def _on_live_res_changed(self, idx):
        res = self.combo_live_res.currentData()
        if res:
            w, h = res
            self.engine.resize(w, h)

    def load_audio(self):
        # Force built-in Qt dialog to prevent Linux portal hangs
        opt = QFileDialog.Option.DontUseNativeDialog if hasattr(QFileDialog, 'Option') else QFileDialog.DontUseNativeDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio Track", "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a);;All Files (*.*)",
            options=opt
        )
        if not path:
            return

        self.audio_path = path
        self.lbl_track.setText(os.path.basename(path))

        cmd = ["ffmpeg", "-y", "-i", self.audio_path, "-f", "f32le", "-ac", "1", "-ar", "44100", "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        raw, _ = proc.communicate()
        self.samples = np.frombuffer(raw, dtype=np.float32)

        pygame.mixer.music.load(self.audio_path)
        self.is_playing = False
        self.btn_play.setText("▶ Play")

    def toggle_play(self):
        if not self.audio_path:
            return

        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.btn_play.setText("▶ Play")
        else:
            if pygame.mixer.music.get_pos() == -1:
                pygame.mixer.music.play()
            else:
                pygame.mixer.music.unpause()
            self.is_playing = True
            self.btn_play.setText("⏸ Pause")

    def _on_tick(self):
        chunk = None
        bass_energy = 0.0

        if self.is_playing and self.samples is not None and len(self.samples) > 0:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                cur_idx = int((pos_ms / 1000.0) * self.sample_rate)
                idx_end = cur_idx + 1024
                if idx_end <= len(self.samples):
                    chunk = self.samples[cur_idx:idx_end]
                    bass_energy = float(np.sqrt(np.mean(chunk[:128]**2))) * 4.0
                    bass_energy = min(1.0, bass_energy)

        if chunk is None:
            t = time.time() * 3.0
            xs = np.linspace(0, 4 * math.pi, 256)
            chunk = (np.sin(xs + t) * 0.15).astype(np.float32)

        frame = self.engine.step(chunk, bass_energy)
        self.viewport.update_frame((frame * 255.0).astype(np.uint8))

    def export_video(self):
        if not self.audio_path:
            self.lbl_track.setText("Please load an audio track first!")
            return

        res_tuple = self.combo_res.currentData()
        res_label = "1080p" if res_tuple[0] == 1920 else "720p"

        opt = QFileDialog.Option.DontUseNativeDialog if hasattr(QFileDialog, 'Option') else QFileDialog.DontUseNativeDialog
        out_path, _ = QFileDialog.getSaveFileName(
            self, f"Save {res_label} Geiss Video", f"geiss_{res_label}_video.mp4",
            "MP4 Video (*.mp4)",
            options=opt
        )
        if not out_path:
            return

        params = {
            "zoom": self.engine.zoom,
            "rot": self.engine.rot,
            "swirl": self.engine.swirl,
            "swirl_falloff": self.engine.swirl_falloff,
            "turb_x": self.engine.turb_x,
            "turb_y": self.engine.turb_y,
            "turb_freq": self.engine.turb_freq,
            "symmetry": self.engine.symmetry,
            "plasma_opacity": self.engine.plasma_opacity,
            "plasma_speed": self.engine.plasma_speed,
            "plasma_scale": self.engine.plasma_scale,
            "plasma_audio_drive": self.engine.plasma_audio_drive,
            "decay": self.engine.decay,
            "blur_k": self.engine.blur_k,
            "chroma": self.engine.chroma,
            "vignette": self.engine.vignette,
            "palette_speed": self.engine.palette_speed,
            "contrast": self.engine.contrast,
            "palette_name": self.engine.palette_name,
            "polar_radius": self.engine.polar_radius,
            "polar_amp": self.engine.polar_amp,
            "ribbon_y": self.engine.ribbon_y,
            "ribbon_amp": self.engine.ribbon_amp,
            "bass_shock": self.engine.bass_shock,
        }

        if self.is_playing:
            self.toggle_play()

        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        self.btn_export.setEnabled(False)

        self.export_thread = EnhancedVideoExportThread(self.audio_path, out_path, res_tuple, params)
        self.export_thread.progress.connect(lambda cur, tot: self.pbar.setValue(int((cur / tot) * 100)))
        self.export_thread.finished.connect(self._on_export_finished)
        self.export_thread.error.connect(self._on_export_error)
        self.export_thread.start()

    def _on_export_finished(self, out_path):
        self.pbar.setVisible(False)
        self.btn_export.setEnabled(True)
        self.lbl_track.setText(f"Exported: {os.path.basename(out_path)}")

    def _on_export_error(self, err_msg):
        self.pbar.setVisible(False)
        self.btn_export.setEnabled(True)
        self.lbl_track.setText(f"Export Error: {err_msg}")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Disable native Linux portal dialogs globally across the app
    if hasattr(Qt, 'ApplicationAttribute') and hasattr(Qt.ApplicationAttribute, 'AA_DontUseNativeDialogs'):
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    elif hasattr(Qt, 'AA_DontUseNativeDialogs'):
        app.setAttribute(Qt.AA_DontUseNativeDialogs, True)

    window = GeissEnhancedStudio()
    window.show()
    sys.exit(app.exec() if hasattr(app, 'exec') else app.exec_())
