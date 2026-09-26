#!/usr/bin/env python3
"""
===============================================================================
   STORYBOOK VIDEO ASSEMBLY ENGINE (v2.0 - Universal Edition)
   Clean, Crash-Proof Python + FFmpeg Multi-Clip Pipeline
   by Anthro Entertainment LLC
===============================================================================
"""

import os
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is required. Run: pip install pyyaml")


def load_genome(path):
    if not os.path.exists(path):
        sys.exit(f"Genome configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_ass_subtitles(genome):
    sub_cfg = genome.get("subtitles", {})
    output_ass = sub_cfg.get("output_file", "storybook_subtitles.ass")
    typo = genome.get("typography", {})
    sound_font = typo.get("subtitle_sound", "Caveat-Regular.ttf").split(".")[0]
    meaning_font = typo.get("subtitle_meaning", "Quicksand-Regular.ttf").split(".")[0]

    header = f"""[Script Info]
Title: {genome['meta']['title']} Subtitles
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
            start = dialog["start"]
            end = dialog["end"]
            sound = dialog.get("sound", "")
            meaning = dialog.get("meaning", "")
            if sound:
                f.write(f"Dialogue: 0,{start},{end},SoundLayer,,0,0,0,,{sound}\n")
            if meaning:
                f.write(f"Dialogue: 0,{start},{end},MeaningLayer,,0,0,0,,{meaning}\n")

    print(f"Generated subtitles: {output_ass}")
    return output_ass


def get_media_duration(path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def main():
    config_file = "FLICKER_GENOME.yaml"
    if "--config" in sys.argv:
        config_file = sys.argv[sys.argv.index("--config") + 1]

    genome = load_genome(config_file)
    soundtrack = genome["soundtrack"]
    typo = genome.get("typography", {})
    fonts_dir = typo.get("fonts_folder", "fonts")
    audio_dir = soundtrack.get("audio_folder", "audio")
    clips_dir = soundtrack.get("clips_folder", "clips")
    final_output = soundtrack.get("output_video", "Final_Storybook.mp4")

    ass_path = build_ass_subtitles(genome)
    rendered_segments = []
    concat_list = "segments_concat.txt"

    print(f"\n--- Assembling Video: {genome['meta']['title']} ---")

    for idx, song in enumerate(soundtrack["songs"]):
        audio_file = os.path.join(audio_dir, song["file"])
        if not os.path.exists(audio_file):
            print(f"Warning: Audio file {audio_file} missing. Generating silent placeholder.")
            os.makedirs(audio_dir, exist_ok=True)
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "15", audio_file
            ], check=True, capture_output=True)

        total_song_dur = get_media_duration(audio_file)
        clip_filenames = song["clips"]
        num_clips = len(clip_filenames)
        slot_dur = total_song_dur / num_clips

        clip_paths = []
        for c in clip_filenames:
            cp = os.path.join(clips_dir, c)
            if not os.path.exists(cp):
                print(f"Warning: Clip {cp} missing. Generating fallback placeholder clip.")
                os.makedirs(clips_dir, exist_ok=True)
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1E142B:s=1920x1080:d=5",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", cp
                ], check=True, capture_output=True)
            clip_paths.append(cp)

        seg_file = f"seg_{idx:02d}.mp4"
        rendered_segments.append(seg_file)

        # Title Card Filter (Safely escapes colons and quotes!)
        raw_title = song["title"].replace("'", "").replace(":", "\\:")
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

        # Build FFmpeg inputs & video scaling
        inputs = []
        filter_parts = []
        for c_idx, cp in enumerate(clip_paths):
            inputs.extend(["-stream_loop", "-1", "-t", str(slot_dur), "-i", cp])
            filter_parts.append(
                f"[{c_idx}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v{c_idx}];"
            )

        # CRASH-PROOF CONCAT LOGIC:
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

        print(f"Rendering Song {song['id']}: {song['title']} ({num_clips} clip(s), {total_song_dur:.1f}s)...")
        subprocess.run(cmd, check=True)

    # Stitch all segments
    with open(concat_list, "w") as f:
        for s in rendered_segments:
            f.write(f"file '{s}'\n")

    print("\nConcatenating segments and embedding ASS subtitles...")
    final_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-vf", f"ass={ass_path}:fontsdir={fonts_dir}",
        "-c:v", "libx264", "-c:a", "copy", final_output
    ]
    subprocess.run(final_cmd, check=True)

    # Clean up temp segment files
    for s in rendered_segments:
        if os.path.exists(s):
            os.remove(s)
    if os.path.exists(concat_list):
        os.remove(concat_list)

    print(f"\n🎉 Video Assembled Successfully: {final_output}")


if __name__ == "__main__":
    main()
