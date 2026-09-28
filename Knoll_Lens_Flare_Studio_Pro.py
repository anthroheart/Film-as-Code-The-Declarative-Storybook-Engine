#!/usr/bin/env python3
"""
===============================================================================
       KNOLL LENS FLARE STUDIO PRO (Cinema Edition)
       AnthroHeart Ecosystem - Cinematic Post-FX Suite
       Features: Aspect Ratio Lock, Polygonal Iris, Chromatic Fringes, 4K Pipeline
       License: Creative Commons BY 4.0
       Created by: Thomas B. Sweet (Anthro Entertainment LLC) using Gemini 3.8 Flash
==============================================================================
"""

import os
import sys
import math
import copy
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

# =============================================================================
# OPTICAL FLARE PHYSICS ENGINE
# =============================================================================

DEFAULT_PRESETS = {
    "Violet Starlight (Flicker Orb)": {
        "core_color": (255, 180, 240),
        "glow_color": (255, 100, 180),
        "ray_color": (240, 200, 255),
        "streak_color": (255, 140, 200),
        "intensity": 1.25,
        "core_size": 25,
        "glow_size": 200,
        "num_rays": 8,
        "ray_length": 320,
        "ray_angle": 15.0,
        "streak_width": 700,
        "streak_height": 6,
        "halo_radius": 150,
        "ghost_spread": 1.05,
        "ghost_scale": 1.0,
        "iris_blades": 6,
        "lens_dust": 0.45,
        "chroma_fringe": 1.2
    },
    "Vintage Anamorphic (35mm Hollywood)": {
        "core_color": (255, 250, 240),
        "glow_color": (255, 190, 80),
        "ray_color": (255, 210, 120),
        "streak_color": (255, 160, 40),
        "intensity": 1.35,
        "core_size": 18,
        "glow_size": 120,
        "num_rays": 0,
        "ray_length": 0,
        "ray_angle": 0.0,
        "streak_width": 1400,
        "streak_height": 8,
        "halo_radius": 0,
        "ghost_spread": 0.85,
        "ghost_scale": 0.8,
        "iris_blades": 0,
        "lens_dust": 0.60,
        "chroma_fringe": 2.0
    },
    "Solar Flare (Warm Starburst)": {
        "core_color": (200, 245, 255),
        "glow_color": (60, 160, 255),
        "ray_color": (100, 210, 255),
        "streak_color": (80, 170, 255),
        "intensity": 1.15,
        "core_size": 35,
        "glow_size": 280,
        "num_rays": 14,
        "ray_length": 450,
        "ray_angle": 0.0,
        "streak_width": 550,
        "streak_height": 5,
        "halo_radius": 210,
        "ghost_spread": 1.15,
        "ghost_scale": 1.1,
        "iris_blades": 8,
        "lens_dust": 0.30,
        "chroma_fringe": 1.0
    },
    "Sci-Fi Cyan Laser": {
        "core_color": (255, 255, 255),
        "glow_color": (255, 220, 50),
        "ray_color": (255, 240, 100),
        "streak_color": (255, 190, 30),
        "intensity": 1.20,
        "core_size": 20,
        "glow_size": 170,
        "num_rays": 6,
        "ray_length": 380,
        "ray_angle": 30.0,
        "streak_width": 950,
        "streak_height": 4,
        "halo_radius": 140,
        "ghost_spread": 1.30,
        "ghost_scale": 0.9,
        "iris_blades": 5,
        "lens_dust": 0.50,
        "chroma_fringe": 1.8
    }
}

GHOST_SPECS = [
    (-0.35, 20, 0.45, (255, 140, 180)),
    (-0.15, 36, 0.25, (200, 120, 255)),
    ( 0.25, 52, 0.20, (150, 200, 255)),
    ( 0.45, 14, 0.50, (100, 255, 200)),
    ( 0.70, 80, 0.15, (255, 180, 100)),
    ( 1.10, 28, 0.35, (220, 100, 255)),
    ( 1.35, 110, 0.12, (180, 220, 255)),
    ( 1.65, 42, 0.30, (255, 150, 150)),
    ( 1.90, 18, 0.40, (140, 255, 220)),
]


def draw_iris_ghost(target_mask, center_x, center_y, radius, blades, rot_angle=0.0):
    if blades < 3:
        cv2.circle(target_mask, (center_x, center_y), radius, 1.0, -1)
    else:
        pts = []
        for i in range(blades):
            ang = rot_angle + (i * 2.0 * math.pi / blades)
            px = int(round(center_x + radius * math.cos(ang)))
            py = int(round(center_y + radius * math.sin(ang)))
            pts.append([px, py])
        cv2.fillPoly(target_mask, [np.array(pts, dtype=np.int32)], 1.0)


def render_knoll_flare_pro(canvas_w, canvas_h, lx, ly, params, dust_pattern=None):
    flare = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    lx_i, ly_i = int(round(lx)), int(round(ly))
    cx, cy = canvas_w / 2.0, canvas_h / 2.0

    intensity = params.get("intensity", 1.0)
    if intensity <= 0.001:
        return flare

    res_scale = math.sqrt((canvas_w * canvas_h) / (1920.0 * 1080.0))

    # 1. Hotspot Core
    core_sz = max(2, int(params.get("core_size", 20) * res_scale))
    core_mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    cv2.circle(core_mask, (lx_i, ly_i), core_sz, 1.0, -1)
    k_core = max(3, core_sz * 2 + 1)
    if k_core % 2 == 0: k_core += 1
    core_blur = cv2.GaussianBlur(core_mask, (k_core, k_core), core_sz * 0.6)
    c_color = np.array(params.get("core_color", (255, 255, 255)), dtype=np.float32) / 255.0
    for c in range(3):
        flare[:, :, c] += core_blur * c_color[c] * 1.9 * intensity

    # 2. Soft Outer Halo Glow
    glow_sz = max(5, int(params.get("glow_size", 160) * res_scale))
    glow_mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    cv2.circle(glow_mask, (lx_i, ly_i), glow_sz, 1.0, -1)
    k_glow = max(5, glow_sz * 2 + 1)
    if k_glow % 2 == 0: k_glow += 1
    glow_blur = cv2.GaussianBlur(glow_mask, (k_glow, k_glow), glow_sz * 0.45)
    g_color = np.array(params.get("glow_color", (255, 180, 100)), dtype=np.float32) / 255.0
    for c in range(3):
        flare[:, :, c] += glow_blur * g_color[c] * 0.9 * intensity

    # 3. Anamorphic Horizontal Streak
    st_w = int(params.get("streak_width", 600) * res_scale)
    st_h = max(1, int(params.get("streak_height", 4) * res_scale))
    if st_w > 0:
        streak_mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
        cv2.line(streak_mask, (lx_i - st_w // 2, ly_i), (lx_i + st_w // 2, ly_i), 1.0, st_h)
        k_sw = max(5, (st_w // 3) * 2 + 1)
        k_sh = max(3, st_h * 4 + 1)
        if k_sw % 2 == 0: k_sw += 1
        if k_sh % 2 == 0: k_sh += 1
        st_blur = cv2.GaussianBlur(streak_mask, (k_sw, k_sh), sigmaX=st_w * 0.22, sigmaY=st_h * 0.6)
        s_color = np.array(params.get("streak_color", (255, 180, 100)), dtype=np.float32) / 255.0
        for c in range(3):
            flare[:, :, c] += st_blur * s_color[c] * 1.3 * intensity

    # 4. Starburst Diffraction Rays with Shimmer Angle
    n_rays = int(params.get("num_rays", 8))
    ray_len = int(params.get("ray_length", 280) * res_scale)
    ray_angle_deg = params.get("ray_angle", 0.0)
    if n_rays > 0 and ray_len > 0:
        ray_mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
        base_ang = math.radians(ray_angle_deg)
        step_angle = math.pi / n_rays
        for i in range(n_rays):
            ang = base_ang + (i * step_angle)
            dx = int(math.cos(ang) * ray_len)
            dy = int(math.sin(ang) * ray_len)
            cv2.line(ray_mask, (lx_i - dx, ly_i - dy), (lx_i + dx, ly_i + dy), 1.0, 1)
        k_ray = max(5, int(9 * res_scale))
        if k_ray % 2 == 0: k_ray += 1
        ray_blur = cv2.GaussianBlur(ray_mask, (k_ray, k_ray), 1.8 * res_scale)
        r_color = np.array(params.get("ray_color", (255, 230, 180)), dtype=np.float32) / 255.0
        for c in range(3):
            flare[:, :, c] += ray_blur * r_color[c] * 0.95 * intensity

    # 5. Concentric Aperture Halo
    halo_r = int(params.get("halo_radius", 140) * res_scale)
    if halo_r > 5:
        halo_mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
        cv2.circle(halo_mask, (lx_i, ly_i), halo_r, 1.0, max(2, int(3 * res_scale)))
        k_halo = max(7, int(19 * res_scale))
        if k_halo % 2 == 0: k_halo += 1
        halo_blur = cv2.GaussianBlur(halo_mask, (k_halo, k_halo), 5.0 * res_scale)
        h_color = np.array(params.get("glow_color", (255, 150, 200)), dtype=np.float32) / 255.0
        for c in range(3):
            flare[:, :, c] += halo_blur * h_color[c] * 0.35 * intensity

    # 6. Polygonal Aperture Ghosts with Chromatic Fringing
    vx = cx - lx
    vy = cy - ly
    g_spread = params.get("ghost_spread", 1.0)
    g_scale = params.get("ghost_scale", 1.0) * res_scale
    blades = int(params.get("iris_blades", 6))
    chroma_fringe = params.get("chroma_fringe", 1.0)

    for (t_fac, rad, opac, tint) in GHOST_SPECS:
        eff_t = t_fac * g_spread
        gx = int(round(lx + eff_t * vx))
        gy = int(round(ly + eff_t * vy))
        eff_rad = max(2, int(rad * g_scale))

        if -eff_rad <= gx < canvas_w + eff_rad and -eff_rad <= gy < canvas_h + eff_rad:
            for ch_idx, scale_offset in enumerate([-0.05 * chroma_fringe, 0.0, 0.05 * chroma_fringe]):
                sub_rad = max(2, int(eff_rad * (1.0 + scale_offset)))
                g_mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
                draw_iris_ghost(g_mask, gx, gy, sub_rad, blades, rot_angle=math.atan2(vy, vx))
                k_g = max(5, sub_rad + (1 if sub_rad % 2 == 0 else 0))
                if k_g % 2 == 0: k_g += 1
                g_blur = cv2.GaussianBlur(g_mask, (k_g, k_g), sub_rad * 0.35)
                tint_val = tint[ch_idx] / 255.0
                flare[:, :, ch_idx] += g_blur * tint_val * (opac * intensity * 0.75)

    # 7. Procedural Illuminated Lens Dust
    dust_intensity = params.get("lens_dust", 0.0)
    if dust_intensity > 0.01 and dust_pattern is not None:
        dust_resized = cv2.resize(dust_pattern, (canvas_w, canvas_h), interpolation=cv2.INTER_LINEAR)
        dust_flare = glow_blur * dust_resized * (dust_intensity * intensity * 0.8)
        for c in range(3):
            flare[:, :, c] += dust_flare * g_color[c]

    return np.clip(flare, 0.0, 1.0)


# =============================================================================
# GUI STUDIO PRO WITH ASPECT-RATIO LOCK
# =============================================================================

class KnollFlareStudioPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Knoll Lens Flare Studio PRO (Cinema Edition) by Anthro Entertainment LLC")
        self.geometry("1340x880")
        self.minsize(1080, 720)
        self.configure(bg="#1A1822")

        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 24.0
        self.vid_w = 1920
        self.vid_h = 1080
        self.current_frame_idx = 0
        self.cached_frame = None

        # Letterbox geometry state
        self.disp_w = 800
        self.disp_h = 450
        self.pad_x = 0
        self.pad_y = 0

        self.flare_pos = [self.vid_w * 0.5, self.vid_h * 0.38]
        self.keyframes = {}
        self.current_params = copy.deepcopy(DEFAULT_PRESETS["Violet Starlight (Flicker Orb)"])

        np.random.seed(42)
        noise = np.random.rand(540, 960).astype(np.float32)
        self.dust_texture = np.where(noise > 0.985, (noise - 0.985) * 60.0, 0.0).astype(np.float32)

        self._build_theme()
        self._build_layout()
        self._set_preset("Violet Starlight (Flicker Orb)")

    def _build_theme(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(".", background="#1A1822", foreground="#E0E0F0", font=("Segoe UI", 9))
        self.style.configure("TLabel", background="#1A1822", foreground="#E0E0F0")
        self.style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground="#FFE28A")
        self.style.configure("TButton", background="#322846", foreground="#FFFFFF", borderwidth=0)
        self.style.map("TButton", background=[("active", "#503E70")])
        self.style.configure("Accent.TButton", background="#6930C3", foreground="#FFFFFF", font=("Segoe UI", 9, "bold"))
        self.style.map("Accent.TButton", background=[("active", "#7E3AF2")])
        self.style.configure("TCombobox", fieldbackground="#2A2438", background="#322846", foreground="#FFFFFF")

        self.option_add("*Entry.foreground", "#000000")
        self.option_add("*Entry.background", "#FFFFFF")
        self.option_add("*Entry.insertBackground", "#000000")
        self.option_add("*TEntry.foreground", "#000000")
        self.option_add("*TEntry.fieldbackground", "#FFFFFF")
        self.option_add("*Listbox.foreground", "#000000")
        self.option_add("*Listbox.background", "#FFFFFF")
        self.style.configure("TEntry", foreground="#000000", fieldbackground="#FFFFFF")

    def _build_layout(self):
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_open = ttk.Button(toolbar, text="📂 Open Video...", command=self.load_video)
        btn_open.pack(side=tk.LEFT, padx=4)

        self.lbl_file = ttk.Label(toolbar, text="No video loaded (Dark canvas)")
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        ttk.Label(toolbar, text="Export Size:").pack(side=tk.LEFT, padx=(16, 4))
        self.combo_export_res = ttk.Combobox(
            toolbar, values=["Match Source (Native)", "1080p (1920x1080)", "720p (1280x720)", "4K UHD (3840x2160)"],
            state="readonly", width=22
        )
        self.combo_export_res.current(0)
        self.combo_export_res.pack(side=tk.LEFT, padx=4)

        btn_export = ttk.Button(toolbar, text="✨ Render & Export Video", style="Accent.TButton", command=self.export_video)
        btn_export.pack(side=tk.RIGHT, padx=6)

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: Canvas Viewport
        left_box = ttk.Frame(main_pane)
        main_pane.add(left_box, weight=3)

        self.canvas = tk.Canvas(left_box, bg="#0E0C13", highlightthickness=1, highlightbackground="#362C4E")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas.bind("<Button-1>", self.on_canvas_drag)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

        transport = ttk.Frame(left_box, padding=4)
        transport.pack(fill=tk.X, padx=4, pady=2)

        self.slider_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(transport, from_=0, to=100, variable=self.slider_var, command=self.on_slider_scrub)
        self.slider.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=6)

        self.lbl_frame_info = ttk.Label(transport, text="Frame: 0 / 0 (00:00:00)")
        self.lbl_frame_info.pack(side=tk.LEFT, padx=6)

        kf_box = ttk.Frame(left_box, padding=4)
        kf_box.pack(fill=tk.X, padx=4, pady=2)
        ttk.Button(kf_box, text="🔑 Set Keyframe Here", command=self.set_keyframe).pack(side=tk.LEFT, padx=4)
        ttk.Button(kf_box, text="❌ Delete Keyframe", command=self.delete_keyframe).pack(side=tk.LEFT, padx=4)
        self.lbl_kf_status = ttk.Label(kf_box, text="No keyframes set (Static position)")
        self.lbl_kf_status.pack(side=tk.LEFT, padx=8)

        # Right: Scrollable Parameter Sidebar
        right_box = ttk.Frame(main_pane, padding=4)
        main_pane.add(right_box, weight=1)

        ttk.Label(right_box, text="Knoll Lens Preset:", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 2))
        self.preset_combo = ttk.Combobox(right_box, values=list(DEFAULT_PRESETS.keys()), state="readonly")
        self.preset_combo.pack(fill=tk.X, pady=(0, 6))
        self.preset_combo.current(0)
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)

        scroll_canvas = tk.Canvas(right_box, bg="#1A1822", highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(right_box, orient=tk.VERTICAL, command=scroll_canvas.yview)
        sliders_frame = ttk.Frame(scroll_canvas)

        sliders_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_window = scroll_canvas.create_window((0, 0), window=sliders_frame, anchor="nw")

        def _on_canvas_resize(event):
            scroll_canvas.itemconfig(scroll_window, width=event.width)
        scroll_canvas.bind("<Configure>", _on_canvas_resize)
        scroll_canvas.configure(yscrollcommand=v_scrollbar.set)

        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.controls = {}
        slider_defs = [
            ("Master Intensity", "intensity", 0.0, 3.0),
            ("Aperture Blades (0=Round, 5-9=Poly)", "iris_blades", 0, 9),
            ("Core Hotspot Radius", "core_size", 2, 80),
            ("Soft Halo Radius", "glow_size", 10, 500),
            ("Diffraction Rays Count", "num_rays", 0, 24),
            ("Ray Length", "ray_length", 0, 800),
            ("Ray Angle / Shimmer (Deg)", "ray_angle", 0, 180),
            ("Anamorphic Streak Width", "streak_width", 0, 1800),
            ("Streak Thickness", "streak_height", 1, 30),
            ("Aperture Halo Radius", "halo_radius", 0, 400),
            ("Ghost Dispersion Spread", "ghost_spread", 0.2, 2.5),
            ("Ghost Elements Scale", "ghost_scale", 0.2, 2.5),
            ("Chromatic Fringe Width", "chroma_fringe", 0.0, 3.0),
            ("Lens Dust & Micro-Scratches", "lens_dust", 0.0, 1.0),
        ]

        for label_text, key, min_val, max_val in slider_defs:
            row = ttk.Frame(sliders_frame)
            row.pack(fill=tk.X, pady=2, padx=2)
            ttk.Label(row, text=label_text).pack(anchor=tk.W)
            var = tk.DoubleVar(value=self.current_params.get(key, min_val))
            s = ttk.Scale(row, from_=min_val, to=max_val, variable=var,
                          command=lambda val, k=key: self.on_param_slider_change(k, val))
            s.pack(fill=tk.X, expand=True)
            self.controls[key] = var

        self.lbl_pos = ttk.Label(right_box, text="Source Pos: X: 960, Y: 540", foreground="#9D8CD7")
        self.lbl_pos.pack(pady=4, anchor=tk.W)

        self.update_preview()

    def on_preset_change(self, event=None):
        name = self.preset_combo.get()
        self._set_preset(name)
        self.update_preview()

    def _set_preset(self, name):
        if name in DEFAULT_PRESETS:
            self.current_params = copy.deepcopy(DEFAULT_PRESETS[name])
            for k, var in self.controls.items():
                if k in self.current_params:
                    var.set(self.current_params[k])

    def on_param_slider_change(self, key, value):
        self.current_params[key] = float(value)
        self.update_preview()

    def load_video(self):
        path = filedialog.askopenfilename(
            title="Open Video Clip",
            filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi *.webm"), ("All Files", "*.*")]
        )
        if not path:
            return

        self.video_path = path
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 24.0
        self.vid_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        self.vid_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

        self.slider.configure(to=max(1, self.total_frames - 1))
        self.lbl_file.configure(text=f"{os.path.basename(path)} ({self.vid_w}x{self.vid_h})")
        self.keyframes.clear()
        self.flare_pos = [self.vid_w * 0.5, self.vid_h * 0.38]
        self.seek_frame(0)

    def seek_frame(self, frame_idx):
        if self.cap is None:
            return
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        self.current_frame_idx = frame_idx
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        if ret:
            self.cached_frame = frame
        self._update_flare_for_frame(frame_idx)
        self.update_preview()

    def on_slider_scrub(self, val):
        idx = int(float(val))
        if idx != self.current_frame_idx:
            self.seek_frame(idx)

    def on_canvas_drag(self, event):
        # Precise coordinate transformation that compensates for letterbox padding
        if self.disp_w <= 0 or self.disp_h <= 0:
            return

        rel_x = event.x - self.pad_x
        rel_y = event.y - self.pad_y

        vx = (rel_x / float(self.disp_w)) * self.vid_w
        vy = (rel_y / float(self.disp_h)) * self.vid_h

        # Clamp safely within actual video bounds
        vx = max(0.0, min(float(self.vid_w), vx))
        vy = max(0.0, min(float(self.vid_h), vy))

        self.flare_pos = [vx, vy]
        self.lbl_pos.configure(text=f"Source Pos: X: {int(vx)}, Y: {int(vy)}")
        self.update_preview()

    def set_keyframe(self):
        f = self.current_frame_idx
        self.keyframes[f] = {"pos": list(self.flare_pos)}
        self.lbl_kf_status.configure(text=f"Keyframes: {len(self.keyframes)} set (Current: Frame {f})")

    def delete_keyframe(self):
        f = self.current_frame_idx
        if f in self.keyframes:
            del self.keyframes[f]
        self.lbl_kf_status.configure(text=f"Keyframes: {len(self.keyframes)} set")
        self.update_preview()

    def _update_flare_for_frame(self, frame_idx):
        if not self.keyframes:
            return
        exact_keys = sorted(self.keyframes.keys())
        if frame_idx in self.keyframes:
            self.flare_pos = list(self.keyframes[frame_idx]["pos"])
            return
        if frame_idx <= exact_keys[0]:
            self.flare_pos = list(self.keyframes[exact_keys[0]]["pos"])
            return
        if frame_idx >= exact_keys[-1]:
            self.flare_pos = list(self.keyframes[exact_keys[-1]]["pos"])
            return
        prev_k = max(k for k in exact_keys if k < frame_idx)
        next_k = min(k for k in exact_keys if k > frame_idx)
        t = (frame_idx - prev_k) / float(next_k - prev_k)
        p0 = self.keyframes[prev_k]["pos"]
        p1 = self.keyframes[next_k]["pos"]
        self.flare_pos = [p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])]

    def update_preview(self):
        cur_sec = (self.current_frame_idx / self.fps) if self.fps > 0 else 0
        h = int(cur_sec // 3600)
        m = int((cur_sec % 3600) // 60)
        s = int(cur_sec % 60)
        self.lbl_frame_info.configure(
            text=f"Frame: {self.current_frame_idx} / {self.total_frames} ({h:02d}:{m:02d}:{s:02d})"
        )

        if self.cached_frame is not None:
            base_bgr = self.cached_frame.copy()
        else:
            base_bgr = np.zeros((self.vid_h, self.vid_w, 3), dtype=np.uint8)
            cv2.line(base_bgr, (0, self.vid_h // 2), (self.vid_w, self.vid_h // 2), (30, 25, 40), 1)
            cv2.line(base_bgr, (self.vid_w // 2, 0), (self.vid_w // 2, self.vid_h), (30, 25, 40), 1)

        # 1. Render flare at exact native video resolution
        flare_float = render_knoll_flare_pro(
            self.vid_w, self.vid_h,
            self.flare_pos[0], self.flare_pos[1],
            self.current_params, self.dust_texture
        )

        base_float = base_bgr.astype(np.float32) / 255.0
        comp_float = 1.0 - (1.0 - base_float) * (1.0 - flare_float)
        comp_bgr = (np.clip(comp_float, 0.0, 1.0) * 255.0).astype(np.uint8)

        # Alignment target reticle
        lx, ly = int(self.flare_pos[0]), int(self.flare_pos[1])
        cv2.circle(comp_bgr, (lx, ly), 6, (0, 255, 255), 1)
        cv2.line(comp_bgr, (lx - 10, ly), (lx + 10, ly), (0, 255, 255), 1)
        cv2.line(comp_bgr, (lx, ly - 10), (lx, ly + 10), (0, 255, 255), 1)

        # 2. Strict Aspect-Ratio Preserving Letterbox/Pillarbox Display
        cw = max(100, self.canvas.winfo_width())
        ch = max(100, self.canvas.winfo_height())

        scale = min(cw / float(self.vid_w), ch / float(self.vid_h))
        self.disp_w = max(1, int(self.vid_w * scale))
        self.disp_h = max(1, int(self.vid_h * scale))

        self.pad_x = (cw - self.disp_w) // 2
        self.pad_y = (ch - self.disp_h) // 2

        resized = cv2.resize(comp_bgr, (self.disp_w, self.disp_h), interpolation=cv2.INTER_AREA)

        padded = np.zeros((ch, cw, 3), dtype=np.uint8)
        padded[:, :] = (14, 12, 19)
        padded[self.pad_y : self.pad_y + self.disp_h, self.pad_x : self.pad_x + self.disp_w] = resized

        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        self.tk_img = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    def export_video(self):
        if not self.video_path or not os.path.exists(self.video_path):
            messagebox.showerror("Error", "Please load a source video clip first.")
            return

        choice = self.combo_export_res.get()
        if "4K" in choice:
            out_w, out_h = 3840, 2160
            tag = "4k"
        elif "720p" in choice:
            out_w, out_h = 1280, 720
            tag = "720p"
        elif "1080p" in choice:
            out_w, out_h = 1920, 1080
            tag = "1080p"
        else:
            # Match Native Source Resolution exactly
            out_w, out_h = self.vid_w, self.vid_h
            tag = "native"

        out_path = filedialog.asksaveasfilename(
            title=f"Save Finished {tag.upper()} Video With Lens Flare",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")]
        )
        if not out_path:
            return

        temp_video = "temp_pro_flare.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(temp_video, fourcc, self.fps, (out_w, out_h))
        cap = cv2.VideoCapture(self.video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        progress_win = tk.Toplevel(self)
        progress_win.title(f"Rendering {tag.upper()} Flare Pass...")
        progress_win.geometry("400x120")
        progress_win.configure(bg="#1A1822")
        lbl_status = ttk.Label(progress_win, text=f"Rendering frame 0 / {total}")
        lbl_status.pack(pady=12)
        pbar = ttk.Progressbar(progress_win, maximum=total, length=320)
        pbar.pack(pady=6)
        self.update()

        try:
            for idx in range(total):
                ret, frame = cap.read()
                if not ret:
                    break

                self._update_flare_for_frame(idx)

                # Render flare directly on native frame to keep 100% native aspect ratio
                flare_float = render_knoll_flare_pro(
                    self.vid_w, self.vid_h,
                    self.flare_pos[0], self.flare_pos[1],
                    self.current_params, self.dust_texture
                )

                base_float = frame.astype(np.float32) / 255.0
                comp_float = 1.0 - (1.0 - base_float) * (1.0 - flare_float)
                comp_bgr = (np.clip(comp_float, 0.0, 1.0) * 255.0).astype(np.uint8)

                # If scaling to a standard container (like 1080p), letterbox properly without stretching
                if (out_w, out_h) != (self.vid_w, self.vid_h):
                    scale = min(out_w / float(self.vid_w), out_h / float(self.vid_h))
                    fit_w = int(self.vid_w * scale)
                    fit_h = int(self.vid_h * scale)
                    scaled_frame = cv2.resize(comp_bgr, (fit_w, fit_h), interpolation=cv2.INTER_LANCZOS4)
                    export_frame = np.zeros((out_h, out_w, 3), dtype=np.uint8)
                    px = (out_w - fit_w) // 2
                    py = (out_h - fit_h) // 2
                    export_frame[py : py + fit_h, px : px + fit_w] = scaled_frame
                else:
                    export_frame = comp_bgr

                writer.write(export_frame)

                if idx % 10 == 0:
                    lbl_status.configure(text=f"Rendering frame {idx} / {total} ({(idx/total)*100:.1f}%)")
                    pbar["value"] = idx
                    progress_win.update()

            cap.release()
            writer.release()

            lbl_status.configure(text="Muxing soundtrack audio...")
            progress_win.update()

            subprocess.run([
                "ffmpeg", "-y",
                "-i", temp_video,
                "-i", self.video_path,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0?",
                out_path
            ], check=True, capture_output=True)

            if os.path.exists(temp_video):
                os.remove(temp_video)
            progress_win.destroy()
            messagebox.showinfo("Success", f"Video compiled to:\n{out_path}")

        except Exception as e:
            if os.path.exists(temp_video):
                os.remove(temp_video)
            progress_win.destroy()
            messagebox.showerror("Render Failed", str(e))


if __name__ == "__main__":
    app = KnollFlareStudioPro()
    app.mainloop()
