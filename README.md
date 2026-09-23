# SRT 字幕处理工具

用于处理和合并 SRT 字幕文件的工具。

## 功能

- 编码转换：将 GB18030 编码的 SRT 文件转换为 UTF-8
- 时间轴合并：将 TS 时间轴文件与 SRT 字幕合并
- 时间偏移：调整字幕时间轴偏移
- 字幕拼接：合并多个 SRT 文件

## 使用方法

### QQ 音乐歌词整理

清洗 `raw.txt` 中歌曲文件名开头的子编号，并从 SRT 缓存复制匹配到的 `-0.srt` / `-1.srt` 文件到 `srts` 目录。`-0.srt` 会重命名为 `编号.srt`；`-1.srt` 仅在内容非空时复制，并重命名为 `编号_ts.srt`。

默认读取当前目录的 `raw.txt`，默认歌词缓存目录为 `E:\SrtCache`：

```
python qqmusic_lyric_collect.py
```

常用参数：

```
python qqmusic_lyric_collect.py --dry-run
python qqmusic_lyric_collect.py --raw raw.txt --lyric-dir E:\SrtCache --output-dir srts
python qqmusic_lyric_collect.py --no-clean
```

### 用原始音频校准歌词时间轴（新增）

`align_lyrics.py` 用每首歌的原始音频和已有歌词做强制对齐，重新估计每句歌词的开始和结束时间，可处理整体偏移和逐句漂移。底层使用 [stable-ts 的 Whisper 强制对齐接口](https://github.com/jianfch/stable-ts#alignment)，使用现有 SRT 的歌词文本，中文长行会按下面的规则拆分。

输入为 `srts/编号.srt`、可选的 `srts/编号_ts.srt`、`raw.txt` 和 `configV2.json`。`raw.txt` 提供歌曲文件名，配置提供视频中的全局偏移。音频目录会递归搜索，支持忽略 `[9]`、`2-1 -` 等文件名前缀和空格差异，以及同名不同格式的音频；排除 `._` 文件。同一级匹配存在多个候选时报告冲突，需要明确指定文件。

**安装可选依赖**（建议 Python 3.10–3.12；本次验证使用 3.12，另需 FFmpeg 在 PATH 中）：

```powershell
python -m venv .venv-align
.\.venv-align\Scripts\python.exe -m pip install -r requirements-align.txt
```

默认 `medium` 模型；首次使用会下载模型到 `.models/whisper`，之后可以复用。推理在本机完成。`--device auto` 在支持时使用 CUDA，否则使用 CPU。依赖固定了已验证的 torch/torchaudio 2.5.1 组合；需要 GPU 时先按 [PyTorch 官方历史版本安装说明](https://pytorch.org/get-started/previous-versions/)安装该版本对应的 CUDA 轮子，再安装上述依赖。普通 pip 安装可能只有 CPU 支持。`base` 可用于快速检查流程，正式校准建议试用 `medium` 或 `large-v3` 并试听比较。

**先检查匹配，不下载或加载模型：**

```powershell
.\.venv-align\Scripts\python.exe align_lyrics.py --audio-root "E:\Workspace\^曲靖-洛阳" --overrides alignment_overrides.example.json --dry-run --output-dir alignment_check_new
```

**先试一首，再批量处理：**

```powershell
.\.venv-align\Scripts\python.exe align_lyrics.py --audio-root "E:\Workspace\^曲靖-洛阳" --tracks 1 --model base --output-dir aligned_srts_trial
.\.venv-align\Scripts\python.exe align_lyrics.py --audio-root "E:\Workspace\^曲靖-洛阳" --overrides alignment_overrides.example.json --model medium --output-dir aligned_srts
```

`--tracks 1 48` 可指定多首；省略时处理配置里的全部歌曲。每次必须使用新的或空的输出目录，避免失败的重跑混入旧结果；原始 SRT、音频和现有 `output.srt` 不会被修改。

**输出：**

- `编号.srt`：单曲内的候选时间轴，包含已同步的译文。先按旧时间关联译文，再一起更新时间；无需另复制 `_ts.srt`，避免重复合并。
- `编号.alignment.json`：模型原始输出，含词级时间和概率，便于诊断。
- `alignment_report.md` / `.json`：音频匹配、语言、每句旧/新时间、偏移量和复核原因。
- `configV2.json`：仅列出本次实际导出的歌曲，保留原全局偏移。可能是整段视频的部分歌曲，需先检查报告。

**复核后生成拼接预览：**

```powershell
.\.venv-align\Scripts\python.exe srt_tool.py --config aligned_srts/configV2.json --srt-dir aligned_srts --output output_aligned.srt
```

全局偏移仅在拼接时加一次。原文文件中的多行会一起用于对齐，因此应使用采集阶段的原文 SRT，译文放在单独的 `_ts.srt` 中。

**中文长行拆分（默认启用）：**

- 仅对中文/粤语歌曲的原文生效；逐个原文行判断：有句间空格，且汉字总数 **大于等于 10**，才进行拆分。正好 10 字也拆，少于 10 字不拆。
- 只统计汉字（含繁体及扩展汉字），不统计标点、英文字母和数字。普通空格、连续空格、全角空格和制表符均可作为句间分隔。
- 按空格分成短句，按原顺序尽量合并相邻短句，但合并后汉字数必须少于 10。单个没有空格的长句始终保留，不从句子内部强行切断。
- 例如 `天空的星星 照亮回家路` 共 10 字，拆成 `天空的星星` 和 `照亮回家路`；`没有人曾体会 没有人曾了解` 共 12 字，也拆成两条独立字幕。
- 拆分发生在音频对齐之前，每个新字幕独立获得模型预测的起止时间，不按字数均分旧时间。报告记录原字幕行及拆分前后的数量；原时间仍表示整条原字幕的窗口。
- 若被拆原文有译文，完整译文会随每条新字幕保留，并标记 `shared_translation_after_split` 供复核，不猜测译文的短句对应关系。

沿用上面的 `align_lyrics.py` 命令即可。若已有旧的校准结果，需要重新对齐并指定新的输出目录（例如 `--output-dir aligned_srts_split`），再使用该目录的配置拼接；单独运行 `srt_tool.py` 不会重新拆分或识别音频。增加 `--no-split-long-lyrics` 可保留旧分句方式。

**语言与个别文件覆盖：** 默认按歌词文字判断中文、日文、韩文和英文；这不是声学语言识别。其他语言、粤语、罗马字歌词或混合语言应显式指定 `--language`，也可使用 `--overrides` JSON 按歌覆盖。随附示例将当前 `38.srt` 的语言设为保加利亚语 `bg`。覆盖文件格式如下，`audio_file` 相对覆盖 JSON 所在目录解析，也可以使用绝对路径：

```json
{
  "1.srt": {"audio_file": "../阿良良木健,洛天依Official - 绝体绝命.mp3", "language": "zh"},
  "48.srt": {"language": "ja"},
  "38.srt": {"language": "bg"}
}
```

**质量与失败处理：** 歌唱中的拖音、和声、伴奏及错误歌词可能影响对齐，不能保证自动达到逐帧精度。默认将低词概率（小于 0.35）、零时长词、时间变化超过 5 秒和过长句子等标为 `needs_review`，仍导出候选供试听；概率不是时间准确率。`--min-probability` 和 `--review-shift` 可调整筛查阈值。缺句、分句变化、非法时间或时间重叠则整首记为 `failed`，不导出旧时间冒充成功。缺失或空 SRT 单独记为跳过，失败歌曲不阻止后续歌曲处理。

退出码：`0` 表示本次没有失败/待复核项（仍可能跳过无歌词歌曲）；`2` 表示有失败或待复核项；`1` 表示运行或输入错误。始终查看报告确认实际覆盖范围。

### configV2 生成

根据 `raw.txt` 自动生成 `configV2.json`，格式为 `srt_list` 中的 `file_name` 和 `time_offset`：

```
python generate_config_v2.py
```

自定义输入输出路径：

```
python generate_config_v2.py --raw raw.txt --output configV2.json
```

### SRT 处理

1. 修改或生成 `configV2.json` 配置：
   - `srt_list`：字幕文件列表，每个文件包含：
     - `file_name`：SRT 文件名
     - `time_offset`：起始偏移秒数，直接使用秒，不再按帧率时间码转换

2. 准备歌词文件：
   - 原歌词文件：`srts/编号.srt`
   - 翻译文件：`srts/编号_ts.srt`（可选）

3. 运行程序：
   ```
   python srt_tool.py
   ```

   自定义歌词目录：

   ```
   python srt_tool.py --srt-dir srts
   ```

4. 处理流程：
   - 读取 `configV2.json`
   - 对每个 `srts/编号.srt` 加载同目录下的 `srts/编号_ts.srt`
   - 当翻译歌词与原歌词的开始时间差不超过 1 秒，且时间重叠部分达到原歌词持续时间的 75% 及以上时，把翻译文本追加到原歌词下一行
   - 按 `time_offset` 重新偏移时间戳
   - 按配置顺序拼接为 `output.srt`
   - 如果下一句开始时间早于上一句结束时间，将下一句开始时间调整为上一句结束时间
   - 输出时清理行首角色标记，例如 `男：歌词` 输出为 `歌词`，单独的 `歌手：` 行会被删除

## 输出

处理后的文件：
- `output.srt`：翻译归并、偏移、拼接、重叠清洗后的最终字幕

### output.srt 拆分

将 `output.srt` 中每个字幕块的第一行和第二行分别输出为独立 SRT 文件：

```
python split_output_srt.py
```

默认输出：
- `output_line1.srt`：每个字幕块的第一行
- `output_line2.srt`：每个字幕块的第二行（没有第二行的字幕块会跳过）

自定义路径：

```
python split_output_srt.py --input output.srt --line1-output output_line1.srt --line2-output output_line2.srt
```

## 依赖

- Python 3.x
