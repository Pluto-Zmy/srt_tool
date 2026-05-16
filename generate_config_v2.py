import argparse
import json
import re
import sys
from pathlib import Path


RAW_LINE_RE = re.compile(r"^音频\s+(\d+)\s*:\s*(.*?)\s*:\s*([\d.]+)\s*$")


def parse_raw(raw_path: Path) -> list[dict[str, str]]:
    srt_list: list[dict[str, str]] = []

    for line_no, line in enumerate(raw_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        match = RAW_LINE_RE.match(line)
        if not match:
            raise ValueError(f"Cannot parse line {line_no}: {line}")

        num = match.group(1)
        time_offset = match.group(3)
        srt_list.append(
            {
                "file_name": f"{num}.srt",
                "time_offset": time_offset,
            }
        )

    return srt_list


def generate_config(raw_path: Path, output_path: Path) -> dict[str, list[dict[str, str]]]:
    config = {"srt_list": parse_raw(raw_path)}
    output_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    return config


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Generate configV2.json from raw.txt.")
    parser.add_argument("--raw", default="raw.txt", help="Path to raw.txt. Default: raw.txt")
    parser.add_argument("--output", default="configV2.json", help="Output config path. Default: configV2.json")
    args = parser.parse_args()

    raw_path = Path(args.raw)
    output_path = Path(args.output)

    if not raw_path.exists():
        raise FileNotFoundError(f"raw file not found: {raw_path}")

    config = generate_config(raw_path, output_path)
    print(f"Generated {output_path} with {len(config['srt_list'])} entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
