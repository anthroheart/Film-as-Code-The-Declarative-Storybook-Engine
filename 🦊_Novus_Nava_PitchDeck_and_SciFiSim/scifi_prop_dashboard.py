#!/usr/bin/env python3
"""
===============================================================================
       CB / SETI SCI-FI PROP RECEIVER (Live Video & Audio Recording Edition)
       Records live interactive screen video AND procedural audio (Degauss,
       knob clicks, squelch pops, static, and lock tones) into a finished MP4.
===============================================================================
"""

import os
import sys
import wave
import math
import time
import random
import subprocess
import numpy as np
import cv2
import pygame

# Initialize Pygame & Mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# =============================================================================
# COLOR PALETTE
# =============================================================================
C_BG          = (10, 12, 16)
C_RACK        = (18, 22, 30)
C_BEZEL       = (38, 46, 62)
C_GRID        = (24, 30, 44)
C_AMBER       = (255, 175, 40)
C_CYAN        = (40, 225, 255)
C_GREEN       = (60, 240, 120)
C_RED         = (255, 60, 75)
C_LED_OFF     = (28, 34, 46)
C_WHITE       = (240, 245, 255)
C_KNOB_BODY   = (48, 54, 68)
C_KNOB_CAP    = (70, 80, 100)

# =============================================================================
# PROCEDURAL AUDIO SYNTHESIZER & RECORDING SOUNDBOARD
# =============================================================================

def make_degauss_waveform():
    sr = 44100
    dur = 0.65
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    hum = np.sin(2.0 * np.pi * 60 * t) * np.exp(-t * 5.0)
    thump = np.sin(2.0 * np.pi * 30 * t) * np.exp(-t * 7.0)
    snap = (np.random.rand(n) * 2 - 1) * np.exp(-t * 40.0)
    mono = (hum * 0.7 + thump * 0.5 + snap * 0.3) * 0.8
    return np.column_stack((mono, mono)).astype(np.float32)

def make_click_waveform():
    sr = 44100
    dur = 0.025
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    mono = np.sin(2.0 * np.pi * 1800 * t) * np.linspace(1.0, 0.0, n) * 0.25
    return np.column_stack((mono, mono)).astype(np.float32)

def make_squelch_pop_waveform():
    sr = 44100
    dur = 0.04
    n = int(sr * dur)
    noise = (np.random.rand(n) * 2 - 1) * np.linspace(0.4, 0.0, n) * 0.3
    return np.column_stack((noise, noise)).astype(np.float32)

def make_lock_waveform():
    sr = 44100
    dur = 0.30
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    # Dual-tone harmonic chime
    t1 = np.sin(2.0 * np.pi * 1420 * t)
    t2 = np.sin(2.0 * np.pi * 2130 * t) * 0.5
    mono = (t1 + t2) * np.exp(-t * 6.0) * 0.35
    return np.column_stack((mono, mono)).astype(np.float32)

RAW_WAVEFORMS = {
    "degauss": make_degauss_waveform(),
    "click": make_click_waveform(),
    "pop": make_squelch_pop_waveform(),
    "lock": make_lock_waveform()
}

class SoundboardManager:
    """Handles both real-time speaker output and timeline event recording for MP4 export."""
    def __init__(self):
        self.sounds = {}
        for name, wave_data in RAW_WAVEFORMS.items():
            int16_data = (np.clip(wave_data, -1.0, 1.0) * 32767).astype(np.int16)
            self.sounds[name] = pygame.sndarray.make_sound(np.ascontiguousarray(int16_data))

        self.is_recording = False
        self.rec_start_time = 0.0
        self.recorded_events = []  # Stores (sound_name, timestamp_offset)
        self.squelch_intervals = [] # Stores (start_sec, end_sec) for atmospheric hiss

    def start_recording(self):
        self.is_recording = True
        self.rec_start_time = time.time()
        self.recorded_events.clear()
        self.squelch_intervals.clear()

    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
            if self.is_recording:
                offset = time.time() - self.rec_start_time
                self.recorded_events.append((sound_name, offset))

    def render_final_audio_track(self, total_duration, output_wav):
        """Assembles all logged events and background hiss into an accurate WAV file."""
        sr = 44100
        n_samples = int(sr * total_duration)
        track = np.zeros((n_samples, 2), dtype=np.float32)

        # 1. Overlay atmospheric background static
        static_noise = (np.random.rand(n_samples, 2).astype(np.float32) * 2.0 - 1.0) * 0.035
        track += static_noise

        # 2. Overlay individual sound events
        for sound_name, offset in self.recorded_events:
            idx = int(offset * sr)
            if idx >= n_samples:
                continue
            wave_data = RAW_WAVEFORMS[sound_name]
            end_idx = min(n_samples, idx + len(wave_data))
            chunk_len = end_idx - idx
            track[idx:end_idx] += wave_data[:chunk_len]

        # Export as standard 16-bit PCM WAV
        audio_int16 = (np.clip(track, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(output_wav, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())

AUDIO_MGR = SoundboardManager()


# =============================================================================
# INTERACTIVE HARDWARE ROTARY KNOB
# =============================================================================

class RotaryKnob:
    def __init__(self, x, y, radius, label, min_val, max_val, default_val, unit=""):
        self.x = x
        self.y = y
        self.radius = radius
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.val = default_val
        self.unit = unit
        self.dragging = False
        self.drag_start_y = 0
        self.drag_start_val = default_val

    def handle_event(self, event, log_callback):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if math.hypot(event.pos[0] - self.x, event.pos[1] - self.y) <= self.radius + 6:
                self.dragging = True
                self.drag_start_y = event.pos[1]
                self.drag_start_val = self.val
                AUDIO_MGR.play("click")
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                log_callback(f"KNOB // {self.label}: {self.val:.2f} {self.unit}")
                return True

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dy = self.drag_start_y - event.pos[1]
            span = self.max_val - self.min_val
            new_val = self.drag_start_val + (dy / 140.0) * span
            old_int = int(self.val)
            self.val = max(self.min_val, min(self.max_val, new_val))
            if int(self.val) != old_int and random.random() < 0.3:
                AUDIO_MGR.play("click")
            return True

        return False

    def draw(self, surf, font):
        pygame.draw.circle(surf, (24, 28, 38), (self.x, self.y), self.radius + 4)
        pygame.draw.circle(surf, C_BEZEL, (self.x, self.y), self.radius + 2, 2)
        pygame.draw.circle(surf, C_KNOB_BODY, (self.x, self.y), self.radius)
        pygame.draw.circle(surf, C_KNOB_CAP, (self.x, self.y), int(self.radius * 0.72))

        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        angle = math.radians(135 + ratio * 270)
        tx = int(self.x + math.cos(angle) * (self.radius - 3))
        ty = int(self.y + math.sin(angle) * (self.radius - 3))
        pygame.draw.line(surf, C_AMBER, (self.x, self.y), (tx, ty), 3)

        lbl = font.render(self.label, True, C_WHITE)
        val = font.render(f"{self.val:.1f}{self.unit}", True, C_CYAN)
        surf.blit(lbl, (self.x - lbl.get_width() // 2, self.y + self.radius + 6))
        surf.blit(val, (self.x - val.get_width() // 2, self.y + self.radius + 20))


# =============================================================================
# REAL-TIME LIVE VIDEO & AUDIO RECORDER
# =============================================================================

class LiveAVRecorder:
    def __init__(self, filename, width, height, fps=30):
        self.final_filename = filename
        self.width = width
        self.height = height
        self.fps = fps
        self.proc = None
        self.recording = False
        self.start_time = 0.0
        self.temp_video = "temp_rec_video.mp4"
        self.temp_audio = "temp_rec_audio.wav"

    def start(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}", "-pix_fmt", "rgb24", "-r", str(self.fps),
            "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            self.temp_video
        ]
        try:
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.recording = True
            self.start_time = time.time()
            AUDIO_MGR.start_recording()
            print(f"[*] Live Recording Active: {self.final_filename}")
            return True
        except Exception as e:
            print(f"[!] Recorder start failed: {e}")
            return False

    def write_frame(self, pygame_surface):
        if not self.recording or not self.proc:
            return
        if pygame_surface.get_size() != (self.width, self.height):
            surf = pygame.transform.scale(pygame_surface, (self.width, self.height))
        else:
            surf = pygame_surface
        try:
            self.proc.stdin.write(pygame.image.tostring(surf, "RGB"))
        except Exception:
            self.stop()

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        total_duration = time.time() - self.start_time

        # 1. Close Video Pipe
        if self.proc:
            try:
                self.proc.stdin.close()
                self.proc.wait()
            except Exception:
                pass

        print(f"[*] Assembling synchronized audio track ({total_duration:.1f}s)...")
        # 2. Render Audio Waveform
        AUDIO_MGR.render_final_audio_track(total_duration, self.temp_audio)

        # 3. Final Mux Video + Audio
        print("[*] Muxing video and audio streams via FFmpeg...")
        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-i", self.temp_video,
                "-i", self.temp_audio,
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                self.final_filename
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(self.temp_video): os.remove(self.temp_video)
            if os.path.exists(self.temp_audio): os.remove(self.temp_audio)
            print(f"[✓] Final Video with Sound ready: {self.final_filename}")
        except Exception as e:
            print(f"[!] FFmpeg Mux Error: {e}")


# =============================================================================
# MAIN PROP SYSTEM
# =============================================================================

class ScifiRadioMonitor:
    def __init__(self, width=1280, height=720):
        self.w = width
        self.h = height
        self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
        pygame.display.set_caption("CB / SETI Receiver Interface // MK-VIII Custom Prop")
        self.clock = pygame.time.Clock()

        self.font_main = pygame.font.SysFont("Courier", 13, bold=True)
        self.font_big  = pygame.font.SysFont("Courier", 16, bold=True)
        self.font_hud  = pygame.font.SysFont("Segoe UI", 12, bold=True)

        self.running = True
        self.is_fullscreen = False

        # Physical Degauss State
        self.degauss_active = False
        self.degauss_timer = 0.0

        # Squelch & Lock Tracker
        self.squelch_open = True
        self.carrier_locked_last = False

        # Telemetry State & Log
        self.log_filename = "scifi_activity_log.txt"
        self.append_log("--- SESSION BOOT: STOCHASTIC CB PROP SYSTEM READY ---")

        # AV Recording
        self.recorder = None
        self.rec_target_duration = 60.0
        self.rec_out_filename = "live_prop_recording.mp4"

        # Popups
        self.menu_open = False
        self.menu_pos = (0, 0)
        self.menu_items = []
        self.hud_open = False
        self.hud_rect = pygame.Rect(self.w // 2 - 220, self.h // 2 - 170, 440, 340)

        # Contact Waterfall Matrix
        self.waterfall_cols = 52
        self.waterfall_rows = 38
        self.waterfall_matrix = np.random.exponential(scale=0.08, size=(self.waterfall_rows, self.waterfall_cols))

        # 32-Band Spectrum Equalizer
        self.eq_bands = 32
        self.eq_levels = np.zeros(self.eq_bands)
        self.eq_peaks = np.zeros(self.eq_bands)

        # Hardware Controls
        self.knobs = []
        self._init_controls()

    def _init_controls(self):
        self.knobs.clear()
        rack_y = int(self.h * 0.74)
        spacing = max(80, int(self.w / 6.5))
        start_x = int(self.w * 0.12)

        self.knobs = [
            RotaryKnob(start_x + spacing * 0, rack_y, 28, "CARRIER", 1415.0, 1425.0, 1420.4, "MHz"),
            RotaryKnob(start_x + spacing * 1, rack_y, 28, "RF GAIN", 0.0, 100.0, 68.0, "dB"),
            RotaryKnob(start_x + spacing * 2, rack_y, 28, "SQUELCH", 0.0, 10.0, 3.2, "Q"),
            RotaryKnob(start_x + spacing * 3, rack_y, 28, "RF BIAS", -5.0, 5.0, 0.4, "V"),
            RotaryKnob(start_x + spacing * 4, rack_y, 28, "JITTER", 0.0, 10.0, 1.8, "ms"),
        ]
        self.btn_degauss_rect = pygame.Rect(start_x + spacing * 5 - 28, rack_y - 20, 72, 40)

    def trigger_degauss(self):
        self.degauss_active = True
        self.degauss_timer = time.time()
        AUDIO_MGR.play("degauss")
        self.waterfall_matrix[:, :] = 1.0
        self.append_log("HARDWARE_ACTION // DEGAUSS_COIL_DISCHARGED")

    def append_log(self, text):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {text}\n")

    def start_recording(self, target_res="1080p", duration=60):
        if self.recorder and self.recorder.recording:
            self.stop_recording()
            return
        w, h = (1920, 1080) if target_res == "1080p" else (1280, 720)
        self.rec_target_duration = duration
        self.rec_out_filename = f"scifi_prop_{target_res}_{int(time.time())}.mp4"
        self.recorder = LiveAVRecorder(self.rec_out_filename, w, h, fps=30)
        if self.recorder.start():
            AUDIO_MGR.play("lock")
            self.append_log(f"LIVE_RECORD_START // File: {self.rec_out_filename} // Res: {w}x{h}")

    def stop_recording(self):
        if self.recorder and self.recorder.recording:
            self.recorder.stop()
            self.append_log(f"LIVE_RECORD_SAVED // File: {self.rec_out_filename}")

    def set_resolution(self, w, h):
        self.w, self.h = w, h
        self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self._init_controls()
        self.hud_rect = pygame.Rect(self.w // 2 - 220, self.h // 2 - 170, 440, 340)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            self.w, self.h = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((self.w, self.h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            self.w, self.h = 1280, 720
            self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self._init_controls()

    def open_context_menu(self, pos):
        self.menu_open = True
        self.menu_pos = pos
        is_rec = self.recorder and self.recorder.recording
        self.menu_items = [
            ("■ Stop Recording" if is_rec else "● Start 1-Min Live Rec (1080p)", self._toggle_rec_1080),
            ("● Start 1-Min Live Rec (720p)", lambda: self.start_recording("720p", 60)),
            ("⚡ Trigger Degauss Coil (D)", self.trigger_degauss),
            ("⚙ Open Settings HUD", lambda: setattr(self, 'hud_open', True)),
            ("Switch to 1080p", lambda: self.set_resolution(1920, 1080)),
            ("Switch to 720p", lambda: self.set_resolution(1280, 720)),
            ("Toggle Fullscreen (F11)", self.toggle_fullscreen),
        ]

    def _toggle_rec_1080(self):
        if self.recorder and self.recorder.recording:
            self.stop_recording()
        else:
            self.start_recording("1080p", 60)

    def update_telemetry(self):
        carrier = self.knobs[0].val
        gain = self.knobs[1].val / 100.0
        squelch = self.knobs[2].val / 10.0
        bias = self.knobs[3].val

        is_hydrogen_lock = abs(carrier - 1420.4) < 0.18

        # Play chime on new carrier lock
        if is_hydrogen_lock and not self.carrier_locked_last:
            AUDIO_MGR.play("lock")
        self.carrier_locked_last = is_hydrogen_lock

        raw_signal_power = gain * (0.85 if is_hydrogen_lock else 0.28) + (bias * 0.04)

        prev_squelch = self.squelch_open
        self.squelch_open = raw_signal_power >= (squelch * 0.45)
        if prev_squelch != self.squelch_open:
            AUDIO_MGR.play("pop")

        # 32-Band Equalizer Update
        for b in range(self.eq_bands):
            if not self.squelch_open:
                target = 0.0
            else:
                stochastic_fluctuation = np.random.exponential(0.12)
                carrier_boost = 0.55 if (is_hydrogen_lock and 14 <= b <= 18) else 0.0
                target = min(1.0, (gain * 0.5) + stochastic_fluctuation + carrier_boost)

            self.eq_levels[b] += (target - self.eq_levels[b]) * 0.35
            if self.eq_levels[b] > self.eq_peaks[b]:
                self.eq_peaks[b] = self.eq_levels[b]
            else:
                self.eq_peaks[b] = max(0.0, self.eq_peaks[b] - 0.012)

        # Waterfall Row Update
        new_row = np.random.exponential(scale=0.06 * gain, size=self.waterfall_cols)
        if self.squelch_open and is_hydrogen_lock:
            for c in range(24, 28):
                new_row[c] = min(1.0, 0.75 + random.random() * 0.25)

        self.waterfall_matrix = np.roll(self.waterfall_matrix, 1, axis=0)
        self.waterfall_matrix[0] = new_row if self.squelch_open else np.zeros(self.waterfall_cols)

    def draw_telemetry_metrics(self, surf, y):
        carrier = self.knobs[0].val
        gain = self.knobs[1].val
        squelch = self.knobs[2].val
        bias = self.knobs[3].val
        jitter_ms = self.knobs[4].val

        gauss_val = abs(bias * 14.2) + (random.random() * 2.5) + (gain * 0.15)
        snr_val = max(-12.0, (gain * 0.38) - (squelch * 2.2) + (18.5 if abs(carrier - 1420.4) < 0.18 else -4.0))
        jitter_ps = (jitter_ms * 142.8) + (random.random() * 8.0)

        pygame.draw.rect(surf, (14, 18, 26), (0, y, self.w, 32))
        pygame.draw.line(surf, C_BEZEL, (0, y + 32), (self.w, y + 32), 1)

        metrics = [
            ("SNR", f"{snr_val:+.1f} dB", C_GREEN if snr_val > 0 else C_RED),
            ("SQUELCH", "GATE OPEN" if self.squelch_open else "CLOSED (MUTED)", C_GREEN if self.squelch_open else C_AMBER),
            ("GAUSS", f"{gauss_val:.1f} mG", C_CYAN),
            ("JITTER", f"{jitter_ps:.1f} ps", C_AMBER if jitter_ms > 4 else C_WHITE),
            ("STATUS", "CARRIER LOCKED" if abs(carrier - 1420.4) < 0.18 and self.squelch_open else "SCANNING NOISE", C_GREEN if abs(carrier - 1420.4) < 0.18 else C_AMBER)
        ]

        spacing = self.w // len(metrics)
        for idx, (label, val_str, col) in enumerate(metrics):
            txt = f"{label}: {val_str}"
            surf.blit(self.font_main.render(txt, True, col), (18 + idx * spacing, y + 8))

    def draw_contact_waterfall(self, surf, rect):
        pygame.draw.rect(surf, (8, 10, 14), rect)
        pygame.draw.rect(surf, C_BEZEL, rect, 2)

        waterfall_surf = pygame.Surface((rect.width - 4, rect.height - 28))
        cell_h = waterfall_surf.get_height() / float(self.waterfall_rows)
        cell_w = waterfall_surf.get_width() / float(self.waterfall_cols)

        carrier = self.knobs[0].val
        jitter_ms = self.knobs[4].val
        is_locked = abs(carrier - 1420.4) < 0.18

        for r_idx in range(self.waterfall_rows):
            line_jitter = int((random.random() - 0.5) * jitter_ms * 2.2) if jitter_ms > 0.5 else 0
            for c_idx in range(self.waterfall_cols):
                val = self.waterfall_matrix[r_idx, c_idx]
                if is_locked and 24 <= c_idx <= 28:
                    val = min(1.0, val * 1.8)

                g_val = int(min(1.0, val * 1.2) * 240)
                b_val = int(min(1.0, val * 1.5) * 255)
                r_val = int(val * 40)

                px = int(c_idx * cell_w) + line_jitter
                py = int(r_idx * cell_h)
                pygame.draw.rect(waterfall_surf, (r_val, g_val, b_val), (px, py, int(cell_w) + 1, int(cell_h) + 1))

        surf.blit(waterfall_surf, (rect.x + 2, rect.y + 24))
        title = "SETI WATERFALL RASTER // 1420.405 MHz HYDROGEN LINE"
        surf.blit(self.font_main.render(title, True, C_WHITE), (rect.x + 8, rect.y + 6))

    def draw_reason_equalizer(self, surf, rect):
        pygame.draw.rect(surf, C_RACK, rect)
        pygame.draw.rect(surf, C_BEZEL, rect, 2)

        title = "32-BAND STOCHASTIC SPECTRUM ANALYZER"
        surf.blit(self.font_main.render(title, True, C_CYAN), (rect.x + 10, rect.y + 6))

        bar_area_x = rect.x + 12
        bar_area_y = rect.y + 28
        bar_area_w = rect.width - 24
        bar_area_h = rect.height - 38

        num_leds = 18
        led_gap = 2
        bar_w = (bar_area_w - (self.eq_bands * 3)) / float(self.eq_bands)
        led_h = (bar_area_h - (num_leds * led_gap)) / float(num_leds)

        for b in range(self.eq_bands):
            bx = int(bar_area_x + b * (bar_w + 3))
            active_leds = int(self.eq_levels[b] * num_leds)

            for l in range(num_leds):
                ly = int(bar_area_y + (num_leds - 1 - l) * (led_h + led_gap))
                if l < 11: on_col = C_GREEN
                elif l < 15: on_col = C_AMBER
                else: on_col = C_RED

                color = on_col if l < active_leds else C_LED_OFF
                pygame.draw.rect(surf, color, (bx, ly, int(bar_w), int(led_h)), border_radius=1)

            peak_l = int(self.eq_peaks[b] * (num_leds - 1))
            py = int(bar_area_y + (num_leds - 1 - peak_l) * (led_h + led_gap))
            pygame.draw.line(surf, C_WHITE, (bx, py), (bx + int(bar_w), py), 2)

    def draw_degauss_button(self, surf):
        rect = self.btn_degauss_rect
        is_firing = self.degauss_active and (time.time() - self.degauss_timer < 0.3)
        btn_col = (255, 120, 60) if is_firing else (55, 25, 30)
        border_col = C_RED if is_firing else (140, 45, 55)

        pygame.draw.rect(surf, btn_col, rect, border_radius=5)
        pygame.draw.rect(surf, border_col, rect, 2, border_radius=5)

        txt = self.font_hud.render("DEGAUSS", True, C_WHITE)
        sub = self.font_main.render("[KEY: D]", True, (190, 190, 210))
        surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.y + 6))
        surf.blit(sub, (rect.centerx - sub.get_width() // 2, rect.y + 22))

    def run(self):
        while self.running:
            self.clock.tick(60)
            now = time.time()

            if self.degauss_active and (now - self.degauss_timer > 0.45):
                self.degauss_active = False

            self.update_telemetry()

            # Stop live recording on duration limit
            if self.recorder and self.recorder.recording:
                if (now - self.recorder.start_time) >= self.rec_target_duration:
                    self.stop_recording()

            # Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop_recording()
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.hud_open: self.hud_open = False
                        elif self.menu_open: self.menu_open = False
                        elif self.is_fullscreen: self.toggle_fullscreen()
                        else: self.stop_recording(); self.running = False
                    elif event.key in [pygame.K_F11, pygame.K_f]:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_d:
                        self.trigger_degauss()

                elif event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.set_resolution(event.w, event.h)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.open_context_menu(event.pos)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_degauss_rect.collidepoint(event.pos):
                        self.trigger_degauss()
                        continue

                    if self.menu_open:
                        mx, my = self.menu_pos
                        mw, mh = 250, len(self.menu_items) * 28 + 12
                        menu_rect = pygame.Rect(mx, my, mw, mh).clamp(pygame.Rect(0, 0, self.w, self.h))
                        for idx, (_, action) in enumerate(self.menu_items):
                            if pygame.Rect(menu_rect.x + 4, menu_rect.y + 6 + idx * 28, mw - 8, 24).collidepoint(event.pos):
                                action()
                                break
                        self.menu_open = False
                        continue

                for knob in self.knobs:
                    knob.handle_event(event, self.append_log)

            # -----------------------------------------------------------------
            # RENDER FRAME
            # -----------------------------------------------------------------
            self.screen.fill(C_BG)

            # 1. Top Bar
            pygame.draw.rect(self.screen, C_RACK, (0, 0, self.w, 42))
            pygame.draw.line(self.screen, C_BEZEL, (0, 42), (self.w, 42), 2)
            self.screen.blit(self.font_main.render("CB/SETI STOCHASTIC PROP RECEIVER // MODEL 1420-S", True, C_CYAN), (18, 14))

            # REC Status Display
            if self.recorder and self.recorder.recording:
                rec_secs = int(now - self.recorder.start_time)
                if int(now * 2) % 2 == 0: pygame.draw.circle(self.screen, C_RED, (self.w - 180, 21), 7)
                self.screen.blit(self.font_main.render(f"REC {rec_secs:02d}s / {int(self.rec_target_duration)}s", True, C_RED), (self.w - 164, 14))
            else:
                self.screen.blit(self.font_main.render("[RIGHT-CLICK FOR 1080P REC WITH AUDIO]", True, (120, 140, 160)), (self.w - 380, 14))

            # 2. Metrics HUD Bar
            self.draw_telemetry_metrics(self.screen, 42)

            # 3. Main Visual Panels
            top_y = 86
            panel_h = int(self.h * 0.44)
            split_w = int(self.w * 0.48)

            self.draw_contact_waterfall(self.screen, pygame.Rect(14, top_y, split_w, panel_h))
            self.draw_reason_equalizer(self.screen, pygame.Rect(split_w + 24, top_y, self.w - split_w - 38, panel_h))

            # 4. Hardware Rack Panel
            rack_rect = pygame.Rect(14, top_y + panel_h + 12, self.w - 28, self.h - (top_y + panel_h + 24))
            pygame.draw.rect(self.screen, C_RACK, rack_rect, border_radius=6)
            pygame.draw.rect(self.screen, C_BEZEL, rack_rect, 2, border_radius=6)
            self.screen.blit(self.font_main.render("ANALOG RECEPTION HARDWARE RACK", True, (130, 145, 175)), (rack_rect.x + 16, rack_rect.y + 10))

            for knob in self.knobs:
                knob.draw(self.screen, self.font_hud)

            self.draw_degauss_button(self.screen)

            # 5. Degauss Screen Glitch
            if self.degauss_active:
                shake_x = random.randint(-8, 8)
                shake_y = random.randint(-8, 8)
                flash_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, 60))
                self.screen.blit(flash_surf, (shake_x, shake_y))

            # Context Menu
            if self.menu_open:
                mx, my = self.menu_pos
                mw, mh = 250, len(self.menu_items) * 28 + 12
                m_rect = pygame.Rect(mx, my, mw, mh).clamp(pygame.Rect(0, 0, self.w, self.h))
                pygame.draw.rect(self.screen, (16, 20, 30), m_rect, border_radius=6)
                pygame.draw.rect(self.screen, C_AMBER, m_rect, 1, border_radius=6)
                m_pos = pygame.mouse.get_pos()
                for idx, (label, _) in enumerate(self.menu_items):
                    item_rect = pygame.Rect(m_rect.x + 4, m_rect.y + 6 + idx * 28, mw - 8, 24)
                    hover = item_rect.collidepoint(m_pos)
                    if hover: pygame.draw.rect(self.screen, (45, 55, 80), item_rect, border_radius=4)
                    self.screen.blit(self.font_hud.render(label, True, C_AMBER if hover else C_WHITE), (item_rect.x + 8, item_rect.y + 4))

            # 6. Stream Live Video Frame to MP4 Pipeline
            if self.recorder and self.recorder.recording:
                self.recorder.write_frame(self.screen)

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    monitor = ScifiRadioMonitor(1280, 720)
    monitor.run()
