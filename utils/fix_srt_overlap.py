import re
import os


def parse_time(time_str):
    time_str = time_str.strip()
    parts = time_str.replace(",", ".").split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def fix_srt_overlap(input_file, output_file=None):
    if output_file is None:
        output_file = input_file

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    subtitles = []

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            index = lines[0].strip()
            time_line = lines[1].strip()
            text = "\n".join(lines[2:])

            match = re.match(
                r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
                time_line,
            )
            if match:
                start_time = match.group(1)
                end_time = match.group(2)
                subtitles.append(
                    {
                        "index": index,
                        "start": start_time,
                        "end": end_time,
                        "text": text,
                        "start_sec": parse_time(start_time),
                        "end_sec": parse_time(end_time),
                    }
                )

    fixed_count = 0
    for i in range(len(subtitles) - 1):
        current = subtitles[i]
        next_sub = subtitles[i + 1]

        if current["end_sec"] > next_sub["start_sec"]:
            current["end"] = next_sub["start"]
            current["end_sec"] = next_sub["start_sec"]
            fixed_count += 1
            print(
                f"第 {current['index']} 句: 结束时间 {subtitles[i]['end']} -> {next_sub['start']}"
            )

    with open(output_file, "w", encoding="utf-8") as f:
        for sub in subtitles:
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n\n")

    print(f"\n处理完成! 共修复 {fixed_count} 处时间重叠问题")
    return fixed_count


if __name__ == "__main__":
    input_srt = "output.srt"
    output_srt = "output_fixed.srt"

    if os.path.exists(input_srt):
        fix_srt_overlap(input_srt, output_srt)
    else:
        print(f"文件 {input_srt} 不存在")
