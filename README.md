<!-- ===================================================================== -->
<!--                   STORYBOOK GENOME ENGINE HEADER                      -->
<!-- ===================================================================== -->

<div align="center">

# 🎬 Film-as-Code: The Declarative Storybook Engine

### A 17-Minute Automated Animated Musical Produced with Zero GUI Timelines

[![License: CC BY 4.0](https://img.shields.io/badge/Creative_Assets-CC_BY_4.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT](https://img.shields.io/badge/Scripts-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Engine](https://img.shields.io/badge/Engine-Python_%2B_FFmpeg_%2B_libass-orange.svg)](https://ffmpeg.org/)
[![Bitcoin Provenance](https://img.shields.io/badge/Provenance-Bitcoin_Anchored-gold.svg)](https://opentimestamps.org/)

**A completely headless, code-driven animation pipeline for children’s books, visual novels, and folk musicals.**

</div>

---

### 💡 What Is This?

Traditional animation workflows require non-linear editors (Premiere, Resolve, After Effects), hours of timeline scrubbing, and endless manual syncing. **The Storybook Genome Engine compiles cinema from pure declarative data.**

- **Zero-GUI Timeline:** 17 minutes and 16 seconds (25,095 frames) stitched, padded, and paced entirely in Python and FFmpeg.
- **Declarative Control (`FLICKER_GENOME.yaml`):** The story text, characters, fonts, clip relationships, and subtitle tracks are completely separated from the assembly logic.
- **Dual-Tier Subtitle System:** Generates `.ass` subtitles with distinct typographical tiers for character sounds vs. internal emotional translations.
- **Dynamic Font Morphing:** Transitions title sequences between distinct typographic states programmatically over custom alpha fades.
- **Zero-Cost Cryptographic Provenance:** Roots the entire release bundle into the **Bitcoin blockchain** using OpenTimestamps and Ed25519 digital signatures.
- **Render Engine:** (`make_video.py`) and (`FlickerRender_v2.py`) are duplicate versions of the same render engine. **You only need to use one.** Pick whichever filename you prefer.

- **Music/Voice Engine:** Suno v6. Please note there may be mentions of ElevenLabs throughout this work, though I did not use that. Suno works better for my needs of speaking with music in the background.

- **Animation Engine:** Kling AI 3.0

- **Image/Art Engine:** FLUX.2 Pro via OpenRouter (via API for batch, though you can do it through OpenRouter website one at a time if that's easier.)

- **Storytelling and Planning Engine:** Claude Sonnet 5 via OpenRouter. This also does coding too. For advanced coding I recommend Gemini 3.8 Flash.

> [!IMPORTANT]
> **A Note for Writers & First-Time Creators**
>
> The YAML file is your project's **master production specification**. It describes the story, assets, prompts, audio, subtitles, and assembly—but changing the YAML does **not automatically regenerate media that has already been rendered**.
>
> - **Changing `lyrics:` or `spoken_script:`** changes the declared text, subtitles, and metadata. It **does not re-sing or rerecord the audio**. To change what is actually heard, generate a new `.wav` file using Suno, ElevenLabs, your own microphone, or another audio tool, then replace the corresponding file in `/audio`.
> - **Changing `start_prompt:` or `end_prompt:`** changes the instructions for generating keyframes. It **does not modify an existing animation** in `/clips`. Regenerate the affected keyframes and motion clip, then replace the corresponding files.
> - **Changing `master_assets` prompts** changes the instructions for asset generation. It **does not retroactively change existing PNGs**. Regenerate the affected image assets when you want those changes to appear.
> - **Changing subtitle text or timestamps** changes the generated subtitle track, but the final movie must be assembled again for those changes to appear in the exported video.
> - **Changing typography, titles, or assembly settings** affects the rendering process, but existing media files are not regenerated.
> - **Running `make_video.py`** assembles the **currently existing** images, audio, and video clips. It does not regenerate creative assets automatically.
>
> Think of the workflow like this:
>
> ```text
>                    FLICKER_GENOME.yaml
>                   "The Blueprint"
>                           │
>          ┌────────────────┼────────────────┐
>          ▼                ▼                ▼
>       Images           Audio           Keyframes
>          │                │                │
>          ▼                ▼                ▼
>      PNG Assets        WAV Files      Motion Generation
>                                           │
>                                           ▼
>                                      MP4 Clips
>          └────────────────┬────────────────┘
>                           ▼
>                    make_video.py
>                    "The Assembly Line"
>                           │
>                           ▼
>                     Final Movie
> ```
>
> **In short:** the YAML is the **blueprint**, the PNG/WAV/MP4 files are the **manufactured parts**, and `make_video.py` is the **assembly line**. If you change the blueprint, regenerate the affected part before the change can appear in the finished film.

> [!TIP]
> **If You Get Stuck**
>
> Don't be intimidated by the terminal or an error message. If something goes wrong, **take a screenshot of the error and paste it into the AI assistant of your choice** (ChatGPT, Claude, Gemini, a local coding assistant, etc.) and ask it to diagnose the problem.
>
> For common Python, FFmpeg, YAML, file-path, or dependency errors, a solution can often be found very quickly. You don't need to be an experienced programmer to use this pipeline—you just need to be willing to ask the machine what went wrong.
>
> **The error message is usually a clue, not a dead end.**

> [!TIP]

> **No API Required**
>
> The Storybook Genome Engine does **not require any paid API, AI subscription, or cloud service to render a film**. API-based scripts are optional conveniences for creators who want to automate and batch-generate large numbers of images and keyframes.
>
> In my own production, I **could not afford the separate Kling API credits** (which are different from the Kling website's monthly membership), so I simply used the Kling website to batch-render the 16 animation clips and then downloaded the completed clips into the project's `/clips` directory.
>
> You can likewise generate or create your assets using **any tools you already have access to**—free web-based generators, local models, hand-drawn artwork, existing images, your own recordings, or manually created video clips. Once the required PNG, WAV, and MP4 assets are placed in the appropriate folders, the Python + FFmpeg assembly engine can build the final movie locally.
>
> **The API is an accelerator, not a requirement.**
>
> ```text
> WITHOUT API
> Your tools → Your assets → Storybook Genome → Python + FFmpeg → Movie
>
> WITH API
> Storybook Genome → Batch API generation → Assets → Python + FFmpeg → Movie
> ```
>
> The same declarative production system works either way. The API simply makes large-scale asset generation faster and more convenient.
>
> **This project was deliberately built so that lack of API access does not prevent someone from making a film.**

---

# Flicker, the Baby Rainbow Dragon: A Forest Moon Folklore Tale

### AnthroHeart Storybook Production Template (v1.0.3)

**Created by Thomas B. Sweet (Saguna Anthroness / becoming Divine Anthro)**
**License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
**Publisher:** Anthro Entertainment LLC — Part of the AnthroHeart Ecosystem Teaching Template Series

---

## 1. Executive Summary & Premise

_Flicker, the Baby Rainbow Dragon_ is a 9-song animated folklore short set on a small, moss-covered moon ringed by ancient trees. On Forest Moon, every young dragon eventually discovers their first flame—a personal, gentle milestone that can never be forced. Flicker's scales remain a quiet, dim grey-blue. As well-meaning friends attempt absurd methods to help him ignite, Flicker learns that some things only arrive when you stop striving and allow yourself to rest.

### Core Creative Rules

- **Tone:** Winnie-the-Pooh whimsy, tenderness, and catharsis. **Rest over spectacle**—the ignition beat is an unguarded, peaceful moment of wonder rather than an explosive climax.
- **House Art Style:** Painterly children's-book illustration with watercolor and gouache textures. All supporting forest folk are **fully bipedal anthropomorphic animals** (standing upright on two legs with human-like posture and hands). Flicker himself is a **feral quadruped baby dragon** whose shifting pastel scales serve as his pre-verbal language.
- **Ignition Beat:** A literal magical flame—glowing in swirling violet, blue, and gold—hovers as an enchanted orb _above_ Flicker's open paws, never touching his body.

---

## 2. Architecture: Declarative YAML Engine

This repository is built as a **reusable production template**. All story elements, character descriptions, prompt texts, clip sequences, audio tags, subtitle timestamps, and font choices are decoupled into a central driver:

```
FLICKER_GENOME.yaml   <-- The Single Source of Truth (Story, Style, Settings)
       │
       ├── generate_images.py      <-- (Optional) Automated master reference generator
       ├── generate_keyframes.py   <-- (Optional) Automated keyframe pair generator
       └── make_video.py           <-- Core assembly engine (FFmpeg + ASS Subtitles)
```

The Python scripts contain **no hardcoded story text**. You can create an entirely new animated film simply by duplicating `FLICKER_GENOME.yaml`, updating the story metadata, and running the same scripts.

---

## Final Video Assembled Successfully: Flicker_The_Baby_Rainbow_Dragon_Final.mp4

```
real	18m46.341s
user	127m35.930s
sys	0m46.281s
```

## 3. Production Matrix: $0 Free Stack vs. High-Speed API Stack

You can build this entire short in a single day using either 100% free web interfaces or automated API scripts:

| Production Phase     | 100% Free ($0) Route                                                             | High-Speed API Route (~$1.50 Total)                                          |
| :------------------- | :------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| **Story & Genome**   | Claude / ChatGPT / Local LLM + Text Editor                                       | Pre-configured `FLICKER_GENOME.yaml`                                         |
| **Image Generation** | **Pollinations.ai** (Keyless FLUX), **Hugging Face Spaces**, or **SeaArt**       | **OpenRouter API** (`black-forest-labs/flux.2-pro`) via `generate_images.py` |
| **Keyframe Pairs**   | Manual web prompt entry with image-to-image references                           | `generate_keyframes.py` using automated `input_references`                   |
| **Video Motion**     | **Kling AI Free Tier** (daily credits), **Luma Dream Machine**, or **Hailuo AI** | **Kling AI Pro Tier** (5s / 10s start-to-end frame pairs)                    |
| **Music & Voices**   | **Suno Free Tier** (50 daily credits) + **ElevenLabs Free Tier**                 | **Suno Paid Plan** (batch stem export) + ElevenLabs                          |
| **Final Assembly**   | **FFmpeg + Python 3** (local open-source engine)                                 | **FFmpeg + Python 3** (local open-source engine)                             |

---

## 4. Directory Structure

Before assembling the final project, organize your workspace as follows:

```
flicker-project/
├── FLICKER_GENOME.yaml             # Storybook declarative specification
├── generate_images.py              # Optional OpenRouter image generator
├── generate_keyframes.py           # Optional OpenRouter keyframe generator
├── make_video.py                   # Final FFmpeg video assembly script
├── 00_Forest_Moon_Clearing.png     # Master environment background
├── characters/                     # 7 Character model reference sheets
│   ├── 01_Flicker.png
│   ├── 02_ElderFen.png
│   ├── 03_Pip.png
│   ├── 04_Ash.png
│   ├── 05_Nell.png
│   ├── 06_Sparrow.png
│   └── 07_Moonkeeper.png
├── keyframes/                      # 32 Keyframe images (01a_start.png to 09b_end.png)
├── audio/                          # 9 Soundtrack files (.wav)
│   ├── 01_LittleFlicker.wav
│   ├── ...
│   └── 09_FlickersLight.wav
├── clips/                          # 16 Kling animation renders (.mp4)
│   ├── 01a.mp4
│   ├── ...
│   └── 09b.mp4
└── fonts/                          # Free Google Fonts (TTF)
    ├── Bungee-Regular.ttf
    ├── Fredoka-SemiBold.ttf
    ├── Quicksand-Regular.ttf
    └── Caveat-Regular.ttf
```

---

## 5. Step-by-Step Production Guide

### Step 0: Environment Setup

1. Ensure [FFmpeg](https://ffmpeg.org/download.html) is installed and accessible in your system `PATH`.
2. Install Python dependencies:
   ```bash
   pip install pyyaml
   ```
3. Download the free Google Fonts into the `fonts/` directory:
   - [Bungee](https://fonts.google.com/specimen/Bungee)
   - [Fredoka](https://fonts.google.com/specimen/Fredoka)
   - [Quicksand](https://fonts.google.com/specimen/Quicksand)
   - [Caveat](https://fonts.google.com/specimen/Caveat)

---

### Step 1: Master Image References

#### Option A: Automated via OpenRouter Script

If you have an OpenRouter API key:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."

# Preview prompts and checks without spending credits:
python3 generate_images.py --dry-run

# Run full batch generation:
python3 generate_images.py

# Regenerate a single asset if needed:
python3 generate_images.py --single 02_ElderFen.png
```

#### Option B: Free Manual Route ($0)

Copy the master asset prompts directly from `FLICKER_GENOME.yaml` under `master_assets:` and paste them into [Pollinations.ai](https://pollinations.ai/) or a free Hugging Face FLUX Space. Save the outputs using the exact filenames listed in the directory structure.

---

### Step 2: Start and End Keyframe Generation

#### Option A: Automated via OpenRouter Script

The automated script feeds the master reference images into the API as `input_references` to maintain strict character visual consistency across scene transitions:

```bash
# Dry run:
python3 generate_keyframes.py --dry-run

# Run generation:
python3 generate_keyframes.py

# Retry only frames that failed or need regeneration:
python3 generate_keyframes.py --single 07b_end.png
```

#### Option B: Free Manual Route ($0)

In any free image-to-image interface:

1. Upload the corresponding character master from `characters/` as an image reference.
2. Paste the `start_prompt` and `end_prompt` from `keyframes.clips` in `FLICKER_GENOME.yaml`.
3. Save each pair into `keyframes/` as `{id}_start.png` and `{id}_end.png` (e.g., `01a_start.png`, `01a_end.png`).

---

### Step 3: Video Motion Generation (Kling AI)

1. Open **Kling AI** (free daily credits or standard tier).
2. Switch to **Start Frame / End Frame** mode.
3. Upload `{id}_start.png` into the first frame slot and `{id}_end.png` into the end frame slot.
4. Set duration to **5 seconds** (or 10 seconds).
5. Set motion mode to gentle/storybook.
6. Download the generated video and place it into `clips/{id}.mp4` (e.g., `clips/01a.mp4`). Repeat for all 16 clips.

---

### Step 4: Music & Narration (Suno & ElevenLabs)

Using the style prompts defined in `FLICKER_GENOME.yaml` under `soundtrack.songs`:

- **Sung Songs (1, 3, 5, 7, 9):** Generate in Suno using the prescribed musical styles (gentle whimsical acoustic folk, comic pizzicato, soft lullaby waltz).
- **Spoken Narration (2, 4, 6, 8):** Generate spoken audio using ElevenLabs (free tier) or Suno's spoken-with-score setting.
- Export each track as a 16-bit WAV file into `audio/` matching the manifest names (e.g., `01_LittleFlicker.wav`).

---

### Step 5: Final Video Assembly

Run the assembly engine:

```bash
python3 make_video.py
```

#### What the Assembly Engine Does Automatically:

1. **Generates Dual-Caption ASS Subtitles:** Creates `flicker_subtitles.ass` with two distinct tiers:
   - _Tier 1 (Caveat font):_ Flicker's wordless sounds (`...Mrrp?`, `Hrr-whuff.`, `Achoo!`).
   - _Tier 2 (Quicksand font):_ Felt meaning / narrative translations (`(The morning is cold and quiet.)`).
2. **Executes Dynamic Font-Morphing:** Crossfades the opening title card from blocky, strained **Bungee** into rounded, relaxed **Fredoka** over a 2-second window during key beats.
3. **Pads and Loops Video Clips:** Scales each Kling clip to 1080p, looping or padding clips to match the exact duration of each audio track.
4. **Burns Subtitles & Exports:** Concatenates all 9 segments and outputs `Flicker_The_Baby_Rainbow_Dragon_Final.mp4`.

---

## 6. Prompt Moderation Post-Mortem & Safety Rules

During development with Black Forest Labs (`flux.2-pro`) on OpenRouter, automated content filters repeatedly threw `HTTP 400 Bad Request` moderation errors. These were triggered by false positives where innocent folklore phrasing resembled child endangerment or hazard patterns.

### Critical Rules for Clean Moderation Passes:

1. **Never combine "baby" with fire tokens:** Automated safety scanners flag `"baby dragon"` + `"flame"` / `"fire"` / `"smoke"`.
   - _Blocked:_ `"Flicker the baby dragon sneezing a small flame on his snout"`
   - _Safe:_ `"Flicker the young fledgling dragon watching an enchanted hovering orb of starlight-fire above his open paws"`
2. **Keep flames off the body:** Describe magical fire as a floating, hovering, or summoned celestial orb in the air above open paws rather than burning on skin, scales, or mouth.
3. **Avoid negative prompt dumping:** Appending long negative keyword lists (e.g., `avoid: gore, weapons, violence`) often triggers keyword scanners that search for the presence of the word itself regardless of context.
4. **Neutralize physical mishaps:** Reword `"tumbles into a bush with singed fur"` to `"rests in a patch of meadow flowers with tousled ears"`.

---

## 7. Adapting the Template for Your Own Story

To create your own animated storybook musical:

1. Make a copy of `FLICKER_GENOME.yaml`:
   ```bash
   cp FLICKER_GENOME.yaml MY_STORY_GENOME.yaml
   ```
2. Modify the `meta`, `master_assets`, `keyframes`, and `soundtrack` blocks with your original characters, scene descriptions, and song titles.
3. Run the engines pointing to your new YAML file:
   ```bash
   python3 generate_images.py --config MY_STORY_GENOME.yaml
   python3 generate_keyframes.py --config MY_STORY_GENOME.yaml
   python3 make_video.py --config MY_STORY_GENOME.yaml
   ```

---

## 8. License & Attribution

This project is open source under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

```
Created by: Thomas B. Sweet (Saguna Anthroness / becoming Divine Anthro)
Publisher: Anthro Entertainment LLC
Series: AnthroHeart Ecosystem Teaching Template Series
Provenance: Bitcoin Block 968289 • Synchro 227 (Full Circle)
```

## 🔒 Cryptographic Provenance: Anchoring to Bitcoin ($0 Cost)

This storybook template includes a built-in **Bitcoin Blockchain Anchoring & Provenance Engine** (`anchor_storybook.py`).

It provides mathematically undeniable proof of creation and prior art for all your images, lyrics, music, and story scripts without spending money on legal registration, third parties, or cryptocurrency gas fees.

---

### Key Protections & Dual Licensing

1. **Self-Sovereign Identity:** The engine generates an Ed25519 cryptographic keypair (`identity.key`) on your machine. You sign your own files directly—no centralized platform needed.
2. **Built-in Dual Licensing:**
   - **MIT License:** Automatically assigned to all Python code and automation scripts.
   - **CC BY 4.0 License:** Automatically assigned to all creative assets (images, audio, videos, story text, lyrics).
3. **OpenTimestamps Integration:** File hashes are permanently rooted into the Bitcoin blockchain via free public calendar nodes.

---

### The 2-Step Creator Workflow

#### Step 1: Create Your Genesis Record

Run the script in your project root and choose **Option [1]**:

```bash
python3 anchor_storybook.py
```

- **What happens:** The script signs every asset, generates `.provenance.json` certificates, submits hashes to OpenTimestamps calendars to create `.ots` files, and records everything in `master_ledger.json`.

#### Step 2: Sync Block Height & Repush

Wait 1 to 2 hours (the time it takes for Bitcoin miners to include the calendar root into a confirmed block). Then run the script again and choose **Option [2]** (`SYNC & UPDATE README`):

```bash
python3 anchor_storybook.py
```

- **What happens:**
  1. The script verifies the proof against the live Bitcoin blockchain.
  2. It extracts the confirmed Bitcoin Block number (e.g., `Bitcoin Block 929481`).
  3. It **automatically updates both `README.md` and `FLICKER_GENOME.yaml`** with the live block number.
  4. It prints the exact Git commands to commit and repush your immutable proof to GitHub:
     ```bash
     git add .
     git commit -m "Anchor Storybook Genesis to Bitcoin Block 929481"
     git push
     ```

---

### 🌐 How Anyone Can Verify Your Work (Zero-Code Verification)

You and your audience do not need Python or terminal commands to verify that your storybook was created at that exact block. Anyone in the world can audit your proof in two independent ways:

#### 1. Drag-and-Drop Web Verification on OpenTimestamps.org

1. Go to [https://opentimestamps.org/](https://opentimestamps.org/) in any web browser.
2. Drag and drop any original file (e.g., `00_Forest_Moon_Clearing.png` or `FLICKER_GENOME.yaml`).
3. Drag and drop its matching timestamp file (e.g., `00_Forest_Moon_Clearing.png.ots`).
4. The site will check the Bitcoin blockchain directly in your browser and display the exact date, time, and confirmed Bitcoin block number—proving the file existed in that exact state on that date.

#### 2. Local Cryptographic Signature Audit

Each file includes a `<filename>.provenance.json` sidecar. This contains the SHA-256 and SHA-512 hashes, your provenance note, the timestamp, and the author's Ed25519 digital signature. This mathematically proves the files have never been altered or tampered with since the moment they were signed.

You are free to share, remix, adapt, and build upon this material for personal, educational, or commercial purposes, provided appropriate attribution is given.
