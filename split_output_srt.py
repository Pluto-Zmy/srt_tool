import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TIME_RANGE_RE = re.compile(r"(.+?\s*-->\s*.+)")


@dataclass
class Cue:
    time_line: str
    lines: list[str]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="gb18030")


def parse_srt(path: Path) -> list[Cue]:
    content = read_text(path)
    blocks = re.split(r"(?:\r?\n){2,}", content.strip())
    cues: list[Cue] = []

    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 2:
            continue

        time_line_index = 1 if "-->" in lines[1] else 0
        if "-->" not in lines[time_line_index]:
            continue

        time_line = lines[time_line_index].strip()
        if not TIME_RANGE_RE.match(time_line):
            continue

        text_lines = [line.rstrip("\r\n") for line in lines[time_line_index + 1 :] if line.strip()]
        cues.append(Cue(time_line=time_line, lines=text_lines))

    return cues


def write_selected_line(cues: list[Cue], line_index: int, output_path: Path) -> int:
    output_lines: list[str] = []
    output_index = 1

    for cue in cues:
        if len(cue.lines) <= line_index:
            continue

        output_lines.append(f"{output_index}\n")
        output_lines.append(f"{cue.time_line}\n")
        output_lines.append(f"{cue.lines[line_index]}\n\n")
        output_index += 1

    output_path.write_text("".join(output_lines), encoding="utf-8")
    return output_index - 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Split output.srt into first-line and second-line srt files.")
    parser.add_argument("--input", default="output.srt", help="Input srt path. Default: output.srt")
    parser.add_argument("--line1-output", default="output_line1.srt", help="First-line output path. Default: output_line1.srt")
    parser.add_argument("--line2-output", default="output_line2.srt", help="Second-line output path. Default: output_line2.srt")
    args = parser.parse_args()

    cues = parse_srt(Path(args.input))
    line1_count = write_selected_line(cues, 0, Path(args.line1_output))
    line2_count = write_selected_line(cues, 1, Path(args.line2_output))

    print(f"Wrote {args.line1_output} with {line1_count} cues.")
    print(f"Wrote {args.line2_output} with {line2_count} cues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
