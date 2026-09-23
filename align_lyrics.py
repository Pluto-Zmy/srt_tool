"""Align existing song lyrics to individual audio files with stable-ts/Whisper.

The original SRT timing is used only to associate translations and report changes.
Inference is local; the optional model dependency is loaded only for actual runs.
"""

import argparse
import json
import math
import re
import shutil
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from qqmusic_lyric_collect import load_tracks
from lyric_split import split_long_lyric_line
from srt_tool import (
    SubtitleCue, clean_lyric_lines, find_translation_lines, load_config,
    parse_srt, write_srt,
)


AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma", ".aiff"}
IGNORED_DIRS = {".git", ".venv", ".venv-align", "node_modules", "__pycache__"}


def audio_key(name: str) -> str:
    stem = unicodedata.normalize("NFKC", Path(name).stem).casefold()
    stem = re.sub(r"^\s*(?:\[\d+\]\s*|\d+(?:[-_.]\d+)*[\s._-]+)+", "", stem)
    return re.sub(r"[\W_]+", "", stem)


def index_audio(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ValueError(f"Audio directory not found: {root}")
    # walk() avoids scanning virtual environments and does not follow symlinks.
    import os
    paths = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in files:
            if not name.startswith("._") and Path(name).suffix.lower() in AUDIO_SUFFIXES:
                paths.append(Path(directory) / name)
    return sorted(paths)


def resolve_audio(name: str, paths: list[Path]) -> Path:
    exact = [path for path in paths if path.name.casefold() == Path(name).name.casefold()]
    matches = exact or [path for path in paths if audio_key(path.name) == audio_key(name)]
    if not matches:
        raise ValueError(f"No audio match: {name}")
    if len(matches) > 1:
        raise ValueError(f"Ambiguous audio for {name}; specify audio_file in --overrides: "
                         + "; ".join(str(path) for path in matches))
    return matches[0]


def choose_language(text: str) -> str:
    """Script-based default, not acoustic language identification."""
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", text):
        return "ko"
    if re.search(r"[\u3400-\u9fff]", text):
        return "zh"
    if re.search(r"[a-zA-Z]", text):
        return "en"
    raise ValueError("Cannot infer lyric language; specify --language or a per-song language override")


def prepare_lyrics(cues: list[SubtitleCue]) -> tuple[list[SubtitleCue], list[str]]:
    sources, texts = [], []
    for cue in cues:
        lines = clean_lyric_lines(cue.lines)
        if lines:
            sources.append(SubtitleCue(cue.start_ms, cue.end_ms, lines))
            # All source lines are sung text. Translations are loaded separately.
            texts.append(" ".join(lines))
    return sources, texts


def prepare_alignment(cues: list[SubtitleCue], language: str,
                      split_long: bool = True) -> tuple[list[SubtitleCue], list[str], list[int]]:
    """Keep source cue ownership; old times are references, never estimated splits."""
    sources, texts, parents = [], [], []
    chinese = language.casefold() in {"zh", "yue", "chinese", "cantonese"}
    for parent, cue in enumerate(cues):
        line_parts = [split_long_lyric_line(line) if chinese and split_long else [line]
                      for line in cue.lines]
        if any(len(parts) > 1 for parts in line_parts):
            groups = [[part] for parts in line_parts for part in parts]
        else:
            groups = [list(cue.lines)]
        for lines in groups:
            sources.append(SubtitleCue(cue.start_ms, cue.end_ms, lines))
            texts.append(" ".join(lines))
            parents.append(parent)
    return sources, texts, parents


def text_key(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split()).casefold()


def validate_alignment(sources: list[SubtitleCue], texts: list[str], result: dict,
                       duration: float, min_probability: float = 0.35,
                       review_shift: float = 5.0,
                       split_flags: list[bool] | None = None) -> tuple[list[SubtitleCue], list[dict]]:
    split_flags = split_flags if split_flags is not None else [False] * len(sources)
    if len(texts) != len(sources) or len(split_flags) != len(sources):
        raise ValueError("Alignment input text/source/split counts differ")
    segments = result.get("segments", [])
    if len(segments) != len(sources):
        raise ValueError(f"Alignment returned {len(segments)} lines; expected {len(sources)}. "
                         "No timestamps were applied.")
    aligned, rows = [], []
    previous_end = 0
    for number, (cue, text, segment) in enumerate(zip(sources, texts, segments), 1):
        if text_key(segment.get("text", "")) != text_key(text):
            raise ValueError(f"Line {number}: alignment changed the lyric grouping/text")
        start, end = float(segment["start"]), float(segment["end"])
        if not all(math.isfinite(value) for value in (start, end)):
            raise ValueError(f"Line {number}: non-finite timestamps")
        start_ms, end_ms = round(start * 1000), round(end * 1000)
        if start_ms < 0 or end_ms <= start_ms or end > duration + 0.05:
            raise ValueError(f"Line {number}: invalid or out-of-audio time window {start}--{end}")
        if start_ms < previous_end:
            raise ValueError(f"Line {number}: overlapping alignment; manual review required")
        previous_end = end_ms
        words = segment.get("words", [])
        reasons = []
        probabilities = []
        if not words:
            reasons.append("missing_word_timestamps")
        for word in words:
            ws, we = float(word.get("start", math.nan)), float(word.get("end", math.nan))
            if not math.isfinite(ws) or not math.isfinite(we) or we <= ws:
                reasons.append("unaligned_word")
            elif ws < start - 0.05 or we > end + 0.05:
                reasons.append("word_outside_line")
            probability = word.get("probability")
            if probability is not None:
                probability = float(probability)
                if math.isfinite(probability) and 0 <= probability <= 1:
                    probabilities.append(probability)
        minimum = min(probabilities) if probabilities else None
        if len(probabilities) != len(words) or not probabilities:
            reasons.append("missing_word_probability")
        if minimum is not None and minimum < min_probability:
            reasons.append("low_word_probability")
        # A child is expected to occupy only part of its parent's window.
        # For splits, flag movement outside that window, not the natural shortening.
        if split_flags[number - 1]:
            shift = max(cue.start_ms - start_ms, end_ms - cue.end_ms, 0)
        else:
            shift = max(abs(start_ms - cue.start_ms), abs(end_ms - cue.end_ms))
        if shift > review_shift * 1000:
            reasons.append("large_timestamp_change")
        if end - start > 20:
            reasons.append("long_line_window")
        rows.append({
            "line": number, "text": text,
            "old_start_ms": cue.start_ms, "old_end_ms": cue.end_ms,
            "start_ms": start_ms, "end_ms": end_ms,
            "start_shift_ms": start_ms - cue.start_ms, "end_shift_ms": end_ms - cue.end_ms,
            "min_word_probability": minimum, "review_reasons": sorted(set(reasons)),
        })
        aligned.append(SubtitleCue(start_ms, end_ms, list(cue.lines)))
    return aligned, rows


class WhisperAligner:
    def __init__(self, model: str, device: str, model_dir: Path):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("FFmpeg is required on PATH to decode the song audio")
        try:
            import stable_whisper
            from stable_whisper.audio import load_audio
        except ImportError as exc:
            raise RuntimeError("Install alignment dependencies: python -m pip install -r requirements-align.txt") from exc
        self.load_audio = load_audio
        self.model = stable_whisper.load_model(
            model, device=None if device == "auto" else device, download_root=str(model_dir)
        )

    def align(self, audio_path: Path, texts: list[str], language: str) -> tuple[dict, float]:
        audio = self.load_audio(str(audio_path), sr=16000)
        duration = len(audio) / 16000
        result = self.model.align(
            audio, "\n".join(texts), language=language, original_split=True,
            regroup=False, remove_instant_words=False, verbose=False,
        )
        if result is None:
            raise ValueError("The model could not align the supplied lyrics")
        return result.to_dict(), duration


def load_overrides(path: Path | None) -> dict:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or any(not isinstance(value, dict) for value in data.values()):
        raise ValueError("Overrides must be an object keyed by SRT filename")
    for value in data.values():
        if "audio_file" in value:
            audio_path = Path(value["audio_file"])
            value["audio_file"] = str((path.parent / audio_path).resolve())
    return data


def build_jobs(config: Path, raw: Path, srt_dir: Path, audio_root: Path,
               overrides: dict, tracks: list[str] | None, language: str,
               split_long: bool = True) -> list[dict]:
    entries = load_config(config)
    names = [entry.file_name for entry in entries]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate SRT filenames in config")
    selected = {Path(item).stem for item in tracks} if tracks else None
    if selected:
        unknown = selected - {Path(entry.file_name).stem for entry in entries}
        if unknown:
            raise ValueError("Unknown track numbers: " + ", ".join(sorted(unknown)))
    raw_tracks = {f"{track.num}.srt": track for track in load_tracks(raw)}
    paths = index_audio(audio_root)
    jobs = []
    for entry in entries:
        if selected and Path(entry.file_name).stem not in selected:
            continue
        # Numbered outputs stay directly under the output directory.
        if Path(entry.file_name).name != entry.file_name:
            raise ValueError(f"Expected a basename in config: {entry.file_name}")
        job = {"file_name": entry.file_name, "time_offset_ms": entry.time_offset_ms}
        jobs.append(job)
        try:
            source = srt_dir / entry.file_name
            if not source.is_file():
                job.update(status="skipped_missing_srt", reason=f"No source lyrics: {source}")
                continue
            cues, texts = prepare_lyrics(parse_srt(source))
            if not texts:
                if source.read_bytes().strip():
                    raise ValueError(f"Non-empty SRT has no usable lyrics: {source}")
                job.update(status="skipped_empty_srt", reason="No sung lyrics")
                continue
            option = overrides.get(entry.file_name, {})
            if option.get("audio_file"):
                audio_path = Path(option["audio_file"])
                if not audio_path.is_file():
                    raise ValueError(f"Audio file not found: {audio_path}")
            else:
                if entry.file_name not in raw_tracks:
                    raise ValueError("No raw.txt entry; specify audio_file in --overrides")
                audio_path = resolve_audio(raw_tracks[entry.file_name].file_name, paths)
            requested_language = option.get("language", language)
            resolved_language = choose_language(" ".join(texts)) if requested_language == "auto" else requested_language
            prepared, _, parents = prepare_alignment(cues, resolved_language, split_long)
            job.update(status="ready", audio_file=str(audio_path.resolve()), language=resolved_language,
                       language_source="text_script" if requested_language == "auto" else "explicit",
                       source_cue_count=len(cues), cue_count=len(prepared),
                       split_source_cues=sum(count > 1 for count in Counter(parents).values()))
        except (ValueError, OSError) as exc:
            job.update(status="failed", reason=str(exc))
    return jobs


def write_review(report: dict, path: Path) -> None:
    lines = ["# 歌词音频对齐报告", "",
             "时间单位为秒；这是模型候选结果，需试听确认。词概率仅用于筛查，不代表时间准确率。", "",
             "译文按校准前的时间关联原文，再跟随原文的新时间窗口。", "",
             f"状态统计：`{json.dumps(report['summary'], ensure_ascii=False)}`", ""]
    if report.get("fatal_error"):
        lines.extend([f"运行中断：{report['fatal_error']}", ""])
    for job in report["tracks"]:
        lines.extend([f"## {job['file_name']} — {job['status']}", ""])
        if "reason" in job:
            lines.extend([job["reason"], ""])
        if "audio_file" in job:
            lines.extend([f"音频：`{job['audio_file']}`", ""])
        if "source_cue_count" in job:
            lines.extend([f"字幕数：{job['source_cue_count']} → {job['cue_count']}；"
                          f"拆分原字幕：{job['split_source_cues']} 条。", ""])
        if "lines" not in job:
            continue
        lines.extend(["拆分条目的原时间指整条原字幕时间，拆分后的新时间由音频对齐生成。", "",
                      "| 行 | 原字幕行 | 歌词 | 原时间 | 新时间 | 复核原因 |",
                      "| --- | --- | --- | --- | --- | --- |"])
        for row in job["lines"]:
            text = row["text"].replace("|", "\\|")
            old = f"{row['old_start_ms']/1000:.3f}–{row['old_end_ms']/1000:.3f}"
            new = f"{row['start_ms']/1000:.3f}–{row['end_ms']/1000:.3f}"
            reasons = ", ".join(row["review_reasons"]) or "—"
            lines.append(f"| {row['line']} | {row.get('source_line', row['line'])} | {text} | {old} | {new} | {reasons} |")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_alignment(args, aligner_factory=WhisperAligner) -> dict:
    source_dir = args.srt_dir or args.config.parent / "srts"
    output_dir = args.output_dir
    if output_dir.resolve() == source_dir.resolve():
        raise ValueError("Output directory must differ from the original SRT directory")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Output directory must be empty; choose a new --output-dir: {output_dir}")
    jobs = build_jobs(args.config, args.raw, source_dir, args.audio_root,
                      load_overrides(args.overrides), args.tracks, args.language,
                      not args.no_split_long_lyrics)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"mode": "dry_run" if args.dry_run else "alignment", "model": args.model,
              "split_long_chinese_lyrics": not args.no_split_long_lyrics,
              "device": args.device, "source_dir": str(source_dir.resolve()),
              "audio_root": str(args.audio_root.resolve()), "tracks": jobs}
    report_path = output_dir / "alignment_report.json"

    def save_report():
        report["summary"] = {status: sum(job["status"] == status for job in jobs)
                             for status in sorted({job["status"] for job in jobs})}
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_review(report, output_dir / "alignment_report.md")

    save_report()
    if args.dry_run:
        return report
    backend = None
    output_entries = []
    try:
        for job in jobs:
            if job["status"] != "ready":
                continue
            print(f"Aligning {job['file_name']} ({job['language']}): {job['audio_file']}", flush=True)
            if backend is None:
                backend = aligner_factory(args.model, args.device, args.model_dir)
            try:
                source_path = source_dir / job["file_name"]
                cues, texts = prepare_lyrics(parse_srt(source_path))
                alignment_cues, texts, parents = prepare_alignment(
                    cues, job["language"], not args.no_split_long_lyrics)
                parent_counts = Counter(parents)
                split_flags = [parent_counts[parent] > 1 for parent in parents]
                translation_path = source_path.with_name(f"{source_path.stem}_ts.srt")
                translations = parse_srt(translation_path) if translation_path.is_file() else []
                result, duration = backend.align(Path(job["audio_file"]), texts, job["language"])
                # Save raw evidence even when timestamp validation fails.
                (output_dir / f"{source_path.stem}.alignment.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                aligned, rows = validate_alignment(alignment_cues, texts, result, duration,
                                                   args.min_probability, args.review_shift, split_flags)
                for parent, new, row in zip(parents, aligned, rows):
                    row["source_line"] = parent + 1
                    row["split_from_source"] = parent_counts[parent] > 1
                    translation_lines = find_translation_lines(cues[parent], translations)
                    new.lines.extend(translation_lines)
                    if translation_lines and row["split_from_source"]:
                        # Translation has no word-to-phrase mapping. Preserve it rather
                        # than guessing its cuts, and make the repeated text reviewable.
                        row["review_reasons"].append("shared_translation_after_split")
                write_srt(aligned, output_dir / job["file_name"])
                job.update(status="needs_review" if any(row["review_reasons"] for row in rows) else "aligned",
                           duration_seconds=duration, lines=rows)
                output_entries.append({"file_name": job["file_name"], "time_offset": job["time_offset_ms"] / 1000})
            except Exception as exc:
                job.update(status="failed", reason=f"{type(exc).__name__}: {exc}")
                print(f"Failed {job['file_name']}: {exc}", file=sys.stderr, flush=True)
            save_report()
    except (Exception, KeyboardInterrupt) as exc:
        report["fatal_error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        # Only files produced in this run enter the preview configuration.
        (output_dir / "configV2.json").write_text(
            json.dumps({"srt_list": output_entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        save_report()
    return report


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Align per-song SRT lyrics to local audio with Whisper.")
    parser.add_argument("--config", type=Path, default=Path("configV2.json"))
    parser.add_argument("--raw", type=Path, default=Path("raw.txt"))
    parser.add_argument("--srt-dir", type=Path)
    parser.add_argument("--audio-root", type=Path, required=True, help="Recursively search this audio directory")
    parser.add_argument("--output-dir", type=Path, default=Path("aligned_srts"), help="New or empty output directory")
    parser.add_argument("--tracks", nargs="+", help="Only these config track numbers, e.g. 1 48")
    parser.add_argument("--overrides", type=Path, help='JSON keyed by SRT filename with audio_file/language')
    parser.add_argument("--language", default="auto", help="Whisper code (zh/ja/en/...) or auto by lyric script")
    parser.add_argument("--model", default="medium")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--model-dir", type=Path, default=Path(".models/whisper"))
    parser.add_argument("--no-split-long-lyrics", action="store_true",
                        help="Keep original Chinese lyric grouping instead of splitting spaced lines with at least 10 Han characters")
    parser.add_argument("--min-probability", type=float, default=0.35, help="Review threshold; not an accuracy guarantee")
    parser.add_argument("--review-shift", type=float, default=5.0, help="Review changes larger than this many seconds")
    parser.add_argument("--dry-run", action="store_true", help="Check inputs and write report without loading a model")
    return parser


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = make_parser()
    args = parser.parse_args(argv)
    if not math.isfinite(args.min_probability) or not 0 <= args.min_probability <= 1:
        parser.error("--min-probability must be between 0 and 1")
    if not math.isfinite(args.review_shift) or args.review_shift < 0:
        parser.error("--review-shift must be non-negative")
    try:
        report = run_alignment(args)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Report: {args.output_dir / 'alignment_report.json'}")
    return 2 if any(job["status"] in {"failed", "needs_review"} for job in report["tracks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
