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
   - 按开始时间的“分:秒”匹配翻译，把翻译文本追加到原歌词下一行
   - 按 `time_offset` 重新偏移时间戳
   - 按配置顺序拼接为 `output.srt`
   - 如果下一句开始时间早于上一句结束时间，将下一句开始时间调整为上一句结束时间

## 输出

处理后的文件：
- `output.srt`：翻译归并、偏移、拼接、重叠清洗后的最终字幕

## 依赖

- Python 3.x
