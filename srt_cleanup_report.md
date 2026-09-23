# SRT 歌词清洗记录（2026-09-22）

全部删除原文、修改前后对照、原编号和起止时间见 [已删除与已修改内容明细](srt_cleanup_changes.md)。

## 已完成的确定项

- 检查 `srts` 下 42 个不带 `_ts` 后缀的 SRT；修改 41 个，`28.srt` 无需修改。
- 删除 216 个非演唱字幕块：歌名/歌手标题、词曲与制作署名、版权声明、纯音乐标注、独立分唱人名。
- 从 `43.srt` 的 11 条歌词行首移除“男：/女：/合：”，保留后面的歌词。
- `49.srt` 原第 11 条（清理后第 7 条，00:00:51,214）：“你曾笑魇引蜂蝶” → “你曾笑靥引蜂蝶”。“靥”表示笑容/酒窝，“魇”表示梦魇，是明确的形近字误写。
- `2.srt`、`15.srt` 只有非演唱信息，现保留为 0 字节空文件。
- 保留 1,958 个歌词字幕块；修改过的文件重新连续编号，所有保留字幕的起止时间均未改变。
- 18 个 `_ts.srt` 文件 SHA-256 校验一致；括号内和声、哼唱、数拍和未能判定的念白保留。

## 待确认项（全部保留原文，尚未修改）

以下仅是疑点，不代表已认定原词错误。请按原版歌词或对应音频确认准确文字；尤其需要确认 `33.srt` 中引号内文句及结尾英语是否实际发声，以及其中念白是否应保留。本次未逐曲听音，不能保证识别仅存在于字幕而未被唱出的普通歌词。

| 文件 | 原编号 → 当前编号 | 歌曲内开始时间 | 原文 | 待确认原因 |
| --- | --- | --- | --- | --- |
| 16.srt | 10 → 6 | 00:00:34,993 | 边坚定来自于远方那坚定的信仰 | “边坚定来自于远方那坚定的信仰”语意可疑，无法确定是否漏字或误写。 |
| 16.srt | 19 → 15 | 00:00:56,941 | 屋檐那串轻脆的风铃 | “轻脆”疑为“清脆”，也可能是原词用字；未按常见搭配直接替换。 |
| 16.srt | 40 → 36 | 00:02:01,534 | 那串轻脆的风铃 | “轻脆”疑为“清脆”，也可能是原词用字；未按常见搭配直接替换。 |
| 16.srt | 20 → 16 | 00:01:00,208 | 许愿要找个流星幸福就要 | “许愿要找个流星幸福就要”及跨条分句可能存在听写或断句问题，需要听音确认。 |
| 16.srt | 41 → 37 | 00:02:04,220 | 许愿要找个流星幸福 | “许愿要找个流星幸福就要”及跨条分句可能存在听写或断句问题，需要听音确认。 |
| 16.srt | 42 → 38 | 00:02:05,945 | 就要彼此互相扶持互相关心 | “许愿要找个流星幸福就要”及跨条分句可能存在听写或断句问题，需要听音确认。 |
| 16.srt | 31 → 27 | 00:01:38,942 | 紧紧的相依的努力攀过吊桥绳索 | “紧紧的相依的努力…”、“真的快乐却是…”语序可疑，未进行语法润色。 |
| 16.srt | 37 → 33 | 00:01:54,533 | 真的快乐却是好多朋友 | “紧紧的相依的努力…”、“真的快乐却是…”语序可疑，未进行语法润色。 |
| 16.srt | 50 → 46 | 00:02:35,984 | 开着车遥远了回到最初的选择 | “开着车遥远了”语意可疑，需要确认实唱文字。 |
| 16.srt | 54 → 50 | 00:02:57,127 | 开着车遥远了回到最初的选择 | “开着车遥远了”语意可疑，需要确认实唱文字。 |
| 16.srt | 58 → 54 | 00:03:50,531 | 开着车遥远了回到最初的选择 | “开着车遥远了”语意可疑，需要确认实唱文字。 |
| 29.srt | 13 → 8 | 00:01:01,260 | 琢风骨 牵魂受魄 | “牵魂受魄”的“受”疑为“授”，但属于创作用词，暂不替换。 |
| 29.srt | 30 → 25 | 00:02:16,365 | 琢风骨 牵魂受魄 | “牵魂受魄”的“受”疑为“授”，但属于创作用词，暂不替换。 |
| 29.srt | 18 → 13 | 00:01:17,326 | 却因你 醉后抛了冰痕 | “抛了冰痕”可能涉及陶瓷意象或听写差异，无法确定替换词。 |
| 29.srt | 35 → 30 | 00:02:32,541 | 却因你 醉后抛了冰痕 | “抛了冰痕”可能涉及陶瓷意象或听写差异，无法确定替换词。 |
| 29.srt | 42 → 37 | 00:02:58,635 | 却因你 醉后抛了冰痕 | “抛了冰痕”可能涉及陶瓷意象或听写差异，无法确定替换词。 |
| 29.srt | 24 → 19 | 00:01:51,443 | 勘忍将月色空耗了 造作 | “勘忍”疑为“堪忍”，尚未找到足以确认原词的依据。 |
| 32.srt | 10 → 4 | 00:00:34,833 | 你笑你哭你的你憾你恨 | “你的你憾你恨”疑似多字或误字，需要原词/音频确认。 |
| 32.srt | 13 → 7 | 00:00:48,382 | 晕墨写到哪一段 溃不成痕 | “溃不成痕”、“痛无生”可能是创作用语或听写错误，暂不按常用词改写。 |
| 32.srt | 29 → 23 | 00:02:06,661 | 裂心剜骨切肤到 痛无生 | “溃不成痕”、“痛无生”可能是创作用语或听写错误，暂不按常用词改写。 |
| 32.srt | 23 → 17 | 00:01:27,074 | 不如我 陪你去 碧落黄昏 | “碧落黄昏”与常见“碧落黄泉”不同，不能仅按典故替换。 |
| 32.srt | 36 → 30 | 00:02:32,683 | 不如我 等你在 碧落黄昏 | “碧落黄昏”与常见“碧落黄泉”不同，不能仅按典故替换。 |
| 32.srt | 46 → 40 | 00:03:15,520 | 等着我 跟你去 碧落黄昏 | “碧落黄昏”与常见“碧落黄泉”不同，不能仅按典故替换。 |
| 32.srt | 37 → 31 | 00:02:40,385 | 此时此生 看镜断念 思念烧身 | “看镜断念”语意可疑，无法确认原词。 |
| 33.srt | 32 → 19 | 00:01:06,046 | 「就让死亡成为 一切的开始吧」 | 引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。 |
| 33.srt | 53 → 40 | 00:02:27,768 | 「救下那颗种子」 | 引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。 |
| 33.srt | 59 → 46 | 00:02:44,180 | 「带着你的光芒 再去试千万次」 | 引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。 |
| 33.srt | 66 → 53 | 00:03:03,868 | 「下一站将去往 最美的梦境里」 | 引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。 |
| 33.srt | 69 → 56 | 00:03:12,350 | Game Start | 引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。 |
| 33.srt | 70 → 57 | 00:03:12,774 | 「Good Night」 | 引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。 |
| 34.srt | 13 → 7 | 00:00:26,818 | 万象宾客悠闲自流 | “万象宾客悠闲自流”、“嘲人陈规墨守”、“这固有”、“扶将座”、“关解国愁”等存在用字疑点；第三方歌词也有同样写法，不能据此自行改词。 |
| 34.srt | 14 → 8 | 00:00:29,277 | 俯仰间 嘲人陈规墨守 | “万象宾客悠闲自流”、“嘲人陈规墨守”、“这固有”、“扶将座”、“关解国愁”等存在用字疑点；第三方歌词也有同样写法，不能据此自行改词。 |
| 34.srt | 17 → 11 | 00:00:39,690 | 这固有 从未写入某一卷书 | “万象宾客悠闲自流”、“嘲人陈规墨守”、“这固有”、“扶将座”、“关解国愁”等存在用字疑点；第三方歌词也有同样写法，不能据此自行改词。 |
| 34.srt | 30 → 24 | 00:01:23,693 | 历来万骨扶将座 | “万象宾客悠闲自流”、“嘲人陈规墨守”、“这固有”、“扶将座”、“关解国愁”等存在用字疑点；第三方歌词也有同样写法，不能据此自行改词。 |
| 34.srt | 31 → 25 | 00:01:25,707 | 愿奉寒江关解国愁 | “万象宾客悠闲自流”、“嘲人陈规墨守”、“这固有”、“扶将座”、“关解国愁”等存在用字疑点；第三方歌词也有同样写法，不能据此自行改词。 |
| 49.srt | 9 → 5 | 00:00:44,190 | 少时好游鸿固原 | “鸿固原”、“古上原”、“少陵园”涉及专名或历史意象，未按常见地名替换。 |
| 49.srt | 25 → 21 | 00:02:06,636 | 老时再游鸿固原 | “鸿固原”、“古上原”、“少陵园”涉及专名或历史意象，未按常见地名替换。 |
| 49.srt | 32 → 28 | 00:02:29,834 | 魂消古上原 | “鸿固原”、“古上原”、“少陵园”涉及专名或历史意象，未按常见地名替换。 |
| 49.srt | 40 → 36 | 00:02:57,242 | 情锁少陵园 | “鸿固原”、“古上原”、“少陵园”涉及专名或历史意象，未按常见地名替换。 |
| 52.srt | 2 → 1 | 00:00:52,610 | Welcome to the broken low | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 3 → 2 | 00:00:54,207 | Welcome to the famous disco live | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 5 → 4 | 00:01:00,907 | Come on lady get me once and right | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 11 → 10 | 00:01:13,063 | Speak if it you know how | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 15 → 14 | 00:01:19,708 | You've better better stay | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 16 → 15 | 00:01:21,188 | You've better better begin | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 17 → 16 | 00:01:22,263 | The prayer to play | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 23 → 22 | 00:01:32,039 | You've better better stay | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 24 → 23 | 00:01:33,586 | You've better better begin | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 25 → 24 | 00:01:35,048 | The prayer to play | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 40 → 39 | 00:02:14,990 | Speak if it you know how | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 44 → 43 | 00:02:21,553 | You've better better stay | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 45 → 44 | 00:02:23,081 | You've better better begin | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 46 → 45 | 00:02:24,325 | The prayer to play | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 52 → 51 | 00:02:33,868 | You've better better stay | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 53 → 52 | 00:02:35,396 | You've better better begin | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 54 → 53 | 00:02:36,607 | The prayer to play | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 61 → 60 | 00:03:14,029 | The prayer to play | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 65 → 64 | 00:03:24,898 | You've better better begin | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 69 → 68 | 00:04:10,866 | Welcome to the broken low | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 70 → 69 | 00:04:12,576 | Welcome to the famous disco live | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 72 → 71 | 00:04:18,767 | Come on lady get me once and right | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 52.srt | 78 → 77 | 00:04:30,922 | Speak if it you know how | broken low / disco live / once and right / Speak if it / You've better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。 |
| 54.srt | 3 → 1 | 00:00:42,618 | I'll always follow you me by your side | “follow you me by your side”、“I can't you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。 |
| 54.srt | 10 → 8 | 00:01:11,863 | Woooo I can't you see as a friend | “follow you me by your side”、“I can't you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。 |
| 54.srt | 13 → 11 | 00:01:24,299 | Woooo I can't you see as a friend | “follow you me by your side”、“I can't you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。 |
| 54.srt | 22 → 20 | 00:02:16,106 | Woooo I can't you see as a friend | “follow you me by your side”、“I can't you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。 |
| 54.srt | 28 → 26 | 00:03:03,799 | I'll always follow you me by your side | “follow you me by your side”、“I can't you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。 |
| 54.srt | 33 → 31 | 00:03:32,981 | Woooo I can't you see as a friend | “follow you me by your side”、“I can't you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。 |
| 46.srt | 21 → 18 | 00:01:30,838 | Have I still been cared | Have I still been cared / No much time / You're who make my makeup's off / You do never know 等非标准英语可能是原歌词，暂不润色。 |
| 46.srt | 23 → 20 | 00:01:35,804 | No much time talking over day and night | Have I still been cared / No much time / You're who make my makeup's off / You do never know 等非标准英语可能是原歌词，暂不润色。 |
| 46.srt | 30 → 27 | 00:02:05,518 | You're who make my makeup's off | Have I still been cared / No much time / You're who make my makeup's off / You do never know 等非标准英语可能是原歌词，暂不润色。 |
| 46.srt | 34 → 31 | 00:02:17,764 | You do never know that love I felt | Have I still been cared / No much time / You're who make my makeup's off / You do never know 等非标准英语可能是原歌词，暂不润色。 |

## 核对参考

以下网页仅用于对照；转载相同文字不等于证明其正确，未据此替换有歧义的歌词。

- [《亲爱的》对照页面](https://www.pythonke.com/songs/panweibo-6214.html)：也出现“轻脆”和“开着车遥远了”，疑点保留。
- [Shazam《别寒江》](https://www.shazam.com/track/621561972/%E5%88%AB%E5%AF%92%E6%B1%9F)：也出现上述疑似误写，保留原文等待确认。
- [Crazy Little Love 对照页面](https://www.vagalume.com.br/initial-d/nuage-crazy-little-love.html)：也有相同的英语语序，未凭语法改词。

## 备份与核验

- 原始 42 个目标文件：`.srt-cleanup-backups/20260922-145423/originals/`（逐字节备份）。
- 每条删除/修改的原编号、时间、前后文本：`.srt-cleanup-backups/20260922-145423/changes.json`。
- 文件汇总及原始 SHA-256：`.srt-cleanup-backups/20260922-145423/summary.json`。
- 翻译文件 SHA-256：`.srt-cleanup-backups/20260922-145423/translation-hashes.json`。
- 已逐条核验清理结果与计划一致，保留字幕的时间戳、顺序和未批准修改的歌词文本一致，非空文件编号连续。

## 文件统计

| 文件 | 清理前条数 | 删除条数 | 行内修改条数 | 清理后条数 |
| --- | ---: | ---: | ---: | ---: |
| 1.srt | 53 | 6 | 0 | 47 |
| 2.srt | 4 | 4 | 0 | 0 |
| 3.srt | 66 | 20 | 0 | 46 |
| 5.srt | 87 | 2 | 0 | 85 |
| 7.srt | 55 | 3 | 0 | 52 |
| 9.srt | 102 | 3 | 0 | 99 |
| 10.srt | 92 | 4 | 0 | 88 |
| 11.srt | 52 | 4 | 0 | 48 |
| 12.srt | 58 | 4 | 0 | 54 |
| 13.srt | 60 | 1 | 0 | 59 |
| 14.srt | 76 | 3 | 0 | 73 |
| 15.srt | 3 | 3 | 0 | 0 |
| 16.srt | 58 | 4 | 0 | 54 |
| 18.srt | 37 | 4 | 0 | 33 |
| 19.srt | 52 | 4 | 0 | 48 |
| 20.srt | 41 | 4 | 0 | 37 |
| 21.srt | 44 | 8 | 0 | 36 |
| 22.srt | 44 | 7 | 0 | 37 |
| 23.srt | 56 | 11 | 0 | 45 |
| 24.srt | 35 | 3 | 0 | 32 |
| 25.srt | 64 | 5 | 0 | 59 |
| 26.srt | 78 | 28 | 0 | 50 |
| 28.srt | 28 | 0 | 0 | 28 |
| 29.srt | 49 | 5 | 0 | 44 |
| 32.srt | 46 | 6 | 0 | 40 |
| 33.srt | 70 | 13 | 0 | 57 |
| 34.srt | 63 | 6 | 0 | 57 |
| 35.srt | 21 | 3 | 0 | 18 |
| 38.srt | 9 | 3 | 0 | 6 |
| 41.srt | 65 | 15 | 0 | 50 |
| 42.srt | 27 | 3 | 0 | 24 |
| 43.srt | 22 | 0 | 11 | 22 |
| 44.srt | 43 | 3 | 0 | 40 |
| 45.srt | 40 | 3 | 0 | 37 |
| 46.srt | 54 | 3 | 0 | 51 |
| 47.srt | 67 | 1 | 0 | 66 |
| 48.srt | 28 | 3 | 0 | 25 |
| 49.srt | 44 | 4 | 1 | 40 |
| 51.srt | 59 | 4 | 0 | 55 |
| 52.srt | 83 | 1 | 0 | 82 |
| 53.srt | 101 | 3 | 0 | 98 |
| 54.srt | 38 | 2 | 0 | 36 |
