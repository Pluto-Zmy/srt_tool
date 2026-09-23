$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$backup = Join-Path $root '.srt-cleanup-backups/20260922-145423'
$summary = Get-Content -LiteralPath (Join-Path $backup 'summary.json') -Raw | ConvertFrom-Json
$changes = Get-Content -LiteralPath (Join-Path $backup 'changes.json') -Raw | ConvertFrom-Json
$issues = @(
    @{File=16;Ids=@(10);Note='“边坚定来自于远方那坚定的信仰”语意可疑，无法确定是否漏字或误写。'},
    @{File=16;Ids=@(19,40);Note='“轻脆”疑为“清脆”，也可能是原词用字；未按常见搭配直接替换。'},
    @{File=16;Ids=@(20,41,42);Note='“许愿要找个流星幸福就要”及跨条分句可能存在听写或断句问题，需要听音确认。'},
    @{File=16;Ids=@(31,37);Note='“紧紧的相依的努力…”、“真的快乐却是…”语序可疑，未进行语法润色。'},
    @{File=16;Ids=@(50,54,58);Note='“开着车遥远了”语意可疑，需要确认实唱文字。'},
    @{File=29;Ids=@(13,30);Note='“牵魂受魄”的“受”疑为“授”，但属于创作用词，暂不替换。'},
    @{File=29;Ids=@(18,35,42);Note='“抛了冰痕”可能涉及陶瓷意象或听写差异，无法确定替换词。'},
    @{File=29;Ids=@(24);Note='“勘忍”疑为“堪忍”，尚未找到足以确认原词的依据。'},
    @{File=32;Ids=@(10);Note='“你的你憾你恨”疑似多字或误字，需要原词/音频确认。'},
    @{File=32;Ids=@(13,29);Note='“溃不成痕”、“痛无生”可能是创作用语或听写错误，暂不按常用词改写。'},
    @{File=32;Ids=@(23,36,46);Note='“碧落黄昏”与常见“碧落黄泉”不同，不能仅按典故替换。'},
    @{File=32;Ids=@(37);Note='“看镜断念”语意可疑，无法确认原词。'},
    @{File=33;Ids=@(32,53,59,66,69,70);Note='引号内的平行文句、Game Start / Good Night 可能是和声、念白、音效台词或仅用于展示的文字；无对应音频，无法判定是否应删除。'},
    @{File=34;Ids=@(13,14,17,30,31);Note='“万象宾客悠闲自流”、“嘲人陈规墨守”、“这固有”、“扶将座”、“关解国愁”等存在用字疑点；第三方歌词也有同样写法，不能据此自行改词。'},
    @{File=49;Ids=@(9,25,32,40);Note='“鸿固原”、“古上原”、“少陵园”涉及专名或历史意象，未按常见地名替换。'},
    @{File=52;Ids=@(2,3,5,11,15,16,17,23,24,25,40,44,45,46,52,53,54,61,65,69,70,72,78);Note='broken low / disco live / once and right / Speak if it / You''ve better / prayer to play 等搭配可疑，可能属于原曲非标准英语或听写差异，未按英语语法重写。'},
    @{File=54;Ids=@(3,10,13,22,28,33);Note='“follow you me by your side”、“I can''t you see as a friend”语序可疑，不能仅凭语法确认实际演唱内容。'},
    @{File=46;Ids=@(21,23,30,34);Note='Have I still been cared / No much time / You''re who make my makeup''s off / You do never know 等非标准英语可能是原歌词，暂不润色。'}
)
$report = [Collections.Generic.List[string]]::new()
$report.Add('# SRT 歌词清洗记录（2026-09-22）')
$report.Add('')
$report.Add('## 已完成的确定项')
$report.Add('')
$report.Add('- 检查 `srts` 下 42 个不带 `_ts` 后缀的 SRT；修改 41 个，`28.srt` 无需修改。')
$report.Add('- 删除 216 个非演唱字幕块：歌名/歌手标题、词曲与制作署名、版权声明、纯音乐标注、独立分唱人名。')
$report.Add('- 从 `43.srt` 的 11 条歌词行首移除“男：/女：/合：”，保留后面的歌词。')
$report.Add('- `49.srt` 原第 11 条（清理后第 7 条，00:00:51,214）：“你曾笑魇引蜂蝶” → “你曾笑靥引蜂蝶”。“靥”表示笑容/酒窝，“魇”表示梦魇，是明确的形近字误写。')
$report.Add('- `2.srt`、`15.srt` 只有非演唱信息，现保留为 0 字节空文件。')
$report.Add('- 保留 1,958 个歌词字幕块；修改过的文件重新连续编号，所有保留字幕的起止时间均未改变。')
$report.Add('- 18 个 `_ts.srt` 文件 SHA-256 校验一致；括号内和声、哼唱、数拍和未能判定的念白保留。')
$report.Add('')
$report.Add('## 待确认项（全部保留原文，尚未修改）')
$report.Add('')
$report.Add('以下仅是疑点，不代表已认定原词错误。请按原版歌词或对应音频确认准确文字；尤其需要确认 `33.srt` 中引号内文句及结尾英语是否实际发声，以及其中念白是否应保留。本次未逐曲听音，不能保证识别仅存在于字幕而未被唱出的普通歌词。')
$report.Add('')
$report.Add('| 文件 | 原编号 → 当前编号 | 歌曲内开始时间 | 原文 | 待确认原因 |')
$report.Add('| --- | --- | --- | --- | --- |')
foreach ($issue in $issues) {
    $name = [string]$issue.File + '.srt'
    $blocks = ([IO.File]::ReadAllText((Join-Path (Join-Path $backup 'originals') $name))).Trim() -split '\r?\n\s*\r?\n'
    $removedIds = @($changes | Where-Object {$_.File -eq $name -and $_.Action -eq 'remove'} | ForEach-Object {$_.OriginalCue})
    foreach ($id in $issue.Ids) {
        $parts = $blocks[$id-1] -split '\r?\n'
        $newId = $id - @($removedIds | Where-Object {$_ -lt $id}).Count
        $text = $parts[2].Replace('|','\|')
        $report.Add('| '+$name+' | '+$id+' → '+$newId+' | '+($parts[1] -split ' --> ')[0]+' | '+$text+' | '+$issue.Note+' |')
    }
}
$report.Add('')
$report.Add('## 核对参考')
$report.Add('')
$report.Add('以下网页仅用于对照；转载相同文字不等于证明其正确，未据此替换有歧义的歌词。')
$report.Add('')
$report.Add('- [《亲爱的》对照页面](https://www.pythonke.com/songs/panweibo-6214.html)：也出现“轻脆”和“开着车遥远了”，疑点保留。')
$report.Add('- [Shazam《别寒江》](https://www.shazam.com/track/621561972/%E5%88%AB%E5%AF%92%E6%B1%9F)：也出现上述疑似误写，保留原文等待确认。')
$report.Add('- [Crazy Little Love 对照页面](https://www.vagalume.com.br/initial-d/nuage-crazy-little-love.html)：也有相同的英语语序，未凭语法改词。')
$report.Add('')
$report.Add('## 备份与核验')
$report.Add('')
$report.Add('- 原始 42 个目标文件：`.srt-cleanup-backups/20260922-145423/originals/`（逐字节备份）。')
$report.Add('- 每条删除/修改的原编号、时间、前后文本：`.srt-cleanup-backups/20260922-145423/changes.json`。')
$report.Add('- 文件汇总及原始 SHA-256：`.srt-cleanup-backups/20260922-145423/summary.json`。')
$report.Add('- 翻译文件 SHA-256：`.srt-cleanup-backups/20260922-145423/translation-hashes.json`。')
$report.Add('- 已逐条核验清理结果与计划一致，保留字幕的时间戳、顺序和未批准修改的歌词文本一致，非空文件编号连续。')
$report.Add('')
$report.Add('## 文件统计')
$report.Add('')
$report.Add('| 文件 | 清理前条数 | 删除条数 | 行内修改条数 | 清理后条数 |')
$report.Add('| --- | ---: | ---: | ---: | ---: |')
foreach ($s in $summary) { $report.Add('| '+$s.File+' | '+$s.BeforeCount+' | '+$s.Removed+' | '+$s.Edited+' | '+$s.AfterCount+' |') }
[IO.File]::WriteAllText((Join-Path $root 'srt_cleanup_report.md'),($report -join "`n")+"`n",[Text.UTF8Encoding]::new($false))
