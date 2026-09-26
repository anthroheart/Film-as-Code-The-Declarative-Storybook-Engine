#!/usr/bin/env python3
"""
Generic Storybook Keyframe Generator Engine
Reads a declarative Storybook GENOME YAML file and produces start/end frames
for Kling animation using input_references for character consistency.

Usage:
    export OPENROUTER_API_KEY="sk-or-v1-..."
    python3 generate_keyframes.py
    python3 generate_keyframes.py --config MY_STORY_GENOME.yaml
    python3 generate_keyframes.py --single 07b_end.png
    python3 generate_keyframes.py --dry-run
"""

import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is required. Please install it with: pip install pyyaml")


def load_genome(path):
    if not os.path.exists(path):
        sys.exit(f"Genome configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_ref_lookup(genome):
    lookup = {}
    env = genome["master_assets"].get("environment")
    if env:
        lookup[env["id"]] = env["file"]
    for char in genome["master_assets"].get("characters", []):
        lookup[char["id"]] = char["file"]
    return lookup


def encode_image_data_url(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Reference file '{path}' does not exist. Run image generator first.")
    mime, _ = mimetypes.guess_type(path)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime or 'image/png'};base64,{data}"


def call_api(prompt, input_references, aspect_ratio, engine_cfg, api_key):
    payload = {
        "model": engine_cfg["model"],
        "prompt": prompt,
        "n": 1,
        "output_format": engine_cfg["output_format"],
        "aspect_ratio": aspect_ratio,
        "input_references": input_references,
    }
    req = urllib.request.Request(
        engine_cfg["api_url"],
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=engine_cfg.get("timeout_seconds", 120)) as resp:
        return json.loads(resp.read())


def main():
    config_file = "FLICKER_GENOME.yaml"
    if "--config" in sys.argv:
        config_file = sys.argv[sys.argv.index("--config") + 1]

    dry_run = "--dry-run" in sys.argv
    single = sys.argv[sys.argv.index("--single") + 1] if "--single" in sys.argv else None

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not dry_run and not api_key:
        sys.exit("Error: OPENROUTER_API_KEY environment variable is not set.")

    genome = load_genome(config_file)
    engine_cfg = genome["engine"]
    styling = genome["styling"]
    ref_lookup = build_ref_lookup(genome)
    key_folder = genome["keyframes"].get("folder", "keyframes")
    aspect_ratio = genome["keyframes"].get("aspect_ratio", "16:9")
    log_path = engine_cfg.get("keyframe_log", "keyframe_results.json")

    os.makedirs(key_folder, exist_ok=True)

    tasks = []
    for clip in genome["keyframes"]["clips"]:
        cid = clip["id"]
        refs = clip.get("references", [])
        start_fn = os.path.join(key_folder, f"{cid}_start.png")
        end_fn = os.path.join(key_folder, f"{cid}_end.png")
        tasks.append((start_fn, clip["start_prompt"], refs))
        tasks.append((end_fn, clip["end_prompt"], refs))

    if single:
        tasks = [t for t in tasks if os.path.basename(t[0]) == single]
        if not tasks:
            sys.exit(f"Single target '{single}' not found in clip manifest.")

    print(f"\n--- Storybook Keyframe Generator Engine ---")
    print(f"Loaded: {genome['meta']['title']}")
    print(f"Queue: {len(tasks)} frame(s)\n")

    results, total_cost = [], 0.0

    for dest, base_prompt, ref_keys in tasks:
        full_prompt = f"{base_prompt.strip()} {styling['global_guidance'].strip()}"

        if dry_run:
            print(f"[DRY RUN] {dest}")
            print(f"References: {[ref_lookup.get(k) for k in ref_keys]}")
            print(f"Prompt: {full_prompt}\n")
            continue

        if os.path.exists(dest) and not single:
            print(f"Skipping existing: {dest}")
            results.append({"file": dest, "status": "skipped"})
            continue

        print(f"Generating {dest}...")
        try:
            ref_payload = [
                {"type": "image_url", "image_url": {"url": encode_image_data_url(ref_lookup[k])}}
                for k in ref_keys if k in ref_lookup
            ]
            res = call_api(full_prompt, ref_payload, aspect_ratio, engine_cfg, api_key)
            b64_json = res["data"][0]["b64_json"]
            with open(dest, "wb") as f:
                f.write(base64.b64decode(b64_json))

            cost = float(res.get("usage", {}).get("cost", 0.0) or 0.0)
            total_cost += cost
            print(f"  Success (${cost:.4f})")
            results.append({"file": dest, "status": "success", "cost": cost})
        except Exception as e:
            print(f"  Failed: {e}")
            results.append({"file": dest, "status": "failed", "error": str(e)})

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({"total_cost_usd": round(total_cost, 4), "results": results}, f, indent=2)
        time.sleep(1)

    print(f"\nKeyframe run complete. Total Cost: ${total_cost:.4f}. Log: {log_path}")


if __name__ == "__main__":
    main()
