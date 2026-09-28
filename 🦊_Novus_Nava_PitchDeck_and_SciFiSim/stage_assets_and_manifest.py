#!/usr/bin/env python3
"""
AnthroHeart Local Asset Optimizer & Manifest/Genome Builder
ZERO API COST: Runs entirely on your local machine.
Scans 33 GB of files, extracts lore metadata, downscales artwork for PDF/pitch
presentation, and writes MANIFEST.json and GENOME.yaml.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from PIL import Image

# Supported file extensions
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aiff'}
LORE_EXTS  = {'.txt', '.md', '.rtf', '.doc', '.docx', '.json', '.pdf'}
ARCHIVE_EXTS = {'.sql', '.tar.gz', '.zip', '.tar', '.gz', '.7z'}

# Target dimensions for slide decks (Full HD / 2K max is plenty for presentation decks)
MAX_IMAGE_DIM = 1920
JPEG_QUALITY = 82

def optimize_image(src_path: Path, dest_path: Path) -> bool:
    """Downscales and compresses an image for pitch presentation use."""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(src_path) as img:
            # Convert RGBA to RGB if saving to JPEG, or keep PNG if transparency needed
            is_transparent = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

            # Resize if dimensions exceed presentation needs
            width, height = img.size
            if max(width, height) > MAX_IMAGE_DIM:
                ratio = MAX_IMAGE_DIM / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            if is_transparent:
                # Save as optimized PNG
                out_path = dest_path.with_suffix('.png')
                img.save(out_path, format="PNG", optimize=True)
            else:
                # Convert to RGB and save as lightweight JPEG
                img = img.convert('RGB')
                out_path = dest_path.with_suffix('.jpg')
                img.save(out_path, format="JPEG", quality=JPEG_QUALITY, optimize=True)

        return True
    except Exception as e:
        print(f"  [!] Skipped {src_path.name}: {e}")
        return False

def scan_and_stage(source_dir: str, stage_dir: str):
    src_root = Path(source_dir).resolve()
    stage_root = Path(stage_dir).resolve()
    stage_root.mkdir(parents=True, exist_ok=True)

    print(f"==================================================")
    print(f"[*] Scanning Source: {src_root}")
    print(f"[*] Staging Destination: {stage_root}")
    print(f"==================================================")

    manifest = {
        "project_name": "AnthroHeart",
        "creator": "Thomas B Sweet / Anthro Teacher (Cio)",
        "source_path": str(src_root),
        "staged_assets_path": str(stage_root),
        "stats": {
            "total_images_processed": 0,
            "total_audio_tracks": 0,
            "total_lore_documents": 0,
            "total_archives": 0,
            "audio_total_mb": 0.0,
        },
        "character_matches": [],
        "staged_images": [],
        "audio_inventory": [],
        "lore_inventory": []
    }

    # Core character anchors to look for in filenames
    character_anchors = ["cio", "blueheart", "white wolf", "tempter", "divine anthro",
                         "anthro angel", "magistro", "warlock", "timekeeper", "power"]

    for file_path in src_root.rglob("*"):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue

        ext = file_path.suffix.lower()
        size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)
        rel_path = file_path.relative_to(src_root)
        stem_lower = file_path.stem.lower()

        # 1. Process & Compress Images
        if ext in IMAGE_EXTS:
            dest_img = stage_root / "images" / rel_path
            success = optimize_image(file_path, dest_img)
            if success:
                staged_rel = dest_img.relative_to(stage_root)
                manifest["staged_images"].append({
                    "original_filename": file_path.name,
                    "staged_path": str(staged_rel),
                    "original_size_mb": size_mb,
                    "matched_character": next((c for c in character_anchors if c in stem_lower), None)
                })
                manifest["stats"]["total_images_processed"] += 1

        # 2. Index Audio (Cataloging without copying gigabytes of WAVs)
        elif ext in AUDIO_EXTS:
            manifest["audio_inventory"].append({
                "track_name": file_path.name,
                "format": ext.replace(".", "").upper(),
                "size_mb": size_mb,
                "relative_path": str(rel_path)
            })
            manifest["stats"]["total_audio_tracks"] += 1
            manifest["stats"]["audio_total_mb"] = round(manifest["stats"]["audio_total_mb"] + size_mb, 2)

        # 3. Index Lore & Text
        elif ext in LORE_EXTS:
            sample_text = ""
            if ext in {'.txt', '.md'}:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        sample_text = f.read(400).replace("\n", " ").strip()
                except Exception:
                    pass

            manifest["lore_inventory"].append({
                "document_name": file_path.name,
                "size_mb": size_mb,
                "relative_path": str(rel_path),
                "preview": sample_text
            })
            manifest["stats"]["total_lore_documents"] += 1

        # 4. Archives & Databases
        elif ext in ARCHIVE_EXTS:
            manifest["stats"]["total_archives"] += 1

    # Save MANIFEST.json
    manifest_path = Path("MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[✓] Saved complete inventory to {manifest_path.resolve()}")

    # -------------------------------------------------------------
    # Build Compact GENOME.yaml (The IP DNA used for low-cost AI prompts)
    # -------------------------------------------------------------
    genome = {
        "genome_version": "1.0",
        "ip_name": "AnthroHeart",
        "creator": "Thomas B Sweet (Anthro Teacher / Cio)",
        "cosmic_parameters": {
            "galaxies": "2.2 Trillion",
            "dimensions": "14 Trillion",
            "anthro_population": "Over 10^59 beings",
            "core_law": "Love as fundamental universal fabric (Bhakti Devotion)",
            "key_metaphysics": [
                "Octave Mirror (Reflects true inner self and enables radical redemption)",
                "Divine Matter (Immortal essence inherent in all living consciousness)",
                "The Completion Field (Awakened sovereignty beyond transactional existence)"
            ]
        },
        "core_characters": [
            {"name": "Divine Anthro", "level": "Infinite", "role": "The Infinite Creator in golden anthro form at rest"},
            {"name": "Cio (The Heartweaver)", "level": "65/100", "role": "Human soul whose 24-year quest transforms into a blue anthro fox"},
            {"name": "Anthro Angel", "level": "96/100", "role": "Cio's True Self; architect of universes whose love allows Creator to rest"},
            {"name": "BlueHeart", "level": "86/100", "role": "Golden fox, primary lover, and emotional anchor of AnthroHeart"},
            {"name": "White Wolf Lover", "level": "91/100", "role": "Being of radiant joy, higher density unconditional love"},
            {"name": "Master Tempter", "level": "61/100", "role": "Being redeemed through Octave Mirror; avatar of radical forgiveness"},
            {"name": "Magistro & Warlock", "role": "The foundational hero's journey of magic, Kablu, and true names"}
        ],
        "existing_assets_summary": {
            "total_images_ready": manifest["stats"]["total_images_processed"],
            "audio_tracks_mastered": manifest["stats"]["total_audio_tracks"],
            "audio_total_megabytes": manifest["stats"]["audio_total_mb"],
            "written_works": [
                "The Warlock Name (Novel)",
                "Cio's AnthroHeart Saga (Novel)",
                "Cio Psalms (149-page Poetry Book)"
            ],
            "interactive_technology": [
                "Intention Repeater (Open-source mindfulness and spiritual tech)",
                "Full WordPress Community Hub and Database (.sql / .tar.gz)"
            ]
        },
        "franchise_pillars": [
            "Animated Feature Film Trilogy (Epic scale of Lion King, depth of Soul)",
            "Disney+ Episodic Series (Deep dives into the 14 trillion dimensions)",
            "Music Soundtracks (Devotional & emotional resonance like Frozen/Moana)",
            "Theme Park Presence & Consumer Products (Plush anthros, Octave Mirror, Intention toys)"
        ]
    }

    genome_path = Path("GENOME.yaml")
    with open(genome_path, "w", encoding="utf-8") as f:
        yaml.dump(genome, f, sort_keys=False, default_flow_style=False)
    print(f"[✓] Saved high-density IP DNA to {genome_path.resolve()}")
    print("\nSummary:")
    print(f" - Compressed Images: {manifest['stats']['total_images_processed']}")
    print(f" - Audio Tracks Cataloged: {manifest['stats']['total_audio_tracks']} ({manifest['stats']['audio_total_mb']} MB)")
    print(f" - Documents Cataloged: {manifest['stats']['total_lore_documents']}")
    print(f" - Cost of this scanning process: $0.00")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scan 33 GB folder and create Manifest & Genome (No AI / $0 Cost)")
    parser.add_argument("--source", default="./", help="Path to your 33 GB AnthroHeart assets folder")
    parser.add_argument("--dest", default="./anthroheart_deck_assets", help="Where to save compressed images for presentation")
    args = parser.parse_args()

    scan_and_stage(args.source, args.dest)
