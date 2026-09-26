#!/usr/bin/env python3
"""
===============================================================================
   ⚓ STORYBOOK BITCOIN GENESIS & PROVENANCE ENGINE (v4.6 - Creator Edition)
   -----------------------------------------------------------------------
   Recursive Blockchain Provenance with Interactive Branding & Sync.

   Licensing Model:
     • Python Automation Scripts: MIT License
     • Creative Assets (Images, Audio, Video, Story, Lyrics): CC BY 4.0

   Author: Fully Configurable via Interactive CLI and Declarative YAML
===============================================================================
"""

import os
import sys
import json
import hashlib
import subprocess
import shutil
import re
import zipfile
import urllib.request
from datetime import datetime, timezone

# --- TERMINAL COLORS ---
C_RESET  = "\033[0m"
C_CYAN   = "\033[1;36m"
C_GREEN  = "\033[1;32m"
C_YELLOW = "\033[1;33m"
C_RED    = "\033[1;31m"
C_BOLD   = "\033[1m"
C_GREY   = "\033[90m"

# --- CONFIGURATION ---
IDENTITY_FILENAME = "identity.key"
MASTER_LEDGER = "master_ledger.json"
LOCAL_LEDGER_NAME = "folder_ledger.json"
GENOME_FILE = "FLICKER_GENOME.yaml"
README_FILE = "README.md"
DEFAULT_BUNDLE_NAME = "storybook_bundle.zip"

OTS_EXEC = shutil.which("ots") or os.path.expanduser("~/.local/bin/ots")

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".vscode", "build", "dist"}
EXCLUDED_EXTS = (
    ".ots", ".provenance.json", ".key", ".tmp", ".log",
    ".cache", "master_ledger.json", "folder_ledger.json",
    "manifest_results.json", "keyframe_results.json"
)

# --- DEPENDENCY CHECKS ---
try:
    from nacl.signing import SigningKey
    from nacl.encoding import HexEncoder
except ImportError:
    sys.exit(
        f"\n{C_RED}Missing required crypto library: PyNaCl{C_RESET}\n"
        f"Install it with: {C_BOLD}pip install pynacl opentimestamps-client pyyaml{C_RESET}\n"
    )

try:
    import yaml
except ImportError:
    yaml = None


# ==============================================================================
#  BRANDING & METADATA RESOLUTION
# ==============================================================================

def detect_genome_metadata(genome_path=GENOME_FILE):
    """Inspects genome YAML if available to provide intelligent defaults."""
    detected_owner  = "My Creative Studio"
    detected_author = "Story Creator"
    detected_title  = "Storybook Project"

    if yaml and os.path.exists(genome_path):
        try:
            with open(genome_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                meta = data.get("meta", {})
                detected_owner  = meta.get("owner", detected_owner)
                detected_author = meta.get("author", detected_author)
                detected_title  = meta.get("title", detected_title)
        except Exception:
            pass

    return detected_owner, detected_author, detected_title

def configure_creator_identity(genome_path=GENOME_FILE):
    """Prompts creator to confirm or customize their identity and branding."""
    def_owner, def_author, project_title = detect_genome_metadata(genome_path)

    print(f"\n{C_BOLD}🎨 CREATOR IDENTITY & COPYRIGHT BRANDING:{C_RESET}")
    print(f"{C_GREY}   (Press Enter to accept default, or type your own custom studio/name){C_RESET}")

    owner_input = input(f"   🏢 Studio / Publisher Entity [{C_CYAN}{def_owner}{C_RESET}]: ").strip()
    signer_name = owner_input if owner_input else def_owner

    author_input = input(f"   ✍️  Author / Lead Creator Name [{C_CYAN}{def_author}{C_RESET}]: ").strip()
    author_name = author_input if author_input else def_author

    return signer_name, author_name, project_title


# ==============================================================================
#  UTILITIES & CHAIN QUERIES
# ==============================================================================

def get_current_block_height():
    """Fetches live Bitcoin tip from public block explorer without extra packages."""
    try:
        req = urllib.request.Request(
            "https://blockstream.info/api/blocks/tip/height",
            headers={"User-Agent": "StorybookAnchor/4.6"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            return int(resp.read().decode().strip())
    except Exception:
        return None

def get_hashes(filepath):
    """Calculates both SHA-256 and SHA-512 in a single streaming pass."""
    sha256, sha512 = hashlib.sha256(), hashlib.sha512()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            sha256.update(chunk)
            sha512.update(chunk)
    return sha256.hexdigest(), sha512.hexdigest()

def extract_block_height(output):
    """Parses OpenTimestamps output for confirmed Bitcoin block numbers."""
    patterns = [
        r"BitcoinBlockHeaderAttestation\((\d+)\)",
        r"Bitcoin block\s+(\d+)",
        r"block\s+(\d+)"
    ]
    heights = set()
    for pattern in patterns:
        for match in re.findall(pattern, output, re.IGNORECASE):
            try:
                heights.add(int(match))
            except ValueError:
                pass
    if heights:
        return sorted(heights)
    return []

def determine_license(filepath):
    """Applies MIT for code, and CC BY 4.0 for all creative story assets."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in [".py", ".sh", ".bash"]:
        return "MIT License (Open Source Software)"
    return "Creative Commons Attribution 4.0 International (CC BY 4.0)"


# ==============================================================================
#  ARCHIVE BUNDLER
# ==============================================================================

def create_bundle_zip(root_dir, output_zip=DEFAULT_BUNDLE_NAME):
    """Packages all project assets into a clean deterministic ZIP file."""
    print(f"\n📦 {C_CYAN}Compressing project assets into archive:{C_RESET} {output_zip}...")
    targets = discover_targets(root_dir)

    targets = [t for t in targets if os.path.basename(t) != output_zip]

    zip_path = os.path.join(root_dir, output_zip)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in targets:
            full_path = os.path.join(root_dir, rel_path)
            zf.write(full_path, arcname=rel_path)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"   {C_GREEN}✔ Archive created:{C_RESET} {output_zip} ({size_mb:.2f} MB, {len(targets)} files bundled)")
    return output_zip


# ==============================================================================
#  AUTOMATED DOCUMENTATION SYNCHRONIZERS
# ==============================================================================

def update_readme_block_height(block_height, readme_path=README_FILE):
    """Updates the Bitcoin Block number in README.md."""
    if not os.path.exists(readme_path):
        return

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        def replace_block(match):
            prefix = match.group(1)
            suffix = match.group(2) if match.group(2) else ""
            return f"{prefix}{block_height}{suffix}"

        pattern = r"(Provenance:\s*Bitcoin Block\s+)[0-9A-Za-z_-]+(\s*\|.*|\s*•.*)?$"
        new_content, count = re.subn(pattern, replace_block, content, flags=re.MULTILINE)

        if count > 0:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"   📄 {C_GREEN}Updated {readme_path}:{C_RESET} Bitcoin Block {block_height}")
        else:
            print(f"   ℹ️  {C_GREY}No existing 'Provenance: Bitcoin Block' pattern found in {readme_path}{C_RESET}")
    except Exception as e:
        print(f"   ⚠️  {C_YELLOW}Could not update {readme_path}: {e}{C_RESET}")

def update_genome_blockchain_anchor(block_height, genome_path=GENOME_FILE):
    """Updates the blockchain_anchor in the Storybook YAML file."""
    if not os.path.exists(genome_path):
        return

    try:
        with open(genome_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_anchor = f'blockchain_anchor: "Bitcoin Block {block_height}"'
        new_content = re.sub(r'blockchain_anchor:\s*"?[^"\n]+"?', new_anchor, content)

        with open(genome_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"   🧬 {C_GREEN}Updated {genome_path}:{C_RESET} Bitcoin Block {block_height}")
    except Exception as e:
        print(f"   ⚠️  {C_YELLOW}Could not update {genome_path}: {e}{C_RESET}")

def update_ledgers(filepath, h256, note, signer, block=None, root_dir="."):
    """Updates local folder and root master ledgers."""
    folder = os.path.dirname(filepath) or "."
    fname = os.path.basename(filepath)
    lic = determine_license(filepath)

    # 1. Update Folder Ledger
    local_path = os.path.join(folder, LOCAL_LEDGER_NAME)
    local_data = []
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except Exception:
            local_data = []

    found = False
    for r in local_data:
        if r.get("filename") == fname:
            if block:
                r["bitcoin_block"] = block
            found = True
            break
    if not found:
        local_data.append({
            "filename": fname,
            "path": filepath,
            "signer": signer,
            "license": lic,
            "sha256": h256,
            "note": note,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bitcoin_block": block
        })
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(local_data, f, indent=2)

    # 2. Update Master Root Ledger
    master_path = os.path.join(root_dir, MASTER_LEDGER)
    master_data = {}
    if os.path.exists(master_path):
        try:
            with open(master_path, "r", encoding="utf-8") as f:
                master_data = json.load(f)
        except Exception:
            master_data = {}

    if h256 not in master_data:
        master_data[h256] = {
            "filename": fname,
            "path": filepath,
            "signer": signer,
            "license": lic,
            "sha256": h256,
            "note": note,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bitcoin_block": block
        }
    elif block:
        master_data[h256]["bitcoin_block"] = block

    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master_data, f, indent=2)


# ==============================================================================
#  CORE PROCESSOR: GENESIS STAMP & VERIFY
# ==============================================================================

def stamp_genesis_file(filepath, sk, root_dir, batch_note, current_tip, signer_name):
    """Creates cryptographic Ed25519 signature manifest and submits Bitcoin OTS stamp."""
    ots_path = filepath + ".ots"
    h256, h512 = get_hashes(filepath)
    lic = determine_license(filepath)

    print(f"   ⚓ {C_YELLOW}Creating Genesis Record:{C_RESET} {filepath}")

    # 1. Create Ed25519 Signed Provenance Sidecar (.provenance.json)
    payload = f"{h512}|{batch_note}|{lic}|{signer_name}"
    signature = sk.sign(payload.encode()).signature.hex()
    manifest = {
        "target": filepath,
        "signer": signer_name,
        "license": lic,
        "sha256": h256,
        "sha512": h512,
        "provenance_note": batch_note,
        "ed25519_signature": signature,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "bitcoin_tip_at_creation": current_tip,
        "status": "Genesis Record Created (Pending Confirmation)"
    }
    with open(filepath + ".provenance.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2. Bitcoin OpenTimestamps Stamp
    if OTS_EXEC and os.path.exists(OTS_EXEC):
        if os.path.exists(ots_path):
            print(f"      {C_YELLOW}⚠️ '{ots_path}' already exists. Skipping stamp step.{C_RESET}")
            update_ledgers(filepath, h256, batch_note, signer_name, root_dir=root_dir)
            return

        try:
            result = subprocess.run(
                [OTS_EXEC, "stamp", filepath],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                update_ledgers(filepath, h256, batch_note, signer_name, root_dir=root_dir)
                print(f"      {C_GREEN}✅ Stamped via OpenTimestamps (Calendar proof pending){C_RESET}")
            elif os.path.exists(ots_path):
                update_ledgers(filepath, h256, batch_note, signer_name, root_dir=root_dir)
                print(f"      {C_GREEN}✅ OTS proof created: {ots_path}{C_RESET}")
            else:
                print(f"      {C_RED}❌ OTS failed for {filepath}{C_RESET}")
                err_msg = (result.stderr or result.stdout or "Unknown error").strip()
                print(f"         {C_GREY}{err_msg}{C_RESET}")
        except Exception as e:
            print(f"      {C_RED}❌ OTS Stamp failed: {e}{C_RESET}")
    else:
        print(f"      {C_YELLOW}⚠️ OpenTimestamps binary ('ots') not found. Signed manifest only.{C_RESET}")
        update_ledgers(filepath, h256, batch_note, signer_name, root_dir=root_dir)

def sync_and_verify_file(filepath, signer_name, root_dir):
    """Upgrades and verifies OTS proof against Bitcoin blockchain."""
    ots_path = filepath + ".ots"

    if not os.path.exists(ots_path):
        return []

    h256, _ = get_hashes(filepath)
    print(f"   🔍 {C_CYAN}Syncing Proof:{C_RESET} {filepath}")

    if not OTS_EXEC or not os.path.exists(OTS_EXEC):
        print(f"      {C_RED}❌ OpenTimestamps binary not found.{C_RESET}")
        return []

    subprocess.run([OTS_EXEC, "upgrade", ots_path], capture_output=True, text=True)
    info_res = subprocess.run([OTS_EXEC, "info", ots_path], capture_output=True, text=True)
    verify_res = subprocess.run([OTS_EXEC, "verify", ots_path], capture_output=True, text=True)

    combined_output = (info_res.stdout or "") + "\n" + (verify_res.stdout or "")
    blocks = extract_block_height(combined_output)

    if blocks:
        canonical_block = str(min(blocks))
        all_blocks_str = ", ".join(f"Block {b}" for b in blocks)

        print(f"      {C_GREEN}🎉 Bitcoin attestation detected!{C_RESET}")
        print(f"      ⛓️  All Confirmations: {C_GREY}{all_blocks_str}{C_RESET}")
        print(f"      ⚓ {C_BOLD}Canonical Anchor:   Bitcoin Block {canonical_block}{C_RESET}")

        update_ledgers(
            filepath,
            h256,
            "Bitcoin Confirmed Asset",
            signer_name,
            block=canonical_block,
            root_dir=root_dir
        )

        master_path = os.path.join(root_dir, MASTER_LEDGER)
        if os.path.exists(master_path):
            try:
                with open(master_path, "r", encoding="utf-8") as f:
                    master_data = json.load(f)
                if h256 in master_data:
                    master_data[h256]["bitcoin_block"] = canonical_block
                    master_data[h256]["bitcoin_blocks"] = blocks
                    with open(master_path, "w", encoding="utf-8") as f:
                        json.dump(master_data, f, indent=2)
            except Exception as e:
                print(f"      {C_YELLOW}⚠️ Could not record block list: {e}{C_RESET}")

        return blocks

    print(f"      {C_YELLOW}⏳ Still awaiting Bitcoin attestation.{C_RESET}")
    update_ledgers(filepath, h256, "Pending Confirmation", signer_name, root_dir=root_dir)
    return []


# ==============================================================================
#  COLLECT TARGETS
# ==============================================================================

def discover_targets(root_dir):
    """Recursively walks directories collecting creative assets & code."""
    targets = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(EXCLUDED_EXTS) or f.startswith("."):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, root_dir)
            targets.append(rel_path)
    return sorted(targets)

def discover_all_ots_targets(root_dir):
    """Finds all files that have a companion .ots file to verify."""
    targets = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".ots"):
                base_file = f[:-4]
                full_base_path = os.path.join(root, base_file)
                if os.path.exists(full_base_path):
                    targets.append(os.path.relpath(full_base_path, root_dir))
    return sorted(targets)


# ==============================================================================
#  MAIN ENTRYPOINT
# ==============================================================================

def main():
    root_dir = os.getcwd()

    print(f"\n{C_BOLD}⚓ STORYBOOK BITCOIN GENESIS & PROVENANCE ENGINE (v4.6){C_RESET}")
    print(f"{C_GREY}Dual License: MIT (Code) / CC BY 4.0 (Story/Art){C_RESET}")

    # Prompt creator to pick their exact publisher/author identity
    signer_name, author_name, project_title = configure_creator_identity()

    print(f"\n📌 Project Scope: {C_CYAN}{project_title}{C_RESET}")
    print(f"🏢 Publisher:    {C_GREEN}{signer_name}{C_RESET}")
    print(f"✍️  Author:       {C_GREEN}{author_name}{C_RESET}\n")

    current_tip = get_current_block_height()
    if current_tip:
        print(f"⛓️  Live Bitcoin Chain Tip: {C_CYAN}Block {current_tip}{C_RESET}")
    else:
        print(f"{C_YELLOW}⚠️  Live Bitcoin network unreachable (offline or filtered). Proceeding in local mode.{C_RESET}")

    if os.path.exists(IDENTITY_FILENAME):
        with open(IDENTITY_FILENAME, "r", encoding="utf-8") as f:
            sk = SigningKey(f.read().strip(), encoder=HexEncoder)
        print(f"🔑 Author Identity Key: {C_GREEN}{IDENTITY_FILENAME} (Loaded){C_RESET}")
    else:
        sk = SigningKey.generate()
        with open(IDENTITY_FILENAME, "w", encoding="utf-8") as f:
            f.write(sk.encode(encoder=HexEncoder).decode())
        print(f"🔑 Author Identity Key: {C_YELLOW}{IDENTITY_FILENAME} (Generated new self-sovereign keypair){C_RESET}")

    print("\n" + "-"*75)
    print(f"{C_BOLD}What would you like to do?{C_RESET}")
    print(f"  {C_CYAN}[1] ZIP & ANCHOR AS SINGLE BUNDLE{C_RESET} (Best practice: 1 stamp anchors everything)")
    print(f"  {C_CYAN}[2] ANCHOR A SINGLE SPECIFIC FILE{C_RESET} (Target one file only)")
    print(f"  {C_CYAN}[3] ANCHOR ALL FILES INDIVIDUALLY{C_RESET} (Recursive pass over every asset)")
    print(f"  {C_CYAN}[4] SYNC & UPDATE README{C_RESET}          (Verify proofs against Bitcoin & prepare repush)")
    print(f"  {C_CYAN}[5] AUDIT ALL LEDGERS{C_RESET}             (View ledger tracking status)")
    print("-"*75)

    choice = input(f"Select an option (1-5) [Default: 1]: ").strip() or "1"

    # --------------------------------------------------------------------------
    # OPTION 1: ZIP & ANCHOR AS SINGLE BUNDLE
    # --------------------------------------------------------------------------
    if choice == "1":
        zip_name = input(f"Archive filename [Default: {DEFAULT_BUNDLE_NAME}]: ").strip() or DEFAULT_BUNDLE_NAME
        note = input(f"Genesis Provenance Note [Default: {project_title} Release Bundle]: ").strip() or f"{project_title} Release Bundle"

        zip_target = create_bundle_zip(root_dir, zip_name)
        stamp_genesis_file(zip_target, sk, root_dir, note, current_tip, signer_name)

        print("\n" + "="*75)
        print(f"{C_GREEN}✅ BUNDLE ARCHIVED & ANCHORED!{C_RESET}")
        print(f"🏢 Signer:  {C_BOLD}{signer_name}{C_RESET}")
        print(f"✍️  Author:  {C_BOLD}{author_name}{C_RESET}")
        print(f"📦 Archive: {C_BOLD}{zip_target}{C_RESET}")
        print(f"⚓ Proof:   {C_BOLD}{zip_target}.ots{C_RESET}")
        print(f"🔏 Manifest: {C_BOLD}{zip_target}.provenance.json{C_RESET}")
        print(f"\n💡 Wait ~1-2 hours for Bitcoin confirmation, then run {C_CYAN}Option [4]{C_RESET} to sync.")
        print("="*75 + "\n")

    # --------------------------------------------------------------------------
    # OPTION 2: ANCHOR A SINGLE FILE
    # --------------------------------------------------------------------------
    elif choice == "2":
        filepath = input("Enter path to file: ").strip().strip("'\"")
        if not os.path.exists(filepath):
            print(f"{C_RED}Error: File '{filepath}' does not exist.{C_RESET}")
            return

        note = input(f"Provenance Note [Default: Single Asset Genesis Anchor]: ").strip() or "Single Asset Genesis Anchor"
        stamp_genesis_file(filepath, sk, root_dir, note, current_tip, signer_name)
        print(f"\n{C_GREEN}✅ Finished processing {filepath}!{C_RESET}\n")

    # --------------------------------------------------------------------------
    # OPTION 3: ANCHOR ALL FILES INDIVIDUALLY
    # --------------------------------------------------------------------------
    elif choice == "3":
        targets = discover_targets(root_dir)
        note = input(f"Genesis Provenance Note [Default: {project_title} Master Asset]: ").strip() or f"{project_title} Master Asset"

        print(f"\nProcessing {len(targets)} assets under publisher '{signer_name}'...\n")
        for t in targets:
            stamp_genesis_file(t, sk, root_dir, note, current_tip, signer_name)

        print(f"\n{C_GREEN}✅ All assets processed.{C_RESET}\n")

    # --------------------------------------------------------------------------
    # OPTION 4: SYNC & VERIFY
    # --------------------------------------------------------------------------
    elif choice == "4":
        targets = discover_all_ots_targets(root_dir)

        if not targets:
            print(f"\n{C_YELLOW}No .ots proof files found to verify.{C_RESET}\n")
            return

        print(f"\n{C_BOLD}🔄 SYNCHRONIZING WITH BITCOIN BLOCKCHAIN ({len(targets)} proofs){C_RESET}\n")

        confirmed_blocks = set()
        file_blocks = {}

        for t in targets:
            blocks = sync_and_verify_file(t, signer_name, root_dir)
            if blocks:
                file_blocks[t] = blocks
                confirmed_blocks.update(blocks)

        if file_blocks:
            print("\n" + "=" * 75)
            print(f"{C_BOLD}⛓️  BITCOIN ATTESTATIONS & CANONICAL PROVENANCE{C_RESET}")
            print("=" * 75)

            for filepath, blocks in file_blocks.items():
                canonical = min(blocks)
                all_blocks_str = ", ".join(f"Block {b}" for b in blocks)

                print(f"\n📄 {C_BOLD}{filepath}{C_RESET}")
                print(f"   🔍 All Calendar Confirmations: {C_GREY}{all_blocks_str}{C_RESET}")
                print(f"   ⚓ {C_GREEN}{C_BOLD}USE THIS CANONICAL BLOCK:   Bitcoin Block {canonical}{C_RESET}")

            print("\n" + "=" * 75)

            primary_block = min(confirmed_blocks)

            print(f"\n🎉 {C_GREEN}Bitcoin confirmations verified!{C_RESET}")
            print(f"📌 {C_BOLD}UNIVERSAL PROJECT ANCHOR: Bitcoin Block {primary_block}{C_RESET}")
            print(f"   {C_GREY}(Reference this single canonical block number for all CC BY 4.0 attributions){C_RESET}\n")

            update_readme_block_height(primary_block, README_FILE)
            update_genome_blockchain_anchor(primary_block, GENOME_FILE)

            print("\n" + "=" * 75)
            print(f"{C_GREEN}🚀 READY FOR GIT REPUSH!{C_RESET}")
            print(f"Anchored to {C_BOLD}Bitcoin Block {primary_block}{C_RESET}.")
            print(f"\n   {C_CYAN}git add .{C_RESET}")
            print(f'   {C_CYAN}git commit -m "Anchor Storybook Genesis to Bitcoin Block {primary_block}"{C_RESET}')
            print(f"   {C_CYAN}git push{C_RESET}\n")
            print("=" * 75 + "\n")

        else:
            print("\n" + "=" * 75)
            print(f"{C_YELLOW}⏳ Proofs are still awaiting Bitcoin attestation.{C_RESET}")
            print("=" * 75 + "\n")

    # --------------------------------------------------------------------------
    # OPTION 5: AUDIT LEDGERS
    # --------------------------------------------------------------------------
    elif choice == "5":
        if os.path.exists(MASTER_LEDGER):
            with open(MASTER_LEDGER, "r") as f:
                data = json.load(f)
            print(f"\n{C_BOLD}📋 Current Master Ledger ({len(data)} tracked files):{C_RESET}\n")
            for h, info in data.items():
                blk_str = f"{C_GREEN}Block {info.get('bitcoin_block')}{C_RESET}" if info.get('bitcoin_block') else f"{C_YELLOW}Pending{C_RESET}"
                lic_str = f"{C_CYAN}{info.get('license', 'Unknown')}{C_RESET}"
                signer_str = f"{C_GREY}({info.get('signer', 'Unknown')}){C_RESET}"
                print(f" • {info.get('path')} [{lic_str}] {signer_str} -> {blk_str}")
            print(f"\nTotal assets recorded in {MASTER_LEDGER}.\n")
        else:
            print(f"\n{C_YELLOW}No {MASTER_LEDGER} found yet. Run an anchoring option first.{C_RESET}\n")

if __name__ == "__main__":
    main()
