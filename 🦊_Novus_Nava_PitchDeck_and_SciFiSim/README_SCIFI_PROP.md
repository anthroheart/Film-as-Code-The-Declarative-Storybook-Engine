# 🛸 Sci-Fi FUI Prop Monitor & Audio/Video Generator

### _Vintage Radio-Astronomy & Studio Rack Simulation for Film & TV Production_

**Inspired by _Contact_ (1997) & _Propellerhead Reason_ Hardware Synthesizer Racks**

### by Thomas B. Sweet (Saguna Anthroness/Aumaroo AnthroHeart Starwalker) at Anthro Entertainment LLC

### License: Creative Commons BY 4.0 w/Attribution

---

## 🌟 Overview

The **Sci-Fi FUI Prop Monitor** is an interactive, real-time Python graphical interface (FUI / Fantasy User Interface) engineered for on-set practical video monitors, green screen backdrops, and post-production background screen loops.

Combining the aesthetics of **vintage SETI radio-telescope receivers** with **analog audio rack hardware**, this tool runs smoothly at 60 FPS in full screen or windowed mode and allows live interaction with simulated physical dials, a functional squelch gate, a CRT degauss coil, and a stochastic radio-frequency waterfall raster.

Crucially, it includes an integrated **Live AV Recorder** that streams both your on-screen visual interactions and procedural sound effects (degauss hums, squelch pops, knob clicks, and carrier lock chimes) directly into a synchronized **1080p or 720p MP4** file.

---

## ⚡ Key Features

- **Interactive "Reason"-Style Rotary Knobs:** Click and drag vertically to smoothly tune **Carrier Frequency**, **RF Gain**, **Squelch**, **RF Bias**, and **Jitter**.
- **SETI "Contact" Waterfall Raster:** A stochastic 2D radio-frequency spectrum displaying atmospheric noise and a lockable **1420.405 MHz Neutral Hydrogen line**.
- **32-Band Segmented LED Spectrum Analyzer:** Vintage studio rack-style VU bars with dynamic green-to-amber-to-red thresholds and floating peak needles.
- **Physical Degauss Coil:** Click the on-screen **`DEGAUSS`** button (or tap **`D`**) to discharge a high-voltage magnetic coil—triggering an authentic 60 Hz hum/thump and a visual phosphor flash.
- **Functional CB Squelch Gate:** Turning the `SQUELCH` knob above the current noise floor cuts off static and gates the LED spectrum with an audible pop.
- **Live Video & Audio MP4 Recording:** Right-click anywhere to record a live 60-second clip of your session directly to an H.264/AAC MP4 video with sample-accurate audio sync.
- **Live Session Telemetry Logging:** Automatically records all knob rotations, carrier locks, and recording events with microsecond timestamps into `scifi_activity_log.txt`.

---

## 🛠️ Installation & Requirements

### 1. Prerequisites

Ensure you have **Python 3.9+** and **FFmpeg** installed on your system.

```bash
# Ubuntu / Debian / FurryOS
sudo apt update && sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

### 2. Python Dependencies

Install the required packages in your active environment:

```bash
pip install pygame numpy opencv-python
```

---

## 🚀 Usage

### 1. Launch the Interface

Run the script to launch the interactive prop console:

```bash
python3 scifi_prop_dashboard.py
```

### 2. Keyboard & Mouse Controls

| Input                             | Action                                                           |
| :-------------------------------- | :--------------------------------------------------------------- |
| **Left-Click + Drag Dial**        | Rotate hardware dials up or down to adjust values                |
| **Right-Click**                   | Open floating context menu (Record, HUD, Resolution, Fullscreen) |
| **`D` Key** or **Degauss Button** | Fire high-voltage CRT degauss coil (audio blast + screen flash)  |
| **`F11`** or **`F`**              | Toggle Fullscreen / Windowed mode                                |
| **`ESC`**                         | Close popup menus / Exit fullscreen / Exit application           |
| **OS Maximize Button**            | Automatically scales the UI to match the display resolution      |

---

## 🎛️ Hardware Rack Modules

### 1. The Dials

- **`CARRIER (MHz)`:** Tunes the reception frequency from 1415.0 to 1425.0 MHz. Tuning to **`1420.4 MHz`** achieves a carrier lock, triggering a bright visual beam on the waterfall and an audible harmonic chime.
- **`RF GAIN (dB)`:** Adjusts receiver sensitivity from 0.0 to 100.0 dB, driving the stochastic noise floor and LED amplitude.
- **`SQUELCH (Q)`:** Sets the threshold gate for the audio and spectrum displays. When raw signal power falls below squelch, the receiver gates shut with a CB audio pop.
- **`RF BIAS (V)`:** Sets DC baseline voltage offset and drives the simulated magnetic Gauss meter.
- **`JITTER (ms)`:** Adds temporal instability and horizontal CRT scanline tearing across the video raster.

### 2. Real-Time Telemetry Bar

The central digital readout bar displays live physical metrics:

- **`SNR`:** Signal-to-Noise Ratio calculated from gain and carrier lock status.
- **`SQUELCH`:** Displays gate status (`GATE OPEN` in green or `CLOSED (MUTED)` in amber).
- **`GAUSS`:** Ambient magnetic flux density measured in milliGauss (`mG`).
- **`JITTER`:** High-frequency scanline deviation measured in picoseconds (`ps`).
- **`STATUS`:** Displays current carrier state (`CARRIER LOCKED` or `SCANNING NOISE`).

---

## 🎥 Real-Time AV Recording Workflow

1. Right-click anywhere on the monitor screen to bring up the context menu.
2. Select **`● Start 1-Min Live Rec (1080p)`** or **`(720p)`**.
3. A flashing red **`REC`** indicator and countdown timer will appear in the top-right corner.
4. Interact with the console: turn dials, trigger degauss blasts, and adjust squelch.
5. The recording will automatically stop and finalize after **60 seconds**, or you can right-click and select **`■ Stop Recording`** at any time.
6. The finished video file will be saved in your working directory as:
   `scifi_prop_1080p_<timestamp>.mp4`

All procedural sounds (degauss coil thump, knob clicks, squelch pops, lock chimes, and ambient radio static) will be rendered into the final MP4 in stereo AAC audio.

---

## 📁 Output File Structure

```
.
├── scifi_prop_dashboard.py      # Main interactive application & recorder
├── scifi_activity_log.txt       # Real-time session telemetry log
├── scifi_prop_1080p_*.mp4       # Final recorded prop videos with audio
└── README.md                    # Documentation
```

---

## 📜 License

- **Code & Architecture:** [MIT License](https://opensource.org/licenses/MIT)
- **Visual & Audio Design:** Creative Commons Attribution 4.0 International (CC BY 4.0)
