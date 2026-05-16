import argparse
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


TIMESTAMP_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})$")
TIME_RANGE_RE = re.compile(r"(.+?)\s*-->\s*(.+)")
TRANSLATION_NOTICE_RE = re.compile(r"^以下歌词翻译由.*提供$")


@dataclass
class SubtitleCue:
    start_ms: int
    end_ms: int
    lines: list[str]


@dataclass
class ConfigEntry:
    file_name: str
    time_offset_ms: int


def parse_time_offset(value) -> int | None:
    if value is None:
        return None

    try:
        seconds = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"time_offset must be seconds, got: {value}") from exc

    return int((seconds * Decimal("1000")).to_integral_value(rounding=ROUND_HALF_UP))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="gb18030")


def parse_timestamp(value: str) -> int:
    match = TIMESTAMP_RE.match(value.strip())
    if not match:
        raise ValueError(f"invalid srt timestamp: {value}")

    hours, minutes, seconds, millis = (int(item) for item in match.groups())
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def format_timestamp(milliseconds: int) -> str:
    milliseconds = max(0, milliseconds)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def parse_srt(path: Path) -> list[SubtitleCue]:
    content = read_text(path)
    blocks = re.split(r"(?:\r?\n){2,}", content.strip())
    cues: list[SubtitleCue] = []

    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 2:
            continue

        time_line_index = 1 if "-->" in lines[1] else 0
        if "-->" not in lines[time_line_index]:
            continue

        match = TIME_RANGE_RE.match(lines[time_line_index].strip())
        if not match:
            continue

        start_ms = parse_timestamp(match.group(1).strip())
        end_ms = parse_timestamp(match.group(2).strip())
        text_lines = [line.rstrip("\r\n") for line in lines[time_line_index + 1 :]]
        cues.append(SubtitleCue(start_ms=start_ms, end_ms=end_ms, lines=text_lines))

    return cues


def write_srt(cues: list[SubtitleCue], output_path: Path) -> None:
    output_lines: list[str] = []

    for index, cue in enumerate(cues, start=1):
        output_lines.append(f"{index}\n")
        output_lines.append(f"{format_timestamp(cue.start_ms)} --> {format_timestamp(cue.end_ms)}\n")
        output_lines.extend(f"{line}\n" for line in cue.lines)
        output_lines.append("\n")

    output_path.write_text("".join(output_lines), encoding="utf-8")


def minute_second_key(milliseconds: int) -> tuple[int, int]:
    total_seconds = milliseconds // 1000
    return total_seconds // 60, total_seconds % 60


def is_translation_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return not TRANSLATION_NOTICE_RE.match(stripped)


def build_translation_map(cues: list[SubtitleCue]) -> dict[tuple[int, int], list[str]]:
    translations: dict[tuple[int, int], list[str]] = {}

    for cue in cues:
        lines = [line.strip() for line in cue.lines if is_translation_line(line)]
        if not lines:
            continue

        key = minute_second_key(cue.start_ms)
        if key not in translations:
            translations[key] = []

        for line in lines:
            if line not in translations[key]:
                translations[key].append(line)

    return translations


def merge_translation(original_cues: list[SubtitleCue], translation_cues: list[SubtitleCue]) -> list[SubtitleCue]:
    translations = build_translation_map(translation_cues)
    merged: list[SubtitleCue] = []

    for cue in original_cues:
        lines = list(cue.lines)
        translation_lines = translations.get(minute_second_key(cue.start_ms), [])
        lines.extend(translation_lines)
        merged.append(SubtitleCue(start_ms=cue.start_ms, end_ms=cue.end_ms, lines=lines))

    return merged


def offset_cues(cues: list[SubtitleCue], offset_ms: int) -> list[SubtitleCue]:
    return [
        SubtitleCue(
            start_ms=cue.start_ms + offset_ms,
            end_ms=cue.end_ms + offset_ms,
            lines=list(cue.lines),
        )
        for cue in cues
    ]


def clean_overlaps(cues: list[SubtitleCue]) -> int:
    fixed_count = 0

    for index in range(1, len(cues)):
        previous = cues[index - 1]
        current = cues[index]

        if current.start_ms < previous.end_ms:
            current.start_ms = previous.end_ms
            if current.end_ms < current.start_ms:
                current.end_ms = current.start_ms
            fixed_count += 1

    return fixed_count


def load_config(config_path: Path) -> list[ConfigEntry]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    entries: list[ConfigEntry] = []

    for item in data.get("srt_list", []):
        file_name = item.get("file_name")
        time_offset_ms = parse_time_offset(item.get("time_offset"))
        if not file_name or time_offset_ms is None:
            continue
        entries.append(ConfigEntry(file_name=file_name, time_offset_ms=time_offset_ms))

    return entries


def process_entry(entry: ConfigEntry, srt_dir: Path) -> list[SubtitleCue] | None:
    source_path = srt_dir / entry.file_name
    if not source_path.exists():
        print(f"Skip missing source: {source_path}")
        return None

    source_cues = parse_srt(source_path)
    translation_path = source_path.with_name(f"{source_path.stem}_ts{source_path.suffix}")

    if translation_path.exists() and translation_path.stat().st_size > 0:
        translation_cues = parse_srt(translation_path)
        source_cues = merge_translation(source_cues, translation_cues)

    return offset_cues(source_cues, entry.time_offset_ms)


def srt_tool(config_path: Path, output_path: Path, srt_dir: Path | None = None) -> None:
    srt_dir = srt_dir or config_path.parent / "srts"
    entries = load_config(config_path)
    output_cues: list[SubtitleCue] = []

    for entry in entries:
        cues = process_entry(entry, srt_dir)
        if cues:
            output_cues.extend(cues)

    fixed_count = clean_overlaps(output_cues)
    write_srt(output_cues, output_path)
    print(f"Wrote {output_path} with {len(output_cues)} cues. Fixed overlaps: {fixed_count}.")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Merge translated lyrics, offset, concatenate, and clean srt files.")
    parser.add_argument("--config", default="configV2.json", help="Path to configV2.json. Default: configV2.json")
    parser.add_argument("--output", default="output.srt", help="Output srt path. Default: output.srt")
    parser.add_argument("--srt-dir", default=None, help="Directory containing numbered srt files. Default: srts next to config")
    args = parser.parse_args()

    srt_dir = Path(args.srt_dir) if args.srt_dir else None
    srt_tool(Path(args.config), Path(args.output), srt_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
