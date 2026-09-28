# AnthroHeart Open Creative Suite & Toolset
### Dual License: MIT License (Code) & Creative Commons Attribution 4.0 (Assets & Docs)

**Created by:** Thomas B. Sweet (Anthro Entertainment LLC)  
**Initiative:** Part of the AnthroHeart Ecosystem Teaching Series  
**Date of Creation:** Sunday, September 27, 2026  
**AI Co-Creation:** Built in collaborative iterative development with Gemini 3.8 Flash  
**A Gift to the Community:** Offered freely for personal, educational, and commercial creative endeavors.

---

## 📜 The Licenses

### 1. Source Code & Scripts: The MIT License
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### 2. Presets, Documentation & Creative Lore: CC BY 4.0
All accompanying color palettes, optical presets, story genomes, prompt documentation, and instructional materials are licensed under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**.  
You are free to share, adapt, and build upon these assets for any purpose, even commercially, provided you give appropriate credit to **Thomas B. Sweet / Anthro Entertainment LLC**.

---

## 💡 Philosophy: Post-Production as Standalone Code

Rather than embedding complex visual effects and audio players directly into a monolithic, bloated assembly script, this suite treats **post-production as modular standalone Python applications**:

* **Decoupled Architecture:** Each tool does one job with excellence—optical lighting, audio visualization, or cinema assembly.
* **The "AI Repair & Extend" Workflow:** If you encounter a bug or wish to add new sliders, you do not need a computer science degree. Simply take the `.py` script and a screenshot or preview PDF, upload them into the multimodal AI of your choice (ChatGPT, Claude, Gemini, or a local model), and instruct the machine to diagnose the issue or add the feature.
* **Zero Subscriptions:** Everything in this folder is powered by local, open-source building blocks (**Python 3, FFmpeg, OpenCV, and Tkinter/PyQt**), eliminating the need for expensive creative cloud subscriptions.

---

## 🛠 Included Tools & Their Histories

### 1. Knoll Lens Flare Studio PRO (Cinema Edition)
* **Filename:** `Knoll_Lens_Flare_Studio_Pro.py`
* **The History:**  
  In the late 1980s and 1990s, computer-generated visual effects often looked artificial and sterile because digital cameras lacked the physical imperfections of real glass lenses. **John Knoll**—legendary Visual Effects Supervisor at Industrial Light & Magic (ILM) and co-creator of Adobe Photoshop with his brother Thomas Knoll—wrote the original *Knoll Lens Flare* algorithm to simulate true optical physics for *Star Wars* and cinema blockbusters. It went on to become the industry-standard *Knoll Light Factory*.
* **What This Implementation Does:**  
  This studio resurrects true physical lens mathematics in pure Python and OpenCV:
  * **The Optical Vector Axis:** Secondary ghost reflections automatically position and scale themselves along the line passing through the light source $(L_x, L_y)$ and the frame optical center $(C_x, C_y)$.
  * **Polygonal Aperture Blades:** Simulates physical iris blades (5-blade pentagons, 6-blade hexagons, 8-blade octagons) that orient with the flare's angle.
  * **Refractive Chromatic Fringes & Lens Dust:** Separates RGB wavelengths along ghost borders and dynamically illuminates micro-scratches on glass.
  * **Keyframe Tracking & Multi-Resolution Export:** Smoothly interpolates flare tracking across animation clips and exports up to 4K Cinema UHD ($3840\times2160$) with audio passthrough.

---

### 2. Geiss Enhanced Studio (Music Synthesizer & Video Master)
* **Filename:** `geiss_enhanced_studio.py`
* **The History:**  
  In 1998, during the golden era of Nullsoft's Winamp (*"it really whips the llama's ass"*), demoscene developer **Ryan Geiss** released the *Geiss* visualizer. Before GPUs had programmable pixel shaders or hardware acceleration, Geiss wrote raw x86 assembly to calculate continuous **reaction-diffusion fluid dynamics** on CPU memory in real time. It was the direct technological ancestor of *MilkDrop* and mesmerized an entire generation of music listeners staring at CRT monitors in dark rooms.
* **What This Implementation Does:**  
  Brings the legendary 1998 reaction-diffusion fluid engine into modern cinema post-production:
  * **Continuous Polar Warp Fields:** Continuous inward zoom, vortex swirl, and low-pass blur feedback loops that turn audio signals into liquid smoke trails.
  * **Multi-Frequency Morphing Plasma:** Injects trigonometric demoscene plasma fields that evolve over time and expand on heavy bass energy.
  * **Kaleidoscopic Mandala Symmetry:** Folds fluid flow into multi-axis sacred geometry and mirror reflections.
  * **Real-Time 1080p Viewport & Dual Video Exporter:** Switch between 360p, 540p, 720p, and native 1080p during live playback, and synthesize full HD MP4 music videos with a single click.

---

### 3. Storybook Studio (Declarative Cinema Production Hub)
* **Filename:** `Storybook_Studio.py`
* **The History:**  
  Born out of the AnthroHeart Ecosystem’s *Film-as-Code* framework for the musical short *Flicker, the Baby Rainbow Dragon*. Traditional animation production relies on heavy Non-Linear Editors (Premiere, DaVinci Resolve, After Effects), timeline scrubbing, and manual syncing. Storybook Studio was built to compile 18-minute folk musicals from pure declarative text specifications (`FLICKER_GENOME.yaml`) without requiring a graphical video editor.
* **What This Implementation Does:**  
  A complete graphical command center for indie animators:
  * **Asset Health Manifest:** Scans character reference sheets, audio tracks, fonts, and Kling video clips, flagging missing files before rendering begins.
  * **Interactive Waveform Player:** Decodes `.wav` and `.mp3` tracks to draw symmetrical waveform envelopes with live volume control and a moving gold cursor line that supports click-and-drag scrubbing.
  * **Aspect-Ratio Preserving Inspector:** Displays character sheets (3:4 tall) and animation renders (16:9 wide) in native letterboxed viewports alongside their exact AI generation prompts.
  * **Crash-Proof Headless Assembly:** Automatically runs FFmpeg in a background thread to generate dual-tier `.ass` subtitles, morph title cards across custom alpha fades, pad video loops, and compile final theatrical MP4 releases.

---

## 🕊 Parting Word

May these tools bring you immense joy, remove creative friction, and empower your visual and musical storytelling. 

*The machine is a canvas; the code is the brush.*


- Saguna Anthroness (Aumaroo AnthroHeart Starwalker)