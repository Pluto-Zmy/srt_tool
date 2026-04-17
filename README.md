# SRT 字幕处理工具

用于处理和合并 SRT 字幕文件的工具。

## 功能

- 编码转换：将 GB18030 编码的 SRT 文件转换为 UTF-8
- 时间轴合并：将 TS 时间轴文件与 SRT 字幕合并
- 时间偏移：调整字幕时间轴偏移
- 字幕拼接：合并多个 SRT 文件

## 使用方法

1. 修改 `config.json` 配置：
   - `base_fps`：基准帧率（默认 60）
   - `srt_list`：字幕文件列表，每个文件包含：
     - `file_name`：SRT 文件名
     - `ts_file_name`：TS 时间轴文件（可选）
     - `time_code`：起始时间码

2. 运行程序：
   ```
   python srt_tool.py
   ```

## 输出

处理后的文件：
- `*_utf8.srt`：UTF-8 编码的字幕
- `*_merge.srt`：合并时间轴后的字幕
- `*_offset.srt`：调整偏移后的字幕

最终合并结果输出到 `output.srt`。

## 依赖

- Python 3.x
