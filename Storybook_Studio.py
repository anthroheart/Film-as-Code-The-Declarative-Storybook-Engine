#!/usr/bin/env python3
"""
===============================================================================
       STORYBOOK STUDIO: DECLARATIVE CINEMA PRODUCTION HUB
       All-In-One GUI, Asset Organizer, Clip & Audio Previewer & Assembly Engine
       Features: Waveform Display, Audio Player, Aspect-Ratio Lock, 1080p Engine
       Framework: AnthroHeart Ecosystem Storybook Engine
       License: Creative Commons BY 4.0 / MIT
       Creator: Anthro Entertainment LLC with Gemini 3.8 Flash
===============================================================================
"""

import os
import sys
import time
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is required. Run: pip install pyyaml")

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    PYGAME_AVAILABLE = True
except Exception as e:
    PYGAME_AVAILABLE = False
    print(f"Warning: pygame.mixer could not initialize: {e}")


# =============================================================================
# CORE ASSEMBLY ENGINE (Crash-Proof FFmpeg Pipeline)
# =============================================================================

def build_ass_subtitles(genome, base_dir="."):
    sub_cfg = genome.get("subtitles", {})
    output_ass = os.path.join(base_dir, sub_cfg.get("output_file", "storybook_subtitles.ass"))
    typo = genome.get("typography", {})
    sound_font = typo.get("subtitle_sound", "Caveat-Regular.ttf").split(".")[0]
    meaning_font = typo.get("subtitle_meaning", "Quicksand-Regular.ttf").split(".")[0]

    header = f"""[Script Info]
Title: {genome.get('meta', {}).get('title', 'Storybook')} Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SoundLayer,{sound_font},52,&H00FFFFFF,&H000000FF,&H004B2260,&H80000000,0,0,0,0,100,100,0,0,1,3,2,2,100,100,120,1
Style: MeaningLayer,{meaning_font},36,&H00E0E0FF,&H000000FF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,100,100,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(header)
        for dialog in sub_cfg.get("dialogue", []):
            start = dialog.get("start", "0:00:00.00")
            end = dialog.get("end", "0:00:05.00")
            sound = dialog.get("sound", "")
            meaning = dialog.get("meaning", "")
            if sound:
                f.write(f"Dialogue: 0,{start},{end},SoundLayer,,0,0,0,,{sound}\n")
            if meaning:
                f.write(f"Dialogue: 0,{start},{end},MeaningLayer,,0,0,0,,{meaning}\n")

    return output_ass


def get_media_duration(path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


# =============================================================================
# GUI APPLICATION INTERFACE
# =============================================================================

class StorybookStudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Storybook Studio - Declarative Cinema Engine by Anthro Entertainment LLC")
        self.geometry("1400x900")
        self.minsize(1100, 750)
        self.configure(bg="#15131C")

        self.project_dir = os.getcwd()
        self.yaml_path = os.path.join(self.project_dir, "FLICKER_GENOME.yaml")
        if not os.path.exists(self.yaml_path) and os.path.exists("FLICKER_GENOME (copy).txt"):
            self.yaml_path = os.path.abspath("FLICKER_GENOME (copy).txt")

        self.genome = {}
        self.is_rendering = False

        # Video Preview Player State
        self.preview_cap = None
        self.preview_total_frames = 0
        self.preview_cur_frame = 0
        self.preview_is_playing = False
        self.preview_image_obj = None

        # Audio Waveform & Player State
        self.current_audio_file = None
        self.audio_samples = None
        self.audio_duration = 0.0
        self.audio_is_playing = False
        self.audio_start_time = 0.0
        self.audio_seek_offset = 0.0
        self.waveform_peaks = None

        self._build_theme()
        self._build_layout()
        self.load_genome_file(self.yaml_path)

        # Background Audio Loop for Cursor Progress
        self._audio_update_loop()

    # -------------------------------------------------------------------------
    # STYLING & PALETTE
    # -------------------------------------------------------------------------
    def _build_theme(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        bg_dark = "#15131C"
        bg_panel = "#1E1A29"
        accent = "#682CC4"
        text_light = "#E8E6F2"
        text_gold = "#FFE28A"

        self.style.configure(".", background=bg_dark, foreground=text_light, font=("Segoe UI", 9))
        self.style.configure("TLabel", background=bg_dark, foreground=text_light)
        self.style.configure("Panel.TFrame", background=bg_panel)
        self.style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground=text_gold, background=bg_panel)
        self.style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground=text_gold)

        self.style.configure("TButton", background="#322846", foreground="#FFFFFF", borderwidth=0, padding=6)
        self.style.map("TButton", background=[("active", "#4D3B6B")])

        self.style.configure("Accent.TButton", background=accent, foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=8)
        self.style.map("Accent.TButton", background=[("active", "#7E3AF2")])

        self.style.configure("TNotebook", background=bg_dark, tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab", background="#282138", foreground="#A9A2C2", padding=[14, 6], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", accent)], foreground=[("selected", "#FFFFFF")])

        self.style.configure("Treeview", background="#1A1724", foreground="#E2E2EC", fieldbackground="#1A1724", rowheight=26)
        self.style.map("Treeview", background=[("selected", "#4A3378")])

        # High-contrast inputs
        self.option_add("*Entry.foreground", "#000000")
        self.option_add("*Entry.background", "#FFFFFF")
        self.option_add("*Entry.insertBackground", "#000000")

    # -------------------------------------------------------------------------
    # MAIN LAYOUT
    # -------------------------------------------------------------------------
    def _build_layout(self):
        top_bar = tk.Frame(self, bg="#1E1A29", padx=12, pady=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        lbl_app = ttk.Label(top_bar, text="🎬 STORYBOOK STUDIO", font=("Segoe UI", 13, "bold"), foreground="#FFE28A", background="#1E1A29")
        lbl_app.pack(side=tk.LEFT, padx=(0, 16))

        btn_browse_yaml = ttk.Button(top_bar, text="📂 Load Story Genome (YAML)...", command=self.browse_yaml)
        btn_browse_yaml.pack(side=tk.LEFT, padx=4)

        self.lbl_yaml_name = ttk.Label(top_bar, text="No YAML Loaded", background="#1E1A29", foreground="#A5A0C0")
        self.lbl_yaml_name.pack(side=tk.LEFT, padx=8)

        btn_init_dirs = ttk.Button(top_bar, text="📁 Create Required Folders", command=self.initialize_directories)
        btn_init_dirs.pack(side=tk.RIGHT, padx=6)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.tab_assemble = ttk.Frame(self.notebook)
        self.tab_organizer = ttk.Frame(self.notebook)
        self.tab_help = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_assemble, text="  ⚡ Assembly & Export  ")
        self.notebook.add(self.tab_organizer, text="  🎬 Clip & Asset Organizer  ")
        self.notebook.add(self.tab_help, text="  💡 Beginner's Handbook  ")

        self._build_assembly_tab()
        self._build_organizer_tab()
        self._build_help_tab()

    # -------------------------------------------------------------------------
    # TAB 1: ASSEMBLY & EXPORT
    # -------------------------------------------------------------------------
    def _build_assembly_tab(self):
        main_split = tk.PanedWindow(self.tab_assemble, orient=tk.HORIZONTAL, bg="#15131C", sashwidth=4)
        main_split.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        left_card = tk.Frame(main_split, bg="#1E1A29", padx=16, pady=16)
        main_split.add(left_card, minsize=420)

        self.lbl_proj_title = ttk.Label(left_card, text="Storybook Title", style="Title.TLabel", background="#1E1A29")
        self.lbl_proj_title.pack(anchor=tk.W, pady=(0, 2))

        self.lbl_proj_sub = ttk.Label(left_card, text="Folklore Subtitle", background="#1E1A29", foreground="#9B95B8")
        self.lbl_proj_sub.pack(anchor=tk.W, pady=(0, 10))

        self.txt_meta = tk.Text(left_card, height=7, bg="#14121B", fg="#D0CEE0", relief=tk.FLAT, font=("Consolas", 9), padx=8, pady=8)
        self.txt_meta.pack(fill=tk.X, pady=(0, 14))

        self.btn_run_assembly = ttk.Button(
            left_card, text="⚡ ASSEMBLE FULL STORYBOOK VIDEO",
            style="Accent.TButton", command=self.start_assembly_thread
        )
        self.btn_run_assembly.pack(fill=tk.X, pady=8)

        self.lbl_render_status = ttk.Label(left_card, text="Ready to compile cinema.", background="#1E1A29", foreground="#FFE28A")
        self.lbl_render_status.pack(anchor=tk.W, pady=4)

        self.progress_bar = ttk.Progressbar(left_card, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=6)

        right_card = tk.Frame(main_split, bg="#1E1A29", padx=12, pady=12)
        main_split.add(right_card, minsize=500)

        ttk.Label(right_card, text="COMPILATION CONSOLE & PIPELINE LOGS", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 6))

        self.log_console = tk.Text(right_card, bg="#0E0C13", fg="#5AF78E", font=("Consolas", 9), insertbackground="white", relief=tk.FLAT)
        self.log_console.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # TAB 2: CLIP & ASSET ORGANIZER WITH WAVEFORM & ASPECT RATIO LOCK
    # -------------------------------------------------------------------------
    def _build_organizer_tab(self):
        pane = tk.PanedWindow(self.tab_organizer, orient=tk.HORIZONTAL, bg="#15131C", sashwidth=4)
        pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Left: Asset Manifest Tree
        tree_frame = tk.Frame(pane, bg="#1E1A29", padx=8, pady=8)
        pane.add(tree_frame, minsize=460)

        top_tree_bar = tk.Frame(tree_frame, bg="#1E1A29")
        top_tree_bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(top_tree_bar, text="PRODUCTION ASSET MANIFEST", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Button(top_tree_bar, text="🔄 Refresh Scan", command=self.refresh_asset_tree).pack(side=tk.RIGHT)

        cols = ("type", "status", "path")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Asset Identifier")
        self.tree.heading("type", text="Category")
        self.tree.heading("status", text="Status")
        self.tree.heading("path", text="Relative File Path")

        self.tree.column("#0", width=180)
        self.tree.column("type", width=90, anchor=tk.CENTER)
        self.tree.column("status", width=90, anchor=tk.CENTER)
        self.tree.column("path", width=160)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Right: Preview, Waveform & Inspector
        preview_frame = tk.Frame(pane, bg="#1E1A29", padx=10, pady=10)
        pane.add(preview_frame, minsize=560)

        ttk.Label(preview_frame, text="INSPECTOR & MOTION PREVIEW", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 4))

        # Viewport Canvas (With strict aspect ratio padding)
        self.canvas_preview = tk.Canvas(preview_frame, bg="#0E0C13", width=540, height=270, highlightthickness=1, highlightbackground="#362C4E")
        self.canvas_preview.pack(fill=tk.BOTH, expand=True, pady=2)

        # Video Transport Controls (Shown on video clips)
        self.video_ctrl_bar = tk.Frame(preview_frame, bg="#1E1A29")
        self.video_ctrl_bar.pack(fill=tk.X, pady=2)

        self.btn_play_pause = ttk.Button(self.video_ctrl_bar, text="▶ Play", command=self.toggle_preview_play)
        self.btn_play_pause.pack(side=tk.LEFT, padx=4)

        self.slider_scrub = ttk.Scale(self.video_ctrl_bar, from_=0, to=100, command=self.on_preview_scrub)
        self.slider_scrub.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        self.lbl_frame_readout = ttk.Label(self.video_ctrl_bar, text="0 / 0", background="#1E1A29")
        self.lbl_frame_readout.pack(side=tk.RIGHT, padx=4)

        # Audio Waveform & Player Widget
        self.audio_panel = tk.Frame(preview_frame, bg="#181522", padx=6, pady=6, highlightthickness=1, highlightbackground="#362C4E")
        self.audio_panel.pack(fill=tk.X, pady=4)

        audio_top_bar = tk.Frame(self.audio_panel, bg="#181522")
        audio_top_bar.pack(fill=tk.X, pady=(0, 4))

        self.btn_audio_play = ttk.Button(audio_top_bar, text="▶ Play Track", command=self.toggle_audio_play)
        self.btn_audio_play.pack(side=tk.LEFT, padx=3)

        self.btn_audio_stop = ttk.Button(audio_top_bar, text="⏹ Stop", command=self.stop_audio)
        self.btn_audio_stop.pack(side=tk.LEFT, padx=3)

        self.lbl_audio_time = ttk.Label(audio_top_bar, text="00:00 / 00:00", background="#181522", font=("Consolas", 10), foreground="#FFE28A")
        self.lbl_audio_time.pack(side=tk.LEFT, padx=10)

        # Volume Slider
        ttk.Label(audio_top_bar, text="🔊", background="#181522").pack(side=tk.LEFT, padx=(12, 2))
        self.slider_volume = ttk.Scale(audio_top_bar, from_=0.0, to=1.0, value=0.8, command=self.on_volume_change)
        self.slider_volume.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=4)

        # Waveform Canvas
        self.canvas_waveform = tk.Canvas(self.audio_panel, bg="#100D16", height=68, highlightthickness=0)
        self.canvas_waveform.pack(fill=tk.X, pady=2)
        self.canvas_waveform.bind("<Button-1>", self.on_waveform_seek)
        self.canvas_waveform.bind("<B1-Motion>", self.on_waveform_seek)

        # Prompt Inspector Textbox
        ttk.Label(preview_frame, text="GENERATION PROMPTS & LYRICS:", font=("Segoe UI", 9, "bold"), background="#1E1A29", foreground="#FFE28A").pack(anchor=tk.W, pady=(6, 2))
        self.txt_prompt_inspect = tk.Text(preview_frame, height=6, bg="#14121B", fg="#E0DEEE", font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=8)
        self.txt_prompt_inspect.pack(fill=tk.X)

    # -------------------------------------------------------------------------
    # TAB 3: BEGINNER'S HANDBOOK
    # -------------------------------------------------------------------------
    def _build_help_tab(self):
        box = tk.Frame(self.tab_help, bg="#1E1A29", padx=16, pady=16)
        box.pack(fill=tk.BOTH, expand=True)

        guide_text = """
========================================================================================
   STORYBOOK GENOME PRODUCTION MANUAL: THE DECLARATIVE ANIMATION BLUEPRINT
========================================================================================

1. THE CORE PHILOSOPHY: BLUEPRINT VS. ASSEMBLY LINE
   Traditional animation requires scrub timelines, non-linear video editors, and manual syncing.
   In this engine, cinema is compiled from pure code and text declarations:

     FLICKER_GENOME.yaml  -->  The Master Architectural Blueprint
     PNG / WAV / MP4      -->  The Manufactured Construction Parts
     Storybook Studio     -->  The Automated Assembly Line Factory

   IMPORTANT: Editing prompt text or lyrics in the YAML describes the story blueprint, but does
   NOT retroactively change existing PNGs or WAVs on your hard drive. If you change a prompt,
   regenerate the corresponding part before running assembly!

----------------------------------------------------------------------------------------
2. FOLDER CHECKLIST & RECOMMENDED WORKFLOW
   Click [Create Required Folders] above to establish your studio structure:
     • characters/       Place your 3:4 character master sheets (01_Flicker.png, etc.)
     • 00_Forest...png   Master environment background image (16:9)
     • keyframes/        Start and end image pairs (01a_start.png, 01a_end.png)
     • clips/            Kling AI 5s/10s generated MP4 animations (01a.mp4 to 09b.mp4)
     • audio/            Suno / ElevenLabs master WAV tracks (01_LittleFlicker.wav, etc.)
     • fonts/            Google Fonts (Bungee, Fredoka, Quicksand, Caveat .ttf files)

----------------------------------------------------------------------------------------
3. AUDIO PLAYER & WAVEFORM TOOLS
   • Select any song in the manifest to load its audio waveform and verify lyrics.
   • Click or drag across the waveform to scrub or seek directly through the track.
   • Use the volume slider to adjust monitor loudness.

4. IMPORTANT
   • Changing the song lyrics, or image/keyframe description will not automatically re-encode the content.
   • If you need new song/change or new video animation segments, please recreate using your favorite tool.
========================================================================================
"""
        txt = tk.Text(box, bg="#14121B", fg="#E2E0F0", font=("Consolas", 10), relief=tk.FLAT, padx=12, pady=12)
        txt.insert(tk.END, guide_text)
        txt.configure(state=tk.DISABLED)
        txt.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # GENOME LOADING & SCANNING
    # -------------------------------------------------------------------------
    def browse_yaml(self):
        path = filedialog.askopenfilename(
            title="Select Story Genome Specification",
            filetypes=[("YAML & Text Files", "*.yaml *.yml *.txt"), ("All Files", "*.*")]
        )
        if path:
            self.load_genome_file(path)

    def load_genome_file(self, path):
        if not os.path.exists(path):
            self.log(f"Genome file not found: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.genome = yaml.safe_load(f)
            self.yaml_path = os.path.abspath(path)
            self.project_dir = os.path.dirname(self.yaml_path)
            self.lbl_yaml_name.configure(text=os.path.basename(path))

            meta = self.genome.get("meta", {})
            self.lbl_proj_title.configure(text=meta.get("title", "Untitled Storybook"))
            self.lbl_proj_sub.configure(text=meta.get("subtitle", "Folklore Tale"))

            self.txt_meta.delete("1.0", tk.END)
            self.txt_meta.insert(tk.END, f"Framework: {meta.get('framework_name', 'Genome')}\n")
            self.txt_meta.insert(tk.END, f"Version  : {meta.get('version', '1.0.0')}  |  License: {meta.get('license', 'CC BY 4.0')}\n")
            self.txt_meta.insert(tk.END, f"Author   : {meta.get('author', 'Unknown')}\n")
            self.txt_meta.insert(tk.END, f"Anchor   : {meta.get('provenance', {}).get('blockchain_anchor', 'N/A')}\n")
            self.txt_meta.insert(tk.END, f"AI Model : {self.genome.get('engine', {}).get('model', 'FLUX.2-Pro')}\n")

            self.refresh_asset_tree()
            self.log(f"Loaded story genome: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("YAML Load Error", f"Could not parse genome configuration:\n{e}")

    def refresh_asset_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.genome:
            return

        # 1. Environment Master
        env = self.genome.get("master_assets", {}).get("environment", {})
        if env:
            efile = env.get("file", "00_Forest_Moon_Clearing.png")
            status = "[READY]" if os.path.exists(os.path.join(self.project_dir, efile)) else "[MISSING]"
            self.tree.insert("", "end", iid="env", text="Master Environment", values=("Background", status, efile))

        # 2. Characters
        char_node = self.tree.insert("", "end", iid="cat_chars", text="Character Model Sheets", open=True)
        for char in self.genome.get("master_assets", {}).get("characters", []):
            cid = char.get("id", "char")
            cfile = char.get("file", "")
            exists = os.path.exists(os.path.join(self.project_dir, cfile))
            status = "[READY]" if exists else "[MISSING]"
            self.tree.insert(char_node, "end", iid=f"char_{cid}", text=cid, values=("Character", status, cfile))

        # 3. Clips (Video Animations)
        clip_node = self.tree.insert("", "end", iid="cat_clips", text="Animation Clips (Kling MP4s)", open=True)
        clips_folder = self.genome.get("soundtrack", {}).get("clips_folder", "clips")
        for clip in self.genome.get("keyframes", {}).get("clips", []):
            clid = clip.get("id", "clip")
            cpath = os.path.join(clips_folder, f"{clid}.mp4")
            exists = os.path.exists(os.path.join(self.project_dir, cpath))
            status = "[READY]" if exists else "[MISSING]"
            self.tree.insert(clip_node, "end", iid=f"clip_{clid}", text=f"Clip {clid}", values=("Kling Video", status, cpath))

        # 4. Audio Tracks
        audio_node = self.tree.insert("", "end", iid="cat_audio", text="Soundtrack & Voice Tracks", open=True)
        audio_folder = self.genome.get("soundtrack", {}).get("audio_folder", "audio")
        for song in self.genome.get("soundtrack", {}).get("songs", []):
            sid = song.get("id", "01")
            sfile = song.get("file", f"{sid}.wav")
            spath = os.path.join(audio_folder, sfile)
            exists = os.path.exists(os.path.join(self.project_dir, spath))
            status = "[READY]" if exists else "[MISSING]"
            self.tree.insert(audio_node, "end", iid=f"song_{sid}", text=f"Song {sid}: {song.get('title')}", values=("Audio Track", status, spath))

        # 5. Fonts
        font_node = self.tree.insert("", "end", iid="cat_fonts", text="Typography (Google Fonts)", open=False)
        fonts_dir = self.genome.get("typography", {}).get("fonts_folder", "fonts")
        for fkey in ["title_before", "title_after", "title_standard", "subtitle_sound", "subtitle_meaning"]:
            fname = self.genome.get("typography", {}).get(fkey)
            if fname:
                fpath = os.path.join(fonts_dir, fname)
                exists = os.path.exists(os.path.join(self.project_dir, fpath))
                status = "[READY]" if exists else "[MISSING]"
                self.tree.insert(font_node, "end", iid=f"font_{fkey}", text=fkey, values=("Font TTF", status, fpath))

    # -------------------------------------------------------------------------
    # INSPECTOR & TREE SELECTION
    # -------------------------------------------------------------------------
    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]

        self.txt_prompt_inspect.delete("1.0", tk.END)
        self.stop_preview()

        # Stop audio if switching to image/video
        if not item_id.startswith("song_"):
            self.stop_audio()

        if item_id == "env":
            env = self.genome.get("master_assets", {}).get("environment", {})
            self.txt_prompt_inspect.insert(tk.END, f"[MASTER ENVIRONMENT PROMPT]\n{env.get('prompt')}")
            full_path = os.path.join(self.project_dir, env.get("file", ""))
            self.display_image_preview(full_path)

        elif item_id.startswith("char_"):
            cid = item_id.replace("char_", "")
            for c in self.genome.get("master_assets", {}).get("characters", []):
                if c.get("id") == cid:
                    self.txt_prompt_inspect.insert(tk.END, f"[CHARACTER: {cid}] (is_anthro: {c.get('is_anthro')})\n{c.get('prompt')}")
                    full_path = os.path.join(self.project_dir, c.get("file", ""))
                    self.display_image_preview(full_path)
                    break

        elif item_id.startswith("clip_"):
            clid = item_id.replace("clip_", "")
            for cl in self.genome.get("keyframes", {}).get("clips", []):
                if cl.get("id") == clid:
                    self.txt_prompt_inspect.insert(tk.END, f"[CLIP {clid} START PROMPT]\n{cl.get('start_prompt')}\n\n")
                    self.txt_prompt_inspect.insert(tk.END, f"[CLIP {clid} END PROMPT]\n{cl.get('end_prompt')}")
                    clips_dir = self.genome.get("soundtrack", {}).get("clips_folder", "clips")
                    full_path = os.path.join(self.project_dir, clips_dir, f"{clid}.mp4")
                    self.load_video_preview(full_path)
                    break

        elif item_id.startswith("song_"):
            sid = item_id.replace("song_", "")
            for s in self.genome.get("soundtrack", {}).get("songs", []):
                if s.get("id") == sid:
                    text_content = s.get("lyrics") or s.get("spoken_script") or ""
                    self.txt_prompt_inspect.insert(tk.END, f"[SONG {sid}: {s.get('title')}] ({s.get('type')})\nStyle Prompt: {s.get('suno_style')}\n\n{text_content}")

                    audio_dir = self.genome.get("soundtrack", {}).get("audio_folder", "audio")
                    full_path = os.path.join(self.project_dir, audio_dir, s.get("file", f"{sid}.wav"))
                    self.load_audio_file(full_path, s.get("title", ""))
                    break

    # -------------------------------------------------------------------------
    # ASPECT-RATIO PRESERVING IMAGE & VIDEO RENDERING
    # -------------------------------------------------------------------------
    def display_image_preview(self, path):
        if not os.path.exists(path):
            self._draw_placeholder_canvas(f"File Missing:\n{os.path.basename(path)}")
            return

        img = cv2.imread(path)
        if img is None:
            return
        self._render_cv2_to_canvas(img)

    def load_video_preview(self, path):
        if not os.path.exists(path):
            self._draw_placeholder_canvas(f"Clip Missing:\n{os.path.basename(path)}")
            return

        self.preview_cap = cv2.VideoCapture(path)
        self.preview_total_frames = int(self.preview_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.preview_cur_frame = 0
        self.slider_scrub.configure(to=max(1, self.preview_total_frames - 1))
        self.lbl_frame_readout.configure(text=f"0 / {self.preview_total_frames}")

        ret, frame = self.preview_cap.read()
        if ret:
            self._render_cv2_to_canvas(frame)

    def _render_cv2_to_canvas(self, bgr_img):
        """Paints BGR frame to canvas strictly maintaining aspect ratio (Letterbox/Pillarbox)."""
        cw = max(100, self.canvas_preview.winfo_width())
        ch = max(100, self.canvas_preview.winfo_height())
        ih, iw, _ = bgr_img.shape

        # Calculate uniform scale preserving original aspect ratio
        scale = min(cw / float(iw), ch / float(ih))
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))

        resized = cv2.resize(bgr_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Pad onto a dark letterbox canvas
        padded = np.zeros((ch, cw, 3), dtype=np.uint8)
        padded[:, :] = (14, 12, 19)

        pad_x = (cw - new_w) // 2
        pad_y = (ch - new_h) // 2
        padded[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = resized

        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        self.preview_image_obj = ImageTk.PhotoImage(pil_img)
        self.canvas_preview.delete("all")
        self.canvas_preview.create_image(0, 0, anchor=tk.NW, image=self.preview_image_obj)

    def _draw_placeholder_canvas(self, msg):
        cw = max(100, self.canvas_preview.winfo_width())
        ch = max(100, self.canvas_preview.winfo_height())
        blank = np.zeros((ch, cw, 3), dtype=np.uint8)
        blank[:, :] = (25, 20, 36)
        cv2.putText(blank, msg, (30, ch // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (160, 130, 240), 1, cv2.LINE_AA)
        self._render_cv2_to_canvas(blank)

    def toggle_preview_play(self):
        if self.preview_cap is None:
            return
        self.preview_is_playing = not self.preview_is_playing
        self.btn_play_pause.configure(text="⏸ Pause" if self.preview_is_playing else "▶ Play")
        if self.preview_is_playing:
            self._preview_loop()

    def _preview_loop(self):
        if not self.preview_is_playing or self.preview_cap is None:
            return

        ret, frame = self.preview_cap.read()
        if not ret:
            self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.preview_cur_frame = 0
            ret, frame = self.preview_cap.read()

        if ret:
            self.preview_cur_frame = int(self.preview_cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.slider_scrub.set(self.preview_cur_frame)
            self.lbl_frame_readout.configure(text=f"{self.preview_cur_frame} / {self.preview_total_frames}")
            self._render_cv2_to_canvas(frame)

        self.after(33, self._preview_loop)

    def on_preview_scrub(self, val):
        if self.preview_cap is None or self.preview_is_playing:
            return
        idx = int(float(val))
        self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = self.preview_cap.read()
        if ret:
            self.lbl_frame_readout.configure(text=f"{idx} / {self.preview_total_frames}")
            self._render_cv2_to_canvas(frame)

    def stop_preview(self):
        self.preview_is_playing = False
        self.btn_play_pause.configure(text="▶ Play")
        if self.preview_cap is not None:
            self.preview_cap.release()
            self.preview_cap = None

    # -------------------------------------------------------------------------
    # AUDIO ENGINE, WAVEFORM SYNTHESIS & MOVING CURSOR
    # -------------------------------------------------------------------------
    def load_audio_file(self, path, title=""):
        self.stop_audio()
        self.current_audio_file = path

        if not os.path.exists(path):
            self._draw_placeholder_canvas(f"Audio File Missing:\n{os.path.basename(path)}")
            self.canvas_waveform.delete("all")
            self.lbl_audio_time.configure(text="00:00 / 00:00")
            return

        # Show album card on viewport
        cw = max(100, self.canvas_preview.winfo_width())
        ch = max(100, self.canvas_preview.winfo_height())
        art = np.zeros((ch, cw, 3), dtype=np.uint8)
        art[:, :] = (20, 16, 28)
        cv2.circle(art, (cw // 2, ch // 2 - 20), 45, (100, 45, 180), -1)
        cv2.putText(art, "AUDIO", (cw // 2 - 28, ch // 2 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(art, title[:40], (30, ch // 2 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 226, 138), 1, cv2.LINE_AA)
        self._render_cv2_to_canvas(art)

        # Fast audio decode to 8kHz mono array for waveform envelope
        try:
            cmd = ["ffmpeg", "-y", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "8000", "-"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            raw, _ = proc.communicate()
            samples = np.frombuffer(raw, dtype=np.float32)

            self.audio_duration = len(samples) / 8000.0 if len(samples) > 0 else 0.0
            self.audio_seek_offset = 0.0

            # Calculate waveform peak bars
            num_bars = 400
            chunk_size = max(1, len(samples) // num_bars)
            peaks = []
            for i in range(num_bars):
                chunk = samples[i * chunk_size : (i + 1) * chunk_size]
                if len(chunk) > 0:
                    peaks.append(float(np.max(np.abs(chunk))))
                else:
                    peaks.append(0.0)

            max_p = max(peaks) if peaks and max(peaks) > 0 else 1.0
            self.waveform_peaks = [p / max_p for p in peaks]

            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.slider_volume.get())

            self._draw_waveform(current_sec=0.0)
            self._update_time_label(0.0)

        except Exception as e:
            self.log(f"Error decoding waveform: {e}")

    def _draw_waveform(self, current_sec=0.0):
        self.canvas_waveform.delete("all")
        if not self.waveform_peaks:
            return

        w = self.canvas_waveform.winfo_width()
        h = self.canvas_waveform.winfo_height()
        if w < 10: w = 540
        if h < 10: h = 68

        mid_y = h / 2.0
        num_bars = len(self.waveform_peaks)
        bar_w = w / float(num_bars)

        prog_ratio = (current_sec / self.audio_duration) if self.audio_duration > 0 else 0.0
        prog_x = prog_ratio * w

        # Draw audio bars (Played = Gold, Unplayed = Soft Violet)
        for i, peak in enumerate(self.waveform_peaks):
            bx = i * bar_w
            bar_h = max(2.0, peak * (h * 0.42))
            color = "#FFE28A" if bx <= prog_x else "#6A4A9C"
            self.canvas_waveform.create_line(bx, mid_y - bar_h, bx, mid_y + bar_h, fill=color, width=max(1, int(bar_w - 1)))

        # Draw moving cursor line & handle
        self.canvas_waveform.create_line(prog_x, 0, prog_x, h, fill="#FFE28A", width=2)
        self.canvas_waveform.create_oval(prog_x - 4, 0, prog_x + 4, 8, fill="#FFE28A", outline="")

    def on_waveform_seek(self, event):
        if not self.current_audio_file or self.audio_duration <= 0.0:
            return

        w = max(10, self.canvas_waveform.winfo_width())
        rel_x = max(0, min(event.x, w))
        target_sec = (rel_x / float(w)) * self.audio_duration

        self.audio_seek_offset = target_sec
        self.audio_start_time = time.time()

        if PYGAME_AVAILABLE and self.current_audio_file:
            pygame.mixer.music.play(start=target_sec)
            self.audio_is_playing = True
            self.btn_audio_play.configure(text="⏸ Pause")

        self._draw_waveform(target_sec)
        self._update_time_label(target_sec)

    def toggle_audio_play(self):
        if not self.current_audio_file or not PYGAME_AVAILABLE:
            return

        if self.audio_is_playing:
            pygame.mixer.music.pause()
            self.audio_is_playing = False
            self.btn_audio_play.configure(text="▶ Play")
        else:
            if pygame.mixer.music.get_pos() == -1:
                pygame.mixer.music.play(start=self.audio_seek_offset)
            else:
                pygame.mixer.music.unpause()
            self.audio_is_playing = True
            self.audio_start_time = time.time() - self.audio_seek_offset
            self.btn_audio_play.configure(text="⏸ Pause")

    def stop_audio(self):
        if PYGAME_AVAILABLE and self.audio_is_playing:
            pygame.mixer.music.stop()
        self.audio_is_playing = False
        self.audio_seek_offset = 0.0
        self.btn_audio_play.configure(text="▶ Play Track")
        self._draw_waveform(0.0)
        self._update_time_label(0.0)

    def on_volume_change(self, val):
        vol = float(val)
        if PYGAME_AVAILABLE:
            pygame.mixer.music.set_volume(vol)

    def _audio_update_loop(self):
        """Smoothly moves the vertical cursor along the waveform canvas."""
        if self.audio_is_playing and self.audio_duration > 0.0 and PYGAME_AVAILABLE:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                cur_sec = self.audio_seek_offset + (pos_ms / 1000.0)
                if cur_sec >= self.audio_duration:
                    self.stop_audio()
                else:
                    self._draw_waveform(cur_sec)
                    self._update_time_label(cur_sec)

        self.after(40, self._audio_update_loop)

    def _update_time_label(self, current_sec):
        cm = int(current_sec // 60)
        cs = int(current_sec % 60)
        tm = int(self.audio_duration // 60)
        ts = int(self.audio_duration % 60)
        self.lbl_audio_time.configure(text=f"{cm:02d}:{cs:02d} / {tm:02d}:{ts:02d}")

    # -------------------------------------------------------------------------
    # UTILITIES & DIRECTORIES
    # -------------------------------------------------------------------------
    def initialize_directories(self):
        req_dirs = ["characters", "keyframes", "audio", "clips", "fonts"]
        created = []
        for d in req_dirs:
            p = os.path.join(self.project_dir, d)
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
                created.append(d)

        self.refresh_asset_tree()
        if created:
            messagebox.showinfo("Folders Initialized", f"Created missing studio folders:\n{', '.join(created)}")
        else:
            messagebox.showinfo("Folders Verified", "All required studio folders already exist.")

    def log(self, text):
        self.log_console.insert(tk.END, f"{text}\n")
        self.log_console.see(tk.END)

    # -------------------------------------------------------------------------
    # THREADED VIDEO ASSEMBLY WORKER
    # -------------------------------------------------------------------------
    def start_assembly_thread(self):
        if self.is_rendering:
            return
        if not self.genome:
            messagebox.showerror("Error", "Please load a valid story genome first.")
            return

        self.is_rendering = True
        self.btn_run_assembly.configure(state=tk.DISABLED)
        self.lbl_render_status.configure(text="Compiling storybook cinema in background...")
        self.progress_bar["value"] = 0

        t = threading.Thread(target=self._run_assembly_worker, daemon=True)
        t.start()

    def _run_assembly_worker(self):
        try:
            self.log("\n=======================================================")
            self.log(f"STARTING ASSEMBLY: {self.genome.get('meta', {}).get('title')}")
            self.log("=======================================================")

            soundtrack = self.genome.get("soundtrack", {})
            typo = self.genome.get("typography", {})
            fonts_dir = os.path.join(self.project_dir, typo.get("fonts_folder", "fonts"))
            audio_dir = os.path.join(self.project_dir, soundtrack.get("audio_folder", "audio"))
            clips_dir = os.path.join(self.project_dir, soundtrack.get("clips_folder", "clips"))
            final_output = os.path.join(self.project_dir, soundtrack.get("output_video", "Final_Storybook.mp4"))

            ass_path = build_ass_subtitles(self.genome, self.project_dir)
            self.log(f"Subtitles compiled: {os.path.basename(ass_path)}")

            songs = soundtrack.get("songs", [])
            total_songs = len(songs)
            rendered_segments = []
            concat_list = os.path.join(self.project_dir, "segments_concat.txt")

            for idx, song in enumerate(songs):
                audio_file = os.path.join(audio_dir, song.get("file", ""))
                if not os.path.exists(audio_file):
                    self.log(f"Warning: Audio {song.get('file')} missing. Synthesizing placeholder.")
                    os.makedirs(audio_dir, exist_ok=True)
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", "15", audio_file
                    ], check=True, capture_output=True)

                total_song_dur = get_media_duration(audio_file)
                clip_filenames = song.get("clips", [])
                num_clips = len(clip_filenames)
                slot_dur = total_song_dur / num_clips if num_clips > 0 else total_song_dur

                clip_paths = []
                for c in clip_filenames:
                    cp = os.path.join(clips_dir, c)
                    if not os.path.exists(cp):
                        self.log(f"Warning: Clip {c} missing. Synthesizing fallback visual.")
                        os.makedirs(clips_dir, exist_ok=True)
                        subprocess.run([
                            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1E142B:s=1920x1080:d=5",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", cp
                        ], check=True, capture_output=True)
                    clip_paths.append(cp)

                seg_file = os.path.join(self.project_dir, f"seg_{idx:02d}.mp4")
                rendered_segments.append(seg_file)

                # Title filter calculation
                raw_title = song.get("title", "").replace("'", "").replace(":", "\\:")
                if song.get("morph_title", False):
                    font_before = os.path.join(fonts_dir, typo.get("title_before", "Bungee-Regular.ttf"))
                    font_after = os.path.join(fonts_dir, typo.get("title_after", "Fredoka-SemiBold.ttf"))
                    title_vf = (
                        f"drawtext=fontfile='{font_before}':text='{raw_title}':fontcolor=white:fontsize=64:"
                        f"x=(w-text_w)/2:y=180:alpha='if(lt(t,3),1,if(lt(t,5),(5-t)/2,0))',"
                        f"drawtext=fontfile='{font_after}':text='{raw_title}':fontcolor=0xFFE28A:fontsize=64:"
                        f"x=(w-text_w)/2:y=180:alpha='if(lt(t,3),0,if(lt(t,5),(t-3)/2,1))'"
                    )
                else:
                    font_std = os.path.join(fonts_dir, typo.get("title_standard", "Quicksand-Regular.ttf"))
                    title_vf = (
                        f"drawtext=fontfile='{font_std}':text='{raw_title}':fontcolor=white:fontsize=50:"
                        f"x=(w-text_w)/2:y=180:alpha='if(lt(t,4),1,0)'"
                    )

                inputs = []
                filter_parts = []
                for c_idx, cp in enumerate(clip_paths):
                    inputs.extend(["-stream_loop", "-1", "-t", str(slot_dur), "-i", cp])
                    filter_parts.append(
                        f"[{c_idx}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v{c_idx}];"
                    )

                if num_clips > 1:
                    concat_inputs = "".join([f"[v{i}]" for i in range(num_clips)])
                    filter_parts.append(f"{concat_inputs}concat=n={num_clips}:v=1:a=0,{title_vf}[outv]")
                else:
                    filter_parts.append(f"[v0]{title_vf}[outv]")

                full_filter = "".join(filter_parts)

                cmd = [
                    "ffmpeg", "-y",
                    *inputs,
                    "-i", audio_file,
                    "-filter_complex", full_filter,
                    "-map", "[outv]", "-map", f"{num_clips}:a",
                    "-t", str(total_song_dur),
                    "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
                    seg_file
                ]

                self.log(f"Rendering Segment {idx + 1}/{total_songs}: {song.get('title')} ({total_song_dur:.1f}s)...")
                subprocess.run(cmd, check=True, capture_output=True)

                pct = int(((idx + 1) / (total_songs + 1)) * 100)
                self.progress_bar["value"] = pct

            with open(concat_list, "w") as f:
                for s in rendered_segments:
                    f.write(f"file '{s}'\n")

            self.log("Burning typography & dual-tier subtitles...")
            final_cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-vf", f"ass={ass_path}:fontsdir={fonts_dir}",
                "-c:v", "libx264", "-c:a", "copy", final_output
            ]
            subprocess.run(final_cmd, check=True, capture_output=True)

            for s in rendered_segments:
                if os.path.exists(s): os.remove(s)
            if os.path.exists(concat_list): os.remove(concat_list)

            self.progress_bar["value"] = 100
            self.log("\n=======================================================")
            self.log(f"🎉 CINEMA COMPILED SUCCESSFULLY:\n{final_output}")
            self.log("=======================================================")
            self.lbl_render_status.configure(text="Assembly Complete!")
            messagebox.showinfo("Assembly Success", f"Your Storybook movie has compiled successfully to:\n{final_output}")

        except Exception as e:
            self.log(f"\n[ERROR ENCOUNTERED]: {e}")
            self.lbl_render_status.configure(text="Assembly halted with an error.")
            messagebox.showerror("Assembly Failed", f"An error occurred during video assembly:\n{e}")

        finally:
            self.is_rendering = False
            self.btn_run_assembly.configure(state=tk.NORMAL)


if __name__ == "__main__":
    app = StorybookStudioApp()
    app.mainloop()
