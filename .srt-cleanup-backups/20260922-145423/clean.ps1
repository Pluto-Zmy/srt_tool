$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$backup = Join-Path $root '.srt-cleanup-backups/20260922-145423'
$originals = Join-Path $backup 'originals'
if (Test-Path -LiteralPath $originals) { throw 'Backup already exists; do not rerun.' }
$null = New-Item -ItemType Directory -Path $originals
$heads = @{1=6;2=4;3=19;5=2;7=3;9=3;10=4;11=4;12=4;13=1;14=3;15=3;16=4;18=4;19=4;20=4;21=8;22=7;23=11;24=3;25=5;26=14;28=0;29=5;32=6;33=13;34=6;35=3;38=3;41=4;42=3;43=0;44=3;45=3;46=3;47=1;48=3;49=4;51=4;52=1;53=3;54=2}
$extras = @{3=@(66);26=@(15,17,19,22,24,26,28,30,32,48,50,52,54,56);41=@(5,9,14,19,23,28,36,41,45,62,64)}
$tsHashes = @(Get-ChildItem -LiteralPath (Join-Path $root 'srts') -Filter '*_ts.srt' | ForEach-Object { [pscustomobject]@{Path=$_.FullName;Hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} })
$files = @(Get-ChildItem -LiteralPath (Join-Path $root 'srts') -Filter '*.srt' | Where-Object {$_.BaseName -notmatch '_ts$'} | Sort-Object {[int]$_.BaseName})
if ($files.Count -ne 42) { throw 'Unexpected target file count.' }
$plans = @()
$changes = @()
foreach ($file in $files) {
    $number = [int]$file.BaseName
    if (-not $heads.ContainsKey($number)) { throw "Unreviewed file: $file" }
    $bytes = [IO.File]::ReadAllBytes($file.FullName)
    $hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191
    $raw = [Text.UTF8Encoding]::new($false,$true).GetString($bytes).TrimStart([char]0xfeff)
    $newline = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
    $blocks = @($raw.Trim() -split '\r?\n\s*\r?\n')
    $kept = @()
    $removed = 0
    $edited = 0
    for ($i=0; $i -lt $blocks.Count; $i++) {
        $lines = @($blocks[$i] -split '\r?\n')
        if ($lines.Count -ne 3 -or [int]$lines[0] -ne ($i+1) -or $lines[1] -notmatch '^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$') { throw "Unexpected structure: $file block $i" }
        $id = [int]$lines[0]
        $text = $lines[2]
        if ($id -le $heads[$number] -or ($extras.ContainsKey($number) -and $id -in $extras[$number])) {
            $changes += [pscustomobject]@{File=$file.Name;OriginalCue=$id;Time=$lines[1];Action='remove';Before=$text;After=''}
            $removed++
            continue
        }
        $clean = $text
        if ($number -eq 43) { $clean = $clean -replace '^(男|女|合)：','' }
        if ($number -eq 49 -and $id -eq 11) {
            if ($clean -cne '你曾笑魇引蜂蝶') { throw 'Unexpected typo context.' }
            $clean = '你曾笑靥引蜂蝶'
        }
        if ($clean -cne $text) {
            $changes += [pscustomobject]@{File=$file.Name;OriginalCue=$id;Time=$lines[1];Action='edit';Before=$text;After=$clean}
            $edited++
        }
        $kept += [pscustomobject]@{OriginalCue=$id;Time=$lines[1];Text=$clean}
    }
    $changed = ($removed+$edited) -gt 0
    $out = if ($kept.Count -eq 0) { '' } else {
        $outBlocks = for ($j=0; $j -lt $kept.Count; $j++) { @([string]($j+1),$kept[$j].Time,$kept[$j].Text) -join $newline }
        ($outBlocks -join ($newline+$newline))+$newline+$newline
    }
    $plans += [pscustomobject]@{File=$file.Name;Path=$file.FullName;BeforeHash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash;BeforeCount=$blocks.Count;Removed=$removed;Edited=$edited;AfterCount=$kept.Count;Changed=$changed;HasBom=$hasBom;Output=$out;Kept=$kept}
    [IO.File]::WriteAllBytes((Join-Path $originals $file.Name),$bytes)
}
# Write only after every original has been backed up and every cue has been validated.
foreach ($plan in $plans) {
    if ((Get-FileHash -LiteralPath $plan.Path -Algorithm SHA256).Hash -ne $plan.BeforeHash) { throw "Concurrent change: $($plan.File)" }
}
foreach ($plan in $plans) {
    if ($plan.Changed) {
        if ($plan.AfterCount -eq 0) { [IO.File]::WriteAllBytes($plan.Path,[byte[]]@()) }
        else { [IO.File]::WriteAllText($plan.Path,$plan.Output,[Text.UTF8Encoding]::new($plan.HasBom)) }
    }
}
# Check every retained cue, including its exact original timestamp and approved text.
foreach ($plan in $plans) {
    $actual = [IO.File]::ReadAllText($plan.Path)
    if ($plan.Changed -and $actual -cne $plan.Output) { throw "Output mismatch: $($plan.File)" }
    if (-not $plan.Changed -and (Get-FileHash -LiteralPath $plan.Path -Algorithm SHA256).Hash -ne $plan.BeforeHash) { throw 'Unchanged file modified.' }
    if ($plan.AfterCount -gt 0) {
        $afterBlocks = @($actual.Trim() -split '\r?\n\s*\r?\n')
        if ($afterBlocks.Count -ne $plan.AfterCount) { throw 'Cue count mismatch.' }
        for ($j=0; $j -lt $afterBlocks.Count; $j++) {
            $parts = @($afterBlocks[$j] -split '\r?\n')
            if ([int]$parts[0] -ne ($j+1) -or $parts[1] -cne $plan.Kept[$j].Time -or $parts[2] -cne $plan.Kept[$j].Text) { throw 'Retained cue mismatch.' }
        }
    }
}
foreach ($ts in $tsHashes) {
    if ((Get-FileHash -LiteralPath $ts.Path -Algorithm SHA256).Hash -ne $ts.Hash) { throw "Translation modified: $($ts.Path)" }
}
$changes | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backup 'changes.json') -Encoding utf8
$plans | Select-Object File,BeforeHash,BeforeCount,Removed,Edited,AfterCount,Changed | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backup 'summary.json') -Encoding utf8
$tsHashes | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backup 'translation-hashes.json') -Encoding utf8
$plans | Select-Object File,BeforeCount,Removed,Edited,AfterCount,Changed | Format-Table -AutoSize
[pscustomobject]@{Checked=$files.Count;Changed=@($plans | Where-Object Changed).Count;Removed=($plans | Measure-Object Removed -Sum).Sum;Edited=($plans | Measure-Object Edited -Sum).Sum;Retained=($plans | Measure-Object AfterCount -Sum).Sum;TranslationsUnchanged=$tsHashes.Count;Backup=$originals} | ConvertTo-Json
