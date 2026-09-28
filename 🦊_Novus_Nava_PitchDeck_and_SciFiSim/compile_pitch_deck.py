#!/usr/bin/env python3
"""
===============================================================================
   ANTHROHEART PITCH DECK COMPILER (Self-Contained Base64 Image Edition)
   Consumes GENOME.yaml and MANIFEST.json to compile Disney-quality decks.
   Features Smart Image Discovery & Base64 Inlining (Images Never Break).
===============================================================================
"""

import os
import sys
import json
import yaml
import base64
import argparse
from pathlib import Path
from openai import OpenAI

ANGLES = [
    {
        "id": 1,
        "name": "Executive Studio & Franchise Vision",
        "tagline": "The Next Multibillion-Dollar Evergreen Franchise (Frozen meets Avatar meets Zootopia)",
        "focus": "High-level studio executives, theatrical trilogy roadmap, commercial potential, and universal emotional resonance."
    },
    {
        "id": 2,
        "name": "Cosmic Mythos & Deep Metaphysics",
        "tagline": "A Realm Where Love is the Fundamental Law (14 Trillion Dimensions)",
        "focus": "Worldbuilding lore, 2.2 trillion galaxies, the Octave Mirror, Divine Matter, and the Infinite Creator in repose."
    },
    {
        "id": 3,
        "name": "Transmedia Ecosystem, Parks & Soundtracks",
        "tagline": "147 Studio Masters, Disney+ Series, Theme Park Lands & Intention Tech",
        "focus": "Synergy across Disney Consumer Products, Imagineering theme park presence, 85+ original songs, and the Intention Repeater app."
    },
    {
        "id": 4,
        "name": "Radical Forgiveness, Redemption & Sovereign Co-Creation",
        "tagline": "The Completion Field, the Master Tempter Arc, and a Gift of Trust",
        "focus": "Cio's 24-year quest, transformation into the Blue Fox Heartweaver, radical redemption through the Octave Mirror, and granting permanent royalty-free rights to Disney."
    }
]

def load_genome_and_manifest():
    if not os.path.exists("GENOME.yaml"):
        sys.exit("[!] Error: GENOME.yaml not found. Please run stage_assets_and_manifest.py first.")
    if not os.path.exists("MANIFEST.json"):
        sys.exit("[!] Error: MANIFEST.json not found. Please run stage_assets_and_manifest.py first.")

    with open("GENOME.yaml", "r", encoding="utf-8") as f:
        genome = yaml.safe_load(f)
    with open("MANIFEST.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return genome, manifest

def find_image_file(raw_path: str) -> Path:
    """Smart image locator: searches all staging and root folders."""
    if not raw_path:
        return None

    filename = Path(raw_path).name
    candidates = [
        Path(raw_path),
        Path("anthroheart_deck_assets") / raw_path,
        Path("anthroheart_deck_assets") / "images" / raw_path,
        Path("anthroheart_deck_assets") / "images" / filename,
        Path("anthroheart_deck_assets") / filename,
        Path("images") / filename,
        Path(filename)
    ]

    for c in candidates:
        if c.is_file():
            return c.resolve()

    # Deep recursive search in staging folder as fallback
    stage_dir = Path("anthroheart_deck_assets")
    if stage_dir.exists():
        for matched in stage_dir.rglob(filename):
            if matched.is_file():
                return matched.resolve()

    return None

def image_to_base64_src(img_path: Path) -> str:
    """Encodes image to base64 Data URI so it can NEVER fail to load."""
    ext = img_path.suffix.lower().replace(".", "")
    mime = "image/png" if ext == "png" else "image/jpeg"
    with open(img_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{data}"

def generate_deck_json(client: OpenAI, genome: dict, image_list: list, pages: int, angle_info: dict, model="gpt-4o-mini"):
    system_prompt = (
        "You are an elite Senior Creative Executive packaging high-concept Disney pitch decks. "
        "Transform the provided IP GENOME into a persuasive, emotionally resonant, executive-ready presentation. "
        "Strictly output valid JSON matching the requested slide schema."
    )

    user_prompt = f"""
Target Slide Count: {pages}
Edition: Version {angle_info['id']} - {angle_info['name']}
Core Angle / Hook: {angle_info['tagline']}
Strategic Focus: {angle_info['focus']}

IP GENOME DATA:
{yaml.dump(genome)}

AVAILABLE STAGED IMAGES (Pick filenames from this list for "image_path"):
{json.dumps(image_list[:50], indent=2)}

Output JSON Schema:
{{
  "deck_title": "AnthroHeart: A Disney Pitch Deck",
  "version_number": {angle_info['id']},
  "version_name": "{angle_info['name']}",
  "version_tagline": "{angle_info['tagline']}",
  "slides": [
    {{
      "page_number": 1,
      "eyebrow": "CATEGORY HEADER",
      "title": "Compelling Theatrical Slide Title",
      "subtitle": "Poetic, punchy executive subtitle",
      "body_paragraphs": ["Persuasive paragraph elaborating on the core narrative or business case."],
      "bullet_points": ["Strategic takeaway 1", "Strategic takeaway 2", "Strategic takeaway 3"],
      "stat_callout": {{"value": "14 Trillion", "label": "Dimensions"}},
      "image_path": "filename_from_list.jpg"
    }}
  ]
}}
Generate exactly {pages} complete, beautifully written slides for this angle.
"""

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    return json.loads(resp.choices[0].message.content)

def render_html_deck(deck_data: dict, output_filename: str, fallback_images: list):
    slides_html = []

    for idx, slide in enumerate(deck_data.get("slides", [])):
        img_tag = ""
        has_img = False
        img_path = find_image_file(slide.get("image_path"))

        # If model picked a missing image, gracefully cycle to an available staged image
        if not img_path and fallback_images:
            fallback_choice = fallback_images[idx % len(fallback_images)]
            img_path = find_image_file(fallback_choice)

        if img_path and img_path.exists():
            b64_src = image_to_base64_src(img_path)
            img_tag = f'<div class="img-box"><img src="{b64_src}" alt="Slide Visual"></div>'
            has_img = True

        bullets = "".join(f"<li>{bp}</li>" for bp in slide.get("bullet_points", []))
        paras = "".join(f"<p>{p}</p>" for p in slide.get("body_paragraphs", []))

        stat_box = ""
        if slide.get("stat_callout"):
            stat_box = f"""
            <div class="stat-pill">
                <span class="stat-val">{slide['stat_callout'].get('value', '')}</span>
                <span class="stat-lbl">{slide['stat_callout'].get('label', '')}</span>
            </div>
            """

        slide_markup = f"""
        <div class="slide">
            <div class="ambient-glow"></div>
            <div class="header">
                <div class="eyebrow">{slide.get('eyebrow', 'ANTHROHEART')}</div>
                <h1 class="title">{slide.get('title', '')}</h1>
                <div class="subtitle">{slide.get('subtitle', '')}</div>
            </div>
            <div class="grid {'has-img' if has_img else 'full'}">
                <div class="text-content">
                    {paras}
                    {f'<ul class="bullets">{bullets}</ul>' if bullets else ''}
                    {stat_box}
                </div>
                {img_tag}
            </div>
            <div class="footer">
                <span>AnthroHeart IP | Walt Disney Internal Pitch Deck</span>
                <span>Edition {deck_data.get('version_number', 1)}: {deck_data.get('version_name', '')}</span>
                <span>Page {slide.get('page_number', idx + 1)}</span>
            </div>
        </div>
        """
        slides_html.append(slide_markup)

    html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{deck_data.get('deck_title', 'AnthroHeart')} - Version {deck_data.get('version_number', 1)}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&family=Cinzel:wght@600;800;900&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #07080c; color: #f0f3fa; font-family: 'Plus Jakarta Sans', sans-serif; }}
    @page {{ size: 1920px 1080px; margin: 0; }}
    @media print {{ .slide {{ page-break-after: always; height: 1080px !important; width: 1920px !important; }} }}
    .slide {{
        width: 1920px; height: 1080px; position: relative;
        background: radial-gradient(circle at 85% 15%, #181d33 0%, #08090f 75%);
        padding: 70px 90px; display: flex; flex-direction: column; justify-content: space-between;
        page-break-after: always; overflow: hidden; border-bottom: 2px solid #121422;
    }}
    .ambient-glow {{
        position: absolute; width: 500px; height: 500px; border-radius: 50%;
        background: radial-gradient(circle, rgba(155, 81, 224, 0.12) 0%, rgba(0,0,0,0) 70%);
        top: -100px; right: -100px; pointer-events: none;
    }}
    .eyebrow {{ font-family: 'Cinzel', serif; font-size: 15px; letter-spacing: 4px; color: #e5b95f; text-transform: uppercase; margin-bottom: 6px; }}
    .title {{ font-size: 46px; font-weight: 800; line-height: 1.15; background: linear-gradient(135deg, #fff 40%, #00d2ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ font-size: 21px; color: #94a3b8; margin-top: 6px; font-weight: 400; }}
    .grid {{ display: grid; gap: 50px; align-items: center; margin: auto 0; }}
    .grid.has-img {{ grid-template-columns: 1.2fr 0.8fr; }}
    .grid.full {{ grid-template-columns: 1fr; }}
    .text-content p {{ font-size: 20px; line-height: 1.6; color: #d6deeb; margin-bottom: 16px; }}
    .bullets {{ list-style: none; display: flex; flex-direction: column; gap: 12px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 22px; border-radius: 12px; backdrop-filter: blur(8px); }}
    .bullets li {{ font-size: 18px; color: #cbd5e1; }}
    .bullets li::before {{ content: "✦ "; color: #e5b95f; }}
    .stat-pill {{ display: inline-flex; flex-direction: column; background: rgba(229,185,95,0.08); border: 1px solid rgba(229,185,95,0.3); padding: 12px 20px; border-radius: 10px; margin-top: 14px; }}
    .stat-val {{ font-size: 30px; font-weight: 800; color: #e5b95f; }}
    .stat-lbl {{ font-size: 12px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; }}
    .img-box {{ height: 480px; border-radius: 16px; overflow: hidden; border: 1px solid rgba(229,185,95,0.3); box-shadow: 0 20px 50px rgba(0,0,0,0.8); background: #0c0d14; }}
    .img-box img {{ width: 100%; height: 100%; object-fit: cover; }}
    .footer {{ display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 14px; font-size: 13px; color: #5d677d; letter-spacing: 2px; text-transform: uppercase; }}
</style>
</head>
<body>
{"".join(slides_html)}
</body>
</html>
"""
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_document)
    print(f"[✓] Rendered: {output_filename} (Images embedded directly in HTML)")

def main():
    parser = argparse.ArgumentParser(description="AnthroHeart Disney Pitch Deck Compiler")
    parser.add_argument("--pages", type=int, default=14, help="Slides per deck (e.g. 10, 14, 20)")
    parser.add_argument("--versions", type=int, default=4, help="Total versions (1 to 4)")
    parser.add_argument("--target-version", type=int, default=None, choices=[1, 2, 3, 4], help="Compile ONLY a specific version (e.g. 4)")
    parser.add_argument("--re-render-only", action="store_true", help="Re-render HTML from existing JSON without spending API credits")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI Model")
    args = parser.parse_args()

    genome, manifest = load_genome_and_manifest()

    # Gather all available staged image paths
    raw_images = [img["staged_path"] for img in manifest.get("staged_images", [])]
    valid_images = [img for img in raw_images if find_image_file(img) is not None]

    if not valid_images:
        # Fallback: scan disk directly if manifest paths were offset
        stage_dir = Path("anthroheart_deck_assets")
        if stage_dir.exists():
            for p in stage_dir.rglob("*"):
                if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    valid_images.append(str(p))

    print(f"[*] Discovered {len(valid_images)} verified local image assets.")

    if args.target_version is not None:
        targets = [a for a in ANGLES if a["id"] == args.target_version]
    else:
        targets = ANGLES[:min(args.versions, len(ANGLES))]

    for angle_info in targets:
        v_num = angle_info["id"]
        json_file = f"anthroheart_deck_v{v_num}.json"
        html_file = f"anthroheart_deck_v{v_num}.html"

        print("\n" + "=" * 70)
        print(f"🎬 Processing Version {v_num}: {angle_info['name']}")
        print("=" * 70)

        # FAST RE-RENDER MODE: Uses your already generated JSON (0 API cost)
        if args.re_render_only and os.path.exists(json_file):
            print(f"[*] Re-rendering HTML from existing {json_file} (Free / 0 API credits)...")
            with open(json_file, "r", encoding="utf-8") as f:
                deck_json = json.load(f)
        else:
            client = OpenAI()
            deck_json = generate_deck_json(client, genome, valid_images, pages=args.pages, angle_info=angle_info, model=args.model)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(deck_json, f, indent=2)

        render_html_deck(deck_json, html_file, valid_images)

    print("\n[✓] Done! All decks updated with embedded images.")

if __name__ == "__main__":
    main()
