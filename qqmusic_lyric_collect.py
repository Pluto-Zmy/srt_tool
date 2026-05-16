import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_LYRIC_DIR = Path(r"E:\SrtCache")


@dataclass
class Track:
    num: int
    file_name: str
    artist: str
    title: str
    start: float
    duration: float | None = None


@dataclass
class LyricFile:
    kind: str
    path: Path
    artist: str
    title: str
    normalized_artist: str
    normalized_title: str


def normalize(value: str | None) -> str:
    if value is None:
        return ""
    replacements = {
        "（": "(",
        "）": ")",
        "&": "and",
    }
    value = value.lower()
    for old, new in replacements.items():
        value = value.replace(old, new)
    return re.sub(r"[\s_\-'\"`.,，、/\\:：\[\]【】()]", "", value)


def clean_song_file_name(file_name: str) -> str:
    cleaned = re.sub(r"^\s*\[\d+\]\s*", "", file_name)
    cleaned = re.sub(r"^\s*\d+[-_. ]+", "", cleaned)
    return cleaned


def clean_raw_file(raw_path: Path) -> int:
    lines = raw_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = 0
    cleaned_lines: list[str] = []

    for line in lines:
        match = re.match(r"^(音频\s+\d+\s*:\s*)(.*?)(\s*:\s*[\d.]+\s*)$", line.rstrip("\r\n"))
        if not match:
            cleaned_lines.append(line)
            continue

        prefix, file_name, suffix = match.groups()
        cleaned_name = clean_song_file_name(file_name)
        if cleaned_name != file_name:
            changed += 1

        newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
        cleaned_lines.append(f"{prefix}{cleaned_name}{suffix}{newline}")

    if changed:
        raw_path.write_text("".join(cleaned_lines), encoding="utf-8")

    return changed


def parse_track_line(line: str) -> Track | None:
    match = re.match(r"^音频\s+(\d+)\s*:\s*(.*?)\s*:\s*([\d.]+)\s*$", line)
    if not match:
        return None

    num = int(match.group(1))
    file_name = match.group(2)
    start = float(match.group(3))
    stem = Path(file_name).stem.strip()
    artist = ""
    title = stem

    dash_match = re.match(r"^(.+?)\s+-\s+(.+)$", stem)
    compact_dash_match = re.match(r"^(.+?)-\s*(.+)$", stem)
    if dash_match:
        artist = dash_match.group(1).strip()
        title = dash_match.group(2).strip()
    elif compact_dash_match:
        artist = compact_dash_match.group(1).strip()
        title = compact_dash_match.group(2).strip()

    return Track(num=num, file_name=file_name, artist=artist, title=title, start=start)


def load_tracks(raw_path: Path) -> list[Track]:
    tracks: list[Track] = []
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        track = parse_track_line(line)
        if track:
            tracks.append(track)

    for index in range(len(tracks) - 1):
        tracks[index].duration = round(tracks[index + 1].start - tracks[index].start, 1)

    return tracks


def strip_parenthesized_text(value: str) -> str:
    value = re.sub(r"_hires$", "", value)
    value = re.sub(r"\s*[\(（][^\)）]*[\)）]\s*", "", value)
    return value.strip()


def parse_lyric_file(path: Path) -> LyricFile:
    match = re.match(r"^(.*)-([01])$", path.stem)
    if not match:
        raise ValueError(f"invalid lyric file name: {path.name}")

    base_name = match.group(1)
    kind = match.group(2)
    parts = base_name.split(" - ")

    artist = parts[0].strip() if parts else ""
    title = parts[1].strip() if len(parts) >= 2 else base_name.strip()

    return LyricFile(
        kind=kind,
        path=path,
        artist=artist,
        title=title,
        normalized_artist=normalize(artist),
        normalized_title=normalize(strip_parenthesized_text(title)),
    )


def load_lyric_files(lyric_dir: Path) -> list[LyricFile]:
    files: list[LyricFile] = []
    for path in lyric_dir.glob("*.srt"):
        if not re.search(r"-[01]\.srt$", path.name):
            continue
        files.append(parse_lyric_file(path))
    return files


def title_variants(title: str) -> list[str]:
    variants = [
        title,
        re.sub(r"_hires$", "", title),
        re.sub(r"\s*\([^)]*\)\s*$", "", title),
        strip_parenthesized_text(title),
    ]
    result: list[str] = []
    for item in variants:
        item = item.strip()
        if item and item not in result:
            result.append(item)
    return result


def artist_tokens(artist: str) -> list[str]:
    tokens = re.split(r"\s*(?:,|，|&| and | _ |/|、)\s*", artist)
    return [normalize(token) for token in tokens if token.strip()]


def has_non_empty_content(path: Path) -> bool:
    if path.stat().st_size == 0:
        return False
    with path.open("r", encoding="utf-8-sig", errors="ignore") as file:
        return bool(file.read().strip())


def find_best_match(track: Track, lyrics: list[LyricFile], kind: str) -> LyricFile | None:
    normalized_titles = {normalize(strip_parenthesized_text(title)) for title in title_variants(track.title)}
    tokens = artist_tokens(track.artist)
    candidates: list[tuple[int, str, LyricFile]] = []

    for lyric in lyrics:
        if lyric.kind != kind:
            continue
        if lyric.normalized_title not in normalized_titles:
            continue
        if not any(token and token in lyric.normalized_artist for token in tokens):
            continue

        score = 0
        if normalize(track.artist) == lyric.normalized_artist:
            score += 10
        if normalize(strip_parenthesized_text(track.title)) == lyric.normalized_title:
            score += 10
        candidates.append((-score, lyric.path.name, lyric))

    if not candidates:
        return None

    return sorted(candidates, key=lambda item: (item[0], item[1]))[0][2]


def copy_lyrics(tracks: list[Track], lyrics: list[LyricFile], output_dir: Path, dry_run: bool) -> tuple[list[tuple[Track, str, LyricFile, Path]], list[tuple[Track, str]]]:
    copied: list[tuple[Track, str, LyricFile, Path]] = []
    missing: list[tuple[Track, str]] = []

    output_dir.mkdir(parents=True, exist_ok=True)

    for track in tracks:
        for kind in ("0", "1"):
            match = find_best_match(track, lyrics, kind)
            if not match:
                missing.append((track, kind))
                continue

            if kind == "1" and not has_non_empty_content(match.path):
                missing.append((track, kind))
                continue

            dest_name = f"{track.num}_ts.srt" if kind == "1" else f"{track.num}.srt"
            dest_path = output_dir / dest_name
            if not dry_run:
                shutil.copy2(match.path, dest_path)
            copied.append((track, kind, match, dest_path))

    return copied, missing


def print_report(cleaned_count: int, copied, missing) -> None:
    print(f"Cleaned raw entries: {cleaned_count}")
    print(f"Copied lyric files: {len(copied)}")
    for track, kind, lyric, dest_path in copied:
        label = "ts" if kind == "1" else "src"
        print(f"  {track.num:>2} {label:<4} -> {dest_path.name}  <=  {lyric.path.name}")

    print(f"Missing matches: {len(missing)}")
    for track, kind in missing:
        label = "ts" if kind == "1" else "src"
        print(f"  {track.num:>2} {label:<4} {track.artist} - {track.title}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Clean raw.txt song sub-numbers and collect cached srt lyrics.")
    parser.add_argument("--raw", default="raw.txt", help="Path to raw.txt. Default: raw.txt")
    parser.add_argument("--lyric-dir", default=str(DEFAULT_LYRIC_DIR), help=f"SRT lyric cache directory. Default: {DEFAULT_LYRIC_DIR}")
    parser.add_argument("--output-dir", default="srts", help="Directory to copy renamed lyrics into. Default: srts")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning song sub-numbers in raw.txt")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without writing lyric files")
    args = parser.parse_args()

    raw_path = Path(args.raw)
    lyric_dir = Path(args.lyric_dir)
    output_dir = Path(args.output_dir)

    if not raw_path.exists():
        raise FileNotFoundError(f"raw file not found: {raw_path}")
    if not lyric_dir.exists():
        raise FileNotFoundError(f"lyric directory not found: {lyric_dir}")

    cleaned_count = 0 if args.no_clean else clean_raw_file(raw_path)
    tracks = load_tracks(raw_path)
    lyrics = load_lyric_files(lyric_dir)
    copied, missing = copy_lyrics(tracks, lyrics, output_dir, args.dry_run)
    print_report(cleaned_count, copied, missing)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
