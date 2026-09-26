#!/usr/bin/env python3
"""
Generic Storybook Image Generator Engine
Reads a declarative Storybook GENOME YAML file and generates master images.

Usage:
    export OPENROUTER_API_KEY="sk-or-v1-..."
    python3 generate_images.py
    python3 generate_images.py --config MY_STORY_GENOME.yaml
    python3 generate_images.py --single 01_Flicker.png
    python3 generate_images.py --dry-run
"""

import base64
import json
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


def build_prompt(base_prompt, is_anthro, styling):
    parts = [base_prompt.strip(), styling["global_guidance"].strip()]
    if is_anthro and "anthro_clause" in styling:
        parts.append(styling["anthro_clause"].strip())
    return " ".join(parts)


def call_image_api(prompt, aspect_ratio, engine_cfg, api_key):
    payload = {
        "model": engine_cfg["model"],
        "prompt": prompt,
        "n": 1,
        "output_format": engine_cfg["output_format"],
        "aspect_ratio": aspect_ratio,
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


def execute_with_retries(prompt, aspect_ratio, engine_cfg, api_key):
    max_retries = engine_cfg.get("max_retries", 4)
    delay = engine_cfg.get("retry_backoff_seconds", 3)
    for attempt in range(1, max_retries + 1):
        try:
            return call_image_api(prompt, aspect_ratio, engine_cfg, api_key)
        except urllib.error.HTTPError as err:
            err_msg = err.read().decode("utf-8", errors="replace")
            print(f"  [Attempt {attempt}] HTTP {err.code}: {err_msg}")
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except urllib.error.URLError as err:
            print(f"  [Attempt {attempt}] Network error: {err}")
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("Max retries exceeded.")


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
    log_path = engine_cfg.get("manifest_log", "manifest_results.json")

    # Collect tasks from master_assets
    tasks = []
    env = genome["master_assets"].get("environment")
    if env:
        tasks.append((env["file"], env["aspect_ratio"], env["prompt"], env.get("is_anthro", False)))

    for char in genome["master_assets"].get("characters", []):
        tasks.append((char["file"], char["aspect_ratio"], char["prompt"], char.get("is_anthro", True)))

    if single:
        tasks = [t for t in tasks if os.path.basename(t[0]) == single]
        if not tasks:
            sys.exit(f"Target '{single}' not found in master assets.")

    print(f"\n--- Storybook Image Generator Engine ---")
    print(f"Loaded: {genome['meta']['title']} ({config_file})")
    print(f"Model: {engine_cfg['model']}")
    print(f"Queue: {len(tasks)} image(s)\n")

    results, total_cost = [], 0.0

    for dest, aspect, raw_prompt, is_anthro in tasks:
        full_prompt = build_prompt(raw_prompt, is_anthro, styling)
        if dry_run:
            print(f"[DRY RUN] {dest} (Aspect: {aspect}, Anthro: {is_anthro})")
            print(f"Prompt: {full_prompt}\n")
            continue

        if os.path.exists(dest) and not single:
            print(f"Skipping existing: {dest}")
            results.append({"file": dest, "status": "skipped"})
            continue

        print(f"Generating {dest}...")
        try:
            res = execute_with_retries(full_prompt, aspect, engine_cfg, api_key)
            b64_json = res["data"][0]["b64_json"]
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
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

    print(f"\nFinished. Total Cost: ${total_cost:.4f}. Log: {log_path}")


if __name__ == "__main__":
    main()
